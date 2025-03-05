from odoo import models, fields, api
from datetime import datetime


class Animal(models.Model):
    _name = "softer.animal"
    _description = "Registro de Animales"
    _rec_name = "numero"

    numero = fields.Char(string="Número de Identificación", required=True)
    fecha_nacimiento = fields.Date(string="Fecha de Nacimiento")
    raza = fields.Selection(
        [
            ("angus", "Angus"),
            ("hereford", "Hereford"),
            ("holstein", "Holstein"),
            ("brahman", "Brahman"),
            ("otras", "Otras"),
        ],
        string="Raza",
        required=True,
    )

    peso = fields.Float(string="Peso (kg)")
    genero = fields.Selection(
        [("macho", "Macho"), ("hembra", "Hembra")], string="Género", required=True
    )

    estado = fields.Selection(
        [("activo", "Activo"), ("vendido", "Vendido"), ("fallecido", "Fallecido")],
        string="Estado",
        default="activo",
        required=True,
    )

    madre_id = fields.Many2one("softer.animal", string="Madre")
    padre_id = fields.Many2one("softer.animal", string="Padre")

    evento_ids = fields.One2many("softer.evento.animal", "animal_id", string="Eventos")

    notas = fields.Text(string="Notas Adicionales")

    @api.depends("fecha_nacimiento")
    def _compute_edad(self):
        for animal in self:
            if animal.fecha_nacimiento:
                today = fields.Date.today()
                edad = today.year - animal.fecha_nacimiento.year
                if today.month < animal.fecha_nacimiento.month or (
                    today.month == animal.fecha_nacimiento.month
                    and today.day < animal.fecha_nacimiento.day
                ):
                    edad -= 1
                animal.edad = edad
            else:
                animal.edad = 0

    edad = fields.Integer(string="Edad (años)", compute="_compute_edad", store=True)
