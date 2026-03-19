{
    "name": "Sync Odoo XML-RPC (sale.order)",
    "version": "17.0.1.2.0",
    "summary": "Synchronize sale orders between Odoo instances via XML-RPC",
    "category": "Sales/Integration",
    "author": "Distribuciones Hoyostools",
    "license": "LGPL-3",
    "website": "https://www.hoyostools.com",
    "depends": ["sale", "base"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/sale_order.xml",
    ],
    "description": """
        This module allows the synchronization of sale orders (`sale.order`) 
        from a source Odoo database to a destination Odoo database via XML-RPC.

        Features:
        - Configurable XML-RPC connection per company
        - Automatic or manual synchronization of sale orders
        - Secure data transfer between Odoo instances
        - Developed and maintained by Distribuciones Hoyostools
    """,
    "installable": True,
    "application": False,
}
