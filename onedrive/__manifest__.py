# -*- coding: utf-8 -*-
{
    "name": "OneDrive / SharePoint Odoo Integration",
    "version": "17.0.1.2.6",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/17.0/onedrive-sharepoint-odoo-integration-17-0-onedrive-838",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/clouds_client.xml"
    ],
    "assets": {},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "microsoftgraph-python",
                "requests"
        ]
},
    "summary": "The tool to automatically synchronize Odoo attachments with OneDrive files in both ways. Microsoft documents. OneDrive cloud. SkyDrive cloud. SharePoint drives. Microsoft Odoo Integration. OneDrive synchronization. Microsoft Azure app. SharePoint synchronization. OneDrive connector. SharePoint connector",
    "description": """
For the full details look at static/description/index.html
* Features *- How synchronization works
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "89.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=44&ticket_version=17.0&url_type_id=3",
}