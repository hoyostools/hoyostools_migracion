{
    'name': 'Product Exact Internal Reference Search',
    'version': '17.0.1.0.0',
    'summary': 'Force exact match when searching by internal reference in products',
    'category': 'Product',
    'author': 'Brawil Solutions SAS',
    'depends': ['product', 'stock'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_quant_views.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
