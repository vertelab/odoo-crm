# Copyright (C) 2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'CRM Campaign Phase',
    'version': '18.0.1.0.0',
    'category': 'Marketing/Campaigns',
    'summary': 'Campaign phases with pricelists and country filtering.',
    'description': '''
CRM Campaign Phase
==================

    Campaign phases with pricelists and country filtering.

    Features:

        - UI Integration: Extends 2 view(s) in the Odoo interface.
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-crm/crm_campaign_phase',
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
