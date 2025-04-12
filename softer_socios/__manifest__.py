{
    "name": "Socios Clubes",
    "summary": "Modulo para socios de clubes",
    "description": "Modulo para socios de clubes",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "application": False,
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "contacts", "account"],
    # "pre_init_hook": "pre_init_hook",
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/socios.xml",
        "views/menu.xml",
        "views/res_config_settings_view.xml",
        "views/message_wizard.xml",
        # "views/cron.xml",
        # "views/res_partner_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
