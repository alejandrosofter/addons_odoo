# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    interes = fields.Float(
        string="Interés (%)",
        help="Porcentaje de interés aplicado a esta forma de pago.",
    )
    descuento = fields.Float(
        string="Descuento (%)",
        help="Porcentaje de descuento aplicado a esta forma de pago.",
    )
    porcentual = fields.Float(
        string="Porcentual (%)",
        help="Porcentaje de descuento aplicado a esta forma de pago.",
    )
    fijo = fields.Float(
        string="Fijo",
        help="Monto fijo aplicado a esta forma de pago.",
    )
    producto = fields.Many2one(
        "product.product",
        string="Producto",
        help="Producto asociado a los cargos o descuentos de esta forma de pago.",
    )
    producto_interes = fields.Many2one(
        "product.product",
        string="Producto de Interés",
        help="Producto asociado al interés de esta forma de pago.",
    )
    producto_descuento = fields.Many2one(
        "product.product",
        string="Producto de Descuento",
        help="Producto asociado al descuento de esta forma de pago.",
    )
