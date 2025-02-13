from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    active_wsap = fields.Boolean(string="Esta Activo", default=False)
    nroWhatsapp = fields.Text(string="Nro de whatsapp")
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
            ("no_configurado", "No Configurado"),
        ],
        string="Estado de WhatsApp",
    )
