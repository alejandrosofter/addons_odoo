# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class SuscripcionAjusteOcasional(models.Model):
    _name = "softer.suscripcion.ajuste"
    _description = "Ajustes Ocasionales en Suscripciones"
    _order = "anio desc, mes desc"

    name = fields.Char(
        string="Descripción",
        required=True,
        help="Descripción del ajuste (ej: Compra de pelotas, Descuento promocional)",
    )
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        required=True,
        ondelete="cascade",
    )
    tipo = fields.Selection(
        [
            ("cargo", "Cargo Adicional"),
            ("descuento_fijo", "Descuento Fijo"),
            ("descuento_porcentaje", "Descuento Porcentual"),
        ],
        string="Tipo de Ajuste",
        required=True,
        default="cargo",
    )

    importe = fields.Float(
        string="Importe",
        required=True,
        help="Importe del ajuste. Positivo para cargos, negativo para descuentos",
    )
    porcentaje = fields.Float(
        string="Porcentaje",
        help="Porcentaje de descuento",
    )

    mes = fields.Selection(
        [
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
        ],
        string="Mes",
        required=True,
        default=lambda self: str(datetime.now().month),
    )

    anio = fields.Integer(
        string="Año",
        required=True,
        default=lambda self: datetime.now().year,
    )

    activo = fields.Boolean(
        string="Activo",
        default=True,
    )
    aplicado = fields.Boolean(
        string="Aplicado",
        default=False,
        help="Indica si el ajuste ha sido aplicado en la facturacion del periodo",
    )

    notas = fields.Text(
        string="Notas",
        help="Notas adicionales sobre el ajuste",
    )

    producto_id = fields.Many2one(
        "product.product",
        required=True,
        string="Producto relacionado",
        help="Producto asociado a este ajuste (opcional)",
    )

    @api.onchange("tipo", "porcentaje", "importe")
    def _onchange_tipo(self):
        if self.tipo == "descuento_porcentaje":
            self.importe = 0
        elif self.tipo in ["cargo", "descuento_fijo"]:
            self.porcentaje = 0

    @api.constrains("importe", "porcentaje", "tipo")
    def _check_valores(self):
        for record in self:
            if record.tipo == "descuento_porcentaje":
                if record.porcentaje <= 0 or record.porcentaje > 100:
                    raise ValidationError("El porcentaje debe estar entre 0 y 100")
            elif record.tipo == "descuento_fijo" and record.importe > 0:
                raise ValidationError("Los descuentos deben tener importe negativo")

    @api.onchange("producto_id")
    def _onchange_producto_id(self):
        if self.producto_id:
            self.importe = self.producto_id.list_price

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.mes}/{record.anio})"
            result.append((record.id, name))
        return result
