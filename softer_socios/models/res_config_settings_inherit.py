from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    diaLiquidacion = fields.Char(string="dias")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()

        self.env["ir.config_parameter"].sudo().set_param(
            "socios.diaLiquidacion", self.diaLiquidacion
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()

        res.update(
            {
                "diaLiquidacion": ir_config.get_param(
                    "socios.diaLiquidacion", default=""
                ),
            }
        )
        return res
