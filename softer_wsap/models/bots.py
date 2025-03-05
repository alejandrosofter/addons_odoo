from odoo import models, fields, api
import requests
import re
import base64
import json
from bs4 import BeautifulSoup
from odoo.exceptions import UserError


class BotWhatsapp(models.Model):
    _name = "bot.whatsapp"
    _description = "Bots de WhatsApp"

    name = fields.Char(string="Nombre del Bot", required=True)
    telefonosAdmin = fields.Char(string="Nros de tel admins (separados por comma)")

    user = fields.Many2one("res.users", string="Usuario", required=True)
    usuariosResponder = fields.Many2many("res.users", string="Usuarios a responder")
    contactosResponder = fields.Many2many("res.partner", string="Contactos a responder")
    telefonosResponder = fields.Char(
        string="Telefonos a responder",
        # compute="_compute_telefonosResponder",
        store=True,
    )
    extraPrompt = fields.Char(
        string="Extra Prompt AI",
    )
    # 0f0302e579d8500732913e5ad1576ae7a26cb7fe
    nroTelefono = fields.Char(
        string="Nro de telefono",
        description="Importante para poder recibir y procesar mensajes",
        required=True,
    )
    claveApi = fields.Char(
        string="Clave api (deber generarla y pegarla aqui)",
        description="Importante para poder recibir y procesar mensajes",
        # required=True,
    )
    hostApi = fields.Char(
        string="Host de la API ",
        description="Importante para poder recibir y procesar mensajes",
        # required=True,
    )
    userApi = fields.Char(
        string="Usuario de la API ",
        description="Importante para poder recibir y procesar mensajes",
        # required=True,
    )
    dbApi = fields.Char(
        string="DB de la API ",
        description="Importante para poder recibir y procesar mensajes",
        # required=True,
    )
    responderAi = fields.Boolean(
        string="Ai Responder",
    )
    responderContactos = fields.Boolean(
        string="Responder Contactos",
    )
    responderTodos = fields.Boolean(
        string="Reponder a todos",
    )
    responderSoloUsuarios = fields.Boolean(
        string="Reponder solo usuarios",
    )
    estaConectado = fields.Boolean(
        string="Conectado?",
        readonly=True,
    )
    port = fields.Char(
        string="Puerto del Bot",
        readonly=True,
    )

    owner = fields.Char(
        string="Owner del Bot",
        readonly=True,
    )
    lastUpdate = fields.Char(
        string="Ultima sync",
        readonly=True,
    )
    default_system = fields.Boolean(
        string="Es Default Sistema",
        default=False,
    )
    status_session = fields.Char(
        string="Estado de session",
        readonly=True,
    )
    status = fields.Char(
        string="Estado Servicio Wsap",
        readonly=True,
    )
    external_id = fields.Char(
        string="ID Externo",
        index=True,
        unique=True,
        readonly=True,
    )
    qr_image = fields.Binary(string="QR Code", attachment=True)

    estaConectado = fields.Boolean(
        string="Conectado?",
        readonly=True,
    )

    @api.onchange("user")
    def _onchange_user(self):
        if self.user:
            self.userApi = self.user.login

            # Obtener el Host (esto depende de tu configuración)
            self.hostApi = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            )
            self.nroTelefono = self.limpiar_numero_telefono(self.user.partner_id.phone)

    @api.onchange("contactosResponder")
    def _onchange_contactosResponder(self):
        phone_numbers = [
            self.limpiar_numero_telefono(contact.phone)
            for contact in self.contactosResponder
            if contact.phone
        ]
        self.telefonosResponder = ",".join(phone_numbers)

    @api.depends("contactosResponder")
    def _compute_telefonosResponder(self):
        for record in self:
            phone_numbers = [
                self.limpiar_numero_telefono(contact.phone)
                for contact in record.contactosResponder
                if contact.phone
            ]
            print(phone_numbers)
            record.telefonosResponder = ",".join(phone_numbers)

    def _update_default_bot(self, bot_id):
        """Desactiva otros bots y actualiza ir.config_parameter"""
        self.search([("id", "!=", bot_id)]).write({"default_system": False})
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp.idBotWsap", str(bot_id)
        )

    @api.model
    def get_status(self):
        """Devuelve el estado del bot de WhatsApp"""
        bot = self.search([], limit=1)
        return bot.is_active if bot else False

    def parse_html_message(self, html_message):
        soup = BeautifulSoup(html_message, "html.parser")
        return soup.get_text(strip=True)

    def limpiar_numero_telefono(self, phone):
        if not phone:
            return ""

        # Eliminar "+" y cualquier carácter no numérico
        phone_cleaned = re.sub(r"\D", "", phone)

        # Si el número empieza con "54", eliminarlo (Argentina)
        if phone_cleaned.startswith("54"):
            phone_cleaned = phone_cleaned[2:]

        return phone_cleaned

    def actualizar_bots_wsap(self):
        """Consulta la API y actualiza el modelo 'bot.whatsapp' con los datos obtenidos"""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")
        print("ACTUALIZANDO BOTS WSAP")
        if not url or not token:
            return False

        try:
            response = self.callApi(f"{url}/bots", token)
            if not response:
                return False
            try:
                data = response.json()
                bot_model = self.env["bot.whatsapp"]
                print(f"ACTUALIZANDO BOTS WSAP: {data}")
                for item in data:

                    existing_bot = bot_model.search(
                        [("external_id", "=", item["id"])], limit=1
                    )
                    newData = item
                    if existing_bot:
                        newData["estaConectado"] = (
                            True if newData["status_session"] == "open" else False
                        )
                        print("newData", newData)
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

    def action_send_whatsapp(self, nro_telefono, mensaje, url_media=None, flow=None):
        """Envía un mensaje a través de la API de WhatsApp."""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:
            raise ValueError("Faltan los parámetros de conexión a la API de WhatsApp")

        url = url.rstrip("/")  # Elimina cualquier "/" extra al final

        for record in self:
            if not record.external_id:
                raise ValueError(
                    f"El bot {record.name} no tiene un ID externo asignado"
                )

            api_url = f"{url}/bots/{record.external_id}/message"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            nro_telefono = self.limpiar_numero_telefono(nro_telefono)
            payload = {
                "nroTelefono": nro_telefono,
                "mensaje": self.parse_html_message(mensaje),
            }
            print(f"Enviando mensaje a {nro_telefono}: {mensaje}")

            if url_media:
                payload["urlMedia"] = url_media
            if flow:
                payload["flow"] = flow

            try:
                response = requests.post(
                    api_url, json=(payload), headers=headers, timeout=20
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise ValueError(
                        f"Error en la API: {response.status_code} - {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                raise ValueError(f"Error de conexión con la API: {str(e)}")

        return False

    def createBotApi(self, vals):
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:

            raise UserError(
                "No se puede crear el bot. Falta la configuración de WhatsApp en 'Ajustes del sistema'."
            )

        url = url.rstrip("/")  # Elimina cualquier "/" extra al final
        api_url = f"{url}/bots/"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            return requests.post(api_url, json=vals, headers=headers, timeout=20)

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión con la API: {str(e)}")

    def getFieldManyToMany(self, field, aux):
        print(field, aux)
        if field:
            aux = []
            for item in field:
                print(item.name)

            return aux
        return ""

    def updateApi(self):
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:
            raise ValueError("Faltan los parámetros de conexión a la API")

        url = url.rstrip("/")
        api_url = f"{url}/bots/{self.external_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        vals = self.env["bot.whatsapp"].search([("id", "=", self.id)]).read()[0]
        print(vals)
        return requests.put(api_url, json=vals, headers=headers, timeout=20)

    def updateBotApi(self, vals):
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:
            raise ValueError("Faltan los parámetros de conexión a la API")

        url = url.rstrip("/")
        api_url = f"{url}/bots/{self.external_id}"
        vals["qr_image"] = None  # No necesitamos este campo en la API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(f"Actualizando API {api_url}", vals)

        try:
            return requests.put(api_url, json=vals, headers=headers, timeout=20)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión con la API: {str(e)}")

    @api.model
    def create(self, vals):
        """Antes de crear en Odoo, valida que la API cree el bot correctamente"""
        try:
            response = self.updateApi()

            if response.status_code == 201:
                data = response.json()
                if "bot" in data and "id" in data["bot"]:
                    vals["external_id"] = data["bot"]["id"]
                    bot = super(BotWhatsapp, self).create(vals)
                    if bot.default_system:
                        self._update_default_bot(bot.id)
                    return bot
                else:
                    raise ValueError("La API no devolvió un ID válido")
            else:
                raise ValueError(
                    f"Error en la API: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión con la API: {str(e)}")

        return False  # Si la API falla, no se crea el registro

    def write(self, vals):
        """Al actualizar un bot, si se activa default_system, desactiva los demás y guarda en ir.config_parameter"""

        res = super(BotWhatsapp, self).write(vals)

        self.updateApi()
        if vals.get("default_system"):
            self._update_default_bot(self.id)
        return res

    def unlink(self):
        """Antes de eliminar en Odoo, elimina el bot en la API"""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")

        if not url or not token:
            raise ValueError("Faltan los parámetros de conexión a la API")

        url = url.rstrip("/")  # Elimina cualquier "/" extra al final

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        for record in self:
            if record.external_id:

                api_url = f"{url}/bots/{record.external_id}"
                print(api_url)
                try:
                    response = requests.delete(api_url, headers=headers, timeout=20)

                    if response.status_code == 200:
                        print(f"Bot {record.name} eliminado en API")
                    else:
                        raise ValueError(
                            f"Error eliminando en API: {response.status_code} - {response.text}"
                        )

                except requests.exceptions.RequestException as e:
                    raise ValueError(f"Error de conexión con la API: {str(e)}")

        return super(BotWhatsapp, self).unlink()

    def action_syncWhatsap(self):
        """Botón para actualizar el código QR o verificar si está conectado"""
        for record in self:
            print("ahora actualizar boots")
            self.env["bot.whatsapp"].actualizar_bots_wsap()

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
            self.callApi(f"{url}/logout", token, action="POST")

            print("ahora actualizar boots")
            self.env["bot.whatsapp"].actualizar_bots_wsap()

    # @api.depends("external_id")
    # def _compute_qr_image(self):
    #     for record in self:
    #         if record.external_id:

    #             record.qr_image_base64 = record._get_qr_from_api()
    #         else:
    #             record.qr_image_base64 = False

    def callApi(self, url, token, action="GET"):
        if not url or not token:
            print(f"Saliendo por falta de URL o token")
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            urlFinal = re.sub(r"(?<!:)//+", "/", f"{url}/")

            if action == "GET":
                print(f"GET {urlFinal}")
                return requests.get(urlFinal, headers=headers, timeout=20)
            else:
                print(f"POST {urlFinal}")
                return requests.post(urlFinal, headers=headers, timeout=20)

        except Exception:
            print(f"Error en la API!")
            return False

    def action_get_qr_api(self):
        """Consulta la API y extrae la imagen en base64"""
        url = self.env["ir.config_parameter"].sudo().get_param("whatsapp.url_whatsapp")
        token = self.env["ir.config_parameter"].sudo().get_param("whatsapp.token_wsap")
        urlQr = f"{url}/bots/{self.external_id}/qr"
        response = self.callApi(urlQr, token)
        print(f"consultando qr a {urlQr}")
        text = response.text
        try:
            if text == "Ya estas logueado":
                print("Ya estas logueado")
                self.estaConectado = True
                self.qr_image = False

            else:

                match = re.search(r"data:image\/\w+;base64,([\w+/=]+)", text)
                if match:
                    base64_image = match.group(1)
                    self.qr_image = base64_image
                    print(base64_image)
                    # self.env["bot.whatsapp"].actualizar_bots_wsap()
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
