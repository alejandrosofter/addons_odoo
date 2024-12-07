from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cloudflare_token = fields.Char(
        string="Cloudflare Token", config_parameter="softer_instancias.cloudflare_token"
    )
    cloudflare_email = fields.Char(
        string="Cloudflare Email", config_parameter="softer_instancias.cloudflare_email"
    )
    serverIp = fields.Char(
        string="Server IP", config_parameter="softer_instancias.serverIp"
    )
