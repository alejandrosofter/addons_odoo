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
            last_member = self.search([], order="member_number desc", limit=1)
            next_number = (
                str(int(last_member.member_number) + 1)
                if last_member and last_member.member_number
                else "1"
            )
            vals["member_number"] = next_number
        record = super(ClubMember, self).create(vals)
        return record
