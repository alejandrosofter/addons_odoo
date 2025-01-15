# -*- coding: utf-8 -*-
{
    "name": "Whatsapp",
    "summary": "Modulo para gestion de mis instancias whatsapp",
    "description": "Aplicativo para manejo de las whatsapp mediante builderbot",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    # any module necessary for this one to work correctlyv
    "depends": [
        "softer_instancias",
    ],
    "assets": {
        "web.assets_frontend": [
            "softer_instancias/static/css/instancias.css",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/whatsapp.xml",
    ],
    "images": ["static/description/icon.png"],
    # only loaded in demonstration mode
    # "demo": [
    #     "demo/demo.xml",
    # ],
}
