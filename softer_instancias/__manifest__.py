# -*- coding: utf-8 -*-
{
    "name": "Instancias",
    "summary": "Modulo para gestion de mis instancias softer",
    "description": "Aplicativo para manejo de las instancias",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    # any module necessary for this one to work correctlyv
    "depends": [
        "base",
        "subscription_package",
        "website",
        "website_sale",
        "account",
        "sale",
        "product",
        "queue_job",
    ],
    "assets": {
        "web.assets_frontend": [
            "softer_instancias/static/css/instancias.css",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/instancias.xml",
        "views/imagenes.xml",
        "views/apps.xml",
        "views/web.xml",
        "views/account_link_view.xml",
        "views/edit_instancia.xml",
        "views/product_template.xml",
        "views/res_config_settings_views.xml",
        "views/dominios.xml",
        "views/utils.xml",
        "views/subscriptions.xml",
    ],
    "images": ["static/description/icon.png"],
    # only loaded in demonstration mode
    # "demo": [
    #     "demo/demo.xml",
    # ],
}
