# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Contacto"

    fecha_nacimiento = fields.Date(
        string="Fecha de Nacimiento",
        help="Fecha de nacimiento del contacto",
        tracking=True,
        store=True,
    )
