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
    'version': '1.0',
    'summary': 'Add montitor capabilities to leads and opportunity',
    'category': 'CRM',
    'description': """
        This module adds cron-jobs and triggers that looks for stale tasks and take action using rules on the opportunity
    """,
    'author': 'Vertel AB',
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
