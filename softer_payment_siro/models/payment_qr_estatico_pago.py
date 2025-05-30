from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentQrEstaticoPago(models.Model):
    _name = "payment.qr.estatico.pago"
    _description = "Pagos de QR Estático"
    _order = "fechaHora desc"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
        default="Nuevo Registro",
        help="Nombre generado automáticamente",
    )

    payment_qr_estatico_id = fields.Many2one(
        "payment.qr.estatico",
        string="QR Estático",
        required=True,
        ondelete="restrict",
        help="QR Estático asociado al pago",
    )

    importe = fields.Float(
        string="Importe", required=True, default=0.0, help="Importe del pago"
    )

    fechaHora = fields.Datetime(
        string="Fecha y Hora",
        required=True,
        default=fields.Datetime.now,
        help="Fecha y hora del pago",
    )

    nro_comprobante = fields.Char(
        string="Número de Comprobante",
        required=True,
        help="Número de comprobante del pago",
    )

    id_referencia_operacion = fields.Char(
        string="ID Referencia Operación",
        required=True,
        help="ID de referencia de la operación",
    )

    nro_cliente_empresa = fields.Char(
        string="Número Cliente Empresa",
        required=True,
        help="Número de cliente de la empresa",
    )

    state = fields.Selection(
        [("pendiente", "Pendiente"), ("sincronizado", "Sincronizado")],
        string="Estado",
        default="pendiente",
        required=True,
        help="Estado del QR estático de pago",
    )
    hash = fields.Char(
        string="Hash",
        help="Hash del pago",
    )
    pagada = fields.Boolean(
        string="Pagada",
        default=False,
        help="Indica si el pago ha sido pagado",
    )
    fecha_pago = fields.Datetime(
        string="Fecha de pago",
        help="Fecha de pago del pago",
    )
    resultado_pago = fields.Char(
        string="Resultado del pago",
        help="Resultado del pago",
    )
    id_resultado = fields.Char(
        string="ID Resultado",
        help="ID del resultado del pago",
    )

    # Campos relacionados para facilitar búsquedas y agrupaciones
    provider_id = fields.Many2one(
        related="payment_qr_estatico_id.provider_id", store=True, readonly=True
    )
    estado_sync = fields.Char(
        string="Estado de sincronización",
        store=True,
        readonly=True,
    )

    nro_terminal = fields.Char(
        related="payment_qr_estatico_id.nro_terminal", store=True, readonly=True
    )

    _sql_constraints = [
        (
            "unique_id_referencia_operacion",
            "unique(id_referencia_operacion)",
            "El ID de referencia debe ser único",
        )
    ]

    @api.constrains("importe")
    def _check_importe(self):
        for record in self:
            if record.importe <= 0:
                raise ValidationError(_("El importe debe ser mayor que cero"))

    def _process_notification_data(self, data):
        """Procesa los datos de la notificación de pago"""
        self.ensure_one()
        endpoint = f"api/Pago/{self.siro_hash}/{data.get('id_resultado')}"
        status_data = self.provider_id._siro_consulta(
            endpoint, payload=None, method="GET"
        )
        self.resultado_pago = status_data.get("MensajeResultado")
        self.id_resultado = data.get("id_resultado")
        if status_data.get("Estado") == "PROCESADA":
            self.pagada = True
            self.fecha_pago = fields.Datetime.now()

    def _call_siro_api(self):
        """Llama al método callSiroApi del payment provider"""
        self.ensure_one()
        try:
            payload = {
                "nro_terminal": self.nro_terminal,
                "Importe": self.importe,
                "URL_OK": "https://www.google.com/ok",
                "URL_ERROR": "https://www.google.com/error",
                "nro_comprobante": self.nro_comprobante,
                "IdReferenciaOperacion": self.id_referencia_operacion,
                "nro_cliente_empresa": self.nro_cliente_empresa,
            }
            response = self.provider_id.callSiroApi(
                "api/Pago/StringQREstatico",
                payload,
            )
            return response.json().get("Hash")
        except Exception as e:
            msg = "Error al obtener QR para registro %s: %s"
            _logger.error(msg, self.id, str(e))
            error_msg = _("Error al obtener el QR desde SIRO: %s")
            raise ValidationError(error_msg % str(e))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            try:
                hash = record._call_siro_api()
                if hash:
                    record.write(
                        {
                            "hash": hash,
                            "state": "sincronizado",
                            "estado_sync": "Sincro ok!",
                        }
                    )
            except Exception as e:
                msg = "Error al obtener QR para registro %s: %s"
                _logger.error(msg, record.id, str(e))
        return records

    def action_sync(self):
        """Sincroniza manualmente con la API de SIRO"""
        self.ensure_one()
        try:
            hash = self._call_siro_api()
            if hash:
                self.write(
                    {
                        "hash": hash,
                        "state": "sincronizado",
                        "estado_sync": "Sincro ok!",
                    }
                )
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Éxito"),
                        "message": _("QR sincronizado correctamente"),
                        "sticky": False,
                        "type": "success",
                    },
                }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": str(e),
                    "sticky": True,
                    "type": "danger",
                },
            }

    @api.depends("nro_cliente_empresa", "nro_comprobante", "importe")
    def _compute_name(self):
        for record in self:
            if (
                not record.nro_cliente_empresa
                or not record.nro_comprobante
                or not record.importe
            ):
                record.name = "Nuevo Registro"
                continue
            record.name = (
                f"{record.nro_cliente_empresa}"
                f"/{record.nro_comprobante}"
                f"/{record.importe}"
            )
