# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class Actividades(models.Model):
    _name = "softer.actividades"
    _description = "Modelo de Actividades"

    name = fields.Char(
        string="Nombre",
        required=True,
    )
    genero = fields.Selection(
        selection=[
            ("M", "Masculino"),
            ("F", "Femenino"),
            ("Todos", "Todos"),
        ],
        string="Género",
        default="Todos",
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
        ],
        string="Estado",
    )
    fechaFin = fields.Date(
        string="Fecha de Fin",
        tracking=True,
        help="Fecha en la que finaliza la actividad",
    )
    pagaCuotaSocial = fields.Boolean(
        string="Paga Cuota Socal",
        help="Indica si los integrantes de la actividad pagan cuota social",
    )
    cobroPorAsistencia = fields.Boolean(
        string="Cobro por Asistencia",
        help="Indica si se cobra por asistencia",
    )
    categoria_suscripcion = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría de Suscripción",
        help="Categoría que se asignará a las suscripciones generadas",
    )
    entrenador = fields.Many2one("res.partner", string="Entrenador")
    administrador = fields.Many2one("res.partner", string="Administrador")
    tipoRangos = fields.Selection(
        [
            ("porFechaNacimiento", "Por Fecha Nacimiento"),
            ("libre", "Libre"),
        ],
        string="Tipo de Rango",
    )

    fechaDesde = fields.Date(string="Rango Desde", tracking=True)
    fechaHasta = fields.Date(string="Rango Hasta", tracking=True)
    integrantes = fields.One2many(
        "softer.actividades.integrantes", "actividad_id", string="Integrantes"
    )
    horarios = fields.One2many(
        "softer.actividades.horarios", "actividad_id", string="Horarios"
    )
    producto_asociado = fields.Many2one(
        "product.product",
        string="Producto Asociado",
        help="Producto principal asociado a esta actividad",
    )
    porcentaje_asistencia_cobro = fields.Float(
        string="Porcentaje Asistencia Cobro",
        help="Porcentaje mínimo de asistencia requerido para el cobro",
        default=100.0,
    )
    condiciones_actividad = fields.Text(
        string="Condiciones de la Actividad",
        help="Condiciones específicas y reglas de la actividad",
    )
    registroSuscripciones = fields.Text(
        string="Registro de Suscripciones",
        readonly=True,
        help="Registro histórico de suscripciones generadas",
    )
    mensajes = fields.One2many(
        "softer.actividades.mensajes", "actividad_id", string="Mensajes"
    )

    def _check_suscripciones(self):
        """
        Verifica y actualiza las suscripciones cuando hay cambios en la actividad
        o sus integrantes.
        """
        for record in self:
            if record.producto_asociado:
                record.subscription_upsert()

    def agregar_cliente_a_actividad(self, cliente_id, nombre_actividad=False):
        """
        Agrega un cliente a una actividad existente o crea una nueva basada en el rango de fechas
        Args:
            cliente_id (int): ID del cliente a agregar
            nombre_actividad (str): Nombre opcional de la actividad a la que se quiere agregar
        Returns:
            dict: Diccionario con el resultado de la operación
        """
        try:
            print(f"agregando cliente {cliente_id} a actividad {nombre_actividad}")
            # Verificar que el cliente existe y es un jugador
            cliente = self.env["res.partner"].browse(cliente_id)
            if not cliente.exists():
                return {"success": False, "message": "El cliente no existe."}

            # Validación de género
            if nombre_actividad:
                actividad = self.search([("name", "=", nombre_actividad)], limit=1)
                if (
                    actividad
                    and actividad.genero != "Todos"
                    and actividad.genero != cliente.genero
                ):
                    return {
                        "success": False,
                        "message": f"El género del cliente no coincide con el requerido por la actividad ({actividad.genero}).",
                    }

            # Buscar el contacto del cliente (el mismo cliente en este caso)
            cliente_contacto_id = cliente.id
            # Si se proporciona nombre de actividad, buscar esa actividad
            if nombre_actividad:
                actividad = self.search([("name", "=", nombre_actividad)], limit=1)
                if not actividad:
                    # crear actividad con ese nombre

                    actividad = (
                        self.env["softer.actividades"]
                        .sudo()
                        .create(
                            {
                                "name": nombre_actividad,
                                "tipoRangos": "libre",
                            }
                        )
                    )
            else:
                # Buscar una actividad con rango por fecha de nacimiento que coincida
                domain = [
                    ("tipoRangos", "=", "porFechaNacimiento"),
                    ("fechaDesde", "<=", cliente.fechaNacimiento),
                    ("fechaHasta", ">=", cliente.fechaNacimiento),
                    ("estado", "=", "activa"),
                ]
                # Agregar filtro de género si es necesario
                domain.append("|")
                domain.append(("genero", "=", "Todos"))
                domain.append(("genero", "=", cliente.genero))

                actividad = self.search(domain, limit=1)

                if not actividad:
                    actividad = self.search(
                        [
                            ("name", "=", "Sin rango"),
                        ],
                        limit=1,
                    )
                    if not actividad:
                        actividad = (
                            self.env["softer.actividades"]
                            .sudo()
                            .create(
                                {
                                    "name": "Sin rango",
                                    "tipoRangos": "libre",
                                }
                            )
                        )

            # Agregar el cliente a la actividad
            resultado = actividad.agregar_integrante(
                cliente_id=cliente.id,
                cliente_contacto_id=cliente_contacto_id,
            )

            if resultado["success"]:
                return {
                    "success": True,
                    "message": f'Cliente agregado exitosamente a la actividad "{actividad.name}".',
                }
            else:
                return resultado

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al agregar cliente a la actividad: {str(e)}",
            }

    def agregar_integrante(self, cliente_id, cliente_contacto_id):
        """
        Agrega un integrante a la actividad
        Args:
            cliente_id (int): ID del cliente (integrante)
            cliente_contacto_id (int): ID del contacto del cliente
        Returns:
            dict: Diccionario con el resultado de la operación
        """
        try:
            # Verificar si el cliente ya está en la actividad
            integrante_existente = self.env["softer.actividades.integrantes"].search(
                [("actividad_id", "=", self.id), ("cliente_id", "=", cliente_id)]
            )

            if integrante_existente:
                return {
                    "success": False,
                    "message": f"El cliente ya está registrado en esta actividad.",
                }

            # Crear el nuevo integrante
            vals = {
                "actividad_id": self.id,
                "cliente_id": cliente_id,
                "cliente_contacto": cliente_contacto_id,
                "estado": "activo",
            }

            self.env["softer.actividades.integrantes"].create(vals)

            return {"success": True, "message": "Integrante agregado exitosamente."}

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al agregar integrante: {str(e)}",
            }

    def subscription_upsert(self):
        """Crea o actualiza suscripciones para los integrantes de la actividad"""
        _logger.info(f"Iniciando subscription_upsert para actividad {self.id}")

        if not self.producto_asociado:
            _logger.warning(f"No hay producto asociado a la actividad {self.id}")
            return

        _logger.info(f"Integrantes a procesar: {len(self.integrantes)}")

        for integrante in self.integrantes:
            _logger.info(
                f"Procesando integrante {integrante.id} - Cliente: "
                f"{integrante.cliente_id.name} - Estado: {integrante.estado}"
            )

            # Buscar suscripción existente
            dominio = [
                ("cliente_id", "=", integrante.cliente_id.id),
                ("idActividad", "=", self.id),
            ]
            _logger.info(f"Buscando suscripción con dominio: {dominio}")

            suscripcion = self.env["softer.suscripcion"].search(dominio, limit=1)

            _logger.info(f"Estado mapeado para suscripción: {integrante.estado}")

            # Preparar motivo con información adicional
            motivo_base = f"Cambio de estado desde actividad {self.name}"
            if integrante.estadoMotivo:
                motivo_base += f" - Motivo: {integrante.estadoMotivo}"
            motivo_base += (
                f" - Asistencia Mensual: {integrante.porcentajeAsistenciaMensual or 0}%"
            )
            motivo_base += (
                f" - Asistencia Global: {integrante.porcentajeAsistenciaGlobal or 0}%"
            )

            if suscripcion:
                # Actualizar suscripción existente
                _logger.info(f"Actualizando suscripción {suscripcion.id}")
                # Crear el registro de cambio de estado directamente
                if integrante.estado != suscripcion.estado:
                    suscripcion.cambiarEstado(
                        integrante.estado,
                        motivo_base,
                        self.env.user.id,
                    )

                    suscripcion.write(
                        {
                            "idActividad": self.id,
                        }
                    )
                else:
                    # Actualizar el estado sin crear un nuevo registro
                    usaSuscripcion = integrante.estado == "activa"
                    suscripcion.write(
                        {
                            "idActividad": self.id,
                            "usoSuscripcion": usaSuscripcion,
                        }
                    )
            else:
                # Crear nueva suscripción
                _logger.info("Creando nueva suscripción")
                suscripcion = self.env["softer.suscripcion"].create(
                    {
                        "cliente_id": integrante.cliente_id.id,
                        "contacto_comunicacion": integrante.cliente_contacto.id,
                        "estado": integrante.estado,
                        "idActividad": self.id,
                        "tieneActividad": True,
                        "paga_debito_automatico": integrante.es_debito_automatico,
                        "categoria_id": self.categoria_suscripcion.id,
                        "fecha_inicio": fields.Date.today(),
                        "fecha_fin": self.fechaFin,
                        "tipo_temporalidad": "mensual",
                        "cantidad_recurrencia": 1,
                        "line_ids": [
                            (
                                0,
                                0,
                                {
                                    "product_id": self.producto_asociado.id,
                                    "cantidad": 1,
                                },
                            )
                        ],
                    }
                )
                suscripcion.cambiarEstado(
                    integrante.estado,
                    motivo_base,
                    self.env.user.id,
                )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "Suscripciones actualizadas correctamente.",
                "type": "success",
                "sticky": True,
            },
        }

    def action_grant_system_access_team(self):
        """Otorga acceso al sistema a todos los integrantes del equipo"""
        integrantes_sin_acceso = self.env["softer.actividades.integrantes"].search(
            [
                ("actividad_id", "=", self.id),
                ("tiene_acceso_sistema", "=", False),
                ("cliente_contacto.vat", "!=", False),
            ]
        )

        if not integrantes_sin_acceso:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Información",
                    "message": "No hay integrantes sin acceso al sistema en este equipo",
                    "type": "info",
                },
            }

        for integrante in integrantes_sin_acceso:
            integrante.action_grant_system_access()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": f"Se han creado {len(integrantes_sin_acceso)} accesos al sistema para el equipo",
                "type": "success",
            },
        }

    def action_alta(self):
        """Da de alta la actividad"""
        self.ensure_one()
        self.write({"estado": "activa"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La actividad ha sido activada correctamente.",
                "type": "success",
            },
        }

    def action_baja(self):
        """Finaliza la actividad"""
        self.ensure_one()
        self.write({"estado": "finalizada"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La actividad ha sido finalizada correctamente.",
                "type": "success",
            },
        }

    def action_generar(self):
        """Regenera las suscripciones de los integrantes"""
        self.ensure_one()
        self.subscription_upsert()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "Las suscripciones han sido regeneradas correctamente.",
                "type": "success",
            },
        }


class ActividadesMensajes(models.Model):
    _name = "softer.actividades.mensajes"
    _description = "Mensajes de WhatsApp para Actividades"
    _order = "fecha_hora desc"

    actividad_id = fields.Many2one(
        "softer.actividades", string="Actividad", required=True, ondelete="cascade"
    )
    fecha_hora = fields.Datetime(
        string="Fecha y Hora", default=lambda self: fields.Datetime.now(), required=True
    )
    tipo_mensaje = fields.Selection(
        [("text", "Texto"), ("media", "Multimedia")],
        string="Tipo de Mensaje",
        required=True,
    )
    archivo = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre del Archivo")
    texto = fields.Text(string="Mensaje")
    registro = fields.Text(
        string="Registro de Envío", help="Registro de a quiénes se envió el mensaje"
    )

    @api.model_create_multi
    def create(self, vals_list):
        mensajes = super().create(vals_list)
        for mensaje in mensajes:
            mensaje._enviar_mensajes_integrantes()
        return mensajes

    def _enviar_mensajes_integrantes(self):
        """Envía el mensaje a todos los integrantes de la actividad"""
        self.ensure_one()
        registro = []

        # Obtener la instancia activa de Evolution API
        instance = self.env["evolution.api.numbers"].search(
            [("estado", "=", "active")], limit=1
        )

        if not instance:
            raise ValidationError("No hay una instancia activa de Evolution API")

        # Obtener todos los integrantes activos con teléfono
        integrantes = self.actividad_id.integrantes.filtered(
            lambda i: i.estado == "activo" and i.cliente_contacto.phone
        )

        for integrante in integrantes:
            try:
                if self.tipo_mensaje == "text":
                    # Enviar mensaje de texto
                    self.env["evolution.api.message"].sudo().create(
                        {
                            "number_id": instance.id,
                            "numeroDestino": integrante.cliente_contacto.phone,
                            "type": "text",
                            "text": self.texto,
                        }
                    )
                else:
                    # Enviar mensaje multimedia
                    self.env["evolution.api.message"].sudo().create(
                        {
                            "number_id": instance.id,
                            "numeroDestino": integrante.cliente_contacto.phone,
                            "type": "media",
                            "text": self.texto or "",
                            "media": self.archivo,
                            "filename": self.nombre_archivo,
                        }
                    )

                registro.append(
                    f"{integrante.cliente_id.name} ({integrante.cliente_contacto.phone}) - Enviado"
                )
            except Exception as e:
                registro.append(
                    f"{integrante.cliente_id.name} ({integrante.cliente_contacto.phone}) - Error: {str(e)}"
                )

        # Actualizar el registro
        self.registro = "\n".join(registro)
