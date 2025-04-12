# -*- coding: utf-8 -*-
from odoo import models, fields


class JugadoresEventosTipos(models.Model):
    _name = "softer.jugadores_eventos_tipos"
    _description = "Tipos de Eventos para Jugadores"

    name = fields.Char(string="Nombre", required=True)


class JugadoresEventos(models.Model):
    _name = "softer.jugadores_eventos"
    _description = "Eventos de Jugadores"

    fecha = fields.Date(string="Fecha", required=True)
    tipoEvento_id = fields.Many2one(
        comodel_name="softer.jugadores_eventos_tipos",
        string="Tipo de Evento",
        required=True,
    )
    detalle = fields.Text(string="Detalle")
    jugador_id = fields.Many2one("res.partner", string="Jugador", required=True)
