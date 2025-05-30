from odoo import models, fields


class SuscripcionInherited(models.Model):
    _inherit = "softer.suscripcion"

    tieneActividad = fields.Boolean(string="Tiene Actividad", default=False)
    idActividad = fields.Many2one(
        "softer.actividades", string="Actividad", tracking=True
    )
    integrante_id = fields.Many2one(
        "softer.actividades.integrantes",
        string="Integrante",
        tracking=True,
    )
    suscripcion_plantilla_id = fields.Many2one(
        "softer.suscripcion.plantilla",
        string="Plantilla de Suscripción",
        help="Plantilla de suscripción asociada al integrante",
        tracking=True,
    )
