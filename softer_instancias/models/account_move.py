from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for record in self:
            if "state" in vals and vals["state"] == "posted":
                self._check_if_paid(record)
        return res

    def _check_if_paid(self, invoice):
        if invoice.amount_residual == 0:
            # Llamar al método para manejar el evento de factura pagada
            self._handle_invoice_paid(invoice)

    def _handle_invoice_paid(self, invoice):
        for line in invoice.invoice_line_ids:
            product = line.product_id
            # Verificar si el producto tiene una instancia asociada
            if product.instancia_id:
                instancia = product.instancia_id
                # Aquí puedes agregar la lógica para manejar la instancia asociada
                # Por ejemplo, actualizar el estado de la instancia, llamar a un webhook, etc.
                self.env["ir.logging"].sudo().create(
                    {
                        "name": "Invoice PAGADOOOOO",
                        "type": "server",
                        "dbname": self.env.cr.dbname,
                        "level": "INFO",
                        "message": f"Invoice {invoice.name} has been paid. Related instance: {instancia.name}",
                        "path": "account.move",
                        "line": "0",
                        "func": "write",
                    }
                )
