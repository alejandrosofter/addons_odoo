# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class DiasSemana(models.Model):
    _name = "consultorio.diassemana"
    _description = "Días de la Semana"

    name = fields.Char(string="Día", required=True)


class ConsultoriosTurnera(models.Model):
    _name = "consultorio.consultorioturnera"
    _description = "Consultorio Turnera"

    desdeHora = fields.Char(string="Desde")
    hastaHora = fields.Char(string="Hasta")
    consultorio = fields.Many2one("consultorio.consultorios", string="Consultorio")
    duracionMinutos = fields.Integer(string="Duración (minutos)")
    dias = fields.Many2many("consultorio.diassemana", string="Días de la semana")

    @api.constrains("desdeHora", "hastaHora")
    def _check_hora_format(self):
        pattern = re.compile(r"^\d{2}:\d{2}$")
        for record in self:
            if record.desdeHora and not pattern.match(record.desdeHora):
                raise ValidationError("La hora en 'Desde' debe estar en formato HH:MM.")
            if record.hastaHora and not pattern.match(record.hastaHora):
                raise ValidationError("La hora en 'Hasta' debe estar en formato HH:MM.")
