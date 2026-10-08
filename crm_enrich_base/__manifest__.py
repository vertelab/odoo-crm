# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2024- Vertel Sverige AB (<https://vertel.se>).
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
    'name': 'CRM: Enrich Base',
    'version': '18.0.1.1.0',
    'summary': 'Adding data.',
    'description': '''
Enrich Base
===========

    Base module for Enrich CRM-leads records with updated data. This module 
          does nothin but are a base fpr other enrichement modules

    Features:

        - Extends Odoo: Builds on crm.lead.
    ''',
    'sequence': '999',
    'author': 'Vertel Sverige AB',
    'category': 'CRM',
    'website': 'https://vertel.se/apps/odoo-crm/crm_enrich_base',
    'images': ['static/description/banner.png'], # 560x280 px.
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-crm',
    'depends': ['crm'],
    'data': [
        'data/ir_action.xml',
        # ~ 'views/res_partner_view.xml',
        
    ],
    'application': False,
    'installable': True,
}
