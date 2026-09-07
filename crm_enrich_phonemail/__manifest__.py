# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2024- Vertel AB (<https://vertel.se>).
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
    'name': 'CRM: Enrich Phonemail',
    'version': '1.1',
    'summary': 'Enrich CRM-leads records with companys website',
    'description': """
      Base module for Enrich CRM-leads records with company's website and contact details
    """,
    'sequence': '999',
    'author': 'Vertel Sverige AB',
    'category': 'CRM',
    'website': 'https://vertel.se/apps/odoo-crm/crm_enrich_phonemail',
    'images': ['static/description/banner.png'],  # 560x280 px.
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-crm',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_view.xml'
    ],
    'application': False,
    'installable': True,
}

