# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PacientesObrasSociales(models.Model):
    _name = "consultorio.pacientesobrasociales"
    _description = "Obras Sociales de Pacientes"

    nroAfiliado = fields.Char(string="Nro. Afiliado")
    paciente_id = fields.Many2one(
        "consultorio.pacientes", string="Paciente", required=True
    )
    name = fields.Char(related="obrasocial.name", store=True, readonly=True)
    nroCredencial = fields.Char(string="Nro. Credencial")
    obrasocial = fields.Many2one("consultorio.obrasociales", string="Obra Social")
    esDefault = fields.Boolean(string="Default")
    sequence = fields.Integer()

    @api.depends("obrasocial")
    def _compute_name(self):
        for record in self:
            record.name = record.obrasocial.name
