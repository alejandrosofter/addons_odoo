# -*- coding: utf-8 -*-
{
    "name": "Compras email ai",
    "summary": "Modulo para gestionar las compras por email recibidas",
    "description": "Modulo para gestion de compras por email",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    # any module necessary for this one to work correctlyv AAAA	ibero-sa.net	2800:6c0:2::1500	14400
    'depends': ['mail', 'account'],
    "assets": {
        "web.assets_frontend": [
            # "softer_instancias/static/css/instancias.css",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/settings.xml",
    ],
    "images": [],
    # only loaded in demonstration mode
    # "demo": [
    #     "demo/demo.xml",
    # ],
}
