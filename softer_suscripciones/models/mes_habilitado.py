from odoo import models, fields, api


class MesHabilitado(models.Model):
    _name = "softer.mes_habilitado"
    _description = "Mes habilitado para suscripción"
    _order = "orden asc"

    code = fields.Selection(
        [
            ("1", "Enero"),
            ("2", "Febrero"),
            ("3", "Marzo"),
            ("4", "Abril"),
            ("5", "Mayo"),
            ("6", "Junio"),
            ("7", "Julio"),
            ("8", "Agosto"),
            ("9", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes",
        required=True,
    )
    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    orden = fields.Integer(string="Orden", compute="_compute_orden", store=True)

    @api.depends("code")
    def _compute_name(self):
        for rec in self:
            rec.name = dict(self._fields["code"].selection).get(rec.code, "")

    @api.depends("code")
    def _compute_orden(self):
        for rec in self:
            try:
                rec.orden = int(rec.code)
            except Exception:
                rec.orden = 0

    @api.model
    def init(self):
        # Crear los 12 meses si no existen
        for code, nombre in self._fields["code"].selection:
            if not self.search([("code", "=", code)], limit=1):
                self.create({"code": code})
