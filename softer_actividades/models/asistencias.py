# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Asistencias(models.Model):
    _name = "softer.asistencias"
    _description = "Modelo de Asistencias"

    actividad_id = fields.Many2one(
        "softer.actividades", string="Actividad", required=True
    )
    fecha = fields.Date(string="Fecha", required=True)

    # Campo computado para el nombre
    name = fields.Char(string="Nombre", compute="_compute_name", store=True)

    # Campo para relacionar con los integrantes
    integrantes_ids = fields.One2many(
        "softer.asistencias.integrantes", "asistencia_id", string="Integrantes"
    )

    @api.depends("actividad_id", "fecha")
    def _compute_name(self):
        for record in self:
            actividad_name = record.actividad_id.name if record.actividad_id else ""
            record.name = (
                f"{actividad_name} - {record.fecha}" if record.fecha else actividad_name
            )

    @api.model
    def create(self, vals):
        # Crear el registro de asistencia
        asistencia = super(Asistencias, self).create(vals)

        # Crear registros de AsistenciasIntegrantes para cada integrante
        for integrante in asistencia.actividad_id.integrantes:
            self.env["softer.asistencias.integrantes"].create(
                {
                    "asistencia_id": asistencia.id,
                    "cliente_id": integrante.cliente_id.id,
                    "asistio": True,  # Inicialmente todos están presentes
                }
            )

        return asistencia

    def unlink(self):
        # Buscar y eliminar los registros relacionados en un solo paso
        integrantes = self.env["softer.asistencias.integrantes"].search(
            [("asistencia_id", "in", self.ids)]
        )
        integrantes.unlink()

        # Llamar al método `unlink` de la superclase para eliminar los registros actuales
        return super().unlink()
