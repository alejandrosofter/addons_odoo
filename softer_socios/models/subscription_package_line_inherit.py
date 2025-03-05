# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SubscriptionPackageLineInherit(models.Model):
    _inherit = "subscription.package.product.line"

    # cliente_orden_venta = fields.Many2one(
    #     "res.partner", string="Cliente Orden de Venta"
    # )
    enabled = fields.Boolean(
        string="Habilitado?", help="Si no esta habilitado no crea item en venta"
    )
    detalle = fields.Text(string="Anotacion", help="Detalle")
