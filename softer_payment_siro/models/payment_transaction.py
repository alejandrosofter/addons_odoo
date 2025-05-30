# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from urllib.parse import quote as url_quote

from werkzeug import urls

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.tools import float_round

from odoo.addons.softer_payment_siro import const
from odoo.addons.softer_payment_siro.controllers.main import SiroController
from datetime import datetime

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    siro_hash = fields.Char(
        string="Hash SIRO",
        readonly=True,
        copy=False,
        help="Hash único generado por SIRO para esta transacción",
    )

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return SIRO-specific rendering values.

        Note: self.ensure_one() from `_get_rendering_values`.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "siro":
            return res

        # Iniciar el pago y obtener los datos del link de pago
        payload = self._siro_prepare_payment_request_payload()
        _logger.info(
            "Enviando solicitud de creación de pago a SIRO:\n%s",
            pprint.pformat(payload),
        )
        payment_data = self.provider_id._siro_make_request("api/pago", payload=payload)

        # Guardar el hash para futuras consultas
        self.siro_hash = payment_data.get("Hash")

        # Extraer la URL de pago y los parámetros
        rendering_values = {
            "api_url": payment_data.get("Url"),
            "token": self.siro_hash,
        }
        return rendering_values

    def _siro_prepare_payment_request_payload(self):
        """Create the payload for the payment request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, SiroController._return_url)
        webhook_url = urls.url_join(
            base_url, f"{SiroController._webhook_url}/{url_quote(self.reference)}"
        )

        amount = float_round(
            self.amount, const.CURRENCY_DECIMALS.get(self.currency_id.name, 2)
        )

        return {
            "id_convenio": self.provider_id.id_convenio,
            "cuit_administrador": self.provider_id.cuit_administrador,
            "monto": amount,
            "moneda": self.currency_id.name,
            "referencia": self.reference,
            "descripcion": f"Pago {self.reference}",
            "cliente": {
                "nombre": self.partner_name,
                "email": self.partner_email,
                "telefono": self.partner_phone,
                "direccion": self.partner_address,
                "codigo_postal": self.partner_zip,
            },
            "urls": {
                "exito": return_url,
                "fracaso": return_url,
                "webhook": webhook_url,
            },
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to find the transaction based on SIRO data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "siro" or len(tx) == 1:
            return tx

        reference = notification_data.get("referencia")
        if not reference:
            raise ValidationError("SIRO: " + _("Datos recibidos sin referencia."))

        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", "siro")]
        )
        if not tx:
            raise ValidationError(
                "SIRO: " + _("No se encontró transacción con referencia %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on SIRO data.

        Note: self.ensure_one()
        """
        if self.provider_id.code != "siro":
            return super()._process_notification_data(notification_data)

        # Extraer datos de la notificación
        id_resultado = notification_data.get("id_resultado")
        if not id_resultado:
            raise ValidationError("SIRO: Datos recibidos sin IdResultado")

        # Actualizar referencia del proveedor
        self.provider_reference = id_resultado
        print(f"reference {self.reference}")
        try:
            # Verificar que exista el hash
            if not self.siro_hash:
                raise ValidationError(
                    f"SIRO: No se encontró el hash para la transacción {self.reference}"
                )

            # Consultar estado actual del pago
            endpoint = f"api/Pago/{self.siro_hash}/{id_resultado}"
            status_data = self.provider_id._siro_consulta(
                endpoint, payload=None, method="GET"
            )
            _logger.info(
                "SIRO: Estado de pago para tx %s: %s",
                self.reference,
                pprint.pformat(status_data),
            )
            print(f"status_data {status_data}")

            # Mapear estados de SIRO a estados de Odoo
            siro_state = status_data.get("Estado", "").upper()
            if not siro_state:
                siro_state = notification_data.get("estado", "").upper()

            if siro_state == "PROCESADA":
                self._set_done()
            elif siro_state == "CANCELADA":
                motivo = status_data.get("Motivo", "Sin motivo")
                self._set_canceled(f"SIRO: Pago {siro_state} - {motivo}")
            elif siro_state in ["REGISTRADA", "GENERADA"]:
                self._set_pending()
            elif siro_state == "ERROR":
                self._set_error(f"SIRO: Estado de pago con error: {siro_state}")
            elif siro_state == "RECHAZADA":
                self._set_error(
                    f"La transacción fue rechazada por el banco {status_data.get('MensajeResultado', '')}"
                )
            else:
                _logger.warning(
                    "SIRO: Estado desconocido para tx %s: %s",
                    self.reference,
                    siro_state,
                )
                self._set_error(f"SIRO: Estado de pago desconocido: {siro_state}")

        except Exception as e:
            _logger.exception(
                "SIRO: Error al procesar pago %s: %s", self.reference, str(e)
            )
            self._set_error(f"SIRO: Error al procesar el pago: {str(e)}")

    @api.model
    def _siro_get_error_msg(self, error_detail):
        """Return the error message corresponding to the payment status.

        :param str error_detail: The error details sent by the provider.
        :return: The error message.
        :rtype: str
        """
        return "SIRO: " + const.ERROR_MESSAGE_MAPPING.get(
            error_detail, const.ERROR_MESSAGE_MAPPING["error_general"]
        )
