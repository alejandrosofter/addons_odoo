# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Softer Payment SIRO",
    "version": "17.0.1.0.0",
    "category": "Accounting/Payment",
    "sequence": 1,
    "author": "Softer",
    "website": "https://www.softer.com.ar",
    "license": "LGPL-3",
    "depends": [
        "payment",
        "account",
        "sale",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/payment_cuentas_imputadas_views.xml",
        # Vistas y Acciones
        "views/payment_provider_views.xml",
        "views/payment_siro_templates.xml",
        "views/payment_qr_estatico_views.xml",
        "views/payment_qr_estatico_pago_views.xml",
        "views/payment_mercado_pago_templates.xml",
        "views/payment_transaction_views.xml",
        "views/payment_adhesiones_views.xml",
        "views/payment_lote_deuda_views.xml",
        "views/payment_rendicion_views.xml",
        "views/payment_pendientes_pago_views.xml",
        "views/sale_order_inherit.xml",
        # Menús (deben cargarse después de las vistas)
        "views/payment_provider_action.xml",
        "views/menu.xml",
        # Datos
        "data/payment_provider_data.xml",
        "data/payment_lote_deuda_sequence.xml",
        "data/ir_cron_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": True,
    "installable": True,
}
