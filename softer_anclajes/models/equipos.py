from odoo import models, fields


class Equipos(models.Model):
    _name = "anclajes.equipos"
    _description = "Modelo para Equipos"

    name = fields.Char(string="Nombre del Equipo", required=True)
    ref = fields.Char(string="Referencia")
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
        ],
        string="Estado",
        default="activo",
    )
