{
    'name': 'Base en impuestos',
    'version': '17.0.1.0.0',
    'author': 'Brawil Solution Sas',
    'category': 'Sales',
    'summary': 'establecer una base de impuesto y cuando se realice una venta o compra se valide si aplica para que se le agrege el impuesto',
    'depends': ['sale', 'product', 'pos_sale', 'point_of_sale', 'account', 'base_automation', 'pos_intermedio'],
    'data': [
        'views/product_template_views.xml',
        'views/account_tax.xml',
        'views/account_fiscal_position.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',  
}