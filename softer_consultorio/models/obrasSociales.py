# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ObrasSociales(models.Model):
    _name = "consultorio.obrasociales"
    _description = "Obras Sociales"

    activa = fields.Boolean(string="Activa")
    name = fields.Char(string="Nombre Obra Social")
    nameShort = fields.Char(string="Abreviatura")
    direccion = fields.Char(string="Dirección")
    telefono = fields.Char(string="Móvil")
    email = fields.Char(string="Email")
    ref = fields.Char(string="Referencia", hide=True)
