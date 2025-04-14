from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    """Instala el módulo antes de la inicialización de la base de datos"""
    cr.execute(
        """
        INSERT INTO ir_module_module (
            name, state, latest_version, author, website,
            category_id, description, shortdesc, icon,
            application, web, license, sequence, auto_install
        ) VALUES (
            'softer_patch_website', 'to install', '17.0.1.0.0',
            'Softer', 'https://www.softer.com.ar',
            (SELECT id FROM ir_module_category WHERE name = 'Website'),
            'Corrige el error KeyError: REQUEST_URI en el método _is_canonical_url',
            'Softer Website Patch', '/base/static/description/icon.png',
            false, false, 'LGPL-3', 100, true
        ) ON CONFLICT (name) DO NOTHING;
    """
    )
