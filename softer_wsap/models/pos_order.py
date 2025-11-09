# -*- coding: utf-8 -*-

from odoo import models, fields


class PosOrder(models.Model):
    _inherit = "pos.order"

    x_phone_number = fields.Char(string="Número de Teléfono")
