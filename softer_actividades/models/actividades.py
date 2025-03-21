# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class EquiposSofter(models.Model):
    _name = "softer.actividades"
    _description = "Modelo de Actividades"

    name = fields.Char(
        string="Nombre",
        required=True,
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
    )
    entrenador = fields.Many2one(
        "res.partner", string="Entrenador", required=True, tracking=True
    )
    administrador = fields.Many2one(
        "res.partner", string="Administrador", required=True, tracking=True
    )
    tipoRangos = fields.Selection(
        [
            ("porFechaNacimiento", "Por Fecha Nacimiento"),
            ("libre", "Libre"),
        ],
        string="Tipo de Rango",
    )

    fechaDesde = fields.Date(string="Fecha Desde", tracking=True)
    fechaHasta = fields.Date(string="Fecha Desde", tracking=True)
    integrantes = fields.One2many(
        "softer.actividades.integrantes", "actividad_id", string="Integrantes"
    )
    horarios = fields.One2many(
        "softer.actividades.horarios", "actividad_id", string="Horarios"
    )
