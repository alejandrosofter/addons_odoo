# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

# from odoo.exceptions import ValidationError # Mantenido como comentario
import logging

_logger = logging.getLogger(__name__)


class SociosEstado(models.Model):
    _name = "socios.estado"
    _description = "Estado del Socio"
    _order = "fecha desc, id desc"

    socio_id = fields.Many2one(
        "res_partner.socio", string="Socio", required=True, ondelete="cascade"
    )
    fecha = fields.Datetime(
        string="Fecha", default=lambda self: fields.Datetime.now(), required=True
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        required=True,
    )
    motivo = fields.Text(string="Motivo")
    usuario_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user.id,
        required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe el método create para ejecutar subscription_upsert"""
        records = super().create(vals_list)
        for record in records:
            record.socio_id.estado = record.estado
            # En lugar de subscription_upsert, crear un registro de cambio de estado en la suscripción
            if record.socio_id.suscripcion_id:
                self.env["softer.suscripcion.motivo_cambio"].create(
                    {
                        "suscripcion_id": record.socio_id.suscripcion_id.id,
                        "estado": record.estado,
                        "fecha": record.fecha,
                        # Usar la fecha del cambio de estado del socio
                        "usuario_id": record.usuario_id.id or self.env.user.id,
                        # Usar usuario del cambio de estado o usuario actual
                        "motivo": record.motivo
                        or f"Cambio de estado del socio a {record.estado}",
                        # Usar motivo si existe, sino generar uno
                    }
                )
        return records

    def write(self, vals):
        """Sobrescribe el método write para ejecutar subscription_upsert"""
        result = super().write(vals)
        return result
