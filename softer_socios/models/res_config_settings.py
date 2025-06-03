# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    default_city = fields.Char(
        string="Ciudad por Defecto",
        config_parameter="socios.default_city",
        default_model="res_partner.socio",
        default="",
    )
    default_state_id = fields.Many2one(
        "res.country.state",
        string="Provincia por Defecto",
        config_parameter="socios.default_state_id",
        default_model="res_partner.socio",
    )
    default_country_id = fields.Many2one(
        "res.country",
        string="País por Defecto",
        config_parameter="socios.default_country_id",
        default_model="res_partner.socio",
    )
    default_zip = fields.Char(
        string="Código Postal por Defecto",
        config_parameter="socios.default_zip",
        default_model="res_partner.socio",
        default="",
    )
    default_edad_adherente = fields.Integer(
        string="Edad Adherente por Defecto",
        config_parameter="socios.default_edad_adherente",
        default_model="res_partner.socio",
        default=18,
        help="Edad por defecto para considerar a un socio como adherente",
    )
    default_categoria_id = fields.Many2one(
        "socios.categoria",
        string="Categoría por Defecto",
        config_parameter="socios.default_categoria_id",
        default_model="res_partner.socio",
        help="Categoría por defecto para nuevos socios",
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_city", self.default_city
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_state_id", self.default_state_id.id or False
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_country_id", self.default_country_id.id or False
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_zip", self.default_zip
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_edad_adherente", self.default_edad_adherente
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "socios.default_categoria_id", self.default_categoria_id.id or False
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        state_id = params.get_param("socios.default_state_id", default=False)
        country_id = params.get_param("socios.default_country_id", default=False)
        edad_adherente = params.get_param("socios.default_edad_adherente", default=18)
        categoria_id = params.get_param("socios.default_categoria_id", default=False)
        res.update(
            default_city=params.get_param("socios.default_city", default=""),
            default_state_id=int(state_id) if state_id else False,
            default_country_id=int(country_id) if country_id else False,
            default_zip=params.get_param("socios.default_zip", default=""),
            default_edad_adherente=int(edad_adherente),
            default_categoria_id=int(categoria_id) if categoria_id else False,
        )
        return res
