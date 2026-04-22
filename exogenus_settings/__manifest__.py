# -*- coding: utf-8 -*-
{
    'name': 'Exógena',
    'version': '17.0',
    'summary': 'Ajustes y formatos para reportes de información exógena en Odoo',
    'description': """
Este módulo contiene todos los ajustes necesarios para la generación de información exógena ante la DIAN. 
Incluye configuraciones por banco, conceptos, columnas, formatos, y asignaciones por cuenta y tercero.
""",
    'category': 'Accounting/Localizations',
    'author': 'Brawil Solutions Sas',
    'website': '',
    'license': 'OEEL-1',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        # Seguridad
        'security/security.xml',
        'security/ir.model.access.csv',

        # Datos iniciales
        'data/format.exogenus.csv',
        'data/column.exogenus.csv',

        # Vistas
        'views/res_bank_view.xml',
        'views/format_exogenus_view.xml',
        'views/res_partner_view.xml',
        'views/account_account_view.xml',
        'views/account_exogenus_view.xml',
        'views/column_exogenus_view.xml',
        'views/concept_exogenus_view.xml',

        # Wizards
        'wizard/configuration_exogenus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
