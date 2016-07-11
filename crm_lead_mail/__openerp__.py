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
    'name': 'CRM Lead Mail',
    'version': '0.1',
    'category': '',
    'summary': "Send mail when a new lead is created",
    'description': """
When a new crm-lead is created from website_contact or mail to info@your_domain.com
a reminder is sent to administers with a copy of the mail or information from
the form.

To make this module work:

1) change the email-template (email_to,reply_to) so they reflect your domain and 
list of users that should have a notification
2) check the mail configuration so users have mail forwarding with a copy activated for
the mail-address to your catchall-address configured in Odoo

Todo:
* not send mail when leads are imported from csv-file or manually added
* the list of email_to could be fetched from group_sale_salesman or other group.

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['base','crm', 'mail', ],
    'data': [
        'crm_lead_mail_data.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
