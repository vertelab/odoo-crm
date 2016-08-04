#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2016- Vertel AB (<http://vertel.se>).
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

import odoorpc
#~ params = odoorpc.session.get('test')
params = odoorpc.session.get('paolos')
odoo = odoorpc.ODOO(params.get('host'),port=params.get('port'))
odoo.login(params.get('database'),params.get('user'),params.get('passwd'))

listing = {
    'ICA Nära': odoo.env.ref('crm_repord.listing_ica_planogramlagt').id,
    'ICA Supermarket': odoo.env.ref('crm_repord.listing_ica_planogramlagt').id,
    'ICA Kvantum': odoo.env.ref('crm_repord.listing_ica_tillgangligt').id,
    'F01': odoo.env.ref('crm_repord.listing_coop_ti').id,
    'F02': odoo.env.ref('crm_repord.listing_coop_pt').id,
    'F03': odoo.env.ref('crm_repord.listing_coop_sa').id,
    'F04': odoo.env.ref('crm_repord.listing_coop_gl').id,
    'F05': odoo.env.ref('crm_repord.listing_coop_ak').id,
    'F06': odoo.env.ref('crm_repord.listing_coop_ak').id,
    'F07': odoo.env.ref('crm_repord.listing_coop_ak').id,
    }

for p in odoo.env['res.partner'].read(odoo.env['res.partner'].search([]),['id','name','role']):
    if listing.get(p.get('role')):
        odoo.env['res.partner'].write(p['id'],{'listing_id': listing[p['role']]})
        print 'Partner %s updated' %p.get('name')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
