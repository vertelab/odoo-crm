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
from openerp import models, fields, api, _
from openerp import http
from openerp.http import request


import logging
_logger = logging.getLogger(__name__)

class rep_order(models.Model):
    _name = "rep.order"
    _inherit = "sale.order"
    
    order_type = fields.Selection([('scrap','Scrap'),('order','Order'),('reminder','Reminder'),('discount','Discount')],default='order',string="Order Type",)
    
    @api.one
    def action_view_sale_order_line_make_invoice(self):
        pass

class res_partner(models.Model):
    _inherit = 'res.partner'

    product_ids = fields.Many2many(comodel_name='product.product', string='Products')
    #~ add_product = fields.Boolean(compute='_add_product')
    #~ remove_product = fields.Boolean(compute='_remove_product')

    #~ @api.one
    #~ def _add_product(self, product_id):
        #~ if product_id not in self.product_ids:
            #~ self.product_ids.append(product_id)

    #~ @api.one
    #~ def _remove_product(self, product_id):
        #~ if product_id in self.product_ids:
            #~ self.product_ids.remove(product_id)

#~ class product_product(models.Model):
    #~ _inherit = 'product.product'

    #~ partner_id = fields.Many2many(comodel_name='res.partner', string='Shop')


class MobileSaleView(http.Controller):
    @http.route(['/crm/<model("res.partner"):parter>/repord'], type='http', auth="public", website=True)
    def repord(self, parter=None, **post):
        products = request.env['res.partner'].sudo().search([('id', '=', parter.id)]).product_ids
        parent_products = request.env['res.partner'].sudo().search([('id', '=', parter.id)]).parent_id.product_ids
        return request.website.render("crm_repord.mobile_order_view", {'partner': parter, 'products': products, 'parent_products': parent_products,})

