from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Instala el módulo después de la inicialización de la base de datos"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.module.module"].search(
        [("name", "=", "softer_patch_website"), ("state", "=", "uninstalled")]
    ).button_install()
