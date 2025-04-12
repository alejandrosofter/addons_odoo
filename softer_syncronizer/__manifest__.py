{
    "name": "Softer Syncronizer",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "summary": "Sincronización de datos entre sistemas",
    "description": """
        Módulo para sincronizar datos entre diferentes sistemas.
        Permite configurar orígenes y destinos de datos, y programar sincronizaciones automáticas.
    """,
    "author": "Softer",
    "website": "https://www.softer.com",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/syncronizer_views.xml",
        "views/syncronizer_origen_views.xml",
        "views/syncronizer_destino_views.xml",
        "views/syncronizer_resultados_views.xml",
        "views/menu.xml",
    ],
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "sequence": 1,
}
