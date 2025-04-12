# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Jugadores(models.Model):
    _inherit = "res.partner"

    fechaNacimiento = fields.Date(string="Fecha de Nacimiento")
    posicion = fields.Selection(
        selection=[
            ("arquero", "Arquero"),
            ("defensa", "Defensa"),
            ("volante", "Volante"),
            ("delantero", "Delantero"),
        ],
        string="Posicion",
        # default="particular",
    )
    estado = fields.Selection(
        selection=[
            ("borrador", "Borrador"),
            ("activa", "Activo/a"),
            ("suspendida", "Suspendido/a"),
            ("baja", "Baja"),
        ],
        string="Estado",
        default="activa",
    )

    esJugador = fields.Boolean(string="Es Jugador", default=False)

    eventos_ids = fields.One2many(
        comodel_name="softer.jugadores_eventos",
        inverse_name="jugador_id",
        string="Eventos",
    )
