# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) {year} {company} (<{mail}>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#
# https://www.odoo.com/documentation/14.0/reference/module.html
#
{
    'name': 'CRM Manual Stage Scoring',
    'version': '17.0.0.0.0',
    'summary': """This module makes it possible to set a probability on stages in CRM""",
    'category': 'Marketing', # Technical Settings|Localization|Payroll Localization|Account Charts|User types|Invoicing|Sales|Human Resources|Operations||Manufacturing|Website|Theme|Administration|Appraisals|Sign|Helpdesk|Administration|Extra Rights|Other Extra Rights|
    'description': """
        With this module, you can set probabilities on stages in the CRM.
        So that when you move a lead/opportunity to that stage, its probability becomes the value you yourself have put instead of Odoo's.
        This without disabling Odoo's probability calculations.
        The way it does this is by setting the value as a manual value instead of automatic, which is what Odoo does.
        You can also set a stage to be a "zero stage" that will make values put in that stage zero.
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-',
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'depends': ['crm'],
    'data': ['views/crm_stage_views.xml'],
    'demo': [],
    'application': False,
    'installable': True,    
    'auto_install': False,
}
