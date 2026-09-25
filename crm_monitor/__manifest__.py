# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2025- Vertel AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'CRM: Lead/opportunity Monitor',
    'version': '18.0.1.0.0',
    'summary': 'Add montitor capabilities to leads and opportunity.',
    'category': 'CRM',
    'description': '''
Lead/opportunity Monitor
========================

    This module adds cron-jobs and triggers that looks for stale tasks and take action using rules on the opportunity

    Features:

        - Automation: Scheduled jobs: CRM Monitor stage checker, CRM Monitor stage checker.
        - UI Integration: Extends 2 view(s) in the Odoo interface.
        - Extends Odoo: Builds on crm.lead, crm.stage, crm.stage.monitor, mail.activity.type.
    ''',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-crm/crm_monitor',
    'repository': 'https://github.com/vertelab/odoo-crm',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'depends': ['crm'],
    'data': [
        'data/cron.xml',
        'data/server_action.xml',
        'views/crm_stage_views.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}

