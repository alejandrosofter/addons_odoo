from odoo import models, fields, api


class AltaActividades(models.Model):
    _inherit = "softer.suscripcion.alta"
    _description = "Alta de Suscripciones con Actividad"

    idActividad = fields.Many2one(
        "softer.actividades",
        string="Actividad",
        help="Actividad relacionada con esta alta",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "idActividad" in vals:
                # Si se proporciona idActividad, asegurarse de que se pase a las suscripciones
                self = self.with_context(default_idActividad=vals["idActividad"])
        return super().create(vals_list)
