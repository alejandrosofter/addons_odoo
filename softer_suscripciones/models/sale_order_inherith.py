# En un archivo como models/sale.py
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    subscription_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", ondelete="set null"
    )
