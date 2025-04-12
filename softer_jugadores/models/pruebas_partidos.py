# -*- coding: utf-8 -*-
from odoo import models, fields


class PruebasPartidos(models.Model):
    _name = "softer.pruebas_partidos"
    _description = "Modelo para gestionar Pruebas Partidos"

    fecha = fields.Date(string="Fecha", required=True)
    resultado = fields.Char(string="Resultado")
    lugar = fields.Char(string="Lugar")
    oponente = fields.Char(string="Oponente")
    detalle = fields.Text(string="Detalle")
    eventos_ids = fields.Many2many(
        "softer.jugadores_eventos",
        string="Eventos",
    )
    prueba_id = fields.Many2one("softer.pruebas", string="Prueba")
