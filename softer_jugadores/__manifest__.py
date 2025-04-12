{
    "name": "Jugadores de clubes",
    "summary": "Modulo para Jugadores de clubes",
    "description": "Modulo para Jugadores de clubes",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "application": False,
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "contacts", "queue_job"],
    # "pre_init_hook": "pre_init_hook",
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        # "views/cron.xml",
        "views/jugadores_views.xml",
        "views/pruebas_views.xml",
        "views/pruebas_partidos_views.xml",
        # "views/res_partner_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
