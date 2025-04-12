# -*- coding: utf-8 -*-
from odoo import models, fields


class PruebasEquiposJugador(models.Model):
    _name = "softer.pruebas_equipos_jugador"
    _description = "Jugadores en Pruebas Equipos"

    jugador_id = fields.Many2one(
        comodel_name="res.partner", string="Jugador", required=True
    )
    pruebas_equipos_id = fields.Many2one(
        comodel_name="softer.pruebas_equipos", string="Prueba Equipo", required=True
    )
