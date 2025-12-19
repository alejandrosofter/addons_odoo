{
    "name": "Anclajes",
    "summary": "Modulo para manejo de anclajes",
    "description": "ABM de anclajes para empresas de servicios petroleros",
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
        "security/groups.xml",
        "security/rules.xml",
        "views/anclajes.xml",
        "views/zonas.xml",
        "views/res_config_settings_view.xml",
        "views/user.xml",
        "views/equipos.xml",
        "data/mail_template.xml",
        "security/ir.model.access.csv",
    ],
    # "data": ["security/ir.model.access.csv", "views/importer.xml"],
    # "images": ["static/description/icon.png"],
    # "pre_init_hook": "pre_init_hook",
    # only loaded in demonstration mode
}
