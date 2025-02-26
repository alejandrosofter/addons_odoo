from odoo import http
from odoo.http import request


class SystrayWsapController(http.Controller):

    @http.route("/systray/wsap/get_status", type="json", auth="user")
    def get_status(self):
        # Obtener el ID del bot desde la configuración
        ir_config = request.env["ir.config_parameter"].sudo()
        id_bot = ir_config.get_param("whatsapp.idBotWsap", default="")
        active = ir_config.get_param("whatsapp.active_wsap", default="")
        active = True if active == "True" else False

        if not id_bot:
            return {"status": "ID de bot no configurado"}

        # Buscar el bot con ese ID
        bot = request.env["bot.whatsapp"].sudo().search([("id", "=", id_bot)], limit=1)

        if bot:
            return {
                "status_session": bot.status_session,
                "status": bot.status,
                "activeWsap": active,
            }
        return
