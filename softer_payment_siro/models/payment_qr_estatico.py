from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentQrEstatico(models.Model):
    _name = "payment.qr.estatico"
    _description = "QR Estático para Pagos"
    _rec_name = "name"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
        help="Nombre generado automáticamente",
    )

    nro_terminal = fields.Char(
        string="Número de Terminal",
        size=10,
        required=True,
        help="Número de terminal (máximo 10 caracteres)",
    )

    imagen = fields.Binary(
        string="Imagen QR", attachment=True, help="Imagen del código QR"
    )

    qr_string = fields.Text(
        string="String QR", readonly=True, help="String QR generado por la API de SIRO"
    )

    state = fields.Selection(
        [("pendiente", "Pendiente"), ("syncronizado", "Sincronizado")],
        string="Estado",
        default="pendiente",
        required=True,
        help="Estado del QR estático",
    )

    provider_id = fields.Many2one(
        "payment.provider",
        string="Proveedor de Pago",
        required=True,
        domain=[("code", "=", "siro")],
        help="Proveedor de pago SIRO",
    )

    @api.depends("nro_terminal", "provider_id.nro_empresa")
    def _compute_name(self):
        for record in self:
            if record.nro_terminal:
                empresa = record.provider_id.nro_empresa or ""
                record.name = f"Terminal {record.nro_terminal}"
                if empresa:
                    record.name = f"{record.name} - Empresa {empresa}"

    def action_sync(self):
        """Sincroniza manualmente con la API de SIRO"""
        self.ensure_one()
        try:
            qr_string = self._call_siro_api()
            if qr_string:
                self.write({"qr_string": qr_string, "state": "syncronizado"})
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

    def _call_siro_api(self):
        """Llama al método callSiroApi del payment provider"""
        self.ensure_one()
        try:
            response = self.provider_id.callSiroApi(
                "api/Pago/StringQREstatico",
                {
                    "nro_empresa": self.provider_id.nro_empresa,
                    "nro_terminal": self.nro_terminal,
                },
            )
            return response.get("StringQREstatico")
        except Exception as e:
            _logger.error("Error al obtener QR para registro %s: %s", self.id, str(e))
            raise ValidationError(_("Error al obtener el QR desde SIRO: %s") % str(e))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            try:
                qr_string = record._call_siro_api()
                if qr_string:
                    record.write({"qr_string": qr_string, "state": "syncronizado"})
            except Exception as e:
                _logger.error(
                    "Error al obtener QR para registro %s: %s", record.id, str(e)
                )
        return records

    @api.constrains("nro_terminal")
    def _check_nro_terminal_length(self):
        for record in self:
            if len(record.nro_terminal) > 10:
                raise ValidationError(
                    _("El número de terminal no puede tener más de 10 caracteres.")
                )
