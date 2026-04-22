# -*- coding: utf-8 -*-
{
    "name": "Factura Electrónica Colombia",
    "summary": "Implementación de Factura Electrónica DIAN para Colombia.",
    "description": """
Este módulo extiende la localización colombiana para habilitar la generación, validación y envío de Factura Electrónica conforme a los requisitos de la DIAN.

Características:
- Generación de XML UBL conforme a la normativa colombiana.
- Validación previa al envío.
- Configuración de secuencias y tipos de documentos electrónicos.
- Cron automático de sincronización/envío.
- Extensión del modelo de factura para incluir campos técnicos DIAN.
    """,
    "version": "17.0",
    "author": "Brawil Solutions Sas",
    "website": "https://brawilsolutions.odoo.com",
    "license": "OPL-1",
    "category": "Accounting/Localizations",
    "depends": [
        "account_debit_note",
        "l10n_co_dian_data",
        "pos_intermedio",
    ],
    

    "data": [
        # Seguridad
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        # Vistas
        "report/account_invoice_report_template.xml",
        "views/account_invoice_views.xml",
        "views/account_invoice_dian_document_views.xml",
        "views/account_journal_views.xml",
        "views/ir_sequence_views.xml",
        "views/res_company_views.xml",
        "views/account_tax_group_views.xml",
        "views/product_template_views.xml",
        "views/account_move_approve.xml",
        "views/pos_payment_method_views.xml",
        "views/account_payment_term.xml",

        # Datos
        "data/product_scheme_data.xml",

        # Automatizaciones
        "data/cron_acp_tacita_dian.xml",
    ],
    
    "installable": True,
    "application": False,
    "auto_install": False,
}
