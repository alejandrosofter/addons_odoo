from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    instancia_id = fields.Many2one("instancias.instancias", string="Instancia")
    app_id = fields.Many2one("instancias.apps", string="App")
