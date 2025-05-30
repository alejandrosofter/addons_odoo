# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Contacto"

    socio_id = fields.Many2one(
        "res_partner.socio",
        string="Socio",
        ondelete="set null",
        help="Socio único asociado a este contacto",
    )
    fecha_nacimiento = fields.Date(
        string="Fecha de Nacimiento",
        help="Fecha de nacimiento del contacto",
        tracking=True,
        store=True,
    )
    genero = fields.Selection(
        selection=[("M", "Masculino"), ("F", "Femenino")],
        string="Género",
        tracking=True,
    )
    payment_adhesion_id = fields.Many2one(
        "payment.adhesiones",
        string="Adhesión SIRO",
        tracking=True,
        domain="[('state', '=', 'confirmed')]",
        help="Adhesión de pago SIRO asociada a este socio",
    )

    _sql_constraints = [
        (
            "socio_id_uniq",
            "unique(socio_id)",
            "Cada contacto solo puede estar vinculado a un único socio.",
        ),
    ]
