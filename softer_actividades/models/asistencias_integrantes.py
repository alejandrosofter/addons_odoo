# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class AsistenciasIntegrantes(models.Model):
    _name = "softer.asistencias.integrantes"
    _description = "Modelo de Asistencias por Integrante"

    asistencia_id = fields.Many2one(
        "softer.asistencias", string="Asistencia", required=True
    )
    integrante_id = fields.Many2one(
        "softer.actividades.integrantes",
        string="Integrante",
        required=True,
        tracking=True,
    )
    asistio = fields.Boolean(
        string="Asistió", default=True
    )  # Inicialmente marcado como True

    # Campos relacionados para mostrar los porcentajes
    porcentaje_mensual = fields.Float(
        string="Asistencia Mensual (%)",
        related="integrante_id.porcentajeAsistenciaMensual",
        readonly=True,
    )
    porcentaje_global = fields.Float(
        string="Asistencia Global (%)",
        related="integrante_id.porcentajeAsistenciaGlobal",
        readonly=True,
    )

    # Campo relacionado para el estado del integrante
    estado = fields.Selection(
        string="Estado",
        related="integrante_id.estado",
        readonly=True,
    )

    # Campo relacionado para el nombre del cliente
    nombre_cliente = fields.Char(
        string="Integrante",
        related="integrante_id.cliente_id.name",
        readonly=True,
    )

    # Campo computado para el nombre del integrante y su estado de asistencia
    name = fields.Char(
        string="Nombre Completo",
        compute="_compute_name",
        store=True,
    )

    @api.depends("integrante_id", "asistio")
    def _compute_name(self):
        for record in self:
            nombres = (
                f"{record.integrante_id.cliente_id.name} "
                if record.integrante_id
                else ""
            )
            estado_asistencia = "Asistió" if record.asistio else "No Asistió"
            record.name = f"{nombres} - {estado_asistencia}"

    @api.model
    def create(self, vals):
        # Asegurarse de que el registro de asistencia se cree correctamente
        return super(AsistenciasIntegrantes, self).create(vals)
