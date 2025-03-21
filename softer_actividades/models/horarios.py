# -*- coding: utf-8 -*-
from odoo import models, fields


class HorariosActividades(models.Model):
    _name = "softer.actividades.horarios"
    _description = "Modelo de Horarios de Actividades"

    dia = fields.Selection(
        [
            ("lunes", "Lunes"),
            ("martes", "Martes"),
            ("miércoles", "Miércoles"),
            ("jueves", "Jueves"),
            ("viernes", "Viernes"),
            ("sábado", "Sábado"),
            ("domingo", "Domingo"),
        ],
        string="Día",
        required=True,
    )
    hora = fields.Float(string="Hora", required=True)
    horaSalida = fields.Float(string="Hora de Salida", required=True)
    actividad_id = fields.Many2one(
        "softer.actividades", string="Actividad", required=True
    )
    recurso = fields.Many2one("softer.recursos", string="Lugar", required=True)
