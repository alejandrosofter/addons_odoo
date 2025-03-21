# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class Integrantes(models.Model):
    _name = "softer.actividades.integrantes"
    _description = "Modelo de Integrantes"

    cliente_id = fields.Many2one(
        "res.partner", string="Integrante", required=True, tracking=True
    )
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("suspendido", "Suspendido"),
            ("baja", "Baja"),
        ],
        string="Estado",
    )
    estadoMotivo = fields.Char(
        string="Motivo Estado",
    )
    cliente_contacto = fields.Many2one(
        "res.partner", string="Contacto Integrante", required=True, tracking=True
    )
    actividad_id = fields.Many2one("softer.actividades", string="Actividad")
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        tracking=True,
        domain="[('cliente_id', '=', cliente_contacto)]",
    )
    fechaNacimiento = fields.Date(
        string="Fecha de Nacimiento",
        compute="_compute_fecha_nacimiento",
        store=True,
        readonly=True,
    )

    @api.depends("cliente_id")
    def _compute_fecha_nacimiento(self):
        for record in self:
            print(record)
            record.fechaNacimiento = (
                record.cliente_id.fechaNacimiento if record.cliente_id else False
            )
