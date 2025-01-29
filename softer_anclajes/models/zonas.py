from odoo import models, fields


class Zonas(models.Model):
    _name = "anclajes.zonas"
    _description = "Modelo para gestionar zonas"

    name = fields.Char(string="Nombre", required=True, unique=True)
