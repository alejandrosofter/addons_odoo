from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Alta(models.Model):
    _name = "softer.suscripcion.alta"
    _description = "Altas de Suscripciones"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha desc"

    name = fields.Char(
        string="Referencia", readonly=True, default=lambda self: _("Nueva Alta")
    )
    fecha = fields.Date(
        string="Fecha", required=True, default=fields.Date.context_today
    )
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)
    cliente_id = fields.Many2one("res.partner", string="Cliente", required=True)
    product_line_ids = fields.One2many(
        "softer.suscripcion.alta.product.line", "alta_id", string="Líneas de Productos"
    )
    suscripcion_ids = fields.One2many(
        "softer.suscripcion", "alta_id", string="Suscripciones", ondelete="cascade"
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("done", "Confirmado"), ("cancel", "Cancelado")],
        string="Estado",
        default="draft",
        tracking=True,
    )
    categoria_id = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría",
        help="Categoría de la suscripción",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nueva Alta")) == _("Nueva Alta"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "softer.suscripcion.alta"
                ) or _("Nueva Alta")
        return super().create(vals_list)

    def action_confirm(self):
        for record in self:
            if not record.product_line_ids:
                raise ValidationError(
                    _("Debe agregar al menos un producto para confirmar el alta.")
                )

            # Crear suscripciones para cada línea de producto
            for line in record.product_line_ids:
                if line.es_unica:
                    # Verificar si ya existe una suscripción activa para este cliente y producto
                    existing_suscripcion = self.env["softer.suscripcion"].search(
                        [
                            ("cliente_id", "=", record.cliente_id.id),
                            ("estado", "=", "activa"),
                            ("line_ids.product_id", "=", line.product_id.id),
                        ]
                    )
                    if existing_suscripcion:
                        raise ValidationError(
                            _(
                                "Ya existe una suscripción activa para el producto %s y el cliente %s"
                            )
                            % (line.product_id.name, record.cliente_id.name)
                        )

                # Calcular la fecha próxima de factura
                suscripcion_model = self.env["softer.suscripcion"]
                fecha_proxima = suscripcion_model._calcular_siguiente_fecha(
                    record.fecha_inicio
                )

                suscripcion_vals = {
                    "cliente_id": record.cliente_id.id,
                    "contacto_comunicacion": record.cliente_id.id,
                    "fecha_inicio": record.fecha_inicio,
                    "fecha_fin": line.fecha_fin if not line.es_indefinido else False,
                    "proxima_factura": fecha_proxima,
                    "paga_debito_automatico": line.es_debito_automatico,
                    "alta_id": record.id,
                    "estado": "activa",
                    "tipo_temporalidad": "mensual",  # Valor por defecto
                    "cantidad_recurrencia": 1,  # Valor por defecto
                    "categoria_id": (
                        record.categoria_id.id if record.categoria_id else False
                    ),
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": line.product_id.id,
                                "cantidad": line.quantity,
                            },
                        )
                    ],
                }
                self.env["softer.suscripcion"].create(suscripcion_vals)

            record.state = "done"

    def action_cancel(self):
        self.state = "cancel"

    def action_draft(self):
        self.state = "draft"


class AltaProductLine(models.Model):
    _name = "softer.suscripcion.alta.product.line"
    _description = "Líneas de Productos en Alta"

    alta_id = fields.Many2one(
        "softer.suscripcion.alta", string="Alta", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    quantity = fields.Float(string="Cantidad", default=1.0, required=True)
    es_indefinido = fields.Boolean(string="Es Indefinido", default=False)
    es_unica = fields.Boolean(string="Es Unica", default=False)
    fecha_fin = fields.Date(string="Fecha Fin")
    es_debito_automatico = fields.Boolean(string="Es Débito Automático", default=False)

    @api.onchange("es_indefinido")
    def _onchange_es_indefinido(self):
        if self.es_indefinido:
            self.fecha_fin = False
