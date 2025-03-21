{
    "name": "Softer Suscripciones",
    "version": "1.0",
    "category": "Sales",
    "summary": "Módulo para gestionar suscripciones a productos",
    "description": """
        Módulo de suscripciones que permite:
        * Registrar suscripciones a productos
        * Gestionar fechas de inicio y fin
        * Control de recurrencia
        * Estados de suscripción
        * Generación automática de ventas según recurrencia
    """,
    "depends": ["base", "sale", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/cron_data.xml",
        "reports/suscripcion_report.xml",
        "views/suscripciones.xml",
        # "views/suscripcion_report_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
