# # -*- coding: utf-8 -*-
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

MODULE_BASE_PATH = '/mobile/contact/'
MODULE_TITLE = _('Contact')

class res_partner(models.Model):
    _inherit = 'res.partner'


class website_crm_partner(http.Controller):

    @http.route([
    MODULE_BASE_PATH + '<model("res.partner"):partner>',
    MODULE_BASE_PATH,
    MODULE_BASE_PATH + 'add',
    MODULE_BASE_PATH + '<model("res.partner"):partner>/delete',
    MODULE_BASE_PATH + '<model("res.partner"):partner>/edit',
    MODULE_BASE_PATH + 'search',
    MODULE_BASE_PATH + 'set_login',
    ], type='http', auth="public", website=True)
    def get_partner(self, partner=None, search='',**post):

        search_domain = [('type','=','contact')]
        model = 'res.partner'
        fields =  ['name','is_company','phone','email','type']
        template = {'list': 'website_crm_partner.object_list', 'detail': 'website_crm_partner.object_detail'}

        if request.httprequest.url[-4:] == 'edit': #Edit
            if request.httprequest.method == 'GET':
                return request.render(template['detail'], {'model': model, 'object': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'title': partner.name, 'db': request.db, 'mode': 'edit'})
            else:
                partner.write({
                    f: post.get(f) for f in fields
                })
                return request.render(template['detail'], {'model': model, 'object': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'title': partner.name, 'db': request.db, 'mode': 'view'})
        elif request.httprequest.url[-3:] == 'add': #Add
            if request.httprequest.method == 'GET':
                return request.render(template['detail'], {'model': model, 'object': None, 'fields': fields, 'root': MODULE_BASE_PATH, 'title': 'Add User', 'db': request.db,'mode': 'add'})
            else:
                record = { f: post.get(f) for f in fields }
                record['type'] = 'contact'
                partner = request.env['res.partner'].create(record)
                return request.render(template['detail'], {'model': model, 'object': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'title': partner.name, 'db': request.db, 'mode': 'view'})
        elif request.httprequest.url[-6:] == 'delete': #Delete
            if partner:
                partner.unlink()
                return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
        elif request.httprequest.url[-6:] == 'search': #Search
            if request.httprequest.method == 'POST':
                search = post.get('search_words')
            search_domain.append(('name','ilike',search))
        elif request.httprequest.url[-9:] == 'set_login': #set login form
            if request.httprequest.method == 'POST':
                return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
            return request.render(template['list'], {'object': None, 'root': MODULE_BASE_PATH, 'title': MODULE_TITLE, 'db': request.db,})
        elif partner:  # Detail
            return request.render(template['detail'], {'model': model, 'object': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'title': partner.name, 'db': request.db, 'mode': 'view'})
        return request.render(template['list'], {
            'objects': request.env['res.partner'].search(search_domain, order='name'),
            'title': MODULE_TITLE,
            'root': MODULE_BASE_PATH,
            'db': request.db,
        })

    @http.route(['/mobile/security/<model("res.partner"):partner>', '/mobile/security'], type='http', auth="user", website=True)
    def mobile_security(self, partner=False, **post):
        return request.render('website_crm_partner.object_list', {
            'model': 'res.partner',
            'objects': request.env['res.partner'].search([('type','=','contact')], order='name'),
            'title': MODULE_TITLE,
            'root': MODULE_BASE_PATH,
            'db': request.db,
})
    #~ @http.route(['/allcategory/<model("product.category"):category>', ], type='http', auth="public", website=True)
    #~ def get_category(self, parent_id=1, **post):
        #~ cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #~ categories = request.env['product.category'].sudo().search([('parent_id', '=', parent_id)], order='id')
        #~ #categories.filtered("category.is_translated(lang)")
        #~ return request.render('website_product_category.page_allcategories', {'categories': categories})



