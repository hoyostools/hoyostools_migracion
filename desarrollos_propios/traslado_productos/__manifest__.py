{
    'name': 'Transferencia de ubicación de existencias',
    'version': '1.0',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_quant_view.xml',
        'views/transfer_wizard_view.xml',
    ],
    'installable': True,
}
