{
    "name": "Softer Portal Sale",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "summary": "Personalización del portal de ventas",
    "description": """
        Personalización del portal de ventas para permitir:
        - Selección múltiple de pedidos
        - Generación de facturas desde el portal
        - Vista personalizada de pedidos
        - Vista extendida de pagos
    """,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "depends": [
        "sale",
        "portal",
        "account",
        "web",
        "website",
        "payment",
    ],
    "data": [
        # "security/ir.model.access.csv",
        # "security/ir.rule.csv",
        # "views/portal_templates.xml",
        # "views/portal_home.xml",
        # "templates/portal_my_orders.xml",
        "templates/payment_portal_templates.xml",
    ],
    # "assets": {
    #     "web.assets_frontend": [
    #         "softer_portal_sale/static/src/css/portal_my_orders.css",
    #         "softer_portal_sale/static/src/js/portal_sale.js",
    #     ],
    #     "web.assets_frontend_lazy": [
    #         "softer_portal_sale/static/src/css/portal_my_orders.css",
    #     ],
    # },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
