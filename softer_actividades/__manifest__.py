{
    "name": "Softer Actividades",
    "version": "1.0",
    "category": "Softer",
    "summary": "Gestión de Actividades",
    "description": """
        Módulo para gestionar actividades
        ===============================

        * Gestión de actividades
        * Gestión de integrantes
        * Gestión de horarios
    """,
    "author": "Softer",
    "website": "https://www.softer.com",
    "depends": ["base", "mail", "softer_suscripciones"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/actividades.xml",
        "views/actividades_integrantes.xml",
        "views/actividades_mensajes.xml",
        "views/asistencias.xml",
        "views/recursos.xml",
        "views/suscripciones_inherit.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
