from odoo import models, fields, api
import requests
import re
import base64


class BotWhatsapp(models.Model):
    _name = "bot.whatsapp"
    _description = "Bots de WhatsApp"

    name = fields.Char(string="Nombre del Bot", required=True)
    port = fields.Char(
        string="Puerto del Bot",
    )
    lastUpdate = fields.Char(string="Ultima sync")
    status_session = fields.Char(
        string="Estado de session",
    )
    status = fields.Char(
        string="Estado gral",
    )
    external_id = fields.Char(
        string="ID Externo",
        index=True,
        unique=True,
    )
    qr_image = fields.Binary(string="QR Code", attachment=True)
    estaConectado = fields.Boolean(string="Conectado?")

    def action_get_qr(self):
        """Botón para actualizar el código QR o verificar si está conectado"""
        for record in self:
            record._get_qr_from_api()

            # if conectado:
            #     record.estaConectado = True
            # else:
            #     record.qr_image_base64 = qr_data
            #     record.estaConectado = False

    def action_syncWhatsap(self):
        """Botón para actualizar el código QR o verificar si está conectado"""
        for record in self:
            print("ahora actualizar boots")
            self.env["res.users"].actualizar_bots_wsap()

    def action_logout(self):
        """Botón para actualizar el código QR o verificar si está conectado"""
        for record in self:
            url = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("whatsapp.url_whatsapp")
            )
            token = (
                self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")
            )
            print(f"Logout de {record.name}")
            self.callApi("logout", url, token, action="POST")

            print("ahora actualizar boots")
            self.env["res.users"].actualizar_bots_wsap()

    # @api.depends("external_id")
    # def _compute_qr_image(self):
    #     for record in self:
    #         if record.external_id:

    #             record.qr_image_base64 = record._get_qr_from_api()
    #         else:
    #             record.qr_image_base64 = False

    def callApi(self, fn, url, token, action="GET"):
        if not url or not token:
            print(f"Saliendo por falta de URL o token")
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            urlFinal = re.sub(r"(?<!:)//+", "/", f"{url}/bots/{self.external_id}/{fn}")

            if action == "GET":
                print(f"GET {urlFinal}")
                response = requests.get(urlFinal, headers=headers, timeout=20)
            else:
                print(f"POST {urlFinal}")
                response = requests.post(urlFinal, headers=headers, timeout=20)
            if response.status_code == 200:
                return response.text
        except Exception:
            print(f"Error en la API!")
            return False
        return False

    def _get_qr_from_api(self):
        """Consulta la API y extrae la imagen en base64"""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        text = self.callApi("qr", url, token)

        try:
            if text == "Ya estas logueado":
                print("Ya estas logueado")
                self.estaConectado = True
                self.qr_image_base64 = False

            else:

                match = re.search(r"data:image\/\w+;base64,([\w+/=]+)", text)
                if match:
                    base64_image = match.group(1)
                    self.qr_image = base64_image
                    self.env["res.users"].actualizar_bots_wsap()
                else:
                    print("No se encontró una imagen base64 válida")
                self.estaConectado = False
        except requests.exceptions.RequestException as e:
            print("Error de conexión:", e)
            return False

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.status_session or 'Desconocido'})"
            result.append((record.id, name))
        return result
