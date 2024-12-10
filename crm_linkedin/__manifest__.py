# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'LinkedIn Lead Generation',
    'summary': 'Generate Leads/Opportunities from linkedin based on country, industries, size, etc.',
    'category': 'Sales/CRM',
    'version': '1.2',
    'depends': [
        'crm',
        'base',
        'automation_oca',
        'hr'
    ],
    'data': [
        'data/enrich_data.xml',
        'security/ir.model.access.csv',
        'views/linkedin_crm_lead_mining_request_views.xml',
        'views/crm_lead_view.xml',
        'views/res_partner_view.xml',
        'views/res_user_view.xml',
        'views/hr_employee_view.xml',
        'data/ir_cron.xml',
        'wizard/linkedin_employee_wizard_view.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
