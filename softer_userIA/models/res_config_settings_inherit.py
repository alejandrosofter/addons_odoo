from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    url_ia = fields.Char(string="URL IA")
    token = fields.Char(string="Token")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param("ia.url_ia", self.url_ia)
        self.env["ir.config_parameter"].sudo().set_param("ia.token", self.token)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "url_ia": ir_config.get_param("ia.url_ia", default=""),
                "token": ir_config.get_param("ia.token", default=""),
            }
        )
        return res
