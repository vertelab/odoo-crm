{
    'name': 'CRM Fetch Mail Action',
'author': 'Vertel Sverige AB',
'website': 'https://vertel.se/apps/odoo-crm/crm_fetchmail',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Adds a server-action for fetching mail.',
    'description': '''
CRM Fetch Mail Action
=====================

    Adds a server-action for fetching mail.

    Features:

        - UI Integration: Extends 1 view(s) in the Odoo interface.
        - Extends Odoo: Builds on crm.lead.
    ''',
    'depends': ['crm', 'mail'],
    'data': [
        'data/server_action.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
