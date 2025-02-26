from odoo import models, fields, api


class WhatsAppMessageWizard(models.TransientModel):
    _name = "whatsapp.message.wizard"
    _description = "Enviar Mensaje por WhatsApp"

    phone = fields.Char(string="Teléfono", required=True)
    message = fields.Text(string="Mensaje", required=True, default="Hola, ¿cómo estás?")
    partner_id = fields.Many2one("res.partner", string="Persona", required=True)

    def action_create_message(self):
        """Antes de crear el registro, llama a send_whatsapp_message y cierra el wizard."""
        self.ensure_one()
        if self.partner_id:
            self.partner_id.send_whatsapp_message(self.message)
        return {"type": "ir.actions.act_window_close"}
