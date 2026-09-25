# -*- coding: utf-8 -*-
##############################################################################
#
#    CRM: Skapad datum och tid
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
    'name': 'CRM: Skapad datum och tid',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': "Shows the creation date and time (without seconds) in CRM list and kanban views.",
    'description': '''
Skapad datum och tid
====================

    Shows the "Created on" column in CRM list views (Leads and Opportunities)
as well as on the kanban cards.

    - The column is always visible and can be sorted.
    - Time is shown without seconds.
    ''',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-crm/crm_lead_created_on',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
