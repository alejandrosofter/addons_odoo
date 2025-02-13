from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    url_whatsapp = fields.Char(string="URL whatsapp")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp.url_whatsapp", self.url_whatsapp
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
            }
        )
        return res
