{
    'name': 'CRM Fetch Mail Action',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Adds a server-action for fetching mail',
    'depends': ['crm', 'mail'],
    'data': [
        'data/server_action.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
