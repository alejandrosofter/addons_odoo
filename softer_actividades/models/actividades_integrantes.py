# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
import string


class Integrantes(models.Model):
    _name = "softer.actividades.integrantes"
    _description = "Modelo de Integrantes"

    # Lista de palabras simples para generar contraseñas
    PALABRAS_CONTRASENA = [
        "casa",
        "perro",
        "gato",
        "sol",
        "luna",
        "mar",
        "rio",
        "arbol",
        "flor",
        "piedra",
        "agua",
        "fuego",
        "aire",
        "tierra",
        "cielo",
        "nube",
        "lluvia",
        "viento",
        "nieve",
        "hielo",
        "pan",
        "leche",
        "queso",
        "huevo",
        "fruta",
        "verde",
        "azul",
        "rojo",
        "amarillo",
        "blanco",
        "negro",
        "gris",
        "rosa",
        "naranja",
        "morado",
        "verde",
        "cafe",
        "plata",
        "oro",
        "bronce",
        "libro",
        "papel",
        "lapiz",
        "pluma",
        "tinta",
        "hoja",
        "rama",
        "tronco",
        "raiz",
        "semilla",
        "mano",
        "pie",
        "ojo",
        "nariz",
        "boca",
        "oreja",
        "cabeza",
        "pelo",
        "diente",
        "lengua",
        "mesa",
        "silla",
        "cama",
        "puerta",
        "ventana",
        "pared",
        "techo",
        "piso",
        "escalera",
        "pasillo",
        "calle",
        "auto",
        "bici",
        "moto",
        "barco",
        "avion",
        "tren",
        "bus",
        "taxi",
        "metro",
        "amigo",
        "familia",
        "padre",
        "madre",
        "hijo",
        "hija",
        "hermano",
        "hermana",
        "abuelo",
        "abuela",
        "escuela",
        "maestro",
        "alumno",
        "clase",
        "libro",
        "cuaderno",
        "lapiz",
        "regla",
        "goma",
        "tijera",
        "juego",
        "pelota",
        "muñeca",
        "carro",
        "barco",
        "avion",
        "tren",
        "lego",
        "puzzle",
        "dado",
    ]

    cliente_id = fields.Many2one(
        "res.partner", string="Integrante", required=True, tracking=True
    )
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("suspendido", "Suspendido"),
            ("baja", "Baja"),
        ],
        string="Estado",
    )
    estadoMotivo = fields.Char(
        string="Motivo Estado",
    )
    cliente_contacto = fields.Many2one(
        "res.partner", string="Contacto Integrante", required=True, tracking=True
    )
    actividad_id = fields.Many2one("softer.actividades", string="Actividad")
    # suscripcion_id = fields.Many2one(
    #     "softer.suscripcion",
    #     string="Suscripción",
    #     tracking=True,
    #     domain="[('cliente_id', '=', cliente_contacto)]",
    # )
    fechaNacimiento = fields.Date(
        string="Fecha de Nacimiento",
        compute="_compute_fecha_nacimiento",
        store=True,
        readonly=True,
    )
    tiene_acceso_sistema = fields.Boolean(
        string="Tiene Acceso al Sistema",
        default=False,
        help="Indica si el integrante tiene acceso al sistema",
    )
    usuario_id = fields.Many2one(
        "res.users", string="Usuario del Sistema", readonly=True
    )
    telefono_whatsapp = fields.Char(
        related="cliente_contacto.phone", string="Teléfono WhatsApp", readonly=True
    )
    numero_documento = fields.Char(
        related="cliente_contacto.vat", string="Número de Documento", readonly=True
    )

    @api.depends("cliente_id")
    def _compute_fecha_nacimiento(self):
        for record in self:
            record.fechaNacimiento = (
                record.cliente_id.fechaNacimiento if record.cliente_id else False
            )

    def _generate_friendly_password(self):
        """Genera una contraseña amigable usando palabras simples y números"""
        # Seleccionar dos palabras aleatorias
        palabra1 = random.choice(self.PALABRAS_CONTRASENA)
        # palabra2 = random.choice(self.PALABRAS_CONTRASENA)
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

        # Crear usuario si no existe
        if not self.usuario_id:
            valores_usuario = {
                "name": self.cliente_contacto.name,
                "login": self.cliente_contacto.vat,  # Usar número de documento como login
                "password": password,
                "partner_id": self.cliente_contacto.id,
                "groups_id": [
                    (6, 0, [self.env.ref("base.group_portal").id])
                ],  # Grupo portal
            }
            usuario = self.env["res.users"].sudo().create(valores_usuario)
            self.usuario_id = usuario.id
        else:
            # Si el usuario existe, activarlo y cambiar la contraseña
            self.usuario_id.sudo().active = True
            self.usuario_id.sudo().password = password

        # Enviar credenciales por WhatsApp si hay teléfono
        if self.cliente_contacto.phone:
            url_sistema = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web/login"
            if not self.usuario_id:
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
                        "message": f"Se ha creado el acceso al sistema para {self.cliente_contacto.name}, pero no se pudo enviar las credenciales por WhatsApp porque no hay instancias activas.",
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
                    "message": f"Se ha creado el acceso al sistema para {self.cliente_contacto.name}, pero no se pudo enviar las credenciales por WhatsApp porque no tiene número de teléfono configurado.",
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
                "message": f"Se ha creado el acceso al sistema para {self.cliente_contacto.name}",
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

        if self.usuario_id:
            self.usuario_id.sudo().active = False
            self.tiene_acceso_sistema = False

            # Notificar por WhatsApp si hay teléfono
            if self.cliente_contacto.phone:
                mensaje = f"""Hola {self.cliente_contacto.name},

Tu acceso al sistema ha sido desactivado. Si crees que esto es un error, por favor contacta al administrador."""

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
                    "message": f"Se ha revocado el acceso al sistema para {self.cliente_contacto.name}",
                    "type": "success",
                },
            }
