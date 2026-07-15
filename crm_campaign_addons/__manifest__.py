# Copyright (C) 2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'CRM Campaign',
    'version': '18.0.1.0.0',
    'category': 'Marketing/Campaigns',
    'summary': 'Campaign management for CRM with objects, calendar, and Gantt',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se',
    'license': 'AGPL-3',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_campaign_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
