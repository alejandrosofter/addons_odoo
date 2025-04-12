# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SuscripcionLine(models.Model):
    _name = "softer.suscripcion.line"
    _description = "Línea de Suscripción"

    suscripcion_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    cantidad = fields.Float(string="Cantidad", default=1.0, required=True)
    anotacion = fields.Text(
        string="Anotación", help="Notas o comentarios sobre esta línea de suscripción"
    )
    company_id = fields.Many2one(
        related="suscripcion_id.company_id", store=True, index=True
    )
