# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Turnos(models.Model):
    _name = "consultorio.turnos"
    _description = "Turnos"

    fechaHora = fields.Datetime(string="Fecha y Hora")
    paciente = fields.Many2one("consultorio.pacientes", string="Paciente")
    consultorio = fields.Many2one("consultorio.consultorios", string="Consultorio")
    estado = fields.Selection(
        [("disponible", "Disponible"), ("ocupado", "Ocupado")],
        string="Estado",
        default="disponible",
    )
    receta = fields.Many2one("consultorio.recetas", string="Receta")
