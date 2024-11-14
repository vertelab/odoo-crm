# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'LinkedIn Lead Generation',
    'summary': 'Generate Leads/Opportunities from linkedin based on country, industries, size, etc.',
    'category': 'Sales/CRM',
    'version': '1.2',
    'depends': [
        'iap_crm',
        'iap_mail',
    ],
    'data': [
        # 'data/crm.iap.lead.industry.csv',
        # 'data/crm.iap.lead.role.csv',
        # 'data/crm.iap.lead.seniority.csv',
        # 'data/mail_template_data.xml',
        # 'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/linkedin_crm_lead_mining_request_views.xml',
        'views/crm_lead_views.xml'
        # 'views/res_config_settings_views.xml',
        # 'views/mail_templates.xml',
        # 'views/crm_menus.xml',
    ],
    'auto_install': True,
    # 'assets': {
    #     'web.assets_backend': [
    #         'crm_iap_mine/static/src/js/**/*',
    #     ],
    # },
    'license': 'LGPL-3',
}
