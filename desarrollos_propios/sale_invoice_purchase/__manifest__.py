{
    "name": "Factura genera Orden de Compra",
    "version": "17.0.24.0",
    "summary": "Cada factura de venta crea automáticamente una orden de compra.",
    "description": """
Módulo que automatiza la creación de órdenes de compra
a partir de facturas de venta en Odoo 17.
""",
    "author": "Distribuciones Hoyostools",
    "website": "https://wwww.hoyostools.com",
    "category": "Accounting",
    "license": "LGPL-3",
    "depends": [
        "account",
        "purchase",
    ],
    "data": [
        'views/res_partner_views.xml',
        'views/purchase_order_view.xml',
        'views/remote_instance_views.xml',
        'views/res_config_settings_views.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

