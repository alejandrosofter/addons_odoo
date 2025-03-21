# -*- coding: utf-8 -*-
from odoo import models, fields


class Recursos(models.Model):
    _name = "softer.recursos"
    _description = "Modelo de Recursos"

    name = fields.Char(string="Nombre", required=True)
    detalle = fields.Text(string="Detalle")
