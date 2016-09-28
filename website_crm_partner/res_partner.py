# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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

from openerp import api, models, fields, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

MODULE_BASE_PATH = '/mobile/sample/'

class res_partner(models.Model):
    _inherit = 'res.partner'



class website_crm_partner(http.Controller):

    @http.route(['/crm/partner/<model("res.partner"):partner>','/crm/partner' ], type='http', auth="user", website=True)
    def get_partners(self, partner=False, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        return request.render('website_crm_partner.partner_list', {'partners': request.env['res.partner'].sudo().search([], order='name',limit=25),            'root': MODULE_BASE_PATH,
            'db': request.db,})
    
    #~ @http.route(['/allcategory/<model("product.category"):category>', ], type='http', auth="public", website=True)
    #~ def get_category(self, parent_id=1, **post):
        #~ cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #~ categories = request.env['product.category'].sudo().search([('parent_id', '=', parent_id)], order='id')
        #~ #categories.filtered("category.is_translated(lang)")
        #~ return request.render('website_product_category.page_allcategories', {'categories': categories})



