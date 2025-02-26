{
    "name": "Users Whatsapp",
    "summary": "Modulo para uso de whatsapp en el usuario",
    "description": "Modulo para usuarios whatsapp",
    "author": "Softer",
    "website": "https://softer.com.ar",
    "category": "Uncategorized",
    "version": "0.1",
    "application": False,
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "contacts", "web"],
    "assets": {
        "web.assets_backend": [
            "softer_wsap/static/src/js/systray_icon.js",
            "softer_wsap/static/src/xml/systray_icon.xml",
        ],
    },
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        # "views/user.xml",
        "views/res_config_settings_view.xml",
        "views/cron.xml",
        "views/bot.xml",
        "views/menu.xml",
        "views/res_partner_view.xml",
        "views/message_wizard.xml",
        "views/mail_message_view.xml",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
