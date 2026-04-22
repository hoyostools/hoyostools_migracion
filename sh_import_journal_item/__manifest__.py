# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Journal Items from CSV/Excel file",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "summary": "Import Journal Items From CSV Module, Import Journal Item From Excel App, Import Journal Entry From CSV, import Journal Entry From Excel, Import Journal Data From CSV, Import mass Journal items, import multiple journals Odoo",
    "description": """ This module is used to import journal items from CSV/Excel files. You just enable the group 'Import Journal Item' in the user setting then after that user can import journal items from the CSV/Excel file.""",
    "version": "0.0.1",
    "depends": [
        "sh_message",
        "account"
    ],
    "application": True,
    "data": [
        'security/import_journal_item_security.xml',
        'security/ir.model.access.csv',
        'wizard/import_journal_item_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'external_dependencies': {'python': ['xlrd'], },
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": 13,
    "currency": "EUR"
}
