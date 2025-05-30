# -*- coding: utf-8 -*-
from odoo import models, fields, api

MESES = [
    ("1", "Enero"),
    ("2", "Febrero"),
    ("3", "Marzo"),
    ("4", "Abril"),
    ("5", "Mayo"),
    ("6", "Junio"),
    ("7", "Julio"),
    ("8", "Agosto"),
    ("9", "Septiembre"),
    ("10", "Octubre"),
    ("11", "Noviembre"),
    ("12", "Diciembre"),
]


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
    periodicidad = fields.Selection(
        [
            ("mensual", "Mensual"),
            ("anual", "Anual"),
        ],
        string="Periodicidad",
        required=True,
        default="mensual",
    )
    dia_facturacion = fields.Integer(
        string="Día de Facturación",
        help="Día del mes en el que se realiza la facturación en caso de que el tipo de temporalidad sea mensual",
        default=1,
    )
    mes_facturacion = fields.Integer(
        string="Mes de Facturación",
        help="Mes en el que se realiza la facturación en caso de que el tipo de temporalidad sea anual",
        default=1,
    )
    esta_suspendida = fields.Boolean(
        string="Está Suspendida",
        help="Indica si la línea de suscripción está suspendida",
        default=False,
    )
    en_suspension = fields.Boolean(
        string="En Suspensión",
        default=False,
    )
    en_activa = fields.Boolean(
        string="En Activa",
        default=True,
    )
    en_baja = fields.Boolean(
        string="En Baja",
        default=False,
    )
    company_id = fields.Many2one(
        related="suscripcion_id.company_id", store=True, index=True
    )
    meses_excluir = fields.Many2many(
        "softer.mes_habilitado",
        string="Meses Excluyentes",
        help="Meses en los que este concepto no se facturará",
    )

    @api.depends("product_id", "cantidad")
    def _compute_name(self):
        """Calcula el nombre de la línea basado en el producto y cantidad"""
        for record in self:
            if record.product_id:
                record.name = f"{record.product_id.name} x {record.cantidad}"
            else:
                record.name = False
