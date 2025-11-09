from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import urllib.parse
import base64
import logging
import uuid

_logger = logging.getLogger(__name__)


class EvolutionApiNumbers(models.Model):
    _name = "evolution.api.numbers"
    _description = "Evolution API WhatsApp Numbers"
    _rec_name = "name"

    def _get_default_webhook_url(self):
        base_url_param = self.env["ir.config_parameter"]
        base_url = base_url_param.sudo().get_param("web.base.url")
        return f"{base_url}/evolution_api/webhook"

    def _get_default_token(self):
        return str(uuid.uuid4())

    name = fields.Char(string="Name", required=True)
    channel = fields.Selection(
        [
            ("WHATSAPP-BAILEYS", "Baileys"),
            # ("evolution", "Evolution"),
            ("WHATSAPP-BUSINESS", "Whatsapp API"),
        ],
        string="Canal",
        required=True,
        default="WHATSAPP-BAILEYS",
    )

    token = fields.Char(string="Token", required=True, default=_get_default_token)
    number = fields.Char(string="Numero", required=True)
    webhook_url = fields.Char(
        string="URL webhook", required=True, default=_get_default_webhook_url
    )
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("created", "Creada"),
            ("open", "Active"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
    )
    esta_creada = fields.Boolean(string="Esta Creada", default=False)
    instance_id = fields.Char(
        string="ID de Instancia Evolution API",
        readonly=True,
    )

    @api.model
    def _call_api(cls, method, endpoint, payload=None):
        ir_config = cls.env["ir.config_parameter"].sudo()
        server_url = ir_config.get_param("evolution_api.url")
        api_key = ir_config.get_param("evolution_api.token")

        if not server_url or not api_key:
            raise UserError(
                (
                    "Por favor, configure la URL del servidor "
                    "y la API Key de Evolution API."
                )
            )

        url = urllib.parse.urljoin(server_url, endpoint)
        headers = {
            "Content-Type": "application/json",
            "apikey": api_key,
        }

        try:
            if method.lower() == "post":
                response = requests.request(
                    method="POST",
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=10,
                )

            elif method.lower() == "get":
                response = requests.get(url=url, headers=headers, timeout=10)
            else:
                raise UserError(f"Método HTTP no soportado: {method}")

            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con Evolution API: {e}")
        except json.JSONDecodeError:
            raise UserError(
                "Respuesta inválida de la API. No se pudo decodificar JSON."
            )

    @api.model
    def _call_evolution_api_create_instance(cls, vals):
        """Llama a la API de Evolution para crear una nueva instancia.

        Args:
            vals (dict): Diccionario con los valores para crear la instancia.

        Returns:
            dict: Diccionario con el ID de la instancia y el código QR.

        Raises:
            UserError: Si la llamada a la API falla o la instancia no se crea.
        """
        payload = {
            "instanceName": vals.get("name"),
            "token": vals.get("token"),
            "qrcode": True,
            "number": vals.get("number"),
            "integration": vals.get("channel").upper(),
            "rejectCall": True,
            "msgCall": "",
            "groupsIgnore": True,
            "alwaysOnline": True,
            "readMessages": True,
            "readStatus": True,
            "syncFullHistory": True,
            "proxyHost": "",
            "proxyPort": "",
            "proxyProtocol": "",
            "proxyUsername": "",
            "proxyPassword": "",
            "webhook": {
                "url": vals.get("webhook_url"),
                "byEvents": True,
                "base64": True,
                "headers": {},
                "events": ["APPLICATION_STARTUP", "MESSAGES_UPSERT"],
            },
            "rabbitmq": {
                "enabled": False,
                "events": ["APPLICATION_STARTUP"],
            },
            "sqs": {
                "enabled": False,
                "events": ["APPLICATION_STARTUP"],
            },
            "chatwootAccountId": "",
            "chatwootToken": "",
            "chatwootUrl": "",
            "chatwootSignMsg": True,
            "chatwootReopenConversation": True,
            "chatwootConversationPending": True,
            "chatwootImportContacts": True,
            "chatwootNameInbox": "",
            "chatwootMergeBrazilContacts": True,
            "chatwootImportMessages": True,
            "chatwootDaysLimitImportMessages": 0,
            "chatwootOrganization": "",
            "chatwootLogo": "",
        }
        print("DEBUG PAYLOAD API CREATE INSTANCE:")
        print(json.dumps(payload, indent=4))

        response_data = cls._call_api("POST", "/instance/create", payload)
        if response_data.get("instance", {}).get("status") in [
            "created",
            "connecting",
        ]:
            instance_id = response_data["instance"]["instanceId"]
            qr_code = response_data.get("qrcode", {}).get("base64")
            return {"instance_id": instance_id, "qr_code": qr_code}
        else:
            raise UserError(
                f"Fallo al crear instancia '{vals.get('name')}': "
                f"{response_data.get('message', 'Mensaje desconocido')}"
            )

    def api_get_instance_connect(self):
        self.ensure_one()
        if not self.esta_creada:
            raise UserError("La instancia no ha sido creada en Evolution API.")

        instance_id = self.name
        response_data = self.sudo()._call_api(
            "GET",
            f"/instance/connect/{instance_id}",
        )

        print("DEBUG: response_data from _call_api:")
        print(f"  {response_data}")
        print("DEBUG: Type of response_data after _call_api: ")
        print(f"  {type(response_data)}")
        # Asegurarse de que response_data es un diccionario
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
                print("DEBUG: response_data after json.loads:")
                print(f"  {response_data}")
                print(f"DEBUG: Type after json.loads: {type(response_data)}")
            except json.JSONDecodeError:
                raise UserError(
                    f"Respuesta inesperada de la API para la instancia "
                    f"'{self.name}'. "
                    "Se esperaba un objeto JSON, pero se recibió "
                    "una cadena no decodificable."
                )

        qr_code_base64 = response_data.get("base64")
        if qr_code_base64 and qr_code_base64.startswith("data:image/png;base64,"):
            qr_code_base64 = qr_code_base64.split(",")[1]

        if qr_code_base64:
            return {
                "pairingCode": response_data.get("pairingCode"),
                "qrCode": qr_code_base64,
            }
        else:
            error_message = response_data.get("message", "Mensaje desconocido")
            final_message = (
                f"Fallo al obtener el código QR para la instancia "
                f"'{self.name}': {error_message or ''} "
                "El código QR no fue proporcionado por la API."
            )
            raise UserError(final_message)

    def action_get_qr_code(self):
        self.ensure_one()
        qr_data = self.api_get_instance_connect()
        print(f"DEBUG QR_DATA_RETURNED: {qr_data}")
        print(f"DEBUG QR_DATA_TYPE: {type(qr_data)}")

        qr_code_snippet = qr_data.get("qrCode") or ""
        print(f"DEBUG QR_CODE_KEY_VALUE: {qr_code_snippet}")

        if qr_code_snippet:
            print(f"DEBUG QR_CODE_IMAGE: {qr_code_snippet[:50]}...")
        else:
            print("DEBUG QR_CODE_IMAGE: No valid QR code string received.")

        if qr_data and qr_data.get("qrCode"):
            wizard_id = self.env["evolution_api.qr.wizard"].create(
                {"qr_code_image": qr_data["qrCode"]}
            )
            return {
                "name": "Código QR de Instancia",
                "type": "ir.actions.act_window",
                "res_model": "evolution_api.qr.wizard",
                "res_id": wizard_id.id,
                "view_mode": "form",
                "target": "new",
                "views": [[False, "form"]],
            }
        else:
            raise UserError("No se pudo obtener el código QR de la instancia.")

    def api_connection_state(self):
        self.ensure_one()
        if not self.esta_creada:
            raise UserError("La instancia no ha sido creada en Evolution API.")

        instance_id = self.instance_id
        response_data = self.sudo()._call_api(
            "GET",
            f"/instance/connectionState/{instance_id}",
        )
        print(response_data)
        if response_data.get("instance", {}).get("state"):
            return response_data["instance"]["state"]
        else:
            raise UserError(
                f"Fallo al obtener el estado de conexión para la instancia "
                f"'{self.name}': "
                f"{response_data.get('message', 'Mensaje desconocido')}"
            )

    @api.model
    def api_get_info(self):
        response_data = self.sudo()._call_api("GET", "/")

        if response_data.get("status") == 200:
            print(response_data)
            return response_data
        else:
            raise UserError(
                f"Fallo al obtener información de la API: "
                f"{response_data.get('message', 'Mensaje desconocido')}"
            )

    def api_find_contacts(self):
        self.ensure_one()
        if not self.esta_creada:
            raise UserError("La instancia no ha sido creada en Evolution API.")

        instance_id = self.name
        # La cláusula 'where' en el payload puede usarse para filtrar
        # contactos específicos. Para una búsqueda general de contactos,
        # se envía un diccionario 'where' vacío según el ejemplo de la
        # documentación de la API.
        payload = {"where": {}}
        response_data = self.sudo()._call_api(
            "POST",
            f"/chat/findContacts/{instance_id}",
            payload=payload,
        )
        # Asumiendo que response_data contendrá una lista de contactos.
        # La documentación no especifica el formato exacto de la respuesta
        # para los contactos, pero típicamente sería una lista de diccionarios.
        print(f"DEBUG: Response from findContacts API: {response_data}")
        return response_data

    def _get_image_from_url(self, url):
        """Descarga una imagen de una URL y la devuelve en base64."""
        if not url:
            return False
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al descargar imagen desde {url}: {e}")
            return False

    def action_sync_contacts(self):
        self.ensure_one()
        self.with_delay()._action_sync_contacts_job()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sincronización de Contactos",
                "message": "La sincronización de contactos ha sido "
                "enviada a la cola para su procesamiento.",
                "sticky": False,
            },
        }

    def _action_sync_contacts_job(self):
        self.ensure_one()
        contacts_data = self.api_find_contacts()
        _logger.info(f"Contactos obtenidos de Evolution API: {contacts_data}")

        if not contacts_data:
            raise UserError(
                "No se pudieron obtener contactos o no se encontraron contactos."
            )

        # Definir el tamaño del lote
        size_lote = 150
        total_synced = 0

        # Dividir los contactos en lotes y encolar un trabajo para cada lote
        for i in range(0, len(contacts_data), size_lote):
            batch = contacts_data[i : i + size_lote]
            self.with_delay()._process_contacts_batch_job(batch)
            # Esto es una estimación, el recuento real lo hace el job del lote
            total_synced += len(batch)

        _logger.info(
            f"Total de {total_synced} contactos enviados para "
            "sincronización en lotes."
        )

    def _process_contacts_batch_job(self, contacts_batch):
        Partner = self.env["res.partner"]
        synced_in_batch = 0

        for contact in contacts_batch:
            remote_jid = contact.get("remoteJid")
            if not remote_jid:
                continue

            phone_number_raw = remote_jid.split("@")[0]
            phone_number = "".join(filter(str.isdigit, phone_number_raw))

            if not phone_number:
                continue

            last_six_digits = phone_number[-6:]
            existing_partner = Partner.search(
                [("mobile", "=ilike", f"%{last_six_digits}")],
                limit=1,
            )

            partner_vals = {
                "name": contact.get("pushName") or phone_number,
                "mobile": phone_number,
            }

            profile_pic_url = contact.get("profilePicUrl")
            if profile_pic_url:
                image_base64 = self._get_image_from_url(profile_pic_url)
                if image_base64:
                    partner_vals["image_1920"] = image_base64

            if existing_partner:
                existing_partner.write(partner_vals)
                _logger.info(
                    "Sincronizado contacto existente: "
                    f"{existing_partner.name} ({phone_number})"
                )
            else:
                Partner.create(partner_vals)
                _logger.info(
                    "Creado nuevo contacto: %s (%s)",
                    partner_vals["name"],
                    phone_number,
                )
            synced_in_batch += 1

        _logger.info(
            f"Lote de contactos procesado: {synced_in_batch} "
            "contactos sincronizados."
        )

    # onxwyhjghutaambw
    def api_instance_delete(self):
        self.ensure_one()
        if not self.esta_creada:
            raise UserError("La instancia no ha sido creada en Evolution API.")

        instance_id = self.name
        response_data = self.sudo()._call_api(
            "DELETE",
            f"/instance/delete/{instance_id}",
        )

        if response_data.get("status") == "SUCCESS":
            _logger.info(f"Instancia '{instance_id}' eliminada exitosamente.")
            # Opcional: Actualizar el estado en Odoo si la instancia se elimina
            # self.write({'estado': 'eliminada', 'esta_creada': False})
            return True
        else:
            raise UserError(
                f"Fallo al eliminar instancia '{self.name}': "
                f"{response_data.get('message', 'Mensaje desconocido')}"
            )

    @api.model
    def create(self, vals):
        api_result = self._call_evolution_api_create_instance(vals)
        vals["esta_creada"] = True
        vals["instance_id"] = api_result["instance_id"]
        record = super().create(vals)

        # La lógica para abrir el wizard ya no va aquí directamente
        # Si deseas abrir el wizard automáticamente, se necesitaría
        # un mecanismo diferente (e.g., desde un botón en la vista)
        return record

    def unlink(self):
        for record in self:
            if record.esta_creada:
                try:
                    record.api_instance_delete()
                except UserError as e:
                    _logger.warning(
                        f"Fallo al eliminar instancia de Evolution API "
                        f"para {record.name}: {e.name}"
                    )
        return super().unlink()
