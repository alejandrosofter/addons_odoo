from odoo import exceptions


def check_installation_code(cr, registry):
    """Verifica el código de instalación durante la activación del módulo."""
    # Aquí puedes solicitar el código de instalación, por ejemplo desde un servidor externo
    code = input("Introduce el código de instalación para este módulo: ")

    # Ejemplo de validación contra un código fijo
    valid_code = "Piteroski1984"

    if code != valid_code:
        raise exceptions.UserError(
            "Código de instalación inválido. No se puede instalar el módulo."
        )
