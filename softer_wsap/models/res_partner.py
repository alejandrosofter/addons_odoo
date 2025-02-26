from odoo import models, fields, api
import re


class ResPartner(models.Model):
    _inherit = "res.partner"

    def send_whatsapp_message(self, message):
        """Envía un mensaje de WhatsApp al partner usando el bot predeterminado."""
        self.ensure_one()

        # Obtener el ID del bot predeterminado desde ir.config_parameter
        bot_id = self.env["ir.config_parameter"].sudo().get_param("whatsapp.idBotWsap")
        if not bot_id:
            raise ValueError("No hay un bot de WhatsApp configurado por defecto.")

        # Buscar el bot en el modelo bot.whatsapp
        bot = self.env["bot.whatsapp"].browse(int(bot_id))
        if not bot or not bot.external_id:
            raise ValueError(
                "El bot seleccionado no tiene un ID válido para enviar mensajes."
            )

        # Verificar que el partner tenga un número de teléfono
        if not self.phone:
            raise ValueError("El contacto no tiene un número de teléfono registrado.")

        # Usar el número de móvil si está disponible, sino el teléfono

        response = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.id,
                "message_type": "whatsapp",
                "idBot": bot.id,
                "body": message,
                "partner_ids": [(4, self.id)],
            }
        )
        return response

    def action_open_whatsapp_modal(self):

        return {
            "type": "ir.actions.act_window",
            "name": "Enviar WhatsApp",
            "res_model": "whatsapp.message.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("softer_wsap.whatsapp_message_wizard_form").id,
            "target": "new",
            "context": {
                "default_phone": self.phone,
                "default_message": f"Hola {self.name}, ¿cómo estás?",
                "default_partner_id": self.id,
            },
        }
