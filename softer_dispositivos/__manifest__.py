# -*- coding: utf-8 -*-
{
    "name": "Dispositivos",
    "summary": "Modulo para gestion de dispositivos",
    "description": "Aplicativo para manejo de dispositivos",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    # any module necessary for this one to work correctly
    "depends": ["base"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/dispositivos.xml",
        "views/menus.xml",
    ],
    "images": ["static/description/icon.png"],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
