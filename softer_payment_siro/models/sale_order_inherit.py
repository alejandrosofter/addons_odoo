from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ref = fields.Char(string="Referencia")

    def name_get(self):
        result = []
        for order in self:
            partner = order.partner_id.name or ""
            name = order.name or ""
            amount = order.amount_total or 0.0
            ref = order.ref or ""
            display = f"{partner} ({name}) [{ref}] ${amount:,.2f}"
            result.append((order.id, display))
        return result
