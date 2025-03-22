{
    "name": "Actividades",
    "summary": "Modulo para administrar Actividades de clubes",
    "description": "Modulo para administrar Actividades de clubes",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "application": False,
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["softer_suscripciones"],
    # "pre_init_hook": "pre_init_hook",
    # always loaded
    "data": [
        "security/groups.xml",
        "security/rules.xml",
        "security/ir.model.access.csv",
        # "views/res_config_settings_view.xml",
        # "views/cron.xml",
        # "security/rules.xml",  # Asegúrate de incluir este archivo
        "views/actividades.xml",
        "views/suscripciones_inherit.xml",
        "views/asistencias.xml",
        "views/recursos.xml",
        # "views/menu.xml",
        # "views/res_partner_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
