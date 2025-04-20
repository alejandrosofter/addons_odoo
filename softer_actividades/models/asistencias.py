# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


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
                    "integrante_id": integrante.id,
                    "asistio": True,  # Inicialmente todos están presentes
                }
            )

        # Calcular porcentajes de asistencia para cada integrante
        asistencia._calcular_porcentajes_asistencia()

        return asistencia

    def write(self, vals):
        result = super(Asistencias, self).write(vals)
        if "integrantes_ids" in vals:
            self._calcular_porcentajes_asistencia()
        return result

    def _calcular_porcentajes_asistencia(self):
        """Calcula los porcentajes de asistencia para cada integrante"""
        for asistencia in self:
            # Obtener el primer día del mes actual
            primer_dia_mes = asistencia.fecha.replace(day=1)
            # Obtener el último día del mes actual
            if asistencia.fecha.month == 12:
                ultimo_dia_mes = asistencia.fecha.replace(
                    year=asistencia.fecha.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                ultimo_dia_mes = asistencia.fecha.replace(
                    month=asistencia.fecha.month + 1, day=1
                ) - timedelta(days=1)

            # Obtener todas las asistencias del mes para esta actividad
            asistencias_mes = self.search(
                [
                    ("actividad_id", "=", asistencia.actividad_id.id),
                    ("fecha", ">=", primer_dia_mes),
                    ("fecha", "<=", ultimo_dia_mes),
                ]
            )

            # Obtener todas las asistencias de la actividad
            asistencias_global = self.search(
                [("actividad_id", "=", asistencia.actividad_id.id)]
            )

            # Para cada integrante de la actividad
            for integrante in asistencia.actividad_id.integrantes:
                # Calcular asistencia mensual
                total_clases_mes = len(asistencias_mes)
                asistencias_mes_integrante = sum(
                    1
                    for a in asistencias_mes
                    for i in a.integrantes_ids
                    if i.integrante_id.id == integrante.id and i.asistio
                )
                porcentaje_mensual = (
                    (asistencias_mes_integrante / total_clases_mes * 100)
                    if total_clases_mes > 0
                    else 0
                )

                # Calcular asistencia global
                total_clases_global = len(asistencias_global)
                asistencias_global_integrante = sum(
                    1
                    for a in asistencias_global
                    for i in a.integrantes_ids
                    if i.integrante_id.id == integrante.id and i.asistio
                )
                porcentaje_global = (
                    (asistencias_global_integrante / total_clases_global * 100)
                    if total_clases_global > 0
                    else 0
                )

                # Actualizar los porcentajes en el integrante
                integrante.write(
                    {
                        "porcentajeAsistenciaMensual": porcentaje_mensual,
                        "porcentajeAsistenciaGlobal": porcentaje_global,
                    }
                )

    def unlink(self):
        # Buscar y eliminar los registros relacionados en un solo paso
        integrantes = self.env["softer.asistencias.integrantes"].search(
            [("asistencia_id", "in", self.ids)]
        )
        integrantes.unlink()

        # Llamar al método `unlink` de la superclase para eliminar los registros actuales
        return super().unlink()
