from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    proximoNroSocio = fields.Integer(string="Proximo Nro socio")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()

        self.env["ir.config_parameter"].sudo().set_param(
            "socios.proximoNroSocio", self.proximoNroSocio
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()

        res.update(
            {
                "proximoNroSocio": ir_config.get_param(
                    "socios.proximoNroSocio", default=1
                ),
            }
        )
        return res
