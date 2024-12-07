# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Disagnosticos(models.Model):
    _name = "consultorio.diagnosticos"
    _description = "Diagnosticos"
    name = fields.Char(string="Nombre")
    detalle = fields.Text(string="Detalle")
