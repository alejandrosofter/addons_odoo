# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Categoria(models.Model):
    _name = "softer.suscripcion.categoria"
    _description = "Categoría de Suscripción"

    name = fields.Char(string="Nombre", required=True)
    detalle = fields.Text(string="Detalle")
