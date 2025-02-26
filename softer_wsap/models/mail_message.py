from odoo import models, fields, api


class MailMessage(models.Model):
    _inherit = "mail.message"

    message_type = fields.Selection(
        selection_add=[("whatsapp", "WhatsApp")],
        ondelete={"whatsapp": "cascade"},
    )

    idBot = fields.Many2one("bot.whatsapp", string="Bot de WhatsApp")

    @api.model
    def create(self, vals):
        """Intercepta la creación del mensaje y envía WhatsApp si corresponde."""
        message = super(MailMessage, self).create(vals)
        print(f"Enviando mensaje a {message.partner_ids}")
        if message.message_type == "whatsapp" and message.idBot:
            message._enviar_mensaje_whatsapp()

        return message

    def _enviar_mensaje_whatsapp(self):
        """Envía el mensaje de WhatsApp a todos los destinatarios."""
        if not self.idBot:
            return

        mensaje = self.body or ""

        for partner in self.partner_ids:
            nro_telefono = partner.phone or ""

            # Envía el mensaje si hay un número válido
            if nro_telefono and mensaje:
                self.idBot.action_send_whatsapp(nro_telefono, mensaje)
