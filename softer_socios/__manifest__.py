# -*- coding: utf-8 -*-
{
    "name": "Softer Socios",
    "version": "17.0.1.0.0",
    "category": "Softer",
    "summary": "Gestión de Socios",
    "description": """
        Módulo para la gestión de socios
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": [
        "base",
        "contacts",
        "softer_wsap",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/socio_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
