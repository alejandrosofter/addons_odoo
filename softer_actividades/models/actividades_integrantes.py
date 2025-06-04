# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
import string
from ..data.palabras_contrasena import PALABRAS_CONTRASENA
import logging

_logger = logging.getLogger(__name__)


class Integrantes(models.Model):
    _name = "softer.actividades.integrantes"
    _description = "Modelo de Integrantes"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "cliente_id asc"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    excluir_socio = fields.Boolean(
        string="Excluir Socio",
        help="Al seleccionar no sera incluido la busqueda de socios " "pendientes.",
        default=False,
    )
    payment_adhesion_id = fields.Many2one(
        "payment.adhesiones",
        string="Adhesión SIRO",
        help="Adhesión de SIRO relacionada con esta suscripción",
        tracking=True,
        create=False,
    )

    suscripcion_plan_id = fields.Many2one(
        "softer.suscripcion.plan",
        string="Plan de Suscripción",
        help="Plan de suscripción asociado al integrante",
        tracking=True,
    )

    apodo = fields.Char(
        string="Apodo",
        help="Apodo o sobrenombre del integrante, en caso de no colocarlo, "
        "se mostrará el nombre del cliente",
        tracking=True,
    )

    socio_id = fields.Many2one(
        "res_partner.socio",
        string="Socio",
        required=True,
        tracking=True,
        # ondelete="restrict",
        help="Socio que consume el servicio",
    )
    cliente_id = fields.Many2one(
        "res.partner",
        string="Integrante",
        required=True,
        tracking=True,
        # compute="_compute_cliente_id",
        store=True,
        readonly=False,  # Allow manual override if needed
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
            ("cancelada", "Cancelada"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        default="activa",
        tracking=True,
    )
    es_debito_automatico = fields.Boolean(
        string="Debito Automatico",
        default=False,
    )
    estadoMotivo = fields.Char(
        string="Motivo Estado",
    )
    porcentajeAsistenciaMensual = fields.Float(
        string="Asistencia Mensual",
        help="Porcentaje de asistencia del integrante en el mes actual",
        default=0,
    )
    porcentajeAsistenciaGlobal = fields.Float(
        string="Asistencia Global",
        help="Porcentaje de asistencia del integrante desde su ingreso",
        default=0,
    )
    cliente_contacto = fields.Many2one(
        "res.partner",
        string="Facturación",
        required=True,
        tracking=True,
        ondelete="restrict",
    )
    actividad_id = fields.Many2one("softer.actividades", string="Actividad")
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        help="Suscripción asociada al integrante",
        ondelete="cascade",
        required=True,
    )
    # suscripcion_ids = fields.One2many(
    #     "softer.suscripcion",
    #     "integrante_id",
    #     string="Suscripciones",
    #     domain=[("tieneActividad", "=", True)],
    #     help="Suscripciones asociadas al integrante",
    # )

    fechaNacimiento = fields.Date(
        string="Fecha de Nacimiento",
        compute="_compute_fecha_nacimiento",
        store=True,
        readonly=False,
        tracking=True,
    )
    tiene_acceso_sistema = fields.Boolean(
        string="Tiene Acceso al Sistema",
        default=False,
        help="Indica si el integrante tiene acceso al sistema",
    )

    telefono_whatsapp = fields.Char(
        string=" WhatsApp",
        related="cliente_contacto.phone",
        readonly=False,
        store=True,
    )
    numero_documento = fields.Char(
        string="Número de Documento",
        related="cliente_contacto.vat",
        readonly=False,
        store=True,
    )
    estado_ids = fields.One2many(
        "softer.actividades.integrantes.estados",
        "integrante_id",
        string="Historial de Estados",
    )

    tieneBeneficio = fields.Boolean(
        string="Tiene Beneficio",
        help="Indica si el integrante tiene algún beneficio especial",
        default=False,
        tracking=True,
    )

    motivoBeneficio = fields.Text(
        string="Motivo del Beneficio",
        help="Descripción del motivo por el cual tiene el beneficio",
        tracking=True,
    )

    @api.depends("socio_id")
    def _compute_cliente_id(self):
        """Calcula el cliente_id basado en el socio_id seleccionado"""
        for record in self:
            if record.socio_id:
                record.cliente_id = record.socio_id.partner_id
            # else:
            #     record.cliente_id = False # Decide if cliente_id should be cleared when socio_id is cleared

    @api.depends("cliente_id.name", "apodo")
    def _compute_name(self):
        """Calcula el nombre del integrante basado en el apodo o nombre del cliente"""
        for record in self:
            if record.apodo:
                record.name = record.apodo
            else:
                record.name = record.cliente_id.name if record.cliente_id else False

    def _generate_friendly_password(self):
        """Genera una contraseña amigable usando palabras simples y números"""
        # Seleccionar una palabra aleatoria
        palabra1 = random.choice(PALABRAS_CONTRASENA)
        # Generar dos números aleatorios
        numeros = "".join(random.choices(string.digits, k=2))
        # Combinar todo
        return f"{palabra1}{numeros}"

    def action_view_suscripciones(self):
        """Acción para ver las suscripciones del cliente"""
        return {
            "name": "Suscripciones",
            "type": "ir.actions.act_window",
            "res_model": "softer.suscripcion",
            "view_mode": "tree,form",
            "domain": [("cliente_id", "=", self.cliente_id.id)],
            "context": {"default_cliente_id": self.cliente_id.id},
        }

    def _get_activity_form_view(self):
        """Retorna la acción para abrir el formulario de la actividad"""
        return {
            "type": "ir.actions.act_window",
            "res_model": "softer.actividades",
            "res_id": self.actividad_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_grant_system_access(self):
        """Otorga acceso al sistema al integrante"""
        self.ensure_one()

        if not self.cliente_contacto.vat:
            raise ValidationError(
                "El contacto debe tener un número de documento configurado"
            )

        # Generar contraseña amigable
        password = self._generate_friendly_password()

        # Buscar si ya existe un usuario para este contacto
        usuario_existente = (
            self.env["res.users"]
            .sudo()
            .search([("partner_id", "=", self.cliente_contacto.id)], limit=1)
        )

        # Crear usuario si no existe
        if not usuario_existente:
            valores_usuario = {
                "name": self.cliente_contacto.name,
                "login": self.cliente_contacto.vat,  # Usar número de documento como login
                "password": password,
                "partner_id": self.cliente_contacto.id,
                "groups_id": [
                    (6, 0, [self.env.ref("base.group_portal").id])
                ],  # Grupo portal
            }
            self.env["res.users"].sudo().create(valores_usuario)
        else:
            # Si el usuario existe, activarlo y cambiar la contraseña
            usuario_existente.sudo().write({"active": True, "password": password})

        # Enviar credenciales por WhatsApp si hay teléfono
        if self.cliente_contacto.phone:
            url_sistema = (
                f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}"
                f"/web/login"
            )
            if not usuario_existente:
                mensaje = f"""¡Hola {self.cliente_contacto.name}!

Te hemos creado un nuevo acceso al sistema:
*Usuario:* {self.cliente_contacto.vat}
*Contraseña:* {password}

*Para acceder al sistema:* {url_sistema}"""
            else:
                mensaje = f"""¡Hola {self.cliente_contacto.name}!

Ya tenías un usuario en el sistema y te hemos enviado nuevas credenciales:
*Usuario:* {self.cliente_contacto.vat}
*Contraseña:* {password}

*Para acceder al sistema:* {url_sistema}"""

            # Buscar la primera instancia de WhatsApp activa
            instance = self.env["evolution.api.numbers"].search(
                [("estado", "=", "active")], limit=1
            )

            if instance:
                self.env["evolution.api.message"].sudo().create(
                    {
                        "number_id": instance.id,
                        "numeroDestino": self.cliente_contacto.phone,
                        "type": "text",
                        "text": mensaje,
                    }
                )
            else:
                self.tiene_acceso_sistema = True
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Advertencia",
                        "message": (
                            f"Se ha creado el acceso al sistema para "
                            f"{self.cliente_contacto.name}, pero no se pudo enviar "
                            f"las credenciales por WhatsApp porque no hay "
                            f"instancias activas."
                        ),
                        "type": "warning",
                        "sticky": True,
                    },
                }
        else:
            # Mostrar advertencia si no hay teléfono
            self.tiene_acceso_sistema = True
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Advertencia",
                    "message": (
                        f"Se ha creado el acceso al sistema para "
                        f"{self.cliente_contacto.name}, pero no se pudo enviar "
                        f"las credenciales por WhatsApp porque no tiene número "
                        f"de teléfono configurado."
                    ),
                    "type": "warning",
                    "sticky": True,
                },
            }

        self.tiene_acceso_sistema = True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": (
                    f"Se ha creado el acceso al sistema para "
                    f"{self.cliente_contacto.name}"
                ),
                "type": "success",
            },
        }

    def action_grant_system_access_team(self):
        """Otorga acceso al sistema a todos los integrantes del equipo"""
        integrantes_sin_acceso = self.search(
            [
                ("actividad_id", "=", self.actividad_id.id),
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

    def action_revoke_system_access(self):
        """Revoca el acceso al sistema del integrante"""
        self.ensure_one()

        # Buscar usuario asociado al contacto
        usuario = (
            self.env["res.users"]
            .sudo()
            .search([("partner_id", "=", self.cliente_contacto.id)], limit=1)
        )

        if usuario:
            usuario.sudo().write({"active": False})
            self.tiene_acceso_sistema = False

            # Notificar por WhatsApp si hay teléfono
            if self.cliente_contacto.phone:
                mensaje = (
                    f"Hola {self.cliente_contacto.name},\n\n"
                    f"Tu acceso al sistema ha sido desactivado. Si crees que "
                    f"esto es un error, por favor contacta al administrador."
                )

                # Buscar la primera instancia de WhatsApp activa
                instance = self.env["evolution.api.numbers"].search(
                    [("estado", "=", "active")], limit=1
                )

                if instance:
                    self.env["evolution.api.message"].sudo().create(
                        {
                            "number_id": instance.id,
                            "numeroDestino": self.cliente_contacto.phone,
                            "type": "text",
                            "text": mensaje,
                        }
                    )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Éxito",
                    "message": (
                        f"Se ha revocado el acceso al sistema para "
                        f"{self.cliente_contacto.name}"
                    ),
                    "type": "success",
                },
            }

    def action_view_estados(self):
        """Abre el formulario para crear un nuevo estado"""
        self.ensure_one()
        return {
            "name": "Nuevo Estado",
            "type": "ir.actions.act_window",
            "res_model": "softer.actividades.integrantes.estados",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_integrante_id": self.id,
                "default_estado": self.env.context.get("default_estado", "activa"),
            },
        }

    @api.onchange("telefono_whatsapp")
    def _onchange_telefono_whatsapp(self):
        """Actualiza el teléfono del contacto cuando cambia el teléfono WhatsApp"""
        if self.cliente_contacto and self.telefono_whatsapp:
            self.cliente_contacto.phone = self.telefono_whatsapp

    @api.onchange("numero_documento")
    def _onchange_numero_documento(self):
        """Actualiza el número de documento del contacto cuando cambia"""
        if self.cliente_contacto and self.numero_documento:
            self.cliente_contacto.vat = self.numero_documento

    @api.onchange("suscripcion_plan_id")
    def _onchange_suscripcion_plan_id(self):
        if self.suscripcion_plan_id:
            return {
                "warning": {
                    "title": "Atención",
                    "message": (
                        "Cambiaste el plan de suscripciones y al guardar "
                        "cambiará el esquema de suscripciones del inscripto."
                    ),
                }
            }

    def agregar_suscripciones_plan(self, vals):
        """Agrega las suscripciones del plan a la suscripción del integrante"""
        print(f"AGREGANDO SUSCRIPCIONES DEL PLAN {vals['suscripcion_plan_id']}")

    def check_suscripcion_plan(self, vals):
        """Verifica si el plan de suscripciones es válido"""
        if self.suscripcion_plan_id:
            if "suscripcion_plan_id" in vals:
                self.agregar_suscripciones_plan(vals)

        return False

    def write(self, vals):
        """Sobrescribe el método write para verificar estado de socio y suscripciones después de cambios"""
        # Validar estado del socio si socio_id está en vals o ya está seteado
        if "socio_id" in vals and vals["socio_id"]:
            socio = self.env["res_partner.socio"].browse(vals["socio_id"])
            if socio and socio.estado != "activa":
                raise UserError(
                    _("No se puede asignar un socio con estado distinto de activo.")
                )
        elif self.socio_id and self.socio_id.estado != "activa":
            raise UserError(
                _("No se puede modificar un integrante con un socio no activo.")
            )

        for rec in self:
            old_suscripcion = rec.suscripcion_id
            res = super().write(vals)
            new_suscripcion = self.suscripcion_id
            if "suscripcion_id" in vals:
                if old_suscripcion and old_suscripcion != new_suscripcion:
                    old_suscripcion.sudo().write({"integrante_id": False})
                if new_suscripcion:
                    new_suscripcion.sudo().write({"integrante_id": rec.id})
        return res

    def _actualizar_estados_por_defecto(self):
        """Actualiza los registros existentes con estados incorrectos"""
        # Buscar registros con estados que no sean 'activa' o 'suspendida'
        registros_a_actualizar = self.search(
            [
                "|",
                "|",
                ("estado", "=", False),
                ("estado", "=", ""),
                ("estado", "=", "activo"),
            ]
        )
        if registros_a_actualizar:
            registros_a_actualizar.write({"estado": "activa"})
            _logger.info(
                f"Se actualizaron {len(registros_a_actualizar)} registros a estado 'activa'"
            )

    @api.model
    def init(self):
        """Método llamado al instalar/actualizar el módulo"""
        super().init()
        self._actualizar_estados_por_defecto()

    @api.onchange("cliente_id")
    def _onchange_cliente_id(self):
        """Actualiza campos relacionados cuando cambia el cliente_id"""
        for record in self:
            if record.cliente_id:
                record.fechaNacimiento = record.cliente_id.fechaNacimiento
                # Assign the recordset directly to the Many2one field
                record.cliente_contacto = record.cliente_id
                # Add extensive debug prints for related fields
                _logger.info(
                    f"DEBUG ONCHANGE: cliente_id selected: {record.cliente_id.id}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: cliente_contacto: {record.cliente_contacto.id if record.cliente_contacto else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: suscripcion_id: {record.suscripcion_id.id if record.suscripcion_id else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: socio_id: {record.socio_id.id if record.socio_id else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: actividad_id: {record.actividad_id.id if record.actividad_id else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: suscripcion_plan_id: {record.suscripcion_plan_id.id if record.suscripcion_plan_id else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: payment_adhesion_id: {record.payment_adhesion_id.id if record.payment_adhesion_id else 'False'}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: telefono_whatsapp: {record.telefono_whatsapp}"
                )
                _logger.info(
                    f"DEBUG ONCHANGE: numero_documento: {record.numero_documento}"
                )

            else:
                record.fechaNacimiento = (
                    False  # Considerar limpiar los campos si cliente_id se vacía
                )
                record.cliente_contacto = False
                record.suscripcion_id = False  # Explicitly set suscripcion_id to False
                # Log when cliente_id is cleared
                _logger.info("DEBUG ONCHANGE: cliente_id cleared.")
                return {}

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.suscripcion_id:
                record.suscripcion_id.sudo().write({"integrante_id": record.id})
        return records
