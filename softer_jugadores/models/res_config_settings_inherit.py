from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    userComet = fields.Char(string="User Comet")
    passComet = fields.Char(string="Pass Comet")
    tieneComet = fields.Boolean(string="¿Tiene Comet?")
    tieneLigaVeteranosCr = fields.Boolean(string="¿Tiene Liga Veteranos CR?")
    userVeteranos = fields.Char(string="Usuario Veteranos")
    claveVeteranos = fields.Char(string="Clave Veteranos")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()

        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.userComet", self.userComet
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.passComet", self.passComet
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.tieneComet", self.tieneComet
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.tieneLigaVeteranosCr", self.tieneLigaVeteranosCr
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.userVeteranos", self.userVeteranos
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "jugadores.claveVeteranos", self.claveVeteranos
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()

        res.update(
            {
                "userComet": ir_config.get_param("jugadores.userComet", default=""),
                "passComet": ir_config.get_param("jugadores.passComet", default=""),
                "tieneComet": ir_config.get_param("jugadores.tieneComet", default=""),
                "tieneLigaVeteranosCr": ir_config.get_param(
                    "jugadores.tieneLigaVeteranosCr", default=""
                ),
                "userVeteranos": ir_config.get_param(
                    "jugadores.userVeteranos", default=""
                ),
                "claveVeteranos": ir_config.get_param(
                    "jugadores.claveVeteranos", default=""
                ),
            }
        )
        return res

    def action_sync_veteranos(self):
        """Acción para sincronizar con Liga Veteranos"""
        return self.env["sync.veteranos"].sync_jugadores()

    def action_sync_comet(self):
        """Acción para sincronizar con Comet"""
        return self.env["sync.comet"].sync_jugadores()
