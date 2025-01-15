# -*- coding: utf-8 -*-
{
    "name": "Importer",
    "summary": "Modulo para importar desde otros lugares info - CON CODIGO DE ACTIVACION NECESARIO",
    "description": "Aplicativo para manejo de importaciones",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
    # any module necessary for this one to work correctly
    "depends": ["base", "queue_job"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/importer.xml",
    ],
    "images": ["static/description/icon.png"],
    "post_init_hook": "check_installation_code",
    # only loaded in demonstration mode
}
