# hooks.py
from odoo import exceptions


def check_installation_code():
    """Verifica el código de instalación durante la activación del módulo."""
    code = input("Introduce el código de instalación para este módulo: ")

    # Código de validación (puedes cambiarlo a lo que desees)
    valid_code = "Piteroski1984"

    if code != valid_code:
        raise exceptions.UserError(
            "Código de instalación inválido. No se puede instalar el módulo."
        )
