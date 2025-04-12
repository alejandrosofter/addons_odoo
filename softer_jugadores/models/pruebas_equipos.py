# -*- coding: utf-8 -*-
from odoo import models, fields


class PruebasEquiposJugadores(models.Model):
    _name = "softer.pruebas_equipos_jugadores"
    _description = "Jugadores de Pruebas Equipos"

    name = fields.Char(string="Nombre", required=True)


class PruebasEquipos(models.Model):
    _name = "softer.pruebas_equipos"
    _description = "Modelo para gestionar Pruebas Equipos"

    name = fields.Char(string="Nombre", required=True)
    jugadores_ids = fields.Many2many(
        comodel_name="softer.pruebas_equipos_jugadores", string="Jugadores"
    )
