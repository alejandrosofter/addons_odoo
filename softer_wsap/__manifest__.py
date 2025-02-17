{
    "name": "Users Whatsapp",
    "summary": "Modulo para uso de whatsapp en el usuario",
    "description": "Modulo para usuarios whatsapp",
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
        "security/ir.model.access.csv",
        "views/user.xml",
        "views/res_config_settings_view.xml",
        "views/cron.xml",
        "views/bot.xml",
        "views/menu.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
