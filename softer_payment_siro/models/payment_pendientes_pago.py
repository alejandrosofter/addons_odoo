from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.softer_payment_siro import const
import re
from datetime import date


class PaymentPendientesPago(models.Model):
    _name = "payment.pendientes.pago"
    _description = "Pendientes de Pago"
    _order = "fecha_actual desc, id desc"

    provider_id = fields.Many2one(
        "payment.provider",
        string="Proveedor de Pago",
        required=True,
        domain="[('code', '=', 'siro')]",
        ondelete="restrict",
        help="Proveedor de pago SIRO para realizar las operaciones",
    )
    base_pagos = fields.Selection(
        [
            ("link", "Link Pagos"),
            ("pmc", "Pago Mis Cuentas"),
        ],
        string="Base de Pagos",
        required=True,
        help="Sistema de pagos a utilizar",
    )
    confirmar_automaticamente = fields.Boolean(
        string="Confirmar Automáticamente",
        default=False,
        help="Si está marcado, el lote se confirmará automáticamente",
    )
    concepto = fields.Selection(
        const.CONCEPTOS_COMPROBANTE,
        string="Concepto",
        required=True,
        default="0",
        help=(
            "Tipo de concepto del pago, se puede generar uno por cada periodo "
            "por cada comprobante/cliente."
        ),
    )
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("procesado", "Procesado"),
        ],
        string="Estado",
        required=True,
        default="pendiente",
    )

    lote_deuda_id = fields.Many2one(
        "payment.lote.deuda",
        string="Lote de Deuda",
        ondelete="restrict",
        help="Lote de deuda relacionado.",
    )
    periodo = fields.Char(string="Período", required=True)
    interes = fields.Float(string="Interés Diario", default=0.0)
    fecha_actual = fields.Date(
        string="Fecha Actual",
        required=True,
        default=fields.Date.context_today,
    )
    fecha_vto1 = fields.Date(string="Fecha Vto 1", required=True)
    fecha_vto2 = fields.Date(string="Fecha Vto 2")
    fecha_vto3 = fields.Date(string="Fecha Vto 3")
    items = fields.One2many(
        "payment.pendientes.pago.item",
        "pendiente_pago_id",
        string="Items de Pendiente de Pago",
        copy=True,
    )
    importe_total = fields.Monetary(
        string="Importe Total",
        compute="_compute_importe_total",
        store=True,
        currency_field="currency_id",
        help="Suma de los importes de los items.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id.id,
    )
    mensaje_cliente = fields.Char(
        string="Mensaje Cliente",
        size=25,
        help=(
            "Mensaje secundario para el ticket de pago (25 caracteres, solo "
            "mayúsculas y números, sin acentos ni ñ ni caracteres especiales)."
        ),
    )
    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
        help=(
            "Nombre generado automáticamente en base al período " "(ej: Pendiente 0524)"
        ),
    )

    @api.constrains("periodo")
    def _check_periodo_format(self):
        for record in self:
            if record.periodo and not re.match(
                r"^(0[1-9]|1[0-2])\d{2}$",
                record.periodo,
            ):
                raise ValidationError(
                    _(
                        "El período debe tener el formato MMAA "
                        "(ej: 0524 para mayo 2024)."
                    )
                )

    @api.onchange("periodo")
    def _onchange_periodo(self):
        if self.periodo and not re.match(
            r"^(0[1-9]|1[0-2])\d{2}$",
            self.periodo,
        ):
            return {
                "warning": {
                    "title": _("Formato de Período incorrecto"),
                    "message": _(
                        "El período debe tener el formato MMAA "
                        "(ej: 0524 para mayo 2024)."
                    ),
                }
            }

    def _get_cotizaciones(self):
        """
        Devuelve las cotizaciones (sale.order) en estado borrador o enviada.
        """
        return self.env["sale.order"].search([("state", "in", ["draft", "sent"])])

    def action_agregar_cotizaciones(self):
        """Agrega las cotizaciones como items en el pendiente de pago, sin duplicar."""
        self.ensure_one()
        if self.estado == "procesado":
            raise UserError(
                "No se pueden agregar cotizaciones a un pendiente ya procesado."
            )
        cotizaciones = self._get_cotizaciones()
        ordenes_existentes = self.items.mapped("order_id").ids
        items_vals = []
        for cot in cotizaciones:
            if cot.id not in ordenes_existentes:
                detalle = ", ".join(
                    f"{linea.name}"
                    + (
                        f" (${linea.price_unit:.2f})"
                        if linea.price_unit and not linea.display_type
                        else ""
                    )
                    for linea in cot.order_line
                    if not linea.display_type or linea.display_type != "line_note"
                )
                vals = {
                    "order_id": cot.id,
                    "cliente_id": cot.partner_id.id,
                    "importe": cot.amount_total,
                    "currency_id": cot.currency_id.id,
                    "detalle_orden": detalle,
                }
                items_vals.append((0, 0, vals))
        if items_vals:
            self.items = [(4, item.id) for item in self.items] + items_vals
        else:
            raise ValidationError(_("No hay cotizaciones nuevas para agregar."))
        return True

    @api.depends("items.importe")
    def _compute_importe_total(self):
        for record in self:
            record.importe_total = sum(item.importe for item in record.items)

    def _generar_mensajes_cliente(self, partner_name, mensaje_cliente):
        """Genera mensaje_ticket y mensaje_pantalla normalizados y formateados."""
        # Normalizar nombre cliente: mayúsculas, sin acentos ni ñ, solo letras/números/espacio
        nombre_cliente = partner_name.upper() if partner_name else ""
        nombre_cliente = (
            nombre_cliente.replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
            .replace("Ñ", "N")
        )
        nombre_cliente = "".join(c for c in nombre_cliente if c.isalnum() or c == " ")
        nombre_cliente = nombre_cliente[:15].ljust(15)
        # Normalizar mensaje_cliente
        mensaje_cliente = mensaje_cliente.upper() if mensaje_cliente else ""
        mensaje_cliente = (
            mensaje_cliente.replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
            .replace("Ñ", "N")
        )
        mensaje_cliente = "".join(c for c in mensaje_cliente if c.isalnum() or c == " ")
        mensaje_cliente = mensaje_cliente[:25].ljust(25)
        mensaje_ticket = f"{nombre_cliente}{mensaje_cliente}"
        mensaje_pantalla = mensaje_ticket[:15]
        return mensaje_ticket, mensaje_pantalla

    def _calcular_interes(self, monto, interes, dias):
        """Devuelve el monto actualizado según interés y días."""
        if not monto or not interes or not dias or dias <= 0:
            return monto
        return monto * ((1 + interes / 100) ** dias)

    def items_agrupados(self):
        """Devuelve una lista de dicts agrupados por cliente con los datos necesarios para el lote de deuda."""
        provider = self.provider_id
        items_por_cliente = {}
        for item in self.items:
            partner = item.cliente_id
            if partner:
                if partner.id not in items_por_cliente:
                    items_por_cliente[partner.id] = []
                items_por_cliente[partner.id].append(item)
        agrupados = []
        for items_cliente in items_por_cliente.values():
            partner = items_cliente[0].cliente_id
            titular = (
                partner.name.upper()[:15].strip() if partner and partner.name else ""
            )
            mensaje_ticket, mensaje_pantalla = self._generar_mensajes_cliente(
                titular, self.mensaje_cliente or ""
            )
            # Cód. pago electrónico: 9 dígitos ID cliente + 10 dígitos id_convenio
            id_cliente = str(partner.id).zfill(9) if partner else "000000000"
            id_convenio = ""
            if provider and hasattr(provider, "id_convenio") and provider.id_convenio:
                id_convenio = str(provider.id_convenio).zfill(10)
            cod_pago_electronico = f"{id_cliente}{id_convenio}"
            importe1 = sum(i.importe for i in items_cliente)
            importe2 = False
            importe3 = False
            if self.fecha_vto1 and self.fecha_vto2 and self.interes:
                dias_2 = (self.fecha_vto2 - self.fecha_vto1).days
                importe2 = self._calcular_interes(importe1, self.interes, dias_2)
            if self.fecha_vto2 and self.fecha_vto3 and self.interes:
                dias_3 = (self.fecha_vto3 - self.fecha_vto2).days
                importe3 = self._calcular_interes(
                    importe2 or importe1, self.interes, dias_3
                )

            if self.concepto and self.periodo:
                factura_id = (
                    str(self.id).zfill(15) + str(self.concepto) + str(self.periodo)
                )
                if not (len(factura_id) == 20 and factura_id.isdigit()):
                    raise ValidationError(
                        _(
                            "El campo factura_id debe tener 20 dígitos numéricos. "
                            "Valor generado: %s" % factura_id
                        )
                    )
            agrupados.append(
                {
                    "titular": id_cliente,
                    "cod_pago_electronico": cod_pago_electronico,
                    "factura_id": factura_id,
                    "partner_id": partner.id if partner else False,
                    "importe1": importe1,
                    "importe2": importe2,
                    "importe3": importe3,
                    "mensaje_ticket": mensaje_ticket,
                    "mensaje_pantalla": mensaje_pantalla,
                }
            )
        return agrupados

    def action_imputar(self):
        """Imputa el pendiente de pago, generando el lote de deuda y sus items completos."""
        self.ensure_one()
        if self.estado == "procesado":
            raise UserError("No se puede volver a imputar un registro ya procesado.")
        if self.estado != "pendiente":
            raise ValidationError(
                _("Solo se puede imputar si el estado es 'pendiente'.")
            )
        provider = self.provider_id
        if not provider:
            raise ValidationError(_("Debe seleccionar un proveedor de pago."))
        lote_vals = {
            "provider_id": provider.id,
            "base_pagos": self.base_pagos,
            "confirmar_automaticamente": self.confirmar_automaticamente,
            "fecha": self.fecha_actual,
            "currency_id": self.currency_id.id,
        }
        lote = self.env["payment.lote.deuda"].create(lote_vals)
        self.lote_deuda_id = lote.id
        for datos in self.items_agrupados():
            vals_item = {
                "lote_id": lote.id,
                "titular": datos["titular"],
                "cod_pago_electronico": datos["cod_pago_electronico"],
                "factura_id": datos["factura_id"],
                "fecha_vto_1": self.fecha_vto1,
                "importe1": datos["importe1"],
                "fecha_vto_2": self.fecha_vto2,
                "importe2": datos["importe2"],
                "fecha_vto_3": self.fecha_vto3,
                "importe3": datos["importe3"],
                "mensaje_ticket": datos["mensaje_ticket"],
                "mensaje_pantalla": datos["mensaje_pantalla"],
                "currency_id": self.currency_id.id,
                "partner_id": datos["partner_id"],
                "interes_dia": self.interes,
                "concepto": self.concepto,
            }
            self.env["payment.lote.deuda.item"].create(vals_item)
        self.confirmar_ordenes()
        self.estado = "procesado"
        return True

    def confirmar_ordenes(self):
        for record in self:
            record.items.mapped("order_id").action_confirm()

    @api.depends("periodo")
    def _compute_name(self):
        for record in self:
            if record.periodo:
                record.name = f"LOTE Periodo {record.periodo} | {record.importe_total}"
            else:
                record.name = "LOTE"

    @api.model
    def cron_revertir_ordenes_vencidas(self):
        """
        Recorre los pendientes de pago y si alguna fecha de vencimiento ya pasó,
        pone las órdenes relacionadas en estado 'draft' (cotización) solo si NO tienen factura.
        """
        hoy = date.today()
        pendientes = self.search(
            [
                "|",
                "|",
                ("fecha_vto1", "<", hoy),
                ("fecha_vto2", "<", hoy),
                ("fecha_vto3", "<", hoy),
                ("estado", "=", "pendiente"),
            ]
        )
        for pendiente in pendientes:
            for item in pendiente.items:
                order = item.order_id
                # Solo cambiar a draft si no tiene facturas asociadas
                if order and order.state != "draft" and not order.invoice_ids:
                    order.state = "draft"

    def pending_ordenes(self, orders):
        """
        Pasa a 'draft' todas las órdenes de venta que no tengan facturas asociadas
        y no estén ya en estado 'draft'.
        """
        for order in orders:
            if order.state != "draft" and not order.invoice_ids:
                order.state = "draft"

    def unlink(self):
        lotes_a_eliminar = []
        ordenes_a_draft = set()
        for record in self:
            lote = record.lote_deuda_id
            if lote and getattr(lote, "state", False) == "pendiente":
                lotes_a_eliminar.append(lote)
                # Agregar órdenes de items_deuda
                for item in lote.items_deuda:
                    if item.order_id:
                        ordenes_a_draft.add(item.order_id)
                # Agregar órdenes de items del pendiente
                for item in record.items:
                    if item.order_id:
                        ordenes_a_draft.add(item.order_id)
        res = super(PaymentPendientesPago, self).unlink()
        self.pending_ordenes(ordenes_a_draft)
        for lote in lotes_a_eliminar:
            lote.unlink()
        return res


class PaymentPendientesPagoItem(models.Model):
    _name = "payment.pendientes.pago.item"
    _description = "Item de Pendiente de Pago"
    _order = "id desc"

    pendiente_pago_id = fields.Many2one(
        "payment.pendientes.pago",
        string="Pendiente de Pago",
        required=True,
        ondelete="cascade",
    )
    order_id = fields.Many2one(
        "sale.order",
        string="Orden de Venta",
        required=True,
        help="Orden de venta relacionada.",
    )
    cliente_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        help="Cliente imputado a la orden.",
    )
    importe = fields.Monetary(
        string="Importe",
        required=True,
        currency_field="currency_id",
        help="Importe imputado.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    detalle_orden = fields.Char(
        string="Detalle Orden",
        help="Resumen de los productos y cantidades de la orden de venta.",
    )
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("imputado", "Imputado"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
    )

    @api.onchange("order_id")
    def _onchange_order_id(self):
        if self.order_id:
            self.importe = self.order_id.amount_total or 0.0
            self.cliente_id = self.order_id.partner_id
            self.detalle_orden = ", ".join(
                f"{linea.name}"
                + (
                    f" (${linea.price_unit:.2f})"
                    if linea.price_unit and not linea.display_type
                    else ""
                )
                for linea in self.order_id.order_line
                if not linea.display_type or linea.display_type != "line_note"
            )
        else:
            self.importe = 0.0
            self.cliente_id = False
            self.detalle_orden = False

    @api.constrains("importe")
    def _check_importe(self):
        for record in self:
            if record.importe <= 0:
                raise ValidationError(_("El importe debe ser mayor a 0."))
