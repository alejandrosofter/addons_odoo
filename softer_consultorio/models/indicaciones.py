# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Indicaciones(models.Model):
    _name = "consultorio.indicaciones"
    _description = "Indicaciones"
    name = fields.Char(string="Nombre")
    detalle = fields.Text(string="Detalle")
