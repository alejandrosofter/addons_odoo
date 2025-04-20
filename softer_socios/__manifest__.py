# -*- coding: utf-8 -*-
{
    "name": "Softer Socios",
    "version": "17.0.1.0.0",
    "category": "Socios",
    "summary": "Gestión de Socios",
    "description": """
        Módulo para la gestión de socios
        ===============================

        Características:
        ----------------
        * Gestión de socios
        * Categorías de socios
        * Estados de socios
        * Historial de estados
        * Socios pendientes de actividad
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": [
        "base",
        "mail",
        "softer_suscripciones",
        "softer_actividades",
    ],
    "data": [
        "security/security.xml",
        # "views/res_partner_inherit.xml",
        "security/ir.model.access.csv",
        "views/socio_views.xml",
        "views/socios_categoria_views.xml",
        "views/socios_pendientes_actividad_views.xml",
        "views/socios_pendientes_actividad_actions.xml",
        "views/res_config_settings_view.xml",
        "views/suscripciones_inherit.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
