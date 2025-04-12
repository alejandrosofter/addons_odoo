from odoo import models, fields, api


class EvolutionApiNumbers(models.Model):
    _name = "evolution.api.numbers"
    _description = "Evolution API WhatsApp Numbers"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
    channel = fields.Selection(
        [
            ("baileys", "Baileys"),
            ("evolution", "Evolution"),
            ("whatsapp_api", "Whatsapp API"),
        ],
        string="Canal",
        required=True,
    )
    token = fields.Char(string="Token", required=True)
    number = fields.Char(string="Numero", required=True)
    estado = fields.Selection(
        [("active", "Active"), ("inactive", "Inactive")],
        string="Estado",
        default="inactive",
        required=True,
    )
