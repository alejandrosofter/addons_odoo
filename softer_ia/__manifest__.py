{
    "name": "Softer IA",
    "version": "17.0.1.0.0",
    "summary": "Módulo para gestionar agentes de IA",
    "description": """
        Módulo para la gestión y configuración de agentes de Inteligencia
        Artificial en Odoo.
    """,
    "category": "Extra Tools",
    "author": "Softer SA",
    "website": "https://www.softer.com.ar",
    "license": "LGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ia_agente_views.xml",
        "views/ia_query_views.xml",
        "views/menus.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
