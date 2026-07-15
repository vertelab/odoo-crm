# Copyright (C) 2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'CRM Campaign Phase',
    'version': '18.0.1.0.0',
    'category': 'Marketing/Campaigns',
    'summary': 'Campaign phases with pricelists and country filtering',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se',
    'license': 'AGPL-3',
    'depends': ['website_crm_campaign'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_campaign_phase_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
