# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SiroController(http.Controller):
    _return_url = "/payment/siro/return"
    _webhook_url = "/payment/siro/webhook"
    _error_url = "/payment/siro/error"

    @http.route(
        _error_url,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def siro_error(self, **data):
        """Procesa el error de SIRO."""
        _logger.info("Siro: recibiendo error: %s", pprint.pformat(data))
        return ""  # Retorno vacío con status 200 para confirmar recepción

    def process_qr_estatico(self, id_referencia, id_resultado):
        qr_estatico_sudo = (
            request.env["payment.qr.estatico.pago"]
            .sudo()
            .search(
                [("id_referencia_operacion", "=", id_referencia)],
                limit=1,
            )
        )
        if not qr_estatico_sudo:
            _logger.error("Siro: QR estático no encontrado: %s", id_referencia)
            return
        qr_estatico_sudo._process_notification_data(
            {
                "id_resultado": id_resultado,
                "referencia": id_referencia,
            }
        )

    def process_transaction(self, id_referencia, id_resultado):
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search(
                [("reference", "=", id_referencia)],
                limit=1,
            )
        )

        if not tx_sudo:
            _logger.error("Siro: transacción no encontrada: %s", id_referencia)
            return

        # Validar el estado del pago
        tx_sudo._process_notification_data(
            {
                "id_resultado": id_resultado,
                "referencia": id_referencia,
                "estado": "pending",  # Estado inicial, se actualizará al consultar
            }
        )
        return True

    @http.route(
        _return_url,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def siro_return(self, **data):
        """Procesa el retorno de SIRO después del pago."""
        _logger.info("Siro: recibiendo retorno de pago: %s", pprint.pformat(data))

        # Extraer los parámetros de la URL
        id_resultado = data.get("IdResultado")
        id_referencia = data.get("IdReferenciaOperacion", "")

        if not id_resultado or not id_referencia:
            _logger.error("Siro: parámetros faltantes en el retorno")
            return request.redirect("/payment/status")
        print(f"id_referencia {id_referencia}")
        if self.process_transaction(id_referencia, id_resultado):
            return request.redirect("/payment/status")
        self.process_qr_estatico(id_referencia, id_resultado)

        return request.send_json({"status": "success"})

    @http.route(
        _webhook_url + "/<string:reference>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def siro_webhook(self, reference, **data):
        """Procesa las notificaciones webhook de SIRO."""
        _logger.info(
            "Siro: recibiendo webhook para referencia %s: %s",
            reference,
            pprint.pformat(data),
        )

        # Validar la referencia
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search(
                [("reference", "=", reference)],
                limit=1,
            )
        )

        if not tx_sudo:
            _logger.error("Siro: transacción no encontrada en webhook: %s", reference)
            raise Forbidden()

        # Procesar la notificación
        tx_sudo._process_notification_data(data)
        return ""  # Retorno vacío con status 200 para confirmar recepción
