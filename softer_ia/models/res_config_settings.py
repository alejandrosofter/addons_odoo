from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    softer_ia_openai_api_key = fields.Char(
        "Clave de API de OpenAI", config_parameter="softer_ia.openai_api_key"
    )
    softer_ia_gemini_api_key = fields.Char(
        "Clave de API de Gemini", config_parameter="softer_ia.gemini_api_key"
    )
    softer_ia_deepseek_api_key = fields.Char(
        "Clave de API de DeepSeek",
        config_parameter="softer_ia.deepseek_api_key",
    )

    enabled_openai = fields.Boolean(
        "Habilitar OpenAI", config_parameter="softer_ia.enabled_openai"
    )
    enabled_gemini = fields.Boolean(
        "Habilitar Gemini", config_parameter="softer_ia.enabled_gemini"
    )
    enabled_deepseek = fields.Boolean(
        "Habilitar DeepSeek", config_parameter="softer_ia.enabled_deepseek"
    )
