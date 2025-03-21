from odoo import models, fields


class SuscripcionInherited(models.Model):
    _inherit = "softer.suscripcion"

    tieneActividad = fields.Boolean(string="Tiene Actividad", default=False)
    idActividad = fields.Many2one(
        "softer.actividades", string="Actividad", tracking=True, required=True
    )
