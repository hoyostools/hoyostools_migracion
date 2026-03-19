{
    'name': 'Portal Sale Order Tracking',
    'version': '17.0.1.0',
    'category': 'Website',
    'author': 'Distribuciones Hoyostools',
    'summary': 'Seguimiento de pedidos desde portal',
    'depends': ['website', 'portal', 'sale_management', 'google_recaptcha'],
    'data': [
        'views/portal_button.xml',
        'views/portal_templates.xml',
        'views/status_logistic_sale_order_web.xml',
    ],
    'installable': True,
    'application': False,
}