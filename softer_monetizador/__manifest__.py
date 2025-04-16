{
    "name": "Control de Pagos de Servicios",
    "summary": "Módulo para gestionar el control de pagos de servicios Odoo",
    "description": """
        Módulo que permite gestionar y controlar los pagos de servicios Odoo.
        Características:
        - Registro de pagos
        - Control de vencimientos
        - Historial de transacciones
        - Notificaciones automáticas
    """,
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Accounting",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "account"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
    "application": True,
}
