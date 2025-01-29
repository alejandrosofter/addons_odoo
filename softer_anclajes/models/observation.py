from odoo import models, fields, api


class Observation(models.Model):
    _name = "anclajes.observaciones"
    _description = "Observation"

    name = fields.Char(string="Detalle")
    fecha = fields.Date(string="Fecha", default=fields.Date.today)
    usuario = fields.Many2one(
        "res.users", string="Usuario", default=lambda self: self.env.user
    )
    anclaje = fields.Many2one("anclajes.anclajes", string="Anclaje")
