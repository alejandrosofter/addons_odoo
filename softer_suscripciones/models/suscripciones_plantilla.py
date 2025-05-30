# -*- coding: utf-8 -*-
from odoo import models, fields


class SuscripcionesPlantillaItem(models.Model):
    _name = "softer.suscripcion.plantilla.item"
    _description = "Items de Plantilla de Suscripción"

    plantilla_id = fields.Many2one(
        "softer.suscripcion.plantilla",
        string="Plantilla",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    cantidad = fields.Float(string="Cantidad", default=1.0, required=True)
    tipo_temporalidad = fields.Selection(
        [
            ("diaria", "Diaria"),
            ("semanal", "Semanal"),
            ("mensual", "Mensual"),
            ("anual", "Anual"),
        ],
        string="Tipo de Temporalidad",
        required=True,
        default="mensual",
    )
    es_indefinido = fields.Boolean(
        string="Es Indefinido",
        help="Si es verdadero, la suscripción no tiene fecha de finalización",
        default=False,
    )
    es_suspencion = fields.Boolean(
        string="En Suspensión",
        help="Si es verdadero, la suscripción se puede suspender",
        default=False,
    )
    es_media_suspension = fields.Boolean(
        string="En Media Suspensión",
        help="Si es verdadero, la suscripción se activa al darle media suspensión",
        default=False,
    )
    es_baja = fields.Boolean(
        string="En Baja",
        help="Si es verdadero, la suscripción se puede dar de baja",
        default=False,
    )
    es_activo = fields.Boolean(
        string="En Activo",
        help="Si es verdadero, la suscripción está activa",
        default=True,
    )
    suscripcion_individual = fields.Boolean(
        string="Suscripción Individual",
        help="Si es verdadero, la suscripción es individual. En caso contrario, se crea una suscripción con varios productos",
        default=False,
    )
    cantidad_recurrencia = fields.Integer(
        string="Cantidad de Recurrencia",
        required=True,
        help="Número de unidades de tiempo entre cada facturación",
        default=1,
    )


class SuscripcionPlantilla(models.Model):
    _name = "softer.suscripcion.plantilla"
    _description = "Plantilla de Suscripción"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True, tracking=True)
    detalle = fields.Text(string="Detalle", tracking=True)
    items = fields.One2many(
        "softer.suscripcion.plantilla.item",
        "plantilla_id",
        string="Items",
        required=True,
    )
    active = fields.Boolean(default=True, tracking=True)
