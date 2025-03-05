from odoo import models, fields


class EventoAnimal(models.Model):
    _name = "softer.evento.animal"
    _description = "Eventos de Animales"
    _order = "fecha desc"

    name = fields.Char(string="Nombre del Evento", required=True)
    fecha = fields.Datetime(
        string="Fecha y Hora", required=True, default=fields.Datetime.now
    )
    tipo = fields.Selection(
        [
            ("vacunacion", "Vacunación"),
            ("pesaje", "Pesaje"),
            ("revision_medica", "Revisión Médica"),
            ("tratamiento", "Tratamiento"),
            ("reproduccion", "Reproducción"),
            ("otro", "Otro"),
        ],
        string="Tipo de Evento",
        required=True,
    )

    descripcion = fields.Text(string="Descripción")
    responsable_id = fields.Many2one(
        "res.users", string="Responsable", default=lambda self: self.env.user
    )
    animal_id = fields.Many2one("softer.animal", string="Animal", required=True)

    costo = fields.Float(string="Costo")
    resultado = fields.Text(string="Resultado/Observaciones")

    estado = fields.Selection(
        [
            ("programado", "Programado"),
            ("en_proceso", "En Proceso"),
            ("completado", "Completado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        default="programado",
        required=True,
    )
