################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2019 N-Development (<https://n-development.com>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

{
    'name': 'CRM: LinkedIn Leads',
    'version': '14.0.0.0.1',
    'summary': 'Creates partners from LinkedIn',
    'category': 'CRM',
    'description': """
        Creates partners from LinkedIn.
    """,
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-crm/linkedin_contacts',
    'images': ['static/description/banner.png'],  # 560x280 px.
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-crm',
    'depends': ['base', 'base_setup'],
    'data': [
        'views/res_users_view.xml',
        'views/res_company_view.xml',
        'views/res_config_view.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
