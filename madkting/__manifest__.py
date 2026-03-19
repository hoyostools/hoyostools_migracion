# -*- coding: utf-8 -*-
{
    'name': "Yuju",

    'summary': """
        Integration with Yuju's platform""",

    'description': """
        Module integration with Yuju's software platform.
        - Create orders into your odoo software from marketplaces like Mercado Libre, Amazon, etc..
        - Create products from Yuju platform into odoo
        - Update your stock from odoo to your Yuju account.
    """,

    'author': "Gerardo A Lopez Vega @glopzvega",
    'email': "gerardo.lopez@yuju.io",
    'website': "https://yuju.io/",
    'category': 'Sales',
    'version': '17.0.2.5.7',
    'license': 'Other proprietary',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale_management',
        'stock',
        'component_event'
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_rule.xml',
        'views/config.xml',
        'views/mappings.xml',
        'views/webhooks.xml',
        'views/sale_order.xml',
        'views/product.xml',
        'views/menu_items.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    "cloc_exclude": [
        # "lib/common.py", # exclude a single file
        # "data/*.xml",    # exclude all XML files in a specific folder
        "controllers/**/*",  # exclude all files in a folder hierarchy recursively
        "log/**/*",  # exclude all files in a folder hierarchy recursively
        "models/**/*",  # exclude all files in a folder hierarchy recursively
        "notifier/**/*",  # exclude all files in a folder hierarchy recursively
        "requirements/**/*",  # exclude all files in a folder hierarchy recursively
        "responses/**/*",  # exclude all files in a folder hierarchy recursively
        "security/**/*",  # exclude all files in a folder hierarchy recursively
        "views/**/*",  # exclude all files in a folder hierarchy recursively
    ]
}

# Version 2.5.7
# Agrega opcion para buscar stock en campos calculados, oculta opcion de ubicaciones hijas
# TODO: se va a agregar funcion para agreupar stock de ubicaciones hijas en ubicacion padre

# Version 2.5.6
# Agrega opcion para actualizar nombre del cliente con direccion de factura

# Version 2.5.5
# Agrega opcion para buscar stock en ubicaciones hijas

# Version 2.5.4
# Fix webhook simple

# Version 2.5.3
# Fix metodo busqueda partners active.

# Version 2.5.2
# Actualiza metodo sen webhook_all para enviar webhook de los productos.

# Version 2.5.1
# Agrega configuracion de envio de webhooks stock por CRON, si no se activa, 
# se envia al momento de crear o actualizar el stock

# Version 2.5.0
# Agrega optimizacion de consultas pedidos y productos, agrega indices a campos usados en busquedas frecuentes
