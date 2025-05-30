# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentCuentasImputadas(models.Model):
    _name = "payment.cuentas.imputadas"
    _description = "Cuentas Imputadas para Pagos"
    _order = "fecha_alta desc"

    fecha_alta = fields.Date(
        string="Fecha de Alta",
        required=True,
        default=fields.Date.context_today,
    )

    estado = fields.Selection(
        [
            ("disponible", "Disponible"),
            ("no_disponible", "No Disponible"),
            ("baja", "Baja"),
        ],
        string="Estado",
        required=True,
        default="disponible",
    )

    cbu = fields.Char(
        string="CBU",
        required=True,
        help="Clave Bancaria Uniforme",
    )

    alias = fields.Char(
        string="Alias",
        help="Alias de la cuenta bancaria",
    )

    cuenta = fields.Char(
        string="Cuenta",
        required=True,
        help="Número de cuenta bancaria",
    )

    ref_cliente = fields.Char(
        string="Referencia Cliente",
        required=True,
        help="Referencia del cliente",
    )

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("cbu_unique", "unique(cbu)", "El CBU debe ser único por cuenta imputada."),
        ("cuenta_unique", "unique(cuenta)", "El número de cuenta debe ser único."),
    ]

    @api.constrains("cbu")
    def _check_cbu_length(self):
        for record in self:
            if record.cbu and len(record.cbu.strip()) != 22:
                raise ValidationError(_("El CBU debe tener exactamente 22 dígitos."))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.cuenta} - {record.ref_cliente}"
            result.append((record.id, name))
        return result
