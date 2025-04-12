{
    "name": "Softer Suscripciones",
    "version": "1.0",
    "category": "Softer",
    "summary": "Gestión de Suscripciones",
    "description": """
        Módulo para gestionar suscripciones
        ==================================

        * Gestión de suscripciones
        * Gestión de altas
        * Gestión de productos
    """,
    "author": "Softer",
    "website": "https://www.softer.com",
    "depends": ["base", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron_data.xml",
        "views/suscripciones.xml",
        "views/alta.xml",
        "views/sale_order_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
