# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ClubMember(models.Model):
    _inherit = "res.partner"

    member_number = fields.Char(
        string="Nro de Socio", copy=False, index=True, unique=True
    )
    fechaNacimiento = fields.Date(string="Fecha de Nacimiento")
    tipoSocio = fields.Selection(
        selection=[("particular", "Particular"), ("empresa", "Empresa")],
        string="Tipo de Socio",
        # default="particular",
    )
    estado = fields.Selection(
        selection=[
            ("borrador", "Borrador"),
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        default="activa",
    )
    fechaAlta = fields.Date(string="Fecha de Alta")
    fechaBaja = fields.Date(string="Fecha de Baja")
    esSocio = fields.Boolean(string="Es Socio", default=False)
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        # ondelete="set null",
    )
    estado_suscripcion = fields.Selection(
        selection=[
            ("borrador", "Borrador"),
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado de Suscripción",
        compute="_compute_estado_suscripcion",
        store=False,
    )

    @api.model
    def action_get_next_member_number(self, args):
        print("obtener prox socio")

        # Lógica para obtener el próximo número disponible

        next_number = self.env["ir.sequence"].next_by_code("member.number.sequence")
        print(f"next_number: ${next_number}")
        self.member_number = next_number

    @api.constrains("tipoSocio", "member_number")
    def _check_member_number_required(self):
        for record in self:
            if record.tipoSocio and not record.member_number:
                raise ValidationError(
                    "El número de socio es obligatorio si el tipo de socio está definido."
                )

    @api.model
    def create(self, vals):
        if vals.get("tipoSocio") and not vals.get("member_number"):
            # Obtener el próximo número de socio desde la configuración
            next_number = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("socios.proximoNroSocio")
            )
            vals["member_number"] = next_number

            # Incrementar el número en 1 y actualizar la configuración
            new_next_number = int(next_number) + 1
            self.env["ir.config_parameter"].sudo().set_param(
                "socios.proximoNroSocio", new_next_number
            )
        record = super(ClubMember, self).create(vals)
        return record

    @api.depends("suscripcion_id")
    def _compute_estado_suscripcion(self):
        for record in self:
            record.estado_suscripcion = (
                record.suscripcion_id.estado if record.suscripcion_id else False
            )
            record.estado = (
                record.suscripcion_id.estado if record.suscripcion_id else False
            )
