from odoo import models, fields, api


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    def action_send_whatsapp(self):
        """Envía un mensaje de WhatsApp al cliente."""
        self.ensure_one()
        if not self.partner_id.mobile and not self.partner_id.phone:
            raise models.ValidationError(
                "El cliente no tiene número de teléfono configurado"
            )

        # Obtener el número de teléfono (primero móvil, luego fijo)
        phone = self.partner_id.mobile or self.partner_id.phone

        # Crear el mensaje
        message = (
            f"Hola {self.partner_id.name},\n"
            f"Tu pedido {self.name} por un total de "
            f"{self.amount_total} {self.currency_id.name} "
            f"ha sido confirmado.\n"
            f"Gracias por tu compra!"
        )

        # Buscar la primera instancia de WhatsApp activa
        instance = self.env["evolution.api.numbers"].search(
            [("estado", "=", "active")], limit=1
        )

        if not instance:
            raise models.ValidationError("No hay instancias de WhatsApp activas")

        # Crear y enviar el mensaje
        self.env["evolution.api.message"].create(
            {
                "number_id": instance.id,
                "numeroDestino": phone,
                "type": "text",
                "text": message,
            }
        )

    def action_send_whatsapp_multi(self):
        """Envía mensajes de WhatsApp a múltiples pedidos."""
        for order in self:
            try:
                order.action_send_whatsapp()
            except Exception as e:
                # Log el error pero continúa con los siguientes
                self.env.logger.error(
                    "Error enviando WhatsApp para %s: %s", order.name, str(e)
                )
