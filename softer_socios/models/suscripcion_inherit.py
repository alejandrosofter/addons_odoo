# -*- coding: utf-8 -*-
from odoo import models, fields


class SuscripcionInherited(models.Model):
    _inherit = "softer.suscripcion"

    tieneSocio = fields.Boolean(string="Tiene Socio", default=False)
    idSocio = fields.Many2one(
        comodel_name="res_partner.socio",
        string="Socio",
        tracking=True,
    )
