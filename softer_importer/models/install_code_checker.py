from odoo import models, fields
from odoo.exceptions import UserError


class InstallCodeChecker(models.TransientModel):
    _name = "install.code.checker"
    _description = "Verificador de Código de Instalación"

    code = fields.Char(string="Código de Instalación", required=True)

    def validate_code(self):
        """Valida el código ingresado por el usuario."""
        valid_code = "Piteroski1984"  # Cambia esto por tu lógica
        if self.code != valid_code:
            raise UserError("El código de instalación es inválido.")
