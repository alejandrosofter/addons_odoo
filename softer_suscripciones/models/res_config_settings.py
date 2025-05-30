# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dias_ejecutar_cron = fields.Char(
        string="Días para ejecutar el cron",
        config_parameter="softer_suscripciones.dias_ejecutar_cron",
        default="1",
        help=(
            "Días del mes (separados por coma) en los que se ejecutará el cron. "
            "Ej: 1,2,3"
        ),
    )
    meses_ejecutar_cron = fields.Char(
        string="Meses para ejecutar el cron",
        config_parameter="softer_suscripciones.meses_ejecutar_cron",
        default="1",
        help=(
            "Meses del año (separados por coma) en los que se ejecutará el cron. "
            "Ej: 1,10,12"
        ),
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "softer_suscripciones.dias_ejecutar_cron", self.dias_ejecutar_cron
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "softer_suscripciones.meses_ejecutar_cron",
            self.meses_ejecutar_cron,
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(
            dias_ejecutar_cron=params.get_param(
                "softer_suscripciones.dias_ejecutar_cron", default="1"
            ),
            meses_ejecutar_cron=params.get_param(
                "softer_suscripciones.meses_ejecutar_cron", default="1"
            ),
        )
        return res
