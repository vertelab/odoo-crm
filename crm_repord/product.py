# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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

class product_product(models.Model):
    _inherit='product.product'
    
    @api.one
    def get_store_code(self,partner_id): # Check customer code in three levels
        partner = self.env['res.partner'].browse(partner_id)
        if self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.id)]): 
            self.store_code = self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.id)])[0].product_code
        elif partner.parent_id and self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.parent_id.id)]): 
            self.store_code = self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.parent_id.id)])[0].product_code
        elif partner.parent_id.parent_id and self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.parent_id.parent_id.id)]): 
            self.store_code = self.env['product.customer.code'].search([('product_id','=',self.id),('partner_id','=',partner.parent_id.parent_id.id)])[0].product_code
        else:
            self.store_code = ''
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
