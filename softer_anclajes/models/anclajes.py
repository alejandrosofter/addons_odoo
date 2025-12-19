from odoo import models, fields, api
import requests
from datetime import timedelta


class Anclajes(models.Model):
    _name = "anclajes.anclajes"
    _description = "Modelo para gestionar anclajes"

    name = fields.Char(string="Nombre", required=True)
    bateria = fields.Char(string="Batería")
    ref = fields.Char(string="Referencia")
    estado = fields.Selection(
        [
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
        ]
    )
    nroCertificado = fields.Char(string="Número de Certificado")
    equipoEnsayo = fields.Many2one(
        "anclajes.equipos", string="Equipo", help="Equipo relacionado con este anclaje"
    )
    observaciones = fields.One2many(
        "anclajes.observaciones", "anclaje", string="Observaciones"
    )

    equipoIngresante = fields.Char(string="Equipo Ingresante")
    fechaEnsayo = fields.Date(string="Fecha Ensayo")
    fechaConstruccion = fields.Date(string="Fecha de Construcción")
    horaEnsayo = fields.Char(string="Hora ")
    anclaje_e = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="E",
        default="",
        required=False,
    )
    anclaje_o = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="O",
        default="",
        required=False,
    )
    anclaje_no = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="NO",
        default="",
        required=False,
    )
    anclaje_ne = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="NE",
        default="",
        required=False,
    )
    anclaje_so = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="SO",
        default="",
        required=False,
    )
    anclaje_se = fields.Selection(
        selection=[("A", "A"), ("R", "R"), ("", "-")],
        string="SE",
        default="",
        required=False,
    )
    certificado = fields.Binary(string="Certificado", attachment=True)
    zona_id = fields.Many2one(
        "anclajes.zonas",
        string="Zona",
        help="Seleccione la zona asociada con el anclaje",
    )
    pozo = fields.Char(string="Pozo")
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user,
        # readonly=True,
    )
    fechaVencimiento = fields.Date(
        string="Fecha Vto", compute="_compute_fecha_vencimiento", store=True
    )

    @api.depends("fechaEnsayo")
    def _compute_fecha_vencimiento(self):
        for record in self:
            if record.fechaEnsayo:
                record.fechaVencimiento = record.fechaEnsayo + timedelta(days=2 * 365)
            else:
                record.fechaVencimiento = (
                    False  # Si no hay fecha de ensayo, el campo queda vacío
                )

    @api.model
    def create(self, vals):
        record = super(Anclajes, self).create(vals)
        if record.user_id:
            template = self.env.ref("softer_anclajes.email_template_new_anclaje")
            if template:
                template.send_mail(record.id, force_send=True)
        return record
