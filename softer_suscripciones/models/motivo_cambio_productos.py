# -*- coding: utf-8 -*-
from odoo import models, fields


class MotivoCambioProductos(models.Model):
    _name = "softer.suscripcion.motivo_cambio_productos"
    _description = "Motivo de Cambio de Productos en Suscripción"
    _order = "fecha desc"

    fecha = fields.Datetime(
        string="Fecha",
        default=lambda self: fields.Datetime.now(),
        required=True,
    )
    esta_suspendida = fields.Boolean(
        string="Está Suspendida",
        help="Indica si la línea de producto está suspendida en este cambio",
        default=False,
    )
    periodicidad = fields.Selection(
        [
            ("mensual", "Mensual"),
            ("anual", "Anual"),
        ],
        string="Periodicidad",
        required=True,
        default="mensual",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        required=True,
    )
    cliente_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
    )
    motivo = fields.Text(
        string="Motivo",
        required=True,
    )
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        required=True,
        ondelete="cascade",
    )
    suscripcion_linea_id = fields.Many2one(
        "softer.suscripcion.line",
        string="Línea de Suscripción",
        required=True,
        ondelete="cascade",
    )
