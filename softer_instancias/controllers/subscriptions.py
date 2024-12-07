from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class SubscriptionController(http.Controller):

    @http.route("/my/subscriptions", type="http", auth="user", website=True)
    def custom_section_subscriptions(self, **kwargs):
        user = request.env.user
        subscriptions = request.env["subscription.package"].search(
            [
                ("user_id", "=", user.id),
            ]
        )

        return request.render(
            "softer_instancias.subscriptions_user_web",
            {"user": user, "subscriptions": subscriptions},
        )

    @http.route(
        "/my/subscriptions/<int:subscription_id>/edit",
        type="http",
        auth="user",
        website=True,
    )
    def edit_subscription_form(self, subscription_id, **kwargs):
        subscription = (
            request.env["subscription.package"].sudo().browse(subscription_id)
        )
        if not subscription:
            return request.redirect("/my/subscriptions")
        return request.render(
            "softer_instancias.subscription_edit", {"subscription": subscription}
        )

    @http.route(
        "/my/subscriptions/<int:subscription_id>/details",
        type="http",
        auth="public",
        website=True,
    )
    def subscription_details(self, subscription_id, **kwargs):
        subscription = (
            request.env["subscription.package"].sudo().browse(subscription_id)
        )
        return request.render(
            "softer_instancias.subscription_details",
            {"subscription": subscription},
        )

    @http.route(
        "/my/subscriptions/<int:subscription_id>/edit",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def edit_subscription(self, subscription_id, **kwargs):
        subscription = (
            request.env["subscription.package"].sudo().browse(subscription_id)
        )
        if not subscription.exists():
            return request.not_found()

        if request.httprequest.method == "POST":
            # Actualizar la suscripción
            subscription.sudo().write(
                {
                    "name": kwargs.get("name"),
                    "start_date": kwargs.get("start_date"),
                    "end_date": kwargs.get("end_date"),
                    "status": kwargs.get("status"),
                }
            )
            return request.redirect(f"/my/subscriptions/{subscription_id}/details")
        return request.render(
            "softer_instancias.edit_subscription", {"subscription": subscription}
        )

    @http.route(
        "/my/subscriptions/<int:subscription_id>/delete",
        type="http",
        auth="public",
        website=True,
    )
    def delete_subscription(self, subscription_id, **kwargs):
        subscription = (
            request.env["subscription.package"].sudo().browse(subscription_id)
        )
        if not subscription.exists():
            return request.not_found()

        subscription.sudo().unlink()
        return request.redirect("/my/subscriptions")
