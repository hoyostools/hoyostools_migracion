# -*- coding: utf-8 -*-
{
    'name': 'Semi-Automatic Reconciliation of Invoices and Payments',
    'version': '17.0.1.9.0',
    'summary': 'Reconcile invoices, credit notes, and payments semi-automatically by customer',
    'description': """
        This module allows you to reconcile invoices, credit notes, and payments 
        semi-automatically in Odoo. Designed to simplify and speed up the reconciliation 
        process for accounting teams.

        Main Features:
            - ✅ Automatic loading of unreconciled invoices, credit notes, and payments
            - ✅ Grouped view by customer
            - ✅ Real-time matching of debits and credits
            - ✅ Clean and intuitive user interface
            - ✅ Designed for companies with high transaction volumes
            """,
    'category': 'Accounting',
    'author': 'Distribuciones Hoyostools',
    'website': 'https://www.hoyostools.com',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'data/journal_data.xml',
        'security/ir.model.access.csv',
        'views/wizard_select_clients_view.xml',
        'views/semi_auto_reconciliation_views.xml',
        'views/cruce_finalizado_views.xml',
        'reports/report_cruce_saldos_template.xml',
        'data/cruce_finalizado_data.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'semi_auto_reconciliation_ht/static/src/js/sum_auto_refresh_list.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
