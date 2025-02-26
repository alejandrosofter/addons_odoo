from odoo import models, fields, api
import requests
import base64


class AccountMoveSend(models.TransientModel):  # <- Debe ser TransientModel
    _name = "account.move.send"
    _inherit = "account.move.send"

    checkbox_send_whatsapp = fields.Boolean(string="Enviar por WhatsApp")

    def action_send_and_print(self):
        """Sobreescribimos la acción para enviar por WhatsApp si está seleccionado."""
        res = super().action_send_and_print()

        for move in self:
            if move.checkbox_send_whatsapp:
                move.send_invoice_whatsapp()

        return res

    def send_invoice_whatsapp(self):
        """Método para enviar la factura por WhatsApp usando el bot por defecto."""
        ir_config = self.env["ir.config_parameter"].sudo()
        id_bot = ir_config.get_param("whatsapp.idBotWsap", default="")

        if not id_bot:
            return
        # print(self.env["account.move.send"]._fields)
        for move in self:
            for partner in move.mail_partner_ids:  # Si existe un campo partner_ids
                if partner.phone:
                    message = f"Hola {partner.display_name}, aquí tienes tu factura {move.display_name}."
                    pdf_url = move._upload_invoice_pdf()
                    if not pdf_url:
                        print(
                            f"No se pudo generar la URL del PDF para {move.display_name}"
                        )
                        return

                    message = f"Hola {partner.display_name}, aquí tienes tu factura {move.display_name}: {pdf_url}"

                    bot = self.env["bot.whatsapp"].browse(int(id_bot))
                    bot.send_invoice_whatsapp(partner.phone, message, pdf_url)

    def _upload_invoice_pdf(self):
        """Genera el PDF de la factura y lo sube a un servidor público, devolviendo la URL."""
        report = self.env.ref("account.account_invoices")
        pdf_content, _ = report._render_qweb_pdf(self.ids)

        # Guarda el PDF en Odoo como adjunto
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"{self.name}.pdf",
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "account.move",
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )

        # Genera una URL pública si Odoo está configurado para compartir archivos
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/web/content/{attachment.id}/{attachment.name}"
