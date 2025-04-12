# -*- coding: utf-8 -*-
from odoo import models, fields


class Pruebas(models.Model):
    _name = "softer.pruebas"
    _description = "Modelo para gestionar Pruebas"

    name = fields.Char(string="Nombre", required=True)
    tipo = fields.Selection(
        selection=[
            ("prueba", "Prueba"),
            ("viaje", "Viaje"),
        ],
        string="Tipo",
        required=True,
    )
    estado = fields.Selection(
        selection=[
            ("abierto", "Abierto"),
            ("cerrado", "Cerrado"),
        ],
        string="Estado",
        default="abierto",
    )
    fechaInicio = fields.Date(string="Fecha de Inicio")
    fechaFin = fields.Date(string="Fecha de Fin")
    categoria = fields.Char(string="Categoría")
    detalle = fields.Text(string="Detalle")
    jugadores_ids = fields.Many2many("res.partner", string="Jugadores")
    equipos_ids = fields.Many2many("softer.pruebas_equipos", string="Equipos")
