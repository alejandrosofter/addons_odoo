# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SocioEstados(models.Model):
    _name = "socios.estado"
    _description = "Estados de Socio"
    _order = "fecha desc"

    socio_id = fields.Many2one(
        "res_partner.socio",
        string="Socio",
        required=True,
        ondelete="cascade",
        index=True,
    )
    fecha = fields.Date(
        string="Fecha", required=True, default=fields.Date.context_today
    )
    estado = fields.Selection(
        selection=[
            ("activa", "Activa"),
            ("finalizada", "Finalizada"),
            ("baja", "Baja"),
            ("suspendida", "Suspendida"),
        ],
        string="Estado",
        required=True,
    )
    motivo = fields.Text(string="Motivo", required=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe el método create para ejecutar subscription_upsert"""
        records = super().create(vals_list)
        for record in records:
            record.socio_id.estado = record.estado
            record.socio_id.subscription_upsert()
        return records

    def write(self, vals):
        """Sobrescribe el método write para ejecutar subscription_upsert"""
        result = super().write(vals)
        if "estado" in vals:
            self.socio_id.subscription_upsert()
        return result
