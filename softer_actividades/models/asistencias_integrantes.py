# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AsistenciasIntegrantes(models.Model):
    _name = "softer.asistencias.integrantes"
    _description = "Modelo de Asistencias por Integrante"

    asistencia_id = fields.Many2one(
        "softer.asistencias", string="Asistencia", required=True
    )
    # integrante_id = fields.Many2one(
    #     "softer.actividades.integrantes", string="Integrante", required=True
    # )
    cliente_id = fields.Many2one(
        "res.partner", string="Integrante", required=True, tracking=True
    )
    asistio = fields.Boolean(
        string="Asistió", default=True
    )  # Inicialmente marcado como True

    # Campo computado para el nombre del integrante y su estado de asistencia
    name = fields.Char(string="Nombre Completo", compute="_compute_name", store=True)

    @api.depends("cliente_id", "asistio")
    def _compute_name(self):
        for record in self:
            nombres = f"{record.cliente_id.name} " if record.cliente_id else ""

            estado_asistencia = "Asistió" if record.asistio else "No Asistió"
            record.name = f"{nombres} - {estado_asistencia}"

    @api.model
    def create(self, vals):
        # Asegurarse de que el registro de asistencia se cree correctamente
        return super(AsistenciasIntegrantes, self).create(vals)
