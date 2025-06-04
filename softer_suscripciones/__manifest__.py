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
        * Gestión de plantillas de suscripción
    """,
    "author": "Softer",
    "website": "https://www.softer.com",
    "depends": [
        "base",
        "sale",
        "softer_payment_siro",
        "sale_management",
        "contacts",
        "softer_socios",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron_data.xml",
        "views/suscripciones.xml",
        "views/sale_order_views.xml",
        "views/suscripciones_planes_views.xml",
        "views/suscripcion_generator_views.xml",
        "views/res_config_settings_view.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
