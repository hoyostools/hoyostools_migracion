# -*- coding: utf-8 -*-
{
    'name': "Acuse de Recibo",

    'summary': """
        Gestión del Acuse de Recibo de Facturas Electrónicas""",

    'description': """
        Este módulo permite gestionar el Acuse de Recibo en Odoo, cumpliendo con los requerimientos normativos 
        de la DIAN en Colombia. Se extienden vistas y modelos relacionados con facturación electrónica y 
        tipos de identificación para registrar y validar los acuses de recibo por parte de los clientes.
    """,

    'author': "Brawil Solutions Sas",
    'website': "",
    'version': '17.0',
    'license': 'OPL-1',
    'category': 'Accounting/Localizations',

    'depends': [
        'base',
        'account',
        'l10n_latam_base',
        'l10n_co_dian_data',
    ],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/l10n_latam_identification_type.xml',
        'views/account_move.xml',
        # 'views/acuse_recibo.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
