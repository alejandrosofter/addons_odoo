from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
from .dominios import Dominios

# Configurar el logger
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DominiosEmail(models.Model):
    _name = "instancias.emailscloudflare"
    _description = "Dominios Emails"

    name = fields.Char(string="Email")
    dominio_id = fields.Many2one("instancias.dominios", string="Dominio")
    mailRedireccion = fields.Char(string="Mail Redireccion")
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("inactiva", "Inactiva"),
            ("error", "Error"),
            ("pendiente", "Pendiente"),
        ],
        string="Estado",
        default="pendiente",
    )

    def send_email(self):
        for record in self:
            try:
                self.envioCloudflare(record)
            except Exception as e:
                logger.error(f"Error al enviar el email: {e}")
                raise UserError(f"Error al enviar el email: {e}")

    def getZone(self, record):
        dominio_obj = self.env["instancias.dominios"]
        try:
            data = dominio_obj.get_cloudflare_zones()

            for zone in data["result"]:
                if zone["name"] == record.dominio_id.name:
                    return zone

        except Exception as e:
            raise UserError(e)

    def getRoutingEmail(self, record):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        zone = self.getZone(record)

        if zone is None:
            raise UserError("La zona no existe")

        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/email/routing/rules"
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

    def envioCloudflare(self, record):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("softer_instancias.cloudflare_token")
        )
        zone = self.getZone(record)
        routingRules = self.getRoutingEmail(record)
        logger.info("LISTA REGLAS!-------------------------")
        logger.info(routingRules)
        if zone is None:
            raise UserError("La zona no existe")

        url = f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/email/routing/rules"
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        data = {
            "name": f"Renvio {record.dominio_id.name}",
            "priority": 0,
            "enabled": True,
            "matchers": [
                {
                    "field": "to",
                    "type": "literal",
                    "value": f"{record.name}@{record.dominio_id.name}",
                }
            ],
            "actions": [{"type": "forward", "value": [f"{record.mailRedireccion}"]}],
        }

        logger.info("Enviando a CLOUDFLARE EMAIL!!-------------------------")
        logger.info(data)
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()  # Devuelve la respuesta en formato JSON
        else:
            raise Exception(
                f"Error email routing: {response.status_code}, {response.text}"
            )
