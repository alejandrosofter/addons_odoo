from odoo import models, fields, api
import requests
from odoo.exceptions import UserError


class WsapMessage(models.Model):
    _name = "wsap.message"
    _description = "Mensajes de WhatsApp"

    mensaje = fields.Text(string="Mensaje", required=True)
    nroTelefono = fields.Char(string="Número de Teléfono", required=True)
    estado = fields.Selection(
        [("enviado", "Enviado"), ("pendiente", "Pendiente"), ("error", "Error")],
        string="Estado",
        default="pendiente",
    )
    idBot = fields.Many2one("bot.whatsapp", string="Bot", required=True)

    @api.model
    def create(self, vals):
        """Crea un mensaje y lo envía automáticamente."""
        message = super(WsapMessage, self).create(vals)
        message.send_message()  # Enviar el mensaje al crear
        return message

    def send_message(self):
        """Envía un mensaje a través de la API de WhatsApp usando el bot asociado."""
        for record in self:
            if not record.idBot:
                raise UserError("El mensaje debe estar asociado a un bot.")

            # Llamar al método action_send_whatsapp del bot
            try:
                record.idBot.action_send_whatsapp(record.nroTelefono, record.mensaje)
                record.estado = "enviado"
            except Exception as e:
                record.estado = "error"
                raise UserError(f"Error al enviar el mensaje: {str(e)}")
