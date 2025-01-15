# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Dispositivos(models.Model):
    _name = "dispositivos.dispositivos"
    _description = "Dispositivos"

    name = fields.Char(string="Name", required=True, help="Record Name")
    host = fields.Char(string="Host", required=False, help="Host name")
    user = fields.Char(string="User", required=False, help="User")
    port = fields.Integer(string="Port", required=False, help="Port")
    password = fields.Char(string="Password", required=False, help="Pasword")
    token = fields.Char(
        string="Token cloudflare", required=False, help="Cloudflare Token"
    )
    tokenApi = fields.Char(string="Token API", required=False, help="API Token")
    is_https = fields.Boolean(string="HTTPS", default=False, help="HTTPS")
    conexion = fields.Selection(
        [
            ("cloudflare", "Cloudflare api"),
            ("api", "API"),
        ],
        string="Conexion",
        default="cloudflare",
    )
