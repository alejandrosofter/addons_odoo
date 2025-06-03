# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SuscripcionesPlanItem(models.Model):
    _name = "softer.suscripcion.plan.item"
    _description = "Items de Plan de Suscripción"

    plan_id = fields.Many2one(
        "softer.suscripcion.plan",
        string="Plan",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    cantidad = fields.Float(string="Cantidad", default=1.0, required=True)
    tipo_temporalidad = fields.Selection(
        [
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
    en_suspension = fields.Boolean(
        string="En Suspensión",
        help="Si es verdadero, el servicio está en suspensión",
        default=False,
    )
    en_media_suspension = fields.Boolean(
        string="En Media Suspensión",
        help="Si es verdadero, el servicio está en media suspensión",
        default=False,
    )
    en_baja = fields.Boolean(
        string="En Baja",
        help="Si es verdadero, el servicio está dado de baja",
        default=False,
    )
    en_activo = fields.Boolean(
        string="En Activo",
        help="Si es verdadero, el servicio está activo",
        default=True,
    )
    dia_facturacion = fields.Selection(
        [(str(i), str(i)) for i in range(1, 32)],
        string="Día de Facturación",
        help=(
            "Día del mes en el que se realiza la facturación en caso de que el "
            "tipo de temporalidad sea mensual"
        ),
        default="1",
    )
    mes_facturacion = fields.Selection(
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
        string="Mes de Facturación",
        help=(
            "Mes en el que se realiza la facturación en caso de que el tipo de "
            "temporalidad sea anual"
        ),
        default="1",
    )
    suscripcion_individual = fields.Boolean(
        string="Suscripción Individual",
        help=(
            "Si es verdadero, la suscripción es individual. En caso contrario, "
            "se crea una suscripción con varios productos"
        ),
        default=False,
    )
    cantidad_recurrencia = fields.Integer(
        string="Cantidad de Recurrencia",
        required=True,
        help="Número de unidades de tiempo entre cada facturación",
        default=1,
    )
    meses_excluir = fields.Many2many(
        "softer.mes_habilitado",
        string="Excluir Meses",
        help="Meses en los que este ítem estará excluido",
    )

    tipo_ajuste = fields.Selection(
        [
            ("cargo", "Cargo %"),
            ("descuento_porcentual", "Descuento %"),
        ],
        string="Tipo de Ajuste",
        default="cargo",
        help=(
            "Indica si la línea es un cargo, un descuento fijo o un descuento "
            "porcentual"
        ),
    )
    importe = fields.Float(
        string="Importe",
        help="Importe fijo para cargos o descuentos fijos",
        default=0.0,
    )
    porcentaje = fields.Float(
        string="Porcentaje",
        help="Porcentaje para descuentos porcentuales",
        default=0.0,
    )

    @api.model
    def write(self, vals):
        res = super().write(vals)
        if vals:
            for rec in self:
                plan = rec.plan_id
                if plan:
                    plan._on_plan_changed()
        return res


class SuscripcionPlan(models.Model):
    _name = "softer.suscripcion.plan"
    _description = "Plan de Suscripción"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True, tracking=True)
    detalle = fields.Text(string="Detalle", tracking=True)
    items = fields.One2many(
        "softer.suscripcion.plan.item",
        "plan_id",
        string="Items",
        required=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    def write(self, vals):
        # if vals:
        #     raise UserError(
        #         _(
        #             "¡Atención! Al guardar, todas las suscripciones asociadas a "
        #             "este plan serán marcadas como pendientes de aplicar el nuevo plan."
        #         )
        #     )
        return super().write(vals)

    def _on_plan_changed(self):
        suscripciones = self.env["softer.suscripcion"].search(
            [("suscripcion_plan_id", "=", self.id)]
        )
        for suscripcion in suscripciones:
            suscripcion.pendiente_cambio_plan = True
