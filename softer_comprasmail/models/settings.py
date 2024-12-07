from odoo import models, fields


class Settings(models.TransientModel):
    _inherit = "res.config.settings"
    chatgpt_token = fields.Char(
        string="Chatgpt Token", config_parameter="softer_instancias.chatgpt_token"
    )
