# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class Suscripcion(models.Model):
    _name = "softer.suscripcion"
    _description = "Modelo de Suscripción"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "Nuevo",
    )

    cliente_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True
    )
    contacto_comunicacion = fields.Many2one(
        "res.partner", string="Comunicacion con...", required=True, tracking=True
    )
    fecha = fields.Date(
        string="Fecha de Creación", default=fields.Date.today, tracking=True
    )
    fecha_inicio = fields.Date(string="Fecha de Comienzo", required=True, tracking=True)
    fecha_fin = fields.Date(string="Fecha Fin", tracking=True)
    proxima_factura = fields.Date(string="Próxima Factura", tracking=True)

    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        default="borrador",
        tracking=True,
    )

    fecha_baja = fields.Date(string="Fecha de Baja", tracking=True)

    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )

    active = fields.Boolean(default=True)

    # Campos adicionales para la gestión de ventas
    sale_order_count = fields.Integer(
        string="Ventas", compute="_compute_sale_order_count"
    )
    sale_order_ids = fields.One2many(
        "sale.order", "subscription_id", string="Órdenes de Venta", copy=False
    )

    # Campos para la facturación
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Facturación",
        compute="_compute_partner_invoice",
        store=True,
        readonly=False,
    )

    # Campos para el seguimiento de la próxima facturación
    ultima_factura = fields.Date(string="Última Factura")

    tipo_temporalidad = fields.Selection(
        [("dia", "Día"), ("semana", "Semana"), ("mes", "Mes"), ("anio", "Año")],
        string="Tipo de Temporalidad",
        required=True,
        default="mes",
        tracking=True,
    )

    cantidad_recurrencia = fields.Integer(
        string="Cantidad de Recurrencia",
        required=True,
        tracking=True,
        help="Número de unidades de tiempo entre cada facturación",
    )

    line_ids = fields.One2many(
        "softer.suscripcion.line",
        "suscripcion_id",
        string="Líneas",
        required=True,
    )

    termino_pago = fields.Many2one(
        "account.payment.term",
        string="Término de Pago",
    )

    nombres_productos = fields.Text(
        string="Productos",
        compute="_compute_productos",
        store=True,
    )
    importeTotal = fields.Text(
        string="$ Total",
        compute="_compute_productos",
        store=False,  # No es necesario almacenar este campo
    )
    nombre_temporalidad = fields.Text(
        string="Factura Cada...",
        compute="_compute_nombre_temporalidad",
        store=False,  # No es necesario almacenar este campo
    )

    @api.onchange("cliente_id")
    def _onchange_cliente_id(self):
        """Actualiza contacto_comunicacion al cambiar cliente_id"""
        if self.cliente_id:
            self.contacto_comunicacion = self.cliente_id.id
        else:
            self.contacto_comunicacion = False

    @api.model
    def create(self, vals):
        # Obtener el cliente y los productos
        cliente = self.env["res.partner"].browse(vals.get("cliente_id"))
        productos = vals.get("nombres_productos", "")

        # Establecer el nombre en el formato {cliente}/{productos}
        vals["name"] = (
            f"{cliente.name}/{productos}" if cliente else "CLIENTE/ACTIVIDADES"
        )

        if vals.get("fecha_inicio") and not vals.get("proxima_factura"):
            vals["proxima_factura"] = vals.get("fecha_inicio")
        return super(Suscripcion, self).create(vals)

    @api.constrains("fecha_inicio", "fecha_fin")
    def _check_fechas(self):
        for record in self:
            if record.fecha_fin and record.fecha_inicio > record.fecha_fin:
                raise ValidationError(
                    "La fecha de fin no puede ser anterior a la fecha de inicio."
                )

    def action_suspender(self):
        self.ensure_one()
        self.estado = "suspendida"

    def action_activar(self):
        self.ensure_one()
        self.estado = "activa"

    def action_reactivar(self):
        self.ensure_one()
        self.estado = "activa"

    def action_baja(self):
        self.ensure_one()
        self.estado = "baja"
        self.fecha_baja = fields.Date.today()

    def _compute_sale_order_count(self):
        """Calcula el número de órdenes de venta relacionadas con la suscripción"""
        for record in self:
            record.sale_order_count = self.env["sale.order"].search_count(
                [("subscription_id", "=", record.id)]
            )

    def action_view_sales(self):
        """Acción para ver las órdenes de venta relacionadas"""
        self.ensure_one()
        return {
            "name": "Órdenes de Venta",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("subscription_id", "=", self.id)],
            "context": {"default_subscription_id": self.id},
        }

    def _prepare_sale_order_values(self):
        """Prepara los valores para crear una orden de venta"""
        self.ensure_one()
        return {
            "partner_id": self.cliente_id.id,
            "subscription_id": self.id,
            "payment_term_id": self.termino_pago,
            "date_order": fields.Datetime.now(),
            "origin": self.name,
            "company_id": self.company_id.id,
        }

    def _prepare_sale_order_line_values(self, order):
        """Prepara las líneas de la orden de venta"""
        lines = []
        for product in self.line_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "product_uom_qty": 1,
                        "price_unit": product.list_price,
                        "order_id": order.id,
                    },
                )
            )
        return lines

    def _calcular_siguiente_fecha(self, fecha_base):
        """Calcula la siguiente fecha según el tipo de temporalidad y cantidad"""
        self.ensure_one()
        if not fecha_base:
            return False

        if self.tipo_temporalidad == "dia":
            return fecha_base + relativedelta(days=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "semana":
            return fecha_base + relativedelta(weeks=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "mes":
            return fecha_base + relativedelta(months=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "anio":
            return fecha_base + relativedelta(years=self.cantidad_recurrencia)
        return False

    def create_sale_order(self):
        """Crea una orden de venta basada en la suscripción"""
        self.ensure_one()
        if self.estado != "activa":
            return False

        # Crear la orden de venta
        sale_order = self.env["sale.order"].create(self._prepare_sale_order_values())

        # Agregar líneas de producto
        lines = self._prepare_sale_order_line_values(sale_order)
        sale_order.write({"order_line": lines})

        # Actualizar fechas de facturación
        self.ultima_factura = fields.Date.today()
        self.proxima_factura = self._calcular_siguiente_fecha(fields.Date.today())

        return sale_order

    @api.onchange("tipo_temporalidad", "cantidad_recurrencia", "fecha_inicio")
    def _onchange_recurrencia(self):
        """Actualiza la próxima fecha de factura al cambiar la recurrencia"""
        if self.fecha_inicio:
            self.proxima_factura = self._calcular_siguiente_fecha(self.fecha_inicio)

    @api.constrains("cantidad_recurrencia")
    def _check_cantidad_recurrencia(self):
        for record in self:
            if record.cantidad_recurrencia <= 0:
                raise ValidationError(
                    "La cantidad de recurrencia debe ser mayor que cero."
                )

    @api.model
    def _cron_generate_sales(self):
        """Método para ser llamado por el cron job"""
        today = fields.Date.today()
        suscripciones = self.search(
            [
                ("estado", "=", "activa"),
                ("proxima_factura", "<=", today),
            ]
        )

        for suscripcion in suscripciones:
            suscripcion.create_sale_order()

        return True

    def unlink(self):
        """Sobrescribe el método de eliminación para archivar en lugar de eliminar"""
        for record in self:
            if record.sale_order_ids:
                # Si hay órdenes de venta relacionadas, archivamos la suscripción
                record.write(
                    {
                        "active": False,
                        "estado": "baja",
                        "fecha_baja": fields.Date.today(),
                    }
                )
                return True
        # Si no hay órdenes de venta, permite la eliminación normal
        return super(Suscripcion, self).unlink()

    def action_archive(self):
        """Método para archivar suscripciones"""
        for record in self:
            record.write(
                {"active": False, "estado": "baja", "fecha_baja": fields.Date.today()}
            )
        return True

    def action_unarchive(self):
        """Método para desarchivar suscripciones"""
        for record in self:
            record.write(
                {
                    "active": True,
                    "estado": "suspendida",  # Lo ponemos en suspendido para revisión
                }
            )
        return True

    @api.depends("cliente_id")
    def _compute_partner_invoice(self):
        for record in self:
            if record.cliente_id:
                addresses = record.cliente_id.child_ids.filtered(
                    lambda x: x.type == "invoice"
                )
                record.partner_invoice_id = (
                    addresses[0] if addresses else record.cliente_id
                )
            else:
                record.partner_invoice_id = False

    @api.depends("line_ids")
    def _compute_productos(self):
        for record in self:
            auxProductos = ", ".join(
                product.product_id.name for product in record.line_ids
            )
            total_importe = sum(line.precio_unitario for line in record.line_ids)
            record.importeTotal = total_importe
            record.nombres_productos = auxProductos
            record.name = f"{record.cliente_id.name}/{auxProductos}"

    @api.depends("tipo_temporalidad", "cantidad_recurrencia")
    def _compute_nombre_temporalidad(self):
        for record in self:
            record.nombre_temporalidad = f"{record.cantidad_recurrencia} {dict(self._fields['tipo_temporalidad'].selection).get(record.tipo_temporalidad, '')}"
