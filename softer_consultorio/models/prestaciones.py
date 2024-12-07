# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Prestaciones(models.Model):
    _name = "consultorio.prestaciones"
    _description = "Prestaciones"
    name = fields.Char(string="Nombre")
    codigo = fields.Char(string="Codigo")
    importe = fields.Float(string="Importe")
    cantidad = fields.Integer(string="Cant. Prestaciones")
    nameShort = fields.Char(string="Abreviatura")
