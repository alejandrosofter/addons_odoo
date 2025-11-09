{
    "name": "Evolution API Integration",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "summary": "Integración con Evolution API para WhatsApp",
    "description": """
        This module integrates Odoo with Evolution API for WhatsApp
        communication.
        Features include:
        - WhatsApp number management
        - Message sending and tracking
        - File attachments support
        - Webhook event tracking
    """,
    "author": "Softer",
    "website": "https://www.softer.com.py",
    "depends": [
        "base",
        "sale",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/evolution_api_views.xml",
        "views/evolution_api_webhook_views.xml",
        "views/message_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_inherit_views.xml",
        "views/evolution_api_qr_wizard_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
