# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Pacientes(models.Model):
    _name = "consultorio.pacientes"
    _description = "Pacientes"

    obrasSociales = fields.One2many(
        "consultorio.pacientesobrasociales", "paciente_id", string="Obras Sociales"
    )
    fechaNacimiento = fields.Date(string="Fecha de Nacimiento")
    name = fields.Char(
        string="Nombre",
    )
    apellido = fields.Char(string="Apellido")
    dni = fields.Char(string="DNI")
    esParticular = fields.Boolean(string="Particular")
    nroTelefono = fields.Char(string="Nro. Telefono")
    email = fields.Char(string="Email")
    ref = fields.Char(string="Referencia")
    esParticular = fields.Boolean(string="Particular")
    obras_sociales_display = fields.Char(
        string="Obras Sociales",
        compute="_compute_obras_sociales_display",
        store=True,
    )

    @api.depends("obrasSociales")
    def _compute_obras_sociales_display(self):
        for record in self:
            record.obras_sociales_display = ", ".join(
                [os.name for os in record.obrasSociales]
            )
