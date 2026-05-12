{
    'name': 'Productos Consulta',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Consulta de productos e inventarios',
    'author': 'Distribuciones Hoyostools sas',
    'depends': [
        'product',
        'stock',
        'campos_hoyos',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True,
}