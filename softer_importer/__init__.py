# -*- coding: utf-8 -*-

from . import controllers
from . import models
import os

# hooks.py
from odoo import exceptions


def pre_init_hook(env):
    """Verifica el código de instalación durante la activación del módulo."""
    print("Chequeando instalación...")

    env.cr.execute("SELECT value FROM ir_config_parameter WHERE key = 'web.base.url'")
    result = env.cr.fetchone()

    # Validar si existe un dominio configurado
    if not result:
        raise exceptions.UserError(
            "No se encontró el dominio del sistema en la configuración."
        )
    dominios_habilitados = os.getenv("DOMINIO_HABILITADO", "localhost")
    dominios_habilitados = [dom.strip() for dom in dominios_habilitados.split(",")]

    domain = result[0]
    if not any(
        domain.startswith(f"http://{dom}") or domain.startswith(f"https://{dom}")
        for dom in dominios_habilitados
    ):
        raise exceptions.UserError(
            f" '{domain}' no está habilitado para instalar este módulo. "
            # f"Dominios permitidos: {', '.join(dominios_habilitados)}"
        )
