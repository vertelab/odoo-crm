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
import datetime
import logging
import base64
_logger = logging.getLogger(__name__)

import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = 'res.partner'

    repord_3p_supplier = fields.Boolean('Resell for')
    repord_3p_partner_pricelist_ids = fields.One2many('rep.order.partner.pricelist', 'partner_id', '3rd Party Pricelists')
    repord_3p_category_ids = fields.One2many('product.category', 'repord_3p_supplier', 'Categories')
    
    @api.multi
    def _get_3p_supplier_pricelist(self, supplier):
        res = self.env['rep.order.partner.pricelist'].search([('partner_id', '=', self.id), ('seller_id', '=', supplier.id)])
        _logger.warn(res)
        if res:
            return res[0].pricelist_id
        if self.parent_id:
            return self.parent_id._get_3p_supplier_pricelist(supplier)
    
    @api.multi
    def _get_repord_pricelist(self):
        if self.property_product_pricelist != self.env.ref('product.list0'):
            return self.property_product_pricelist
        elif self.parent_id:
            return self.parent_id._get_repord_pricelist()
        else:
            return self.property_product_pricelist
        
class rep_order_partner_pricelist(models.Model):
    _name = 'rep.order.partner.pricelist'
    _description = 'Pricelist Lines'
    
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    seller_id = fields.Many2one('res.partner', 'Seller', domain=[('repord_3p_supplier', '=', True)], required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)

class product_pricelist(models.Model):
    _inherit = 'product.pricelist'
    
    repord_3p_partner_pricelist_id = fields.Many2one('rep.order.partner.pricelist', '3rd Party Pricelist')
    
class rep_order(models.Model):
    _inherit = "rep.order"
    
    third_party_supplier = fields.Many2one('res.partner', 'Third Party Supplier', compute='repord_set_3p_supplier', store=True, readonly=False)
    order_type = fields.Selection(selection_add = [('3rd_party', 'Third Party Order')])
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True, readonly=True,
        compute='repord_set_pricelist', store=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="Pricelist for current sales order.")
    
    @api.one
    @api.depends('order_type', 'order_line', 'order_line.product_id')
    def repord_set_3p_supplier(self):
        if self.order_type == '3rd_party':
            for line in self.order_line:
                if line.product_id and line.product_id.categ_id and line.product_id.categ_id.repord_3p_supplier:
                    self.third_party_supplier = line.product_id.categ_id.repord_3p_supplier
                    return
        self.third_party_supplier = None
    
    #This gets overwritten by the onchange when using the view
    @api.one
    @api.depends('order_type', 'third_party_supplier', 'partner_id', 'state')
    def repord_set_pricelist(self):
        _logger.warn(self.pricelist_id)
        if self.partner_id and self.state == 'draft':
            pricelist = None
            if self.order_type == '3rd_party' and self.third_party_supplier:
                pricelist = self.partner_id._get_3p_supplier_pricelist(self.third_party_supplier)
            if pricelist:
                self.pricelist_id = pricelist
            else:
                self.pricelist_id = self.partner_id._get_repord_pricelist()

                
    
class product_category(models.Model):
    _inherit = 'product.category'
    
    repord_3p_supplier = fields.Many2one('res.partner', 'Resell for', inverse='_repord_set_3p_supplier', readonly=False, domain=[('repord_3p_supplier', '=', True)])
    
    @api.one
    def _repord_set_3p_supplier(self):
        for category in self.child_id:
            category.repord_3p_supplier = self.repord_3p_supplier
    
#~ class MobileSaleView(openerp.addons.crm_repord.MobileSaleView):
    #~ 
