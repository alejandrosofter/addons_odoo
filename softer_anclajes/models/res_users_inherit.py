from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    ref = fields.Char(string="Referencia")
