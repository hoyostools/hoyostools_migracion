{
    'name': 'Custom Profitability',
    'version': '1.0',
    'category': 'Product',
    'summary': 'Añade un campo para calcular el precio de lista basado en la renta esperada.',
    'description': 'Este módulo añade un campo "Renta a ganar" al modelo de productos y calcula automáticamente el precio de lista.',
    'author': 'Brayan Jimenez',
    'depends': ['product'],
    'data': [
        'views/product_template_view.xml',    
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
