{
    'name': 'Portal Sale History',
    'version': '1.2',
    'category': 'Website',
    'summary': 'Consulta de historial de ordenes de venta desde el portal',
    'depends': ['portal', 'sale_management', 'website', 'website_sale_product_configurator','compra_productos_peti'],
    'data': [
        'views/portal_templates.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "portal_sale_history/static/src/js/cart.js",
            "portal_sale_history/static/src/css/portal_sale_history.css",
        ],

    },
    'installable': True,
    'application': False,
}
