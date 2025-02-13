from odoo import models, fields, api


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    tipo = fields.Selection(
        [
            ("otro", "Otros"),
            ("feriado", "Feriado (*)"),
            ("vacaciones", "Vacaciones (*)"),
            ("pedido_dias", "Pedido de Dias (*)"),
            ("enfermedad", "Enfermedad (*)"),
            ("llegada_tarde", "Llegada Tarde (**)"),
            ("salida_temprana", "Salida Temprana (**)"),
            ("inasistencia", "Inasistencia (**)"),
        ],
        string="Tipo",
        required=True,
    )
    assistance_id = fields.Many2one(
        "hr.assistance",
        string="Asistencia Referencia",
        # ondelete="cascade",
    )

    @api.onchange("tipo")
    def _onchange_tipo(self):
        if self.tipo and self.tipo in dict(self._fields["tipo"].selection):
            self.name = dict(self._fields["tipo"].selection)[self.tipo]
        else:
            self.name = ""
