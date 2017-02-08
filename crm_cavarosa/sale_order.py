# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)


class sale_order_generator(models.TransientModel):
    _name = 'sale.order.generator'

    order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=True)
    @api.model
    def get_default_partner_ids(self):
        return self.env['res.partner'].browse(self._context.get('active_ids', []))
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', default=get_default_partner_ids)

    @api.one
    def generate_sale_orders(self):
        categs = self.get_so_categs(self.partner_ids)
        for p in self.partner_ids:
            values = self.order_id.onchange_partner_id(p.id)['value']
            values['partner_id'] = p.id
            order = self.order_id.copy(values)
            order.categ_ids = categs
            order.action_button_confirm()

    @api.model
    def get_so_categs(self, partners):
        rp_categs = partners[0].category_id
        for rp in partners[1:]:
            rp_categs &= rp.category_id
        so_categs = self.env['crm.case.categ'].browse([])
        if len(rp_categs) > 0:
            for rpc in rp_categs.mapped('name'):
                exist_categ = self.env['crm.case.categ'].search([]).filtered(lambda sc: sc.name == rpc)
                if len(exist_categ) > 0:
                    so_categs |= exist_categ[0]
                else:
                    so_categs |= self.env['crm.case.categ'].create({'name': rpc})
        return so_categs
