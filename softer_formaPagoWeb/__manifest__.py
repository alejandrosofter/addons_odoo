# -*- coding: utf-8 -*-
{
    "name": "Forma de Pago Web fees",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "summary": "Extiende payment.method con interés, descuento y productos asociados",
    "description": "Agrega campos de interés, descuento, producto de interés y producto de descuento a las formas de pago web.",
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": ["payment", "product"],
    "data": [
        "views/payment_method_views.xml",
        "views/payment_form_inherit.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
