from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _create_invoices(self, grouped=False, final=False, date=None):
        """Sobrescribimos para manejar la creación de facturas desde el portal"""
        orders_to_invoice = self.filtered(lambda o: o.invoice_status == "to invoice")
        if not orders_to_invoice:
            raise UserError(_("No hay órdenes para facturar."))

        return super(SaleOrder, orders_to_invoice)._create_invoices(
            grouped=grouped, final=final, date=date
        )
