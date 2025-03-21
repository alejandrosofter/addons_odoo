# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class SuscripcionLine(models.Model):
    _name = "softer.suscripcion.line"
    _description = "Línea de Suscripción"

    suscripcion_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    cantidad = fields.Float(string="Cantidad", default=1.0, required=True)
    precio_unitario = fields.Float(string="Precio Unitario", required=True)
    importe = fields.Float(string="Importe", compute="_compute_importe", store=True)
    anotacion = fields.Text(
        string="Anotación", help="Notas o comentarios sobre esta línea de suscripción"
    )
    company_id = fields.Many2one(
        related="suscripcion_id.company_id", store=True, index=True
    )

    @api.depends("cantidad", "precio_unitario")
    def _compute_importe(self):
        for line in self:
            line.importe = line.cantidad * line.precio_unitario

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.precio_unitario = self.product_id.list_price
