# modelo para sincronizar datos entre Odoo y otras plataformas
# tiene los siguientes campos:
# - nombre
# - descripcion
# - fecha de creacion
# - estado de la sincronizacion
# - mensaje de la sincronizacion
# - datos de la sincronizacion
# - destino (jugadores,equipos)
# - origen (del modelo syncronizer_origen)

from odoo import models, fields, api
import requests
import time
import base64
from datetime import datetime
import threading
import logging

_logger = logging.getLogger(__name__)


class SofterSyncronizer(models.Model):
    _name = "softer.syncronizer"
    _description = "Sincronizador"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(string="Nombre", required=True)
    origen_id = fields.Many2one(
        "softer.syncronizer.origen",
        string="Origen",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    destino_id = fields.Many2one(
        "softer.syncronizer.destino",
        string="Destino",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    active = fields.Boolean(default=True, string="Activo", tracking=True)
    description = fields.Text(string="Descripción", tracking=True)
    create_date = fields.Datetime(
        string="Fecha de Creación", readonly=True, default=fields.Datetime.now
    )
    last_sync_date = fields.Datetime(
        string="Última Sincronización", readonly=True, tracking=True
    )
    next_sync_date = fields.Datetime(string="Próxima Sincronización", tracking=True)
    sync_interval = fields.Selection(
        [
            ("manual", "Manual"),
            ("hourly", "Cada hora"),
            ("daily", "Diario"),
            ("weekly", "Semanal"),
            ("monthly", "Mensual"),
        ],
        string="Intervalo de Sincronización",
        default="manual",
        required=True,
        tracking=True,
    )
    resultado_ids = fields.One2many(
        "softer.syncronizer.resultados",
        "sincronizador_id",
        string="Resultados",
        tracking=True,
    )

    def _prepare_request_headers(self):
        """Prepara los headers para la petición según el tipo de autenticación"""
        headers = {
            "Content-Type": "application/json",
        }

        if self.origen_id.auth_type == "basic":
            headers["Authorization"] = (
                f"Basic {base64.b64encode(f'{self.origen_id.auth_user}:{self.origen_id.auth_password}'.encode()).decode()}"
            )
        elif self.origen_id.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.origen_id.auth_token}"
        elif self.origen_id.auth_type == "header":
            headers[self.origen_id.auth_header] = self.origen_id.auth_token

        return headers

    def _prepare_request_params(self):
        """Prepara los parámetros para la petición"""
        params = {}
        for param in self.origen_id.param_ids:
            if param.active:
                params[param.name] = param.value
        return params

    def _check_task_status(self, task_id, resultado):
        """Verifica el estado de la tarea y espera hasta que esté completada"""
        start_time = time.time()
        while True:
            try:
                # Verificar si se ha excedido el timeout
                print("CHEQUEANDO TAREA")
                if time.time() - start_time > self.origen_id.task_timeout:
                    raise Exception(
                        f"Timeout esperando la finalización de la tarea {self.origen_id.task_timeout}"
                    )

                # Reemplazar {taskId} en la URL de status
                status_url = self.origen_id.task_status_url.replace("{taskId}", task_id)
                response = requests.get(
                    status_url, headers=self._prepare_request_headers(), timeout=30
                )
                response.raise_for_status()
                status_data = response.json()

                # Verificar el estado de la tarea
                task_status = status_data.get("status")
                if task_status == "COMPLETED":
                    return True
                elif task_status == "ERROR":
                    error_msg = status_data.get("error", "Error desconocido")
                    raise Exception(f"Tarea fallida: {error_msg}")
                elif task_status in ["PENDING", "PROCESSING"]:
                    # Actualizar el mensaje con el estado actual
                    resultado.write(
                        {
                            "mensaje": f"Estado de la tarea: {task_status}",
                            "detalles": f"Tipo: {status_data.get('type', 'N/A')}\n"
                            f"Creada: {status_data.get('created_at', 'N/A')}\n"
                            f"Completada: {status_data.get('completed_at', 'N/A')}",
                        }
                    )
                else:
                    raise Exception(f"Estado de tarea desconocido: {task_status}")

                # Esperar el intervalo configurado antes de la siguiente verificación
                time.sleep(self.origen_id.task_interval)

            except requests.exceptions.RequestException as e:
                raise Exception(f"Error al verificar el estado de la tarea: {str(e)}")

    def _download_and_save_result(self, resultado):
        """Descarga y guarda el resultado de la sincronización"""
        try:
            # Reemplazar {taskId} en la URL de resultados
            results_url = self.origen_id.urlResultados.replace(
                "{taskId}", resultado.taskId
            )
            print(f"DESCARGANDO RESULTADO {results_url}")
            response = requests.get(
                results_url, headers=self._prepare_request_headers(), timeout=30
            )
            response.raise_for_status()
            print(f"RESULTADO DESCARGADO {results_url}")
            print(f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            # Guardar el resultado
            resultado.write(
                {
                    "archivo": base64.b64encode(response.content),
                    "nombre_archivo": f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                }
            )

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al descargar el resultado: {str(e)}")

    def _thread_sync(self, dbname, uid, sync_id, resultado_id, task_id):
        """Método que se ejecuta en el hilo separado"""
        # Crear nuevo cursor y environment para este hilo
        registry = api.Registry(dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, uid, {})

            try:
                # Obtener los registros con el nuevo cursor
                syncronizer = env["softer.syncronizer"].browse(sync_id)
                resultado = env["softer.syncronizer.resultados"].browse(resultado_id)

                # Marcar como iniciado
                resultado.write(
                    {"estado": "working", "mensaje": "Procesando sincronización"}
                )
                cr.commit()

                # Esperar y verificar el estado de la tarea
                print("ESPERANDO Y VERIFICANDO EL ESTADO DE LA TAREA")
                syncronizer._check_task_status(task_id, resultado)
                cr.commit()

                # Descargar y guardar el resultado
                print("DESCARGANDO Y GUARDANDO EL RESULTADO")
                syncronizer._download_and_save_result(resultado)
                cr.commit()

                # Actualizar el estado final
                print("ACTUALIZANDO EL ESTADO FINAL")
                syncronizer.write(
                    {
                        "last_sync_date": fields.Datetime.now(),
                    }
                )
                cr.commit()

                # Actualizar el estado del resultado a completado
                resultado.write(
                    {
                        "estado": "extract",
                        "mensaje": "Sincronización completada exitosamente",
                    }
                )
                cr.commit()

                print("ACTUALIZACION FINALIZADA")
                return True

            except Exception as e:
                _logger.error("Error en el hilo de sincronización: %s", str(e))
                # Manejar errores
                resultado.write(
                    {
                        "estado": "error",
                        "mensaje": f"Error durante la sincronización: {str(e)}",
                        "registros_procesados": 0,
                        "registros_exitosos": 0,
                        "registros_fallidos": 1,
                        "detalles": str(e),
                    }
                )
                cr.commit()
                raise

    def sync_with_task(self):
        """Ejecuta la sincronización con tarea asíncrona"""
        try:
            headers = self._prepare_request_headers()
            params = self._prepare_request_params()

            # Usar el método HTTP configurado
            print(f"URL: {self.origen_id.url} method {self.origen_id.method}")
            if self.origen_id.method == "post":
                response = requests.post(
                    self.origen_id.url, headers=headers, json=params, timeout=30
                )
            else:  # GET
                response = requests.get(
                    self.origen_id.url, headers=headers, params=params, timeout=30
                )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Error en la respuesta inicial: {data.get('message')}")

            task_id = data.get("task_id")
            if not task_id:
                raise Exception("No se recibió task_id en la respuesta")

            # Obtener el último resultado creado
            resultado = self.env["softer.syncronizer.resultados"].search(
                [("sincronizador_id", "=", self.id)], order="create_date desc", limit=1
            )

            if not resultado:
                raise Exception("No se encontró el registro de resultado")

            # Actualizar el resultado con el task_id
            resultado.write(
                {
                    "taskId": task_id,
                    "mensaje": "Iniciando sincronización en segundo plano",
                }
            )
            self.env.cr.commit()

            # Crear un nuevo hilo con una nueva conexión a la BD
            thread = threading.Thread(
                target=self._thread_sync,
                args=(self.env.cr.dbname, self.env.uid, self.id, resultado.id, task_id),
            )
            thread.daemon = True
            thread.start()

        except Exception as e:
            _logger.error("Error al iniciar la sincronización: %s", str(e))
            if "resultado" in locals():
                resultado.write(
                    {
                        "estado": "error",
                        "mensaje": f"Error durante la sincronización: {str(e)}",
                        "registros_procesados": 0,
                        "registros_exitosos": 0,
                        "registros_fallidos": 1,
                        "detalles": str(e),
                    }
                )

    def action_run_sync(self):
        """Ejecuta la sincronización según el tipo de origen"""
        if self.origen_id.esConTask:
            # Crear el resultado antes de iniciar la sincronización
            self.env["softer.syncronizer.resultados"].create(
                {
                    "name": f"Sincronización {self.name} - {fields.Datetime.now()}",
                    "sincronizador_id": self.id,
                    "fecha_sincronizacion": fields.Datetime.now(),
                    "estado": "pending",
                    "mensaje": "Iniciando sincronización en segundo plano",
                }
            )

            # Iniciar la sincronización en segundo plano
            self.sync_with_task()

            # Mostrar mensaje al usuario y abrir el registro de resultado
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Sincronización iniciada",
                    "message": "La sincronización se está ejecutando en segundo plano. Puede seguir el progreso en el registro de resultados.",
                    "type": "info",
                    "sticky": False,
                    # "next": {
                    #     "type": "ir.actions.act_window",
                    #     "res_model": "softer.syncronizer.resultados",
                    #     "res_id": resultado.id,
                    #     "view_mode": "form",
                    #     "target": "current",
                    # },
                },
            }
        else:
            try:
                # TODO: Implementar lógica de sincronización directa
                self.write(
                    {
                        "last_sync_date": fields.Datetime.now(),
                    }
                )
                return True
            except Exception as e:
                _logger.error("Error en la sincronización directa: %s", str(e))
                return False
