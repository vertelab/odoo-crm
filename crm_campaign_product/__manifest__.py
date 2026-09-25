# Copyright (C) 2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'CRM Campaign Product',
    'version': '18.0.1.0.0',
    'category': 'Marketing/Campaigns',
    'summary': 'Link products to CRM campaigns.',
    'description': '''
CRM Campaign Product
====================

    Link products to CRM campaigns.

    Features:

        - UI Integration: Extends 1 view(s) in the Odoo interface.
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-crm/crm_campaign_product',
    'license': 'AGPL-3',
    'depends': ['crm_campaign_addons', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_campaign_product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
