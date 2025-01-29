from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    chat_channel_id = fields.Many2one("discuss.channel", string="Canal de Chat")
    es_virtual = fields.Boolean(string="Es Virtual", default=False)
    estado_whatsapp = fields.Selection(
        [
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
            ("no_configurado", "No Configurado"),
        ],
        string="Estado de WhatsApp",
    )
    tiene_wsap = fields.Boolean(string="Tiene WhatsApp", default=False)
    prompt = fields.Text(string="Prompt Personalizado")

    @api.model
    def create(self, vals):
        # Crear un canal privado para el usuario
        channel = self.env["mail.channel"].create(
            {
                "name": vals.get("name", "Canal de Chat"),
                "public": "private",  # Privado
            }
        )
        vals["chat_channel_id"] = channel.id
        return super(ResUsersInherit, self).create(vals)
