from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    evolution_api_url = fields.Char(
        string="URL Evolution API", config_parameter="evolution_api.url"
    )
    evolution_api_token = fields.Char(
        string="Token Evolution API", config_parameter="evolution_api.token"
    )

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        ir_config.set_param("evolution_api.url", self.evolution_api_url or "")
        ir_config.set_param("evolution_api.token", self.evolution_api_token or "")

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "evolution_api_url": ir_config.get_param(
                    "evolution_api.url", default=""
                ),
                "evolution_api_token": ir_config.get_param(
                    "evolution_api.token", default=""
                ),
            }
        )
        return res
