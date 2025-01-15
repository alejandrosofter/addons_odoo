# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Whatsapp(models.Model):
    _name = "whatsapp.whatsapp"
    _description = "Whatsapp"
    name = fields.Char(string="Nombre")
    user = fields.Many2one("res.users", string="User")
    instancia = fields.Many2one("instancias.instancias", string="Instancia")
    # lista estado
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("inactiva", "Inactiva"),
        ],
        string="Estado",
        default="activa",
    )
