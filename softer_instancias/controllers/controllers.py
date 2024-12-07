from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class UserAccount(http.Controller):
    @http.route(
        "/my/instancias/start/<int:instancia_id>",
        type="http",
        auth="user",
        website=True,
    )
    def start_instancia(self, instancia_id, **kwargs):
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)
        if instancia:
            instancia.action_start()
        return request.redirect("/my/instancias")

    @http.route(
        "/my/instancias/stop/<int:instancia_id>", type="http", auth="user", website=True
    )
    def stop_instancia(self, instancia_id, **kwargs):
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)
        if instancia:
            instancia.action_stop()
        return request.redirect("/my/instancias")

    @http.route(
        "/my/instancias/delete/<int:instancia_id>",
        type="http",
        auth="user",
        website=True,
    )
    def delete_instancia(self, instancia_id, **kwargs):
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)
        if instancia:
            instancia.action_delete()
        return request.redirect("/my/instancias")

    @http.route("/my/instancias", type="http", auth="user", website=True)
    def custom_section(self, **kwargs):
        user = request.env.user
        instancias = request.env["instancias.instancias"].search(
            [
                ("user_id", "=", user.id),
            ]
        )
        _logger.info(instancias)  # Añadir log

        return request.render(
            "softer_instancias.instancias_user_web",
            {"user": user, "instancias": instancias},
        )

    @http.route("/my/home", type="http", auth="user", website=True)
    def custom_home(self, **kwargs):
        user = request.env.user
        instancias = request.env["instancias.instancias"].search(
            [("user_id", "=", user.id)]
        )
        instancias_count = len(instancias)
        _logger.info(f"Cantidad de instancias: {instancias_count}")  # Añadir log

        return request.render(
            "softer_instancias.custom_my_home",
            {
                "user": user,
                "instancias_count": 4343,  # Pasa el conteo de instancias
            },
        )

    @http.route(
        "/my/instancias/edit/<int:instancia_id>", type="http", auth="user", website=True
    )
    def edit_instancia_form(self, instancia_id, **kwargs):
        user_id = request.env.user.id
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)
        dominios = request.env["instancias.dominios"].get_available_dominios(user_id)
        if not instancia:
            return request.redirect("/my/instancias")
        return request.render(
            "softer_instancias.instancias_edit",
            {"instancia": instancia, "dominios": dominios},
        )

    @http.route(
        "/my/instancias/eliminarInstancia/<int:instancia_id>",
        type="http",
        auth="user",
        website=True,
    )
    def eliminarInstancia(self, instancia_id, **kwargs):
        # user_id = request.env.user.id
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)
        if not instancia:
            return request.redirect("/my/instancias")
        return request.render(
            "softer_instancias.eliminarInstancia",
            {"instancia": instancia},
        )

    @http.route(
        "/my/instancias/edit/<int:instancia_id>",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def edit_instancia(self, instancia_id, **kwargs):
        instancia = request.env["instancias.instancias"].sudo().browse(instancia_id)

        if instancia:
            instancia.write(
                {
                    "name": kwargs.get("name"),
                    "dominios_id": int(kwargs.get("dominios_id")),
                    "subdominio": kwargs.get("subdominio"),
                }
            )
        return request.redirect("/my/instancias")
