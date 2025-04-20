# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class IntegrantesEstados(models.Model):
    _name = "softer.actividades.integrantes.estados"
    _description = "Historial de Estados de Integrantes"
    _order = "fecha desc"

    fecha = fields.Datetime(
        string="Fecha",
        default=lambda self: fields.Datetime.now(),
        required=True,
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
            ("cancelada", "Cancelada"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        required=True,
    )
    motivo = fields.Text(
        string="Motivo",
        required=True,
    )
    idUsuario = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user.id,
        required=True,
    )
    integrante_id = fields.Many2one(
        "softer.actividades.integrantes",
        string="Integrante",
        required=True,
        ondelete="cascade",
    )

    @api.model
    def create(self, vals):
        """Sobrescribe el método create para actualizar el estado del integrante"""
        record = super().create(vals)
        if record.integrante_id:
            record.integrante_id.write(
                {
                    "estado": record.estado,
                    "estadoMotivo": record.motivo,
                }
            )
        return record
