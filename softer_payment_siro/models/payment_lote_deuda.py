from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import re
import base64
from odoo.exceptions import UserError
from odoo import _
from datetime import timedelta
from odoo.addons.softer_payment_siro import const


def _format_number(number, length, decimals=0):
    """Formatea un número a string con longitud fija y decimales."""
    if not number:
        number = 0
    # Multiplicar por 100 para mover los decimales
    number = int(round(number * (10**decimals), 0))
    return str(number).zfill(length)


def _format_date(date_value):
    """Formatea una fecha al formato AAAAMMDD."""
    if not date_value:
        return "00000000"
    return date_value.strftime("%Y%m%d")


class PaymentLoteDeudaItem(models.Model):
    _name = "payment.lote.deuda.item"
    _description = "Items de Deuda para Lotes de Pago"
    _rec_name = "factura_id"

    lote_id = fields.Many2one(
        "payment.lote.deuda",
        string="Lote de Deuda",
        required=True,
        ondelete="cascade",
    )

    titular = fields.Char(
        string="Titular",
        size=9,
        required=True,
        help="Número de identificación del titular (9 dígitos numéricos)",
    )

    cod_pago_electronico = fields.Char(
        string="Código de Pago Electrónico",
        size=19,
        required=True,
        help="Código de pago electrónico (19 dígitos numéricos)",
    )

    factura_id = fields.Char(
        string="ID Factura",
        size=20,
        required=True,
        help="Identificador de la factura (20 caracteres)",
    )

    fecha_vto_1 = fields.Date(
        string="Fecha Vencimiento 1",
        required=True,
        help="Primera fecha de vencimiento",
    )

    importe1 = fields.Monetary(
        string="Importe 1",
        required=True,
        currency_field="currency_id",
        help="Importe para el primer vencimiento",
    )

    fecha_vto_2 = fields.Date(
        string="Fecha Vencimiento 2",
        help="Segunda fecha de vencimiento",
    )

    importe2 = fields.Monetary(
        string="Importe 2",
        currency_field="currency_id",
        help="Importe para el segundo vencimiento",
    )

    fecha_vto_3 = fields.Date(
        string="Fecha Vencimiento 3",
        help="Tercera fecha de vencimiento",
    )

    importe3 = fields.Monetary(
        string="Importe 3",
        currency_field="currency_id",
        help="Importe para el tercer vencimiento",
    )

    mensaje_ticket = fields.Char(
        string="Mensaje Ticket",
        size=40,
        help="Mensaje a mostrar en el ticket (máx. 40 caracteres)",
    )

    mensaje_pantalla = fields.Char(
        string="Mensaje Pantalla",
        size=15,
        help="Mensaje a mostrar en la pantalla (máx. 15 caracteres)",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        related="lote_id.currency_id",
        store=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        help="Cliente asociado a este item de deuda",
        required=True,
    )

    order_id = fields.Many2one(
        "sale.order",
        string="Pedido de Venta",
        help="Pedido de venta relacionado a este item de deuda",
    )
    interes_dia = fields.Float(
        string="Interes % Día",
        help="Interes % por día",
        default=0.0,
    )

    concepto = fields.Selection(
        const.CONCEPTOS_COMPROBANTE,
        string="Concepto",
        required=True,
        default="0",
        help="Tipo de concepto del pago, se puede generar uno por cada periodo por cada comprobante/cliente.",
    )

    @api.onchange("order_id")
    def _onchange_order_id(self):
        if self.order_id:
            self.importe1 = self.order_id.amount_total or 0.0
            self.importe2 = self.order_id.amount_total or 0.0
            self.importe3 = self.order_id.amount_total or 0.0
            self.fecha_vto_1 = self.order_id.date_order
            self.fecha_vto_2 = self.order_id.date_order + timedelta(days=1)
            self.fecha_vto_3 = self.order_id.date_order + timedelta(days=2)

            self.factura_id = str(self.order_id.id).zfill(20)
            if self.order_id.partner_id:
                self.partner_id = self.order_id.partner_id
            else:
                self.partner_id = False
        else:
            self.importe1 = 0.0
            self.fecha_vto_1 = False
            self.factura_id = False
            self.partner_id = False

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.titular = str(self.partner_id.id).zfill(9)
            provider = self.env["payment.provider"].search(
                [("code", "=", "siro")], limit=1
            )
            if provider:
                self.cod_pago_electronico = f"{self.titular}{provider.id_convenio}"
            else:
                self.cod_pago_electronico = False
        else:
            self.titular = False
            self.cod_pago_electronico = False

    @api.constrains("titular")
    def _check_titular(self):
        for record in self:
            if (
                not record.titular
                or not record.titular.isdigit()
                or len(record.titular) != 9
            ):
                raise ValidationError(
                    "El titular debe contener exactamente 9 dígitos numéricos."
                )

    @api.constrains("cod_pago_electronico")
    def _check_cod_pago_electronico(self):
        for record in self:
            if (
                not record.cod_pago_electronico
                or not record.cod_pago_electronico.isdigit()
                or len(record.cod_pago_electronico) != 19
            ):
                raise ValidationError(
                    "El código de pago electrónico debe contener exactamente 19 dígitos numéricos."
                )

    @api.constrains("factura_id")
    def _check_factura_id(self):
        for record in self:
            if not record.factura_id or len(record.factura_id) > 20:
                raise ValidationError(
                    "El ID de factura no puede superar los 20 caracteres."
                )

    @api.constrains("fecha_vto_1", "fecha_vto_2", "fecha_vto_3")
    def _check_fechas_vencimiento(self):
        today = date.today()
        for record in self:
            if record.fecha_vto_1 and record.fecha_vto_1 < today:
                raise ValidationError(
                    "La fecha de vencimiento 1 no puede ser anterior a hoy."
                )
            if record.fecha_vto_2:
                if not record.fecha_vto_1:
                    raise ValidationError(
                        "No puede definir fecha de vencimiento 2 sin fecha de vencimiento 1."
                    )
                if record.fecha_vto_2 <= record.fecha_vto_1:
                    raise ValidationError(
                        "La fecha de vencimiento 2 debe ser posterior a la fecha de vencimiento 1."
                    )
            if record.fecha_vto_3:
                if not record.fecha_vto_2:
                    raise ValidationError(
                        "No puede definir fecha de vencimiento 3 sin fecha de vencimiento 2."
                    )
                if record.fecha_vto_3 <= record.fecha_vto_2:
                    raise ValidationError(
                        "La fecha de vencimiento 3 debe ser posterior a la fecha de vencimiento 2."
                    )

    @api.constrains("importe1", "importe2", "importe3")
    def _check_importes(self):
        for record in self:
            if record.importe1 <= 0:
                raise ValidationError("El importe 1 debe ser mayor a 0.")
            if record.fecha_vto_2 and not record.importe2:
                raise ValidationError(
                    "Debe definir importe 2 si define fecha de vencimiento 2."
                )
            if record.fecha_vto_3 and not record.importe3:
                raise ValidationError(
                    "Debe definir importe 3 si define fecha de vencimiento 3."
                )
            if record.importe2 and record.importe2 < record.importe1:
                raise ValidationError("El importe 2 debe ser mayor al importe 1.")
            if record.importe3 and record.importe3 < record.importe2:
                raise ValidationError("El importe 3 debe ser mayor al importe 2.")

    @api.constrains("mensaje_ticket", "mensaje_pantalla")
    def _check_mensajes(self):
        for record in self:
            if record.mensaje_ticket and len(record.mensaje_ticket) > 40:
                raise ValidationError(
                    "El mensaje del ticket no puede superar los 40 caracteres."
                )
            if record.mensaje_pantalla and len(record.mensaje_pantalla) > 15:
                raise ValidationError(
                    "El mensaje de pantalla no puede superar los 15 caracteres."
                )

    @api.onchange(
        "interes_dia", "fecha_vto_1", "fecha_vto_2", "fecha_vto_3", "importe1"
    )
    def _onchange_interes_dia(self):
        if self.fecha_vto_1 and self.fecha_vto_2 and self.importe1 and self.interes_dia:
            dias_2 = (self.fecha_vto_2 - self.fecha_vto_1).days
            self.importe2 = self.importe1 * ((1 + self.interes_dia / 100) ** dias_2)
        if self.fecha_vto_2 and self.fecha_vto_3 and self.importe2 and self.interes_dia:
            dias_3 = (self.fecha_vto_3 - self.fecha_vto_2).days
            self.importe3 = self.importe2 * ((1 + self.interes_dia / 100) ** dias_3)

    def _generate_pmc_line(self):
        """Genera la línea de texto para Pago Mis Cuentas."""
        # Validar campos requeridos
        if not (self.titular and self.cod_pago_electronico and self.factura_id):
            raise ValidationError("Titular, Código de Pago y Factura son requeridos.")

        # Formatear campos según especificación
        titular = self.titular.ljust(9)
        cod_pago = self.cod_pago_electronico.ljust(19)
        factura = self.factura_id.ljust(20)
        fecha1 = _format_date(self.fecha_vto_1)
        importe1 = _format_number(self.importe1, 11, 2)
        fecha2 = _format_date(self.fecha_vto_2)
        importe2 = _format_number(self.importe2, 11, 2)
        fecha3 = _format_date(self.fecha_vto_3)
        importe3 = _format_number(self.importe3, 11, 2)
        msj_ticket = (self.mensaje_ticket or "").ljust(40)
        msj_pantalla = (self.mensaje_pantalla or "").ljust(15)

        # Construir línea según formato
        line = (
            f"{titular}{cod_pago}{factura}{fecha1}{importe1}"
            f"{fecha2}{importe2}{fecha3}{importe3}"
            f"{msj_ticket}{msj_pantalla}"
        )

        return line


class PaymentLoteDeuda(models.Model):
    _name = "payment.lote.deuda"
    _description = "Lotes de Deuda para Pagos"
    _order = "fecha desc"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        readonly=True,
        copy=False,
        default="/",
    )

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

    fecha = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
        help="Fecha del lote de deuda",
    )

    state = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("aplicado", "Aplicado"),
            ("enviado", "Enviado"),
            ("procesado", "Procesado"),
            ("error", "Error"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
        tracking=True,
        help="Estado del lote de deuda",
    )

    nro_transaccion = fields.Char(
        string="Número de Transacción",
        readonly=True,
        copy=False,
        help="Número de transacción generado por el sistema de pagos",
    )

    detalle_estado = fields.Text(
        string="Detalle del Estado",
        readonly=True,
        help="Información detallada sobre el estado actual del lote",
    )

    base_pagos_info = fields.Text(
        string="Información Base de Pagos",
        help="Información adicional sobre la base de pagos",
    )

    items_deuda = fields.One2many(
        "payment.lote.deuda.item",
        "lote_id",
        string="Items de Deuda",
        copy=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    active = fields.Boolean(
        default=True,
        help="Permite archivar/desarchivar el lote",
    )

    # Campos para información de procesamiento
    fecha_registro = fields.Datetime(
        string="Fecha de Registro",
        readonly=True,
        help="Fecha en que se registró el lote en el sistema de pagos",
    )
    estado_proceso = fields.Selection(
        [
            ("PENDIENTE", "Pendiente"),
            ("PROCESADA", "Procesado"),
            ("ERROR", "Error"),
        ],
        string="Estado de Proceso",
        readonly=True,
        help="Estado del proceso del lote",
    )

    fecha_envio = fields.Datetime(
        string="Fecha de Envío",
        readonly=True,
        help="Fecha en que se envió el lote al sistema de pagos",
    )

    fecha_proceso = fields.Datetime(
        string="Fecha de Proceso",
        readonly=True,
        help="Fecha en que se procesó el lote en el sistema de pagos",
    )

    registros_correctos = fields.Integer(
        string="Registros Correctos",
        readonly=True,
        help="Cantidad de registros procesados correctamente",
    )

    registros_erroneos = fields.Integer(
        string="Registros con Error",
        readonly=True,
        help="Cantidad de registros con errores",
    )

    registros_procesados = fields.Integer(
        string="Registros Procesados",
        readonly=True,
        help="Cantidad total de registros procesados",
    )

    total_primer_vencimiento = fields.Monetary(
        string="Total 1er Vencimiento",
        readonly=True,
        currency_field="currency_id",
        help="Importe total del primer vencimiento",
    )

    total_segundo_vencimiento = fields.Monetary(
        string="Total 2do Vencimiento",
        readonly=True,
        currency_field="currency_id",
        help="Importe total del segundo vencimiento",
    )

    total_tercer_vencimiento = fields.Monetary(
        string="Total 3er Vencimiento",
        readonly=True,
        currency_field="currency_id",
        help="Importe total del tercer vencimiento",
    )

    error_descripcion = fields.Text(
        string="Descripción del Error",
        readonly=True,
        help="Descripción detallada del error si ocurrió alguno",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe el método create para asignar la secuencia del nombre."""
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("payment.lote.deuda") or "/"
                )
        return super().create(vals_list)

    def action_procesar(self):
        """
        Procesa el lote de deuda.
        Solo se pueden procesar lotes en estado 'aplicado'.
        """
        self.ensure_one()
        if self.state != "aplicado":
            raise UserError(_("Solo se pueden procesar lotes en estado aplicado."))
        request = self.provider_id.callSiroApi(
            "siro/Pagos",
            {
                "confirmar_automaticamente": self.confirmar_automaticamente,
                "base_pagos": self.base_pagos_info,
            },
            method="POST",
            api="siro",
        ).json()
        print(request)
        if request.get("nro_transaccion"):
            self.nro_transaccion = request.get("nro_transaccion")
            self.state = "enviado"
            self.detalle_estado = "Lote enviado exitosamente"
            return [
                {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Éxito"),
                        "message": _("Se ha procesado correctamente el lote!"),
                        "sticky": False,
                        "type": "success",
                    },
                },
                {"type": "ir.actions.client", "tag": "reload"},
            ]
        else:
            self.state = "error"
            self.detalle_estado = "Error al procesar el lote"
            return [
                {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Error"),
                        "message": _("Error al procesar el lote!"),
                        "sticky": False,
                        "type": "danger",
                    },
                },
                {"type": "ir.actions.client", "tag": "reload"},
            ]

    def set_procesamiento_values(self, response):
        """
        Actualiza los valores del lote según la respuesta de la API.

        Args:
            response (dict): Respuesta de la API con los valores del procesamiento
        """
        self.ensure_one()

        estado = response.get("estado", "").upper()

        # Construir mensaje detallado
        detalles = []
        if response.get("fecha_registro"):
            detalles.append(f"Fecha Registro: {response['fecha_registro']}")
        if response.get("fecha_envio"):
            detalles.append(f"Fecha Envío: {response['fecha_envio']}")
        if response.get("fecha_proceso"):
            detalles.append(f"Fecha Proceso: {response['fecha_proceso']}")

        # Agregar información de registros si está disponible
        if response.get("cantidad_registros_correctos"):
            detalles.append(
                f"Registros Correctos: {response['cantidad_registros_correctos']}"
            )
        if response.get("cantidad_registros_erroneos"):
            detalles.append(
                f"Registros con Error: {response['cantidad_registros_erroneos']}"
            )
        if response.get("cantidad_registros_procesados"):
            detalles.append(
                f"Registros Procesados: {response['cantidad_registros_procesados']}"
            )

        # Agregar totales si están disponibles
        if response.get("total_primer_vencimiento"):
            detalles.append(
                f"Total 1er Vencimiento: {response['total_primer_vencimiento']}"
            )
        if response.get("total_segundo_vencimiento"):
            detalles.append(
                f"Total 2do Vencimiento: {response['total_segundo_vencimiento']}"
            )
        if response.get("total_tercer_vencimiento"):
            detalles.append(
                f"Total 3er Vencimiento: {response['total_tercer_vencimiento']}"
            )

        # Agregar errores si existen
        if response.get("error_descripcion"):
            detalles.append(f"Error: {response['error_descripcion']}")
        if response.get("errores"):
            detalles.append("Errores:")
            for error in response["errores"]:
                detalles.append(f"- {error}")

        # Convertir fechas ISO8601 a formato Odoo
        def convert_datetime(value):
            if not value:
                return False
            # Remover la parte de microsegundos y zona horaria si existe
            value = value.split(".")[0].replace("T", " ")
            return value

        # Actualizar valores del lote
        vals = {
            "state": "procesado" if estado == "PROCESADA" else self.state,
            "estado_proceso": estado,
            "detalle_estado": "\n".join(detalles),
            "fecha_registro": convert_datetime(response.get("fecha_registro")),
            "fecha_envio": convert_datetime(response.get("fecha_envio")),
            "fecha_proceso": convert_datetime(response.get("fecha_proceso")),
            "registros_correctos": response.get("cantidad_registros_correctos"),
            "registros_erroneos": response.get("cantidad_registros_erroneos"),
            "registros_procesados": response.get("cantidad_registros_procesados"),
            "total_primer_vencimiento": response.get("total_primer_vencimiento"),
            "total_segundo_vencimiento": response.get("total_segundo_vencimiento"),
            "total_tercer_vencimiento": response.get("total_tercer_vencimiento"),
            "error_descripcion": response.get("error_descripcion"),
        }

        self.write(vals)

        # Retornar notificación según el estado
        if estado == "PROCESADA":
            raise UserError(_("El lote se ha procesado correctamente!"))
        if estado == "ERROR":
            raise UserError(
                _(
                    "Hay error en el lote, verifica los datos y vuelve a procesar el lote."
                )
            )
        print(response)

        if estado == "PENDIENTE":
            raise UserError(
                _(
                    "El lote está pendiente de procesamiento. Las imputaciones comienzan a las 9.30 AM todos los dias habiles."
                )
            )

    def action_check_proceso(self):
        """
        Verifica el estado del lote de deuda.
        """
        self.ensure_one()

        if not self.nro_transaccion:
            raise UserError(_("El lote no tiene número de transacción."))

        request = self.provider_id.callSiroApi(
            f"siro/Pagos/{self.nro_transaccion}",
            {},
            method="GET",
            api="siro",
        ).json()

        return self.set_procesamiento_values(request)

    def action_cancelar(self):
        """
        Cancela el lote de deuda.
        Solo se pueden cancelar lotes en estado 'pendiente' o 'aplicado'.
        """
        self.ensure_one()
        if self.state not in ["pendiente", "aplicado"]:
            raise UserError(
                _("Solo se pueden cancelar lotes en estado pendiente o aplicado.")
            )

        self.write(
            {"state": "cancelado", "detalle_estado": "Lote cancelado por el usuario"}
        )
        return True

    def action_aplicar_base_pagos(self):
        """
        Aplica la base de pagos según el tipo seleccionado.
        Cambia el estado a 'aplicado' si la generación es exitosa.
        """
        self.ensure_one()

        # Validar que existan items
        if not self.items_deuda:
            raise UserError(_("No se puede aplicar el lote sin items de deuda."))

        # Calcular totales antes de aplicar
        total_primer_vencimiento = sum(self.items_deuda.mapped("importe1"))
        total_segundo_vencimiento = sum(self.items_deuda.mapped("importe2"))
        total_tercer_vencimiento = sum(self.items_deuda.mapped("importe3"))
        self.write(
            {
                "total_primer_vencimiento": total_primer_vencimiento,
                "total_segundo_vencimiento": total_segundo_vencimiento,
                "total_tercer_vencimiento": total_tercer_vencimiento,
            }
        )

        if self.base_pagos == "pmc":
            self._aplicar_pago_miscuentas()
        elif self.base_pagos == "link":
            raise UserError(
                _("La integración con Link Pagos está pendiente de implementación.")
            )
        else:
            raise UserError(_("Base de pagos no soportada: %s") % self.base_pagos)

        # Si llegamos aquí, la aplicación fue exitosa
        self.write(
            {
                "state": "aplicado",
                "detalle_estado": "Base de pagos aplicada exitosamente",
            }
        )

        return [
            {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Éxito"),
                    "message": _(
                        "La base de pagos se ha aplicado correctamente, chequea que este todo correcto y luego haz click en el botón de CONFIRMAR para procesar el lote."
                    ),
                    "sticky": False,
                    "type": "success",
                },
            },
            {"type": "ir.actions.client", "tag": "reload"},
        ]

    def _aplicar_pago_miscuentas(self):
        """
        Genera el texto para Pago Mis Cuentas con el formato requerido.
        """
        if not self.items_deuda:
            raise UserError(_("No hay items de deuda para procesar."))

        # Validar que todos los campos requeridos estén completos
        for item in self.items_deuda:
            required_fields = [
                item.titular,
                item.cod_pago_electronico,
                item.factura_id,
                item.fecha_vto_1,
                item.importe1,
            ]
            if not all(required_fields):
                msg = _(
                    "Todos los items deben tener al menos el primer "
                    "vencimiento completo."
                )
                raise UserError(msg)

            # Validar longitudes de campos
            if len(str(item.titular)) != 9:
                raise UserError(_("El titular debe tener exactamente 9 dígitos."))

            if len(str(item.cod_pago_electronico)) > 20:
                msg = _(
                    "El código de pago electrónico no puede superar los "
                    "20 caracteres."
                )
                raise UserError(msg)

            if len(str(item.factura_id)) > 20:
                msg = _("El ID de factura no puede superar los 20 caracteres.")
                raise UserError(msg)

            if len(str(item.mensaje_ticket or "")) > 40:
                msg = _("El mensaje del ticket no puede superar los " "40 caracteres.")
                raise UserError(msg)

            if len(str(item.mensaje_pantalla or "")) > 15:
                msg = _("El mensaje de pantalla no puede superar los " "15 caracteres.")
                raise UserError(msg)

        # Generar contenido del archivo
        content = []

        # Cabecera del archivo (Tipo 0)
        # Formato según especificación:
        # - Código registro (1): '0' valor fijo
        # - Código Banelco (3): '400' valor fijo
        # - Código empresa (4): '0000' valor fijo
        # - Fecha archivo (8): AAAAMMDD
        # - Filler (264): pos 17='1', pos 18-280='0'
        # Total: 280 caracteres
        header = "0"  # Tipo registro (1)
        header += "400"  # Código Banelco (3)
        header += "0000"  # Código empresa (4)
        header += fields.Date.today().strftime("%Y%m%d")  # Fecha archivo (8)
        header += "1"  # Filler pos 17 = '1'
        header += "0" * 263  # Filler pos 18-280 = '0'
        content.append(header)

        # Detalle de items (Tipo 5)
        total_importe = 0
        for item in self.items_deuda:
            # Formato según especificación:
            # - Código registro (1): '5' valor fijo
            # - CPE/Nro referencia (19):
            #   * 9 dígitos: identificador único del usuario (NO usar nro comprobante)
            #   * 10 dígitos: id convenio de Banco Roela
            # - Id factura (20):
            #   * 15 pos: número de comprobante/factura
            #   * 1 pos: concepto (0-9)
            #   * 4 pos: período MMAA
            detail = "5"  # Tipo registro (1)

            # CPE: 9 dígitos titular + 10 dígitos id convenio
            # Asegurar que titular sea numérico y tenga 9 dígitos
            titular = "".join(c for c in str(item.titular) if c.isdigit())
            if len(titular) != 9:
                raise UserError(
                    _(
                        "El titular debe tener exactamente 9 dígitos numéricos para "
                        "identificar al usuario."
                    )
                )

            # Obtener los últimos 10 dígitos del código de pago como id convenio
            cod_pago = str(item.cod_pago_electronico)
            if len(cod_pago) < 10:
                raise UserError(
                    _(
                        "El código de pago debe contener al menos 10 dígitos para el "
                        "id de convenio."
                    )
                )
            id_convenio = cod_pago[-10:]

            # Formar CPE: titular + id_convenio
            cpe = titular + id_convenio
            detail += cpe

            # Id factura (20): 15 comprobante + 1 concepto + 4 MMAA
            factura = str(item.factura_id)
            # Tomar solo los primeros 15 caracteres del comprobante
            nro_comprobante = factura[:15].ljust(15, "0")
            # Concepto: usar 0 si no está especificado
            concepto = item.concepto
            # Período: obtener mes y año del primer vencimiento
            periodo = item.fecha_vto_1.strftime("%m%y")
            detail += nro_comprobante + concepto + periodo

            # Código moneda (1)
            detail += "0"

            # Fecha 1° vencimiento (8) e importe (11)
            detail += item.fecha_vto_1.strftime("%Y%m%d")
            importe1 = int(item.importe1 * 100)
            detail += str(importe1).zfill(11)
            total_importe += importe1

            # Fecha 2° vencimiento (8) e importe (11)
            if item.fecha_vto_2 and item.importe2:
                detail += item.fecha_vto_2.strftime("%Y%m%d")
                importe2 = int(item.importe2 * 100)
                detail += str(importe2).zfill(11)
            else:
                detail += item.fecha_vto_1.strftime("%Y%m%d")
                detail += str(importe1).zfill(11)

            # Fecha 3° vencimiento (8) e importe (11)
            if item.fecha_vto_3 and item.importe3:
                detail += item.fecha_vto_3.strftime("%Y%m%d")
                importe3 = int(item.importe3 * 100)
                detail += str(importe3).zfill(11)
            else:
                fecha_2 = item.fecha_vto_2 or item.fecha_vto_1
                importe_2 = importe2 if item.fecha_vto_2 else importe1
                detail += fecha_2.strftime("%Y%m%d")
                detail += str(importe_2).zfill(11)

            # Filler 1 (19)
            detail += "0" * 19

            # Nro referencia anterior (19): igual al CPE
            detail += cpe

            # Mensaje ticket (40): 15 nombre ente + 25 info adicional
            mensaje_ticket = (item.mensaje_ticket or "").upper()
            mensaje_ticket = "".join(c for c in mensaje_ticket if c.isalnum())
            detail += mensaje_ticket.ljust(40)

            # Mensaje pantalla (15): primeras 15 pos del mensaje ticket
            mensaje_pantalla = mensaje_ticket[:15] if mensaje_ticket else ""
            detail += mensaje_pantalla.ljust(15)

            # Código de barras (60)
            detail += " " * 60

            # Filler 2 (29)
            detail += "0" * 29

            content.append(detail)

        # Pie del archivo (Tipo 9)
        # Formato según especificación:
        # - Código registro (1): '9' valor fijo
        # - Código Banelco (3): '400' valor fijo
        # - Código empresa (4): '0000' valor fijo
        # - Fecha archivo (8): AAAAMMDD
        # - Cantidad registros (7): cantidad de registros detalle
        # - Filler 1 (7): ceros
        # - Total importe (16): 14 enteros y 2 decimales sin separador
        # - Filler 2 (234): ceros
        # Total: 280 caracteres
        footer = "9"  # Tipo registro (1)
        footer += "400"  # Código Banelco (3)
        footer += "0000"  # Código empresa (4)
        footer += fields.Date.today().strftime("%Y%m%d")  # Fecha archivo (8)
        footer += str(len(self.items_deuda)).zfill(7)  # Cantidad registros (7)
        footer += "0" * 7  # Filler 1 (7)
        # Total importe: convertir a entero con 2 decimales
        total_importe_str = str(int(total_importe)).zfill(16)
        footer += total_importe_str  # Total importe (16)
        footer += "0" * 234  # Filler 2 (234)
        content.append(footer)

        # Generar texto final
        content = "\n".join(content)

        self.write(
            {
                "base_pagos_info": content,
                "detalle_estado": "Texto generado exitosamente",
                "state": "procesado",
            }
        )

        return True
