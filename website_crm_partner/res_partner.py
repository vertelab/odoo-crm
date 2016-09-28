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
import werkzeug

import logging
_logger = logging.getLogger(__name__)

MODULE_BASE_PATH = '/mobile/crm/'

class res_partner(models.Model):
    _inherit = 'res.partner'


class website_crm_partner(http.Controller):

    @http.route(['/mobile/crm/partner/<model("res.partner"):partner>', '/mobile/crm/partner/', '/mobile/crm/partner/add', '/mobile/crm/partner/<model("res.partner"):partner>/edit'], type='http', auth="public", website=True)
    def get_partner(self, partner=False, **post):
        _logger.warn('create', post.get('name'))
        if request.httprequest.method == 'POST':
            if post.get('search'): #search
                partners = request.env['res.partner'].search(['&', ('name', 'ilike', post['search_words']), ('type', '=', 'contact')], order='name',limit=25)
                return request.render('website_crm_partner.partner_list', {'partners': partners, 'root': MODULE_BASE_PATH, 'db': request.db,})
            else:
                if partner: #edit
                    request.env['res.partner'].write({
                        'name': post.get('name'),
                        'comment': post.get('comment', ''),
                    })
                elif post.get('save'): #create
                    request.env['res.partner'].create({
                        'name': post.get('name'),
                        'type': post.get('type'),
                        'comment': post.get('comment', ''),
                    })
                return werkzeug.utils.redirect('/mobile/crm/partner', 302)
        else: #read
            if partner:
                if request.httprequest.url[-4:] == 'edit':
                    return request.render('website_crm_partner.partner_edit', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db,})
                else:
                    return request.render('website_crm_partner.partner_detail', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db,})
            else:
                if request.httprequest.url[-3:] == 'add':
                    return request.render('website_crm_partner.partner_edit', {'partner': None, 'root': MODULE_BASE_PATH, 'db': request.db,})
                else:
                    partners = request.env['res.partner'].search([('type', '=', 'contact')], order='name',limit=25)
                    return request.render('website_crm_partner.partner_list', {'partners': partners, 'root': MODULE_BASE_PATH, 'db': request.db,})



    #~ @http.route(['/allcategory/<model("product.category"):category>', ], type='http', auth="public", website=True)
    #~ def get_category(self, parent_id=1, **post):
        #~ cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #~ categories = request.env['product.category'].sudo().search([('parent_id', '=', parent_id)], order='id')
        #~ #categories.filtered("category.is_translated(lang)")
        #~ return request.render('website_product_category.page_allcategories', {'categories': categories})



