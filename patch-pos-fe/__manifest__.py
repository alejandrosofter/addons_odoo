# -*- coding: utf-8 -*-
{
    "name": "Patch POS Facturación Electrónica",
    "summary": "Valida automáticamente facturas AFIP desde el POS",
    "description": """
        Este módulo asegura que las facturas creadas desde el punto de venta
        se validen automáticamente en AFIP si el diario tiene configuración AFIP.

        Soluciona el problema donde las facturas creadas desde el POS se generan
        correctamente pero no se imputan automáticamente en AFIP hasta que se
        validan manualmente desde el módulo de facturación.
    """,
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Point of Sale",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "depends": [
        "point_of_sale",
        "l10n_ar_afipws_fe",
    ],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
