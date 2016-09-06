# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
##############################################################################

{
    'name': 'CRM Customer Latest activity',
    'version': '0.1',
    'category': 'crm',
    'summary': "Catch customer activites and updates a date",
    'description': """
        latest_activity a datetime with latest activity by the customer
        * invoice
        * stock picking
        * users login
        * sale order
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['account', 'stock','sale'],
    'data': [
        'res_partner_view.xml',
        #'wizard/res_partner_phonecall_wizard_view.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
