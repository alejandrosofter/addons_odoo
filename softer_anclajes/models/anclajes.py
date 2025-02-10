from odoo import models, fields
import requests


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
    fechaEnsayo = fields.Date(string="Fecha de Ensayo")
    fechaConstruccion = fields.Date(string="Fecha de Construcción")
    horaEnsayo = fields.Char(string="Hora de Ensayo")
    anclaje_no = fields.Selection(
        selection=[("A", "Aprobado"), ("R", "Rechazado"), ("", "Sin definir")],
        string="Anclaje NO",
        default="",
        required=False,
    )
    anclaje_ne = fields.Selection(
        selection=[("A", "Aprobado"), ("R", "Rechazado"), ("", "Sin definir")],
        string="Anclaje NE",
        default="",
        required=False,
    )
    anclaje_so = fields.Selection(
        selection=[("A", "Aprobado"), ("R", "Rechazado"), ("", "Sin definir")],
        string="Anclaje SO",
        default="",
        required=False,
    )
    anclaje_se = fields.Selection(
        selection=[("A", "Aprobado"), ("R", "Rechazado"), ("", "Sin definir")],
        string="Anclaje SE",
        default="",
        required=False,
    )
    certificado = fields.Binary(string="Certificado", attachment=True)
    zona_id = fields.Many2one(
        "anclajes.zonas",
        string="Zona",
        help="Seleccione la zona asociada con el anclaje",
    )
    pozo = fields.Char(string="Pozoo")
    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        default=lambda self: self.env.user,
        # readonly=True,
    )
