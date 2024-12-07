# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Consultorios(models.Model):
    _name = "consultorio.consultorios"
    _description = "Consultorios"

    activa = fields.Boolean(string="Activa")
    name = fields.Char(string="Nombre")
    nameShort = fields.Char(string="Abreviatura")
    direccion = fields.Char(string="Dirección")
    telefono = fields.Char(string="Móvil")
    email = fields.Char(string="Email")
    turnera = fields.One2many("consultorio.consultorioturnera", "consultorio")
