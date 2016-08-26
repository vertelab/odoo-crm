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
    'name': 'CRM Meeting',
    'version': '0.1',
    'category': '',
    'summary': "Create call lists and meetings",
    'description': """
        * Wizard create call list for checked res.partner
        * Wizard create meetings for checked res.partner
        * (Wizard create call list / meetings for crm.lead)
        * Add field latest meeting for res.partner
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['crm', 'calendar_kanban', 'calendar'],
    'data': [
        'res_partner_view.xml',
        'wizard/res_partner_phonecall_wizard_view.xml',
        'wizard/res_partner_meeting_wizard_view.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
