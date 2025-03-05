{
    "name": "Gestión de Ganado",
    "version": "17.0.1.0.0",
    "category": "Agriculture",
    "summary": "Módulo para gestión de ganado",
    "description": """
        Módulo para la gestión de ganado que incluye:
        - Registro de animales
        - Control de nacimientos
        - Gestión de razas
        - Registro de eventos
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/animal_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "icon": "/softer_animales/static/description/icon.png",
}
