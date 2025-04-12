from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json


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
                                "error": (
                                    "Una o más órdenes no están listas " "para facturar"
                                ),
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
