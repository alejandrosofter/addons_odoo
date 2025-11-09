"""
Este módulo define el modelo `ia.agente` para la gestión de agentes de IA.
"""

from odoo import fields, models, api
from odoo.exceptions import UserError


class IaAgente(models.Model):
    """
    Modelo para gestionar agentes de IA.
    """

    _name = "ia.agente"
    _description = "Agente de IA"

    # Consolidar todos los modelos en una única lista incluyendo el proveedor.
    ALL_MODELS = [
        ("openai", "gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("openai", "gpt-4", "GPT-4"),
        ("openai", "gpt-4o", "GPT-4o"),
        ("gemini", "gemini-pro", "Gemini Pro"),
        ("gemini", "gemini-1.5-flash", "Gemini 1.5 Flash"),
        ("gemini", "gemini-1.5-pro", "Gemini 1.5 Pro"),
        ("deepseek", "deepseek-chat", "DeepSeek Chat"),
        ("deepseek", "deepseek-coder", "DeepSeek Coder"),
    ]

    name = fields.Char("Nombre", required=True)
    prompt = fields.Text("Prompt")
    estado = fields.Selection(
        [("activo", "Activo"), ("deshabilitado", "Deshabilitado")],
        string="Estado",
        default="activo",
        required=True,
    )

    # El campo 'model' se elimina, 'model_name' lo reemplaza.
    model_name = fields.Selection(
        selection="_get_model_names",
        string="Nombre del Modelo",
        readonly=False,
        required=False,
    )

    is_global = fields.Boolean("Es Global", default=False)

    @api.model
    def _get_model_names(self):
        # Devolver todos los modelos (ID, Nombre) para el campo de selección.
        return [(model_id, model_name) for _, model_id, model_name in self.ALL_MODELS]

    def _get_langchain_settings(self):
        self.ensure_one()

        ir_config = self.env["ir.config_parameter"].sudo()
        enabled_openai = (
            ir_config.get_param("softer_ia.enabled_openai", default="False") == "True"
        )
        enabled_gemini = (
            ir_config.get_param("softer_ia.enabled_gemini", default="False") == "True"
        )
        enabled_deepseek = (
            ir_config.get_param("softer_ia.enabled_deepseek", default="False") == "True"
        )

        openai_api_key = ir_config.get_param("softer_ia.openai_api_key")
        gemini_api_key = ir_config.get_param("softer_ia.gemini_api_key")
        deepseek_api_key = ir_config.get_param("softer_ia.deepseek_api_key")

        config = {}

        # Determinar el proveedor basado en el model_name seleccionado.
        provider = False
        for p, mid, _mname in self.ALL_MODELS:
            if mid == self.model_name:
                provider = p
                break

        if provider == "openai":
            if not enabled_openai:
                raise UserError("OpenAI no está habilitado en la configuración.")
            if not openai_api_key:
                raise UserError("La clave de API de OpenAI no está definida.")
            config["model"] = self.model_name
            config["api_key"] = openai_api_key
        elif provider == "gemini":
            if not enabled_gemini:
                raise UserError("Gemini no está habilitado en la configuración.")
            if not gemini_api_key:
                raise UserError("La clave de API de Gemini no está definida.")
            config["model"] = self.model_name
            config["google_api_key"] = gemini_api_key
        elif provider == "deepseek":
            if not enabled_deepseek:
                raise UserError("DeepSeek no está habilitado en la configuración.")
            if not deepseek_api_key:
                raise UserError("La clave de API de DeepSeek no está definida.")
            config["model"] = self.model_name
            config["api_key"] = deepseek_api_key
            config["base_url"] = "https://api.deepseek.com/v1"
        else:
            raise UserError(f"Modelo de IA '{self.model_name}' no soportado.")

        # Configuración común para todos los modelos (ej. temperatura).
        config["temperature"] = 0.7
        return config

    @api.model
    def get_provider_from_model_name(self, model_id):
        """
        Obtiene el proveedor de IA dado un model_id.
        """
        for provider, mid, _mname in self.ALL_MODELS:
            if mid == model_id:
                return provider
        return False
