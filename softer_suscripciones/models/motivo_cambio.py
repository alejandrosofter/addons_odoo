# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MotivoCambioEstado(models.Model):
    _name = "softer.suscripcion.motivo_cambio"
    _description = "Motivos de Cambio de Estado en Suscripciones"
    _order = "fecha desc"

    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        required=True,
        ondelete="cascade",
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
    motivo = fields.Text(string="Motivo", required=True)
    usuario_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user.id,
        required=True,
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        suscripcion = res.suscripcion_id
        if suscripcion and res.estado:
            # Cambiar estado de la suscripción
            suscripcion.estado = res.estado
            # Setear los estados de las líneas según el estado de la suscripción
            for line in suscripcion.line_ids:
                suspender = False
                if res.estado == "suspendida":
                    suspender = not line.en_suspension
                elif res.estado == "activa":
                    suspender = not line.en_activa
                elif res.estado == "baja":
                    suspender = not line.en_baja
                if line.esta_suspendida != suspender:
                    self.env["softer.suscripcion.motivo_cambio_productos"].create(
                        {
                            "suscripcion_id": suscripcion.id,
                            "suscripcion_linea_id": line.id,
                            "motivo": res.motivo,
                            "cliente_id": suscripcion.cliente_id.id,
                            "product_id": line.product_id.id,
                            "periodicidad": line.periodicidad,
                            "esta_suspendida": suspender,
                            "fecha": res.fecha,
                        }
                    )
                line.write({"esta_suspendida": suspender})
                # Agregar registro movitov_cambio_producto

        return res
