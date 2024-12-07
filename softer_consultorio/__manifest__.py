# -*- coding: utf-8 -*-
{
    "name": "Consultorio",
    "summary": "Modulo para gestion de tu consultorio de salud",
    "description": "Aplicativo para manejo de consultorios",
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
        "views/pacientes.xml",
        "views/consultorios.xml",
        "views/obrasociales.xml",
        "views/pacientesObrasSociales.xml",
        "views/recetas.xml",
        "views/turnos.xml",
        "views/medicamentos.xml",
        "views/anteojos.xml",
    ],
    "images": ["static/description/icon.png"],
}
