# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2027- Vertel AB (<http://vertel.se>).
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
    'name': 'CRM Campaign Product',
    'version': '0.3',
    'category': 'crm',
    'description': """
        Extends Crm Campaign with products
""",
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-crm/crm_campaign_product',
    'images': ['static/description/banner.png'], # 560x280 px.
    'depends': ['crm_campaign_vrtl', 'stock'],
    'data': [
        'views/product_view.xml',
        'security/ir.model.access.csv',

    ],
    'installable': True,
}

