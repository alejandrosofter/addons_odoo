from odoo import models, fields


class SofterSyncronizerOrigenParam(models.Model):
    _name = "softer.syncronizer.origen.param"
    _description = "Parámetro de Origen de Sincronización"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True)
    value = fields.Char(string="Valor", required=True)
    active = fields.Boolean(string="Activo", default=True)
    origen_id = fields.Many2one(
        "softer.syncronizer.origen", string="Origen", required=True, ondelete="cascade"
    )
