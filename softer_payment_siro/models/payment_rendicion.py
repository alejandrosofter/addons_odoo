# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime
from odoo.addons.softer_payment_siro import const

_logger = logging.getLogger(__name__)


def _parse_fecha(fecha_str):
    """Convierte string de fecha SIRO (YYYYMMDD) a objeto date."""
    try:
        return datetime.strptime(fecha_str, "%Y%m%d").date()
    except ValueError:
        return False


def _parse_importe(importe_str):
    """Convierte string de importe SIRO a float."""
    try:
        return float(importe_str) / 100  # Los importes vienen multiplicados por 100
    except ValueError:
        return 0.0


class PaymentRendicion(models.Model):
    _name = "payment.rendicion"
    _description = "Rendición de Pagos SIRO"
    _order = "fecha_pago desc, id desc"

    fecha_pago = fields.Date(
        string="Fecha de Pago",
        required=True,
        index=True,
    )
    fecha_acreditacion = fields.Date(
        string="Fecha de Acreditación",
        required=True,
        index=True,
    )
    fecha_vto_1 = fields.Date(
        string="Fecha de Vencimiento",
        required=True,
    )
    importe_pagado = fields.Monetary(
        string="Importe Pagado",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    usuario = fields.Char(
        string="Usuario",
        required=True,
        index=True,
    )
    id_concepto = fields.Char(
        string="ID Concepto",
        required=True,
        index=True,
    )

    nro_comprobante_concepto = fields.Selection(
        const.CONCEPTOS_COMPROBANTE,
        string="Concepto Comprobante",
        required=True,
        default="0",
        help=f"Tipo de concepto del pago, se puede generar uno por cada periodo por cada comprobante/cliente. Los conceptos de los comprobantes son: {const.CONCEPTOS_COMPROBANTE}",
    )
    nro_comprobante_periodo = fields.Char(
        string="Periodo Nro Comprobante",
        required=True,
        index=True,
    )
    nro_comprobante_nro = fields.Char(
        string="Nro Comprobante",
        required=True,
        index=True,
    )
    codigo_barras = fields.Char(
        string="Código de Barras",
        required=True,
        index=True,
    )
    id_comprobante = fields.Char(
        string="ID Comprobante",
        required=True,
        index=True,
    )
    canal_cobro = fields.Selection(
        [
            # Puntos de pago físicos
            ("PF", "Pago Fácil"),
            ("RP", "Rapipago"),
            ("PP", "Provincia Pagos"),
            ("CE", "Cobro Express"),
            ("CEF", "Cobro Express sin factura"),
            ("RSF", "Rapipago sin factura"),
            ("FSF", "Pago Fácil sin factura"),
            ("ASF", "Plus Pagos sin factura"),
            ("PSF", "Bapro sin factura"),
            # Bancos y cajeros
            ("CJ", "Cajeros"),
            ("BM", "Banco Municipal"),
            ("BR", "Banco de Córdoba"),
            # Servicios de pago
            ("ASJ", "Plus Pagos"),
            ("LK", "Link Pagos"),
            ("PC", "Pago Mis Cuentas"),
            # Tarjetas
            ("MC", "Mastercard"),
            ("VS", "Visa"),
            ("MCR", "Mastercard rechazado"),
            ("VSR", "Visa rechazo"),
            # Débito directo
            ("DD+", "Débito Directo"),
            ("DD-", "Reversión Débito Directo"),
            ("DDR", "Rechazo Débito Directo"),
            # Botones de pago
            ("BPD", "Botón de Pagos Débito"),
            ("BPC", "Botón de Pagos Crédito"),
            ("BPR", "Botón de Pagos Rechazado"),
            # Canales online
            ("PCO", "PC Online"),
            ("LKO", "LK Online"),
            ("PCV", "Alta de deuda en PMC en Línea"),
            ("LKV", "Alta de deuda en LK Pagos en Línea"),
            # Transferencias
            ("TI", "Transferencia Imputada"),
            # QR y otros medios digitales
            ("TQR", "Pago con QR - Billetera virtual"),
            ("QRE", "QR Estático"),
            ("DB", "Debin"),
        ],
        string="Canal de Cobro",
        required=True,
    )
    codigo_rechazo = fields.Char(
        string="Código de Rechazo",
    )
    descripcion_rechazo = fields.Text(
        string="Descripción del Rechazo",
    )
    estado_pago = fields.Selection(
        [("pending", "Pendiente"), ("done", "Aceptado"), ("rejected", "Rechazado")],
        string="Estado de Pago",
        default="pending",
    )
    estado = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("asignada", "Asignada"),
            ("facturada", "Facturada"),
            ("pagada", "Pagada"),
        ],
        string="Estado Rendición",
        default="pending",
    )
    estado_orden = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("asignada", "Asignada"),
            ("facturada", "Facturada"),
            ("pagada", "Pagada"),
        ],
        string="Estado de Orden",
        default="pending",
    )
    detalle_orden = fields.Text(
        string="Detalle de Orden",
    )
    cuotas = fields.Integer(
        string="Cuotas",
        default=1,
    )
    order_id = fields.Many2one(
        "sale.order",
        string="Pedido de Venta",
        help="Pedido de venta relacionado a este item de deuda",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        help="Cliente asociado a la rendición de pago.",
    )
    payment_pendiente_pago_id = fields.Many2one(
        "payment.pendientes.pago",
        string="Lote de Pago",
        help="Registro de lote de pago asociado a esta rendición SIRO.",
    )
    tarjeta = fields.Char(
        string="Tarjeta",
    )
    payment_transaction_id = fields.Many2one(
        "payment.transaction",
        string="Transacción de Pago",
        readonly=True,
        ondelete="set null",
        help="Transacción de pago asociada a esta rendición",
    )
    id_pago = fields.Char(
        string="ID Pago",
        size=4,
        help="ID de pago (4 posiciones)",
    )
    id_resultado = fields.Char(
        string="ID Resultado",
        size=36,
        help="ID de resultado (36 posiciones)",
    )
    id_referencia_operacion = fields.Char(
        string="Referencia Operación",
        size=100,
        help="Referencia de la operación (100 posiciones)",
    )
    id_cliente_extendido = fields.Char(
        string="Cliente Extendido",
        size=15,
        help="ID cliente extendido (15 posiciones)",
    )
    nro_terminal = fields.Char(
        string="Nro Terminal",
        size=10,
        help="Número de terminal (10 posiciones)",
    )

    _sql_constraints = [
        (
            "unique_comprobante_fecha",
            "unique(id_comprobante, fecha_pago)",
            "El ID de comprobante ya existe para esa fecha.",
        ),
    ]

    @api.constrains("importe_pagado")
    def _check_importe_pagado(self):
        for record in self:
            if record.importe_pagado <= 0:
                raise ValidationError(_("El importe pagado debe ser mayor a cero."))

    @api.constrains("cuotas")
    def _check_cuotas(self):
        for record in self:
            if record.cuotas < 1:
                raise ValidationError(
                    _("El número de cuotas debe ser mayor o igual a 1.")
                )

    @api.model
    def _prepare_rendicion_vals(self, linea):
        """
        Procesa una línea del archivo de rendición SIRO.
        Formato fijo según especificación v5.2
        """
        # Posiciones según manual SIRO v5.2
        pos = {
            "fecha_pago": (0, 8),  # AAAAMMDD
            "fecha_acred": (8, 16),  # AAAAMMDD
            "fecha_vto": (16, 24),  # AAAAMMDD
            "importe": (24, 36),  # 11 enteros 2 decimales
            "usuario": (36, 44),  # 8 posiciones
            "id_concepto": (44, 45),  # 1 posiciones
            "codigo_barras": (45, 104),  # 59 posiciones
            "id_comprobante": (103, 123),  # 20 posiciones
            "canal": (123, 126),  # 3 posiciones
            "codigo_rechazo": (126, 129),  # 5 posiciones
            "desc_rechazo": (129, 149),  # 50 posiciones
            "cuotas": (149, 151),  # 2 posiciones
            "tarjeta": (151, 166),  # 20 posiciones
            "id_pago": (226, 230),  # 4 posiciones
            "id_resultado": (236, 272),  # 4 posiciones
            "id_referencia_operacion": (272, 372),  # 100 posiciones
            "id_cliente_extendido": (372, 387),  # 40 posiciones
            "nro_terminal": (387, 397),  #
        }

        # Extraer valores según posiciones

        vals = {
            "estado_pago": "pending",
            "fecha_pago": _parse_fecha(
                linea[pos["fecha_pago"][0] : pos["fecha_pago"][1]]
            ),
            "fecha_acreditacion": _parse_fecha(
                linea[pos["fecha_acred"][0] : pos["fecha_acred"][1]]
            ),
            "fecha_vto_1": _parse_fecha(
                linea[pos["fecha_vto"][0] : pos["fecha_vto"][1]]
            ),
            "importe_pagado": _parse_importe(
                linea[pos["importe"][0] : pos["importe"][1]]
            ),
            "id_comprobante": linea[
                pos["id_comprobante"][0] : pos["id_comprobante"][1]
            ].strip(),
            "usuario": linea[pos["usuario"][0] : pos["usuario"][1]].strip(),
            "codigo_barras": linea[
                pos["codigo_barras"][0] : pos["codigo_barras"][1]
            ].strip(),
            "id_concepto": linea[pos["id_concepto"][0] : pos["id_concepto"][1]].strip(),
            "codigo_rechazo": linea[
                pos["codigo_rechazo"][0] : pos["codigo_rechazo"][1]
            ].strip()
            or False,
            "descripcion_rechazo": linea[
                pos["desc_rechazo"][0] : pos["desc_rechazo"][1]
            ].strip()
            or False,
            "cuotas": int(linea[pos["cuotas"][0] : pos["cuotas"][1]].strip() or "1"),
            "tarjeta": linea[pos["tarjeta"][0] : pos["tarjeta"][1]].strip() or False,
            "canal_cobro": linea[pos["canal"][0] : pos["canal"][1]].strip(),
            "nro_terminal": linea[
                pos["nro_terminal"][0] : pos["nro_terminal"][1]
            ].strip(),
            "id_cliente_extendido": linea[
                pos["id_cliente_extendido"][0] : pos["id_cliente_extendido"][1]
            ].strip(),
            "id_referencia_operacion": linea[
                pos["id_referencia_operacion"][0] : pos["id_referencia_operacion"][1]
            ].strip(),
            "id_resultado": linea[
                pos["id_resultado"][0] : pos["id_resultado"][1]
            ].strip(),
            "id_pago": linea[pos["id_pago"][0] : pos["id_pago"][1]].strip(),
        }

        # Extraer y validar los componentes del nro_comprobante
        id_comprobante = vals["id_comprobante"]
        if len(id_comprobante) < 20:
            raise ValidationError(
                _(
                    f"El id_comprobante '{id_comprobante}' es demasiado corto para extraer los componentes SIRO."
                )
            )
        vals["nro_comprobante_nro"] = id_comprobante[:15]
        vals["nro_comprobante_concepto"] = id_comprobante[15:16]
        vals["nro_comprobante_periodo"] = id_comprobante[16:20]
        # Validar que las posiciones 16-20 sean numéricas y no vacías
        if not id_comprobante[15:20].isdigit():
            raise ValidationError(
                _(
                    f"Las posiciones 16-20 del id_comprobante '{id_comprobante}' deben ser numéricas y no vacías."
                )
            )

        if vals["codigo_rechazo"]:
            vals["estado_pago"] = "rejected"
        else:
            vals["estado_pago"] = "done"
        partner = self.env["res.partner"].search(
            [("id", "=", vals["usuario"])], limit=1
        )
        if not partner:
            raise ValidationError(
                _(f"No se encontró el cliente para el usuario '{vals['usuario']}'.")
            )
        vals["partner_id"] = partner.id
        payment_pendiente_pago = self.env["payment.pendientes.pago"].search(
            [
                ("nro_comprobante_nro", "=", vals["nro_comprobante_nro"]),
            ],
            limit=1,
        )
        if not payment_pendiente_pago:
            raise ValidationError(
                _(
                    f"No se encontró el pendiente de pago para el nro_comprobante_nro '{vals['nro_comprobante_nro']}'."
                )
            )
        vals["payment_pendiente_pago_id"] = payment_pendiente_pago.id

        return vals

    def _cron_procesar_rendiciones(self):
        """Procesa las rendiciones de SIRO diariamente."""
        _logger.info("Iniciando procesamiento automático de rendiciones SIRO")

        try:
            # Obtener el provider de SIRO
            provider = self.env["payment.provider"].search(
                [("code", "=", "siro")], limit=1
            )
            if not provider:
                _logger.error("No se encontró el proveedor de pagos SIRO")
                return False

            # Preparar fechas en formato YYYY-MM-DD
            # fecha_desde = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            # fecha_hasta = datetime.now().strftime("%Y-%m-%d")
            fecha_desde = "2020-11-01"
            fecha_hasta = "2020-11-10"
            # Llamar a la API de SIRO
            payload = {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "cuit_administrador": provider.cuit_administrador,
                "nro_empresa": provider.id_convenio,
            }

            _logger.info("Consultando rendiciones con payload: %s", payload)

            response = provider.callSiroApi(
                "siro/Listados/Proceso",
                payload=payload,
                method="POST",
                api="siro",
            ).json()

            # Procesar cada línea de rendición
            for linea in response:
                try:

                    vals = self._prepare_rendicion_vals(linea)

                    existing = self.search(
                        [
                            ("id_comprobante", "=", vals["id_comprobante"]),
                            ("fecha_pago", "=", vals["fecha_pago"]),
                        ],
                        limit=1,
                    )

                    if not existing:
                        try:

                            self.create(vals)
                            _logger.info("Rendición creada: %s", vals["id_comprobante"])
                        except Exception as create_exc:
                            _logger.error(
                                "Error creando rendición (puede ser duplicado): %s",
                                str(create_exc),
                            )
                            print(f"Error creando rendición: {create_exc}")
                            continue
                    else:

                        existing.write(vals)
                        _logger.info(
                            "Rendición actualizada: %s", vals["id_comprobante"]
                        )
                except Exception as e:
                    _logger.error("Error procesando línea de rendición: %s", str(e))

                    continue

            _logger.info("Procesamiento de rendiciones SIRO completado")
            return True

        except Exception as e:
            _logger.error("Error al procesar rendiciones SIRO: %s", str(e))

            return False

    def get_payment_method_id(self, canal):
        """Devuelve el payment.method.id correspondiente al canal SIRO."""

        method = self.env["payment.method"].search([("code", "=", "siro_all")], limit=1)
        return method.id if method else None

    def pagar_facturar(self):
        for rendicion in self:
            lote = rendicion.payment_pendiente_pago_id
            partner = rendicion.partner_id
            journal = lote.provider_id.journal_id

            # 1. Buscar todas las órdenes de venta del cliente en el lote
            ordenes = lote.items.filtered(lambda i: i.cliente_id == partner).mapped(
                "order_id"
            )
            if not ordenes:
                raise ValidationError(
                    _("No hay órdenes de venta para este cliente en el lote.")
                )

            # 2. Confirmar las órdenes si es necesario
            for orden in ordenes:
                if orden.state not in ["sale", "done"]:
                    orden.action_confirm()

            # 3. Crear una sola factura para todas las órdenes y validarla
            facturas = ordenes._create_invoices()
            for factura in facturas:
                if not factura.partner_id or factura.partner_id != partner:
                    factura.partner_id = partner.id
                factura.action_post()

            # 4. Registrar el pago sobre la(s) factura(s)
            siro_payment_method_line = journal.inbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id.code == "siro"
            )
            if not siro_payment_method_line:
                raise ValidationError(
                    _(
                        f"El diario {journal.display_name} no tiene configurada la línea de método de pago SIRO."
                    )
                )
            payment = False
            for factura in facturas:
                payment_register = (
                    self.env["account.payment.register"]
                    .with_context(
                        active_model="account.move",
                        active_ids=factura.ids,
                    )
                    .create(
                        {
                            "amount": rendicion.importe_pagado,
                            "journal_id": journal.id,
                            "payment_date": fields.Date.context_today(self),
                            "payment_method_line_id": siro_payment_method_line.id,
                        }
                    )
                )
                payment_register.action_create_payments()
                payment = self.env["account.payment"].search(
                    [
                        ("journal_id", "=", journal.id),
                        ("partner_id", "=", partner.id),
                        ("amount", "=", rendicion.importe_pagado),
                        ("date", "=", fields.Date.context_today(self)),
                    ],
                    limit=1,
                )
            rendicion.estado = "pagada"
            return payment

    def action_pagar_facturar(self):
        for rendicion in self:

            # Primero crear el pago
            try:
                pago = self.pagar_facturar()
            except Exception as e:
                print(str(e))
                return False
            # Luego crear la transacción y asociar el pago
            payment_method_id = self.env["payment.method"].search(
                [("code", "=", "siro_all")], limit=1
            )

            tx_vals = {
                "amount": rendicion.importe_pagado,
                "currency_id": rendicion.currency_id.id,
                "partner_id": rendicion.partner_id.id,
                "provider_id": rendicion.payment_pendiente_pago_id.provider_id.id,
                "provider_code": "siro",
                "reference": self.get_nro_referencia(rendicion.id_comprobante),
                "state": "done",
                "sale_order_ids": [
                    (
                        6,
                        0,
                        rendicion.payment_pendiente_pago_id.items.mapped(
                            "order_id"
                        ).ids,
                    )
                ],
                "payment_method_id": payment_method_id.id,
                "payment_id": pago.id,
            }
            print(tx_vals)
            try:
                tx = self.env["payment.transaction"].create(tx_vals)
                rendicion.payment_transaction_id = tx.id
            except Exception as e:
                print(f"Error creando transacción: {e}")
            return True

    @api.model
    def create(self, vals):
        # Crear la rendición normalmente
        rendicion = super().create(vals)

        if rendicion.estado_pago == "done":
            rendicion.action_pagar_facturar()
        return rendicion

    def get_nro_referencia(self, id_comprobante):
        """
        Devuelve un número de referencia único para payment.transaction.
        Si existe, agrega _1, _2, etc. al final.
        """
        env = self.env if hasattr(self, "env") else self
        base_ref = id_comprobante
        ref = base_ref
        i = 1
        while env["payment.transaction"].search_count([("reference", "=", ref)]) > 0:
            ref = f"{base_ref}_{i}"
            i += 1
        return ref
