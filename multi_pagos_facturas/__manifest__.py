{
    'name': 'Multi Invoice Payment',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Pago multiple de facturas agrupado por cliente',
    'author': 'Distribuciones Hoyostools',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/multi_invoice_payment_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}