# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SocioPaymentInherit(models.Model):
    _inherit = "res_partner.socio"

    payment_adhesion_id = fields.Many2one(
        "payment.adhesiones",
        string="Adhesión SIRO",
        tracking=True,
        domain="[('state', '=', 'confirmed')]",
        help="Adhesión de pago SIRO asociada a este socio",
    )

    paga_debito_automatico = fields.Boolean(
        string="Paga Débito Automático",
        default=False,
        tracking=True,
        help="Indica si el socio paga mediante débito automático",
    )

    @api.onchange("payment_adhesion_id")
    def _onchange_payment_adhesion_id(self):
        if self.payment_adhesion_id:
            self.paga_debito_automatico = True
        else:
            self.paga_debito_automatico = False

    @api.constrains("payment_adhesion_id", "paga_debito_automatico")
    def _check_payment_adhesion(self):
        for record in self:
            if record.payment_adhesion_id and not record.paga_debito_automatico:
                raise ValidationError(
                    _(
                        "No puede asignar una adhesión SIRO si no está marcada la "
                        "opción de pago por débito automático."
                    )
                )
            if not record.payment_adhesion_id and record.paga_debito_automatico:
                raise ValidationError(
                    _(
                        "Debe seleccionar una adhesión SIRO si marca la opción "
                        "de pago por débito automático."
                    )
                )
