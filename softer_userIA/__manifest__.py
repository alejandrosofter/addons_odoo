{
    "name": "Users IA",
    "summary": "Modulo para usuarios IA whatsapp",
    "description": "Modulo para usuarios IA whatsapp",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail"],
    # always loaded
    "data": [
        "views/userIa.xml",
        "views/res_config_settings_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
