from odoo import models, fields, api
import requests
import json
import re


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    active_wsap = fields.Boolean(string="Esta Activo", default=False)
    nroWhatsapp = fields.Text(string="Nro de whatsapp")
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
            ("no_configurado", "No Configurado"),
        ],
        string="Estado de WhatsApp",
    )
    idBotWsap = fields.Many2one("bot.whatsapp", string="Bot para WhatsApp")

    def callApi(self, fn, url, token, action="GET"):

        if not url or not token:
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            urlFinal = re.sub(r"(?<!:)//+", "/", f"{url}/{fn}")

            if action == "GET":
                print(f"GET {urlFinal}")
                response = requests.get(urlFinal, headers=headers, timeout=20)
            else:
                print(f"POST {urlFinal}")
                response = requests.post(urlFinal, headers=headers, timeout=20)
            if response.status_code == 200:
                return response
        except requests.exceptions.RequestException as e:
            print("Error de conexión:", e)
            return False
        return False

    def actualizar_bots_wsap(self):
        """Consulta la API y actualiza el modelo 'bot.whatsapp' con los datos obtenidos"""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:
            return False

        try:
            response = self.callApi("bots", url, token)
            if not response:
                return False
            try:
                data = response.json()
                bot_model = self.env["bot.whatsapp"]
                print(f"ACTUALIZANDO BOTS WSAP: {data}")
                for item in data:

                    bot_nombre = item["nombre"]

                    existing_bot = bot_model.search(
                        [("external_id", "=", item["id"])], limit=1
                    )
                    newData = {
                        "external_id": item["id"],
                        "name": bot_nombre,
                        "status_session": item["status_session"],
                        "lastUpdate": item["lastUpdate"],
                        "port": item["port"],
                        "status": item["status"],
                        "estaConectado": item["status_session"] == "open",
                    }
                    if existing_bot:
                        # Actualizar datos si ya existe
                        existing_bot.write(newData)
                    else:
                        # Crear nuevo bot
                        bot_model.create(newData)

                return True

            except json.JSONDecodeError as e:
                print("Error al decodificar JSON:", e)
        except requests.exceptions.RequestException as e:
            print("Error de conexión:", e)

        return False
