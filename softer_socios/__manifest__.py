# -*- coding: utf-8 -*-
{
    "name": "Softer Socios",
    "version": "17.0.1.0.0",
    "category": "Softer",
    "summary": "Gestión de Socios",
    "description": """
        Módulo para la gestión de socios.
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": [
        "base",
        "mail",
        "softer_suscripciones",
        "softer_payment_siro",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/socios_categoria_data.xml",
        "views/res_partner_inherit.xml",
        "views/socios_categoria_views.xml",
        "views/socio_views.xml",
        "views/socio_payment_views.xml",
        "views/socio_estados_views.xml",
        "views/socios_pendientes_actividad_views.xml",
        "views/res_config_settings_view.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
