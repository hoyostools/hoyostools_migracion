{
    'name': 'Retail Product Extension',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'depends': ['product', 'stock'],
    'author': 'Distribuciones Hoyostools',
    'website': 'https://www.hoyostools.com',
    'license': 'LGPL-3',
    'summary': 'Agrega pestaña Retail al producto y modelo de productos retail',
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/retail_product_view.xml',
    ],
    'installable': True,
    'application': False,
}
