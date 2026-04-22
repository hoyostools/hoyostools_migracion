# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Sale Order Lines from CSV/Excel file",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": "Import Quotation Lines From CSV Module, Import Quotation Lines From Excel App, Import SO Lines From CSV, import SO Lines From XLS, import sales order line from XLSX Odoo import sale order line data import sale order line from excel import sale order line from csv import bulk sale order line sale order line import mass sale order line Import mass sale order line data Import Data from Excel Import Data from CSV Import Quotations",
    "description": """
    
This module is useful to import Sale Order Lines from CSV/Excel. You can import custom fields from CSV or Excel.

 Import Sale Order Lines From CSV Odoo, Import Sale Order Lines From excel Odoo
 Import Quotation Lines From CSV Module, Import Quotation Lines From Excel, Import Sale Order Lines From CSV, Import Sale Order Lines From Excel, Import SO Lines From CSV, Import SO Lines From XLS XLSX Odoo.
 Import Quotation Lines From CSV Module, Import Quotation Lines From Excel App, Import SO Lines From CSV, import SO Lines From XLS XLSX Odoo 
 Importar líneas de orden de venta de CSV Odoo, Importar líneas de orden de venta de Excel Odoo
Importar líneas de cotización desde el módulo CSV, Importar líneas de cotización desde Excel, Importar líneas de orden de venta desde CSV, Importar líneas de orden de venta desde Excel, Importar líneas SO desde CSV, Importar líneas SO desde XLS XLSX Odoo.
 Importar líneas de cotización desde el módulo CSV, Importar líneas de cotización desde la aplicación Excel, Importar líneas SO desde CSV, importar líneas SO desde XLS XLSX Odoo
                    """,
    "version": "0.0.1",
    "depends": [
        "sale_management",
        "sh_message",
    ],
    "application": True,
    "data": [
        'security/import_sol_security.xml',
        'security/ir.model.access.csv',
        'wizard/import_sol_wizard_views.xml',
        'views/sale_views.xml',
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": 13,
    "currency": "EUR"
}
