from odoo import models, fields, api


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    esDefault = fields.Boolean(string="Es Default", default=False)
