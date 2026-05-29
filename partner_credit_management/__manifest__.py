# -*- coding: utf-8 -*-
{
    "name": "Partner Credit Management",
    "version": "17.0.1.0.0",
    "summary": "Gestión de crédito para clientes y validación en ventas",
    "author": "Brawil Solution Sas",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": [
        "contacts",
        "sale_management",
        "account",
    ],
    "data": [
        "security/group_control_credito.xml",
        "security/ir.model.access.csv",
        "views/credit_risk_type_views.xml",
        "views/credit_config_wizard_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'partner_credit_management/static/src/js/pos_credit_block.js',
        ],
    },
    "installable": True,
    "application": False,
}