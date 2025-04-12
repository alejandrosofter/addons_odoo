from odoo import models, fields, api
import base64
import json
import logging
import re

_logger = logging.getLogger(__name__)


class SofterSyncronizerResultados(models.Model):
    _name = "softer.syncronizer.resultados"
    _description = "Resultados de Sincronización"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_sincronizacion desc"

    name = fields.Char(
        string="Nombre",
        required=True,
        default=lambda self: "Nuevo Resultado",
        tracking=True,
    )
    sincronizador_id = fields.Many2one(
        "softer.syncronizer",
        string="Sincronizador",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    fecha_sincronizacion = fields.Datetime(
        string="Fecha de Sincronización",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("success", "Exitoso"),
            ("error", "Error"),
            ("warning", "Advertencia"),
            ("working", "Trabajando"),
            ("pending", "Pendiente"),
            ("extract", "Extraido"),
        ],
        string="Estado",
        required=True,
        default="success",
        tracking=True,
    )
    mensaje = fields.Text(
        string="Mensaje",
        tracking=True,
    )
    registros_procesados = fields.Integer(
        string="Registros Procesados",
        default=0,
        tracking=True,
    )
    registros_exitosos = fields.Integer(
        string="Registros Exitosos",
        default=0,
        tracking=True,
    )
    registros_fallidos = fields.Integer(
        string="Registros Fallidos",
        default=0,
        tracking=True,
    )
    detalles = fields.Text(
        string="Detalles",
        tracking=True,
    )
    archivo = fields.Binary(
        string="Archivo de Resultados",
        attachment=True,
        tracking=False,
    )
    nombre_archivo = fields.Char(
        string="Nombre del Archivo",
        tracking=True,
    )
    taskId = fields.Char(string="ID de Tarea", tracking=True)
    nro_registro_actual = fields.Integer(
        string="Registro Actual",
        default=0,
        help="Número del registro que se está procesando actualmente",
        tracking=True,
    )
    total_registros = fields.Integer(
        string="Total de Registros",
        default=0,
        help="Total de registros a procesar",
        tracking=True,
    )
    clave_busqueda = fields.Char(
        string="Clave de Búsqueda",
        default="id",
        help="Campo por el cual se buscarán los registros en el JSON de entrada",
        tracking=True,
    )

    clave_modelo = fields.Char(
        string="Campo de Búsqueda en Modelo",
        default="id",
        help="Campo del modelo destino que se usará para buscar registros existentes",
        tracking=True,
    )

    def cleanFile(self, content):
        """Esta función quita la última coma del array en un JSON."""

        # Decodificar si el contenido está en bytes
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Expresión regular para capturar una coma seguida de un cierre de objeto y un salto de línea antes de ]
        content = re.sub(r",\s*\n\s*]", "\n]", content)

        return content

    def action_apply_results(self):
        """Aplica los resultados de la sincronización al modelo destino."""
        self.ensure_one()

        if not self.archivo:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "No hay archivo de resultados para aplicar.",
                    "type": "danger",
                    "sticky": False,
                },
            }

        try:
            # Hacer rollback de cualquier transacción abortada
            self.env.cr.rollback()

            # Usar sudo para asegurar permisos
            self_sudo = self.sudo()

            # Decodificar el archivo
            content = base64.b64decode(self.archivo)
            content = self.cleanFile(content)
            data = json.loads(content)

            # Obtener el modelo destino
            destino = self_sudo.sincronizador_id.destino_id
            if not destino:
                raise ValueError("No se encontró el destino configurado")

            # Obtener el modelo
            model = self.env[destino.model_id.model].sudo()

            # Contadores para estadísticas
            registros_procesados = 0
            registros_exitosos = 0
            registros_fallidos = 0
            errores = []

            # Actualizar total de registros
            self_sudo.write({"total_registros": len(data), "estado": "working"})

            # Aplicar los resultados
            for record in data:
                registros_procesados += 1
                try:
                    # Actualizar registro actual
                    self_sudo.write({"nro_registro_actual": registros_procesados})

                    # Obtener el valor de la clave de búsqueda
                    search_value = record.get(self.clave_busqueda)
                    if not search_value:
                        registros_fallidos += 1
                        errores.append(
                            f"El registro no tiene valor para la clave '{self.clave_busqueda}': {record}"
                        )
                        continue

                    # Crear un savepoint para este registro
                    savepoint = self.env.cr.savepoint()
                    try:
                        # Buscar si existe el registro por la clave de búsqueda
                        existing = model.search(
                            [(self.clave_modelo, "=", search_value)]
                        )

                        # Transformar los datos usando el script del destino
                        transformed_data = destino.transform_data(
                            record, registros_procesados, existing
                        )

                        # Crear o actualizar el registro
                        if existing:
                            existing.write(transformed_data)
                            created_record = existing
                        else:
                            # Si no existe, crear nuevo
                            transformed_data[self.clave_modelo] = search_value
                            created_record = model.create(transformed_data)

                        # Ejecutar postCreateEdit si existe en el script de transformación
                        if hasattr(destino, "postCreateEdit"):
                            try:
                                destino.postCreateEdit(record, created_record)
                            except Exception as post_edit_error:
                                _logger.warning(
                                    "Error en postCreateEdit para el registro %s: %s",
                                    search_value,
                                    str(post_edit_error),
                                )
                                # Si hay error en postCreateEdit, hacemos rollback del savepoint
                                savepoint.rollback()
                                raise

                        registros_exitosos += 1
                        # Commit explícito después de procesar cada registro
                        self.env.cr.commit()

                    except Exception as e:
                        # En caso de error, hacemos rollback del savepoint
                        savepoint.rollback()
                        raise

                except Exception as e:
                    registros_fallidos += 1
                    errores.append(f"Error procesando registro: {str(e)}")
                    _logger.error("Error procesando registro: %s", str(e))
                    continue

            # Actualizar estado y estadísticas
            self_sudo.write(
                {
                    "estado": "success" if registros_fallidos == 0 else "warning",
                    "mensaje": (
                        "Resultados aplicados exitosamente"
                        if registros_fallidos == 0
                        else "Resultados aplicados con advertencias"
                    ),
                    "detalles": f"Se procesaron {registros_procesados} registros al modelo {destino.model_id.name}. "
                    f"Exitosos: {registros_exitosos}, Fallidos: {registros_fallidos}",
                    "registros_procesados": registros_procesados,
                    "registros_exitosos": registros_exitosos,
                    "registros_fallidos": registros_fallidos,
                    "nro_registro_actual": 0,  # Resetear el contador
                }
            )

            if errores:
                self_sudo.detalles += "\n\nErrores encontrados:\n" + "\n".join(errores)

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Éxito" if registros_fallidos == 0 else "Advertencia",
                    "message": f"Se procesaron {registros_procesados} registros. "
                    f"Exitosos: {registros_exitosos}, Fallidos: {registros_fallidos}",
                    "type": "success" if registros_fallidos == 0 else "warning",
                    "sticky": False,
                },
            }

        except Exception as e:
            _logger.error("Error al aplicar resultados: %s", str(e))
            self_sudo.write(
                {
                    "estado": "error",
                    "mensaje": "Error al aplicar resultados",
                    "detalles": str(e),
                    "nro_registro_actual": 0,  # Resetear el contador
                }
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": f"Error al aplicar resultados: {str(e)}",
                    "type": "danger",
                    "sticky": False,
                },
            }
