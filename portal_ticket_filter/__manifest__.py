{
    'name': 'Portal Helpdesk Ticket Filter',
    'version': '17.0.1.0.0',
    'summary': 'Show only logged user tickets in portal',
    'author': 'Distribuciones Hoyostools',
    'depends': [
        'helpdesk',
        'portal',
        'website_helpdesk'
    ],
    'data': [
        'views/portal_ticket_views.xml',
    ],
    'installable': True,
    'application': False,
}