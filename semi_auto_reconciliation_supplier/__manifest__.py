{
    'name': 'Cruce Proveedores',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Conciliación semiautomática para proveedores',
    'author': 'Distribuciones Hoyostools',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cruce_finalizado_supplier_data.xml',
        'views/cruce_finalizado_supplier_views.xml',
        'views/semi_auto_reconciliation_supplier_views.xml',
        'views/wizard_supplier_view.xml',
        'reports/report_cruce_proveedores_template.xml',
    ],
    'installable': True,
    'application': False,
}