from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

# Configurar el logger
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Dominios(models.Model):
    _name = "instancias.dominios"
    _description = "Dominios"

    name = fields.Char(string="Dominio", required=True)
    user_id = fields.Many2one("res.users", string="Usuario")
    esPublico = fields.Boolean(string="Es Publico")
    emails = fields.One2many(
        "instancias.emailscloudflare", "dominio_id", string="Emails"
    )
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("pendiente", "Pendiente"),
            ("error", "Error"),
            ("procesando", "Procesando..."),
        ],
        string="Estado",
        default="pendiente",
    )

    @api.model
    def get_available_dominios(self, user_id):
        # Obtener dominios públicos o del usuario
        return self.search(["|", ("user_id", "=", user_id), ("esPublico", "=", True)])

    def action_createDomain(self):

        for record in self:
            try:

                zone = self.getZone(record)

                if zone is None:
                    zone = self.createZone(record)
                self.createDnsZone(record, zone)

            except Exception as e:
                raise UserError(f"upss error {e}")

    def createDnsZone(self, record, zone):
        if self.getDnsRecord(record.dominios_id.name, zone) is None:
            self.createDns(record.dominios_id.name, zone)
        if (
            record.subdominio != ""
            and self.getDnsRecord(
                f"{record.subdominio}.{record.dominios_id.name}", zone
            )
            is None
        ):
            self.createDns(f"{record.subdominio}.{record.dominios_id.name}", zone)
        emailRouting = self.enableEmailRouting(zone)
        logger.info(emailRouting)

    def getEmailRouting(self, zone):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )

        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/email/routing"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(
                f"Error email routing: {response.status_code}, {response.text}"
            )

    def enableEmailRouting(self, zone):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )

        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/email/routing/enable"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(
                f"Error email routing: {response.status_code}, {response.text}"
            )

    def createDns(self, dominio, zone):

        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        serverIp = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.serverIp")
        )
        # logging.info(f"Cloudflare Token: {token}")

        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/dns_records"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        data = {
            "type": "A",
            "name": dominio,
            "content": serverIp,
            "ttl": 1,
            "priority": 0,
            "proxied": False,
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(
                f"Error create dns: {response.status_code}, {response.text}"
            )

    def getDnsRecord(self, dominio, zone):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/dns_records"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)

        for record in response.json()["result"]:
            if record["name"] == dominios_id.name:
                return record
        return None

    def createZone(self, record):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        url = "https://api.cloudflare.com/client/v4/zones"
        headers = {
            "Authorization": "Bearer " + token,
        }

        data = {
            "name": record.dominios_id.name,
            "jump_start": True,
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def get_cloudflare_zones(self):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        url = "https://api.cloudflare.com/client/v4/zones"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def getZone(self, record):

        try:
            data = self.get_cloudflare_zones(record)

            for zone in data["result"]:
                if zone["name"] == record.dominios_id.name:
                    return zone

        except Exception as e:
            raise UserError(e)
