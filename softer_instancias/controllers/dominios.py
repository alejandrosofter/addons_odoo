from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class DominiosController(http.Controller):

    @http.route("/my/dominios", type="http", auth="user", website=True)
    def custom_section_dominios(self, **kwargs):
        user = request.env.user
        dominios = request.env["instancias.dominios"].search(
            [
                ("user_id", "=", user.id),
            ]
        )

        return request.render(
            "softer_instancias.dominios_user_web",
            {"user": user, "dominios": dominios},
        )

    @http.route(
        "/my/dominios/<int:dominio_id>/edit", type="http", auth="user", website=True
    )
    def edit_dominio_form(self, dominio_id, **kwargs):
        dominio = request.env["instancias.dominios"].sudo().browse(dominio_id)
        if not dominio:
            return request.redirect("/my/dominios")
        return request.render("softer_instancias.dominios_edit", {"dominio": dominio})

    @http.route(
        "/my/dominios/<int:dominio_id>/emails", type="http", auth="public", website=True
    )
    def list_emails(self, dominio_id, **kwargs):
        # Listar los emails asociados al dominio_id
        emails = (
            request.env["instancias.emailscloudflare"]
            .sudo()
            .search([("dominio_id", "=", int(dominio_id))])
        )
        dominio = request.env["instancias.dominios"].sudo().browse(dominio_id)
        return request.render(
            "softer_instancias.dominios_emails",
            {"emails": emails, "dominio": dominio},
        )

    @http.route(
        "/my/dominios/<int:dominio_id>/emails/new",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def add_email(self, dominio_id, **kwargs):
        if request.httprequest.method == "POST":
            # Crear un nuevo email
            request.env["instancias.emailscloudflare"].sudo().create(
                {
                    "name": kwargs.get("name"),
                    "dominio_id": dominio_id,
                    "mailRedireccion": kwargs.get("mailRedireccion"),
                    "estado": "pendiente",
                }
            )
            return request.redirect(f"/my/dominios/{dominio_id}/emails")
        dominio = request.env["instancias.dominios"].sudo().browse(dominio_id)
        return request.render("softer_instancias.add_email", {"dominio": dominio})

    @http.route(
        "/my/dominios/<int:dominio_id>/emails/edit/<int:email_id>",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def edit_email(self, dominio_id, email_id, **kwargs):
        email = request.env["instancias.emailscloudflare"].sudo().browse(email_id)
        if not email.exists():
            return request.not_found()  # Manejar caso de email no encontrado

        if request.httprequest.method == "POST":
            # Actualizar el email existente
            email.sudo().write(
                {
                    "name": kwargs.get("name"),
                    "mailRedireccion": kwargs.get("mailRedireccion"),
                    "estado": kwargs.get("estado"),
                }
            )
            return request.redirect("/my/dominios/%s/emails" % dominio_id)
        dominio = request.env["instancias.dominios"].sudo().browse(dominio_id)
        return request.render(
            "softer_instancias.edit_email", {"email": email, "dominio": dominio}
        )

    @http.route(
        "/my/dominios/<int:dominio_id>/emails/delete/<int:email_id>",
        type="http",
        auth="public",
        website=True,
    )
    def delete_email(self, dominio_id, email_id, **kwargs):
        email = request.env["instancias.emailscloudflare"].sudo().browse(email_id)
        if not email.exists():
            return request.not_found()  # Manejar caso de email no encontrado

        email.sudo().unlink()
        return request.redirect("/my/dominios/%s/emails" % dominio_id)
