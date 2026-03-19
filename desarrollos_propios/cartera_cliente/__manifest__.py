{
    'name': 'Cartera Cliente',
    'version': '17.0.2.0',
    'summary': 'Reporte de cartera por cliente',
    'author': 'Distribuciones Hoyostools Sas',
    'category': 'Accounting',
    'depends': ['base', 'contacts', 'account'],
    'data': [
        'security/cartera_groups.xml',
        'views/cartera_wizard_view.xml',
        'security/ir.model.access.csv',
        'views/cartera_menu.xml',
        'report/cartera_report_template.xml',
    ],
    'installable': True,
    'application': False,
}
