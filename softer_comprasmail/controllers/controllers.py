from odoo import http
from odoo.http import request
import logging
from odoo.modules.module import get_module_resource


class UserAccount(http.Controller):

    @http.route("/test", type="http", auth="user")
    def test(self, **kwargs):
        filename = "facturaTest6.jpg"
        cred_path = get_module_resource("softer_comprasmail", "static/data", filename)
        if not cred_path:
            return f"NO encuentro archivo"
        attachments = [
            {
                "fname": filename,
                "content": open(cred_path, "rb").read(),
            },
        ]

        msg_dict = {
            "message_type": "email",
            "subtype": "account.mail.mt_email_out",
            "email_from": "4XwRt@example.com",
            "email_to": "4XwRt@example.com",
            "subject": "PRUEBA",
            "body": "PRUEBA",
            "attachments": attachments,
        }

        http.request.env["account.move"].message_new(msg_dict)
