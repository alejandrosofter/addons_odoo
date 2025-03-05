# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SubscriptionPackagInherit(models.Model):
    _inherit = "subscription.package"

    # cliente_orden_venta = fields.Many2one(
    #     "res.partner", string="Cliente Orden de Venta"
    # )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        help="Select the invoice address associated with this record.",
        string="Invoice Address",
        readonly=False,  # Permite edición
    )
    formaPago = fields.Selection(
        selection=[("manual", "Manual"), ("debitoAutomatico", "Debito Automatico")],
        string="Forma de pago",
        # default="particular",
    )

    partner_shipping_id = fields.Many2one(
        "res.partner",
        help="Add shipping/service address",
        string="Shipping/Service Address",
        readonly=False,  # Permite edición
    )
