from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.payment.controllers.portal import PaymentPortal
import json
import logging

# Configurar el logger específicamente para este módulo
_logger = logging.getLogger("softer_portal_sale")
_logger.setLevel(logging.INFO)


class CustomerPortalInherit(CustomerPortal):

    @http.route(
        ["/my/orders/generate_invoice"],
        type="http",
        auth="user",
        website=True,
        csrf=True,
        methods=["POST"],
    )
    def portal_generate_invoice(self, order_ids=None, csrf_token=None, **kw):
        try:
            if not order_ids:
                return request.make_response(
                    json.dumps(
                        {
                            "success": False,
                            "error": "No se seleccionaron órdenes",
                        }
                    ),
                    headers=[("Content-Type", "application/json")],
                )

            # Convertir order_ids a lista de enteros si es necesario
            if isinstance(order_ids, str):
                order_ids = [int(id) for id in order_ids.split(",")]
            elif isinstance(order_ids, list):
                order_ids = [int(id) for id in order_ids]

            orders = request.env["sale.order"].sudo().browse(order_ids)

            # Verificar que el usuario tenga acceso a los pedidos
            for order in orders:
                if not order.partner_id.id == request.env.user.partner_id.id:
                    return request.make_response(
                        json.dumps(
                            {
                                "success": False,
                                "error": "No tiene acceso a una o más órdenes",
                            }
                        ),
                        headers=[("Content-Type", "application/json")],
                    )
                if order.invoice_status != "to invoice":
                    return request.make_response(
                        json.dumps(
                            {
                                "success": False,
                                "error": "Una o más órdenes no están listas para facturar",
                            }
                        ),
                        headers=[("Content-Type", "application/json")],
                    )

            # Crear facturas
            invoices = orders._create_invoices()

            if not invoices:
                return request.make_response(
                    json.dumps(
                        {
                            "success": False,
                            "error": "No se pudieron crear las facturas",
                        }
                    ),
                    headers=[("Content-Type", "application/json")],
                )

            # Confirmar facturas
            invoices.action_post()

            # Actualizar estado de las órdenes
            orders.write({"invoice_status": "invoiced"})

            # Retornar URL de redirección
            return request.make_response(
                json.dumps(
                    {
                        "success": True,
                        "redirect_url": "/my/invoices/%s" % invoices[0].id,
                    }
                ),
                headers=[("Content-Type", "application/json")],
            )

        except Exception as e:
            return request.make_response(
                json.dumps(
                    {
                        "success": False,
                        "error": "Error al generar la factura: %s" % str(e),
                    }
                ),
                headers=[("Content-Type", "application/json")],
            )


class PaymentPortalInherit(PaymentPortal):

    def _get_extra_payment_form_values(self, **kwargs):
        """Return a dict of extra payment form values to include in the rendering context.

        :param dict kwargs: Optional data. This parameter is not used here.
        :return: The dict of extra payment form values.
        :rtype: dict
        """

        values = super()._get_extra_payment_form_values(**kwargs)

        _logger.info("=== Inicio _get_extra_payment_form_values ===")
        _logger.info("kwargs recibidos: %s", kwargs)

        try:
            if kwargs.get("invoice_id"):
                invoice = (
                    request.env["account.move"]
                    .sudo()
                    .search([("id", "=", int(kwargs.get("invoice_id")))], limit=1)
                )

                if invoice:
                    # Preparar datos de las líneas
                    lines_data = []
                    for line in invoice.invoice_line_ids:
                        lines_data.append(
                            {
                                "product_id": {
                                    "id": line.product_id.id,
                                    "name": line.product_id.name,
                                },
                                "quantity": line.quantity,
                                "price_unit": line.price_unit,
                                "price_subtotal": line.price_subtotal,
                            }
                        )

                    # Agregar nuestros valores personalizados
                    values.update(
                        {
                            "invoice": invoice,
                            "lines": lines_data,
                            "user": (
                                "Sin Registro (solicita por wsap tu usuario!)"
                                if request.env.user.name == "Public user"
                                else request.env.user.name
                            ),
                            "reference": invoice.name,
                        }
                    )
                    _logger.info("Valores personalizados agregados")
                else:
                    _logger.warning(
                        "Factura no encontrada: %s", kwargs.get("invoice_id")
                    )

        except Exception as e:
            _logger.error(
                "Error en _get_extra_payment_form_values: %s", str(e), exc_info=True
            )
            raise

        return values

    @http.route(["/payment/pay"], type="http", auth="public", website=True)
    def payment_pay(self, **kwargs):
        _logger.info("=== Inicio payment_pay ===")
        _logger.info("kwargs recibidos: %s", kwargs)
        return super().payment_pay(**kwargs)
