from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):

    @http.route(
        ["/shop/address"], type="http", methods=["POST"], auth="public", website=True
    )
    def address(self, **kw):
        # Remove integrante_ids from kw if present
        if "integrante_ids" in kw:
            del kw["integrante_ids"]
        return super(WebsiteSaleInherit, self).address(**kw)
