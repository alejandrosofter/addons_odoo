# -*- coding: utf-8 -*-
{
    "name": "Importer",
    "summary": "Modulo para importar desde otros lugares info",
    "description": "Aplicativo para manejo de importaciones",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    # any module necessary for this one to work correctly
    "depends": ["base", "queue_job"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/importer.xml",
    ],
    "images": ["static/description/icon.png"],
    # only loaded in demonstration mode
}
