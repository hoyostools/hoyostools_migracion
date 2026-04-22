# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Payments From CSV File | Import Payments From Excel File",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": "Import Payment CSV Import Payment Excel Import Payment From XLSX Import Mass Payment Import Bulk Payment Import Partner Payment Import Payment From XLS Payment Import Payments Import Customer Payment Import Supplier Payment Import Vendor Payment Import Customer and Supplier Payment from Excel File Import Customer Payment from Excel File Import  Supplier Payment from Excel File Account Payment Import Import Payment Voucher Odoo",
    "description": """This module is useful to bulk import partner payments with payment details from CSV/Excel file. You can import partners by partner name, email, contact number, reference & database ID. Additionally, we provide the option to create a partner if never exists & an auto-posted payment option. So you do not need to enter records manually. You can also import custom fields from CSV or Excel file.""",
    "version": "0.0.2",
    "depends": [
        'account',
        'sh_message',
    ],
    "data": [
        'security/sh_import_payment_groups.xml',
        'security/ir.model.access.csv',
        'wizard/sh_import_payment_views.xml',
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 17,
    "currency": "EUR"
}
