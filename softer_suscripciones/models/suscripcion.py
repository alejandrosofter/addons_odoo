# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class MotivoCambioEstado(models.Model):
    _name = "softer.suscripcion.motivo_cambio"
    _description = "Motivos de Cambio de Estado en Suscripciones"
    _order = "fecha desc"

    suscripcion_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", required=True, ondelete="cascade"
    )
    fecha = fields.Datetime(
        string="Fecha", default=lambda self: fields.Datetime.now(), required=True
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
            ("baja", "Baja"),
            ("suspendida", "Suspendida"),
        ],
        string="Estado",
        required=True,
    )
    motivo = fields.Text(string="Motivo", required=True)
    usuario_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user.id,
        required=True,
    )


class Suscripcion(models.Model):
    _name = "softer.suscripcion"
    _description = "Modelo de Suscripción"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )

    cliente_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        tracking=True,
        ondelete="cascade",
    )
    alta_id = fields.Many2one(
        "softer.suscripcion.alta", string="Alta", tracking=True, ondelete="cascade"
    )
    cliente_facturacion = fields.Many2one(
        "res.partner", string="Cliente Facturación", required=True, tracking=True
    )
    integrante_id = fields.Many2one(
        "softer.actividades.integrantes",
        string="Integrante",
        tracking=True,
        domain="[('cliente_contacto', '=', cliente_facturacion)]"
    )
    fecha = fields.Date(
        string="Fecha de Creación", default=fields.Date.today, tracking=True
    )
    fecha_inicio = fields.Date(string="Fecha de Comienzo", required=True, tracking=True)
    fecha_fin = fields.Date(string="Fecha Fin", tracking=True)
    proxima_factura = fields.Date(
        string="Próxima Factura",
        tracking=True,
        compute="_compute_proxima_factura",
        store=True,
        readonly=False,
    )

    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
            ("cancelada", "Cancelada"),
            ("suspendida", "Suspendida"),
        ],
        string="Estado",
        default="activa",
        tracking=True,
    )

    fecha_baja = fields.Date(string="Fecha de Baja", tracking=True)

    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )

    active = fields.Boolean(default=True)

    usoSuscripcion = fields.Boolean(
        string="Usa Suscripción?",
        default=True,
        tracking=True,
        help="Indica si la suscripción debe ser considerada para la "
        "generación automática de órdenes de venta",
    )

    categoria_id = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría",
        help="Categoría de la suscripción",
    )

    paga_debito_automatico = fields.Boolean(
        string="Paga Débito Automático",
        default=False,
        tracking=True,
        help="Indica si la suscripción se paga mediante débito automático",
    )

    facturar_al_generar = fields.Boolean(
        string="Facturar al Generar",
        default=False,
        tracking=True,
        help="Indica si se debe facturar automáticamente al generar la "
        "orden de venta",
    )

    notificar_al_generar = fields.Boolean(
        string="Notificar al Generar",
        default=False,
        tracking=True,
        help="Indica si se debe enviar una notificación al generar la "
        "orden de venta",
    )

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
        [
            ("diaria", "Diaria"),
            ("semanal", "Semanal"),
            ("mensual", "Mensual"),
            ("anual", "Anual"),
        ],
        string="Tipo de Temporalidad",
        required=True,
        default="mensual",
        tracking=True,
    )

    cantidad_recurrencia = fields.Integer(
        string="Cantidad de Recurrencia",
        required=True,
        tracking=True,
        help="Número de unidades de tiempo entre cada facturación",
        default=1,
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

    motivosCambioEstado = fields.One2many(
        "softer.suscripcion.motivo_cambio",
        "suscripcion_id",
        string="Historial de Cambios de Estado",
    )

    @api.onchange("cliente_id")
    def _onchange_cliente_id(self):
        """Actualiza cliente_facturacion al cambiar cliente_id"""
        if self.cliente_id:
            self.cliente_facturacion = self.cliente_id.id
        else:
            self.cliente_facturacion = False

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe el método create para registrar el estado inicial"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "softer.suscripcion"
                ) or _("New")

            # Crear el registro de cambio de estado si viene de subscription_upsert
            if self.env.context.get("from_subscription_upsert") and "estado" in vals:
                self.env["softer.suscripcion.motivo_cambio"].create(
                    {
                        "suscripcion_id": vals.get(
                            "id"
                        ),  # Se actualizará después del create
                        "estado": vals["estado"],
                        "motivo": vals.get("motivo_cambio", "Creación de suscripción"),
                        "usuario_id": self.env.user.id,
                    }
                )
        return super().create(vals_list)

    @api.constrains("fecha_inicio", "fecha_fin")
    def _check_fechas(self):
        for record in self:
            if record.fecha_fin and record.fecha_inicio > record.fecha_fin:
                raise ValidationError(
                    "La fecha de fin no puede ser anterior a la fecha de inicio."
                )

    def action_suspender(self):
        """Suspende la suscripción"""
        self.ensure_one()
        self.write({"estado": "suspendida"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La suscripción ha sido suspendida correctamente.",
                "type": "success",
            },
        }

    def action_activar(self):
        self.ensure_one()
        self.estado = "activa"

    def action_reactivar(self):
        self.ensure_one()
        self.estado = "activa"

    def action_baja(self):
        """Da de baja la suscripción"""
        self.ensure_one()
        self.write({"estado": "baja"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La suscripción ha sido dada de baja correctamente.",
                "type": "success",
            },
        }

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
            "payment_term_id": self.termino_pago.id if self.termino_pago else False,
            "date_order": fields.Datetime.now(),
            "origin": self.name,
            "company_id": self.company_id.id,
        }

    def _prepare_sale_order_line_values(self, order):
        """Prepara las líneas de la orden de venta"""
        lines = []
        for line in self.line_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": line.product_id.id,
                        "product_uom_qty": line.cantidad,
                        "price_unit": line.product_id.list_price,
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

        if self.tipo_temporalidad == "diaria":
            return fecha_base + relativedelta(days=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "semanal":
            return fecha_base + relativedelta(weeks=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "mensual":
            return fecha_base + relativedelta(months=self.cantidad_recurrencia)
        elif self.tipo_temporalidad == "anual":
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
                ("usoSuscripcion", "=", True),
            ]
        )

        _logger.info(f"Se encontraron {len(suscripciones)} suscripciones para generar")

        for suscripcion in suscripciones:
            try:
                _logger.info(f"Procesando suscripción: {suscripcion.name}")
                result = suscripcion.generar()
                if result and result.get("type") == "ir.actions.client":
                    _logger.info(f"Orden generada exitosamente para {suscripcion.name}")
                else:
                    _logger.warning(
                        f"No se pudo generar la orden para {suscripcion.name}"
                    )
            except Exception as e:
                _logger.error(
                    f"Error al generar orden de venta para suscripción "
                    f"{suscripcion.name}: {str(e)}"
                )

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
            # Calcular el total usando el precio actual del producto multiplicado por la cantidad
            total_importe = sum(
                line.product_id.list_price * line.cantidad for line in record.line_ids
            )
            record.importeTotal = total_importe
            record.nombres_productos = auxProductos
            record.name = f"{record.cliente_id.name}/{auxProductos}"

    @api.depends("tipo_temporalidad", "cantidad_recurrencia")
    def _compute_nombre_temporalidad(self):
        for record in self:
            record.nombre_temporalidad = f"{record.cantidad_recurrencia} {dict(self._fields['tipo_temporalidad'].selection).get(record.tipo_temporalidad, '')}"

    def print_adhesion(self):
        """Imprime el formulario de adhesión de la suscripción"""
        self.ensure_one()
        return self.env.ref(
            "softer_suscripciones.action_report_suscripcion_adhesion"
        ).report_action(self)

    @api.depends("cliente_id")
    def _compute_nombres_productos(self):
        for record in self:
            record.nombres_productos = ", ".join(
                record.cliente_id.mapped("product_line_ids.product_id.name")
            )

    @api.depends("fecha_inicio", "tipo_temporalidad", "cantidad_recurrencia")
    def _compute_proxima_factura(self):
        """Calcula la próxima fecha de facturación para cada suscripción"""
        for record in self:
            if (
                record.fecha_inicio
                and record.tipo_temporalidad
                and record.cantidad_recurrencia
            ):
                record.proxima_factura = record._calcular_siguiente_fecha(
                    record.fecha_inicio
                )
            else:
                record.proxima_factura = False

    def cambiarEstado(self, estado, motivo, usuario_id):
        """Cambia el estado de la suscripción y registra el cambio en el historial"""
        self.ensure_one()
        if self.estado != estado:
            # Registrar el cambio de estado
            self.env["softer.suscripcion.motivo_cambio"].create(
                {
                    "suscripcion_id": self.id,
                    "estado": estado,
                    "motivo": motivo,
                    "usuario_id": usuario_id,
                }
            )
            # Actualizar el estado de la suscripción
            self.write(
                {
                    "estado": estado,
                    "fecha_baja": fields.Date.today() if estado == "baja" else False,
                    "usoSuscripcion": estado == "activa",
                }
            )
            return True
        return False

    def action_alta(self):
        """Da de alta la suscripción"""
        self.ensure_one()
        self.write({"estado": "activa"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La suscripción ha sido activada correctamente.",
                "type": "success",
            },
        }

    def action_finalizar(self):
        """Finaliza la suscripción"""
        self.ensure_one()
        self.write({"estado": "finalizada"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "La suscripción ha sido finalizada correctamente.",
                "type": "success",
            },
        }

    def action_generar(self):
        """Acción para generar la orden de venta"""
        self.ensure_one()
        return self.generar()

    def generar(self):
        """Genera la orden de venta y actualiza los valores para la próxima generación"""
        self.ensure_one()
        if self.estado != "activa":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Advertencia",
                    "message": "Solo se pueden generar órdenes de venta para suscripciones activas.",
                    "type": "warning",
                },
            }

        # Crear la orden de venta
        sale_order = self.create_sale_order()
        if not sale_order:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "No se pudo crear la orden de venta.",
                    "type": "error",
                },
            }

        # Actualizar fechas de facturación
        self.ultima_factura = fields.Date.today()
        self.proxima_factura = self._calcular_siguiente_fecha(fields.Date.today())

        # Confirmar la orden de venta
        sale_order.action_confirm()

        # Si está configurado para facturar al generar, crear las facturas
        if self.facturar_al_generar:
            sale_order._create_invoices()

        # Si está configurado para notificar al generar, enviar notificación
        if self.notificar_al_generar:
            sale_order.message_post(
                body="Se ha generado la orden de venta automáticamente."
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "Se ha generado y confirmado la orden de venta correctamente.",
                "type": "success",
            },
        }
