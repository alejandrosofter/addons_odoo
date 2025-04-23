# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SuscripcionLine(models.Model):
    _name = "softer.suscripcion.line"
    _description = "Línea de Suscripción"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
        readonly=True,
    )

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

    @api.depends("product_id", "cantidad")
    def _compute_name(self):
        """Calcula el nombre de la línea basado en el producto y cantidad"""
        for record in self:
            if record.product_id:
                record.name = f"{record.product_id.name} x {record.cantidad}"
            else:
                record.name = False
