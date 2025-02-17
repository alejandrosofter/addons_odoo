from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    url_whatsapp = fields.Char(string="URL whatsapp")
    token_wsap = fields.Char(string="Token ")
    # bot_wsap = fields.Char(string="ID Bot Whatsapp")
    active_wsap = fields.Boolean(string="Esta Activo", default=False)

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp.url_whatsapp", self.url_whatsapp
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp.token_wsap", self.token_wsap
        )
        # self.env["ir.config_parameter"].sudo().set_param(
        #     "whatsapp.bot_wsap", self.bot_wsap
        # )
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp.active_wsap", self.active_wsap
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "url_whatsapp": ir_config.get_param(
                    "whatsapp.url_whatsapp", default=""
                ),
                "token_wsap": ir_config.get_param("whatsapp.token_wsap", default=""),
                # "bot_wsap": ir_config.get_param("whatsapp.bot_wsap", default=""),
                "active_wsap": ir_config.get_param("whatsapp.active_wsap", default=""),
            }
        )
        return res

    def action_actualizar_bots_wsap(self):
        """Ejecuta manualmente la actualización de bots solo para el usuario actual"""
        self.env.user.actualizar_bots_wsap()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Actualización completada",
                "message": "Tu bot de WhatsApp se ha actualizado correctamente.",
                "sticky": False,
            },
        }
