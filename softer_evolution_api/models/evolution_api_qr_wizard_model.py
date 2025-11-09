from odoo import models, fields


class EvolutionApiQrWizard(models.TransientModel):
    _name = "evolution_api.qr.wizard"
    _description = "Evolution API QR Code Wizard"

    qr_code_image = fields.Binary(string="Código QR", readonly=True)
