# -*- coding: utf-8 -*-
{
    "name": "Documento Soporte DIAN",
    "summary": "Gestión de Documento Soporte para adquisiciones a no obligados a facturar.",
    "description": """
Este módulo permite la creación y gestión del Documento Soporte exigido por la DIAN en Colombia para operaciones con proveedores no obligados a expedir factura electrónica.

Características:
- Extiende la localización colombiana con funcionalidad específica del Documento Soporte.
- Adapta vistas de diario y factura.
- Control y validación de información requerida por la normativa.
    """,
    "version": "17.0",
    "author": "Brawil Solutions Sas",
    "email": "",
    "website": "",
    "category": "Accounting/Localizations",
    "license": "OPL-1",
    "currency": "COP",

    # Dependencias
    "depends": [
        "base",
        "l10n_co_e_invoicing",
        "account",
    ],

    # Datos cargados
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/account_journal_views.xml",
        "views/account_invoice_views.xml",
    ],

    "application": True,
    "installable": True,
    "auto_install": False,
}
