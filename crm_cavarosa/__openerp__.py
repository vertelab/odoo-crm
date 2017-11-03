# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'CRM Cavarosa',
    'version': '1.0',
    'category': 'Tools',
    'description': """
CRM configuration for Cavarosa AB
=================================
* A server action that generates sale orders from an exist order as template
* An email template
* Controller for email customers to accept or reject order
""",
    'author': 'Vertel AB',
    'website': 'https://vertel.se',
    'depends': ['sale_crm', 'mass_mailing_sale', 'email_template', 'website','delivery_pickup','crm_campaign_addons'],
    'data': [
        'res_partner_data.xml',
        'sale_order_view.xml',
        'sale_order_data.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
