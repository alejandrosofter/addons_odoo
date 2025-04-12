# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    subscription_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        tracking=True,
        help="Suscripción relacionada con esta orden de venta",
        ondelete="set null",
    )

    @api.model
    def create(self, vals):
        """Sobrescribe el método create para manejar la suscripción"""
        if vals.get("subscription_id"):
            subscription = self.env["softer.suscripcion"].browse(
                vals["subscription_id"]
            )
            if subscription:
                # Si viene de una suscripción, usar los datos de la suscripción
                if not vals.get("partner_id"):
                    vals["partner_id"] = subscription.cliente_id.id
                if not vals.get("payment_term_id"):
                    vals["payment_term_id"] = subscription.termino_pago.id
        return super(SaleOrder, self).create(vals)
