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

MODULE_BASE_PATH = '/mobile/contact/'
MODULE_TITLE = _('Contact')

class res_partner(models.Model):
    _inherit = 'res.partner'


class website_crm_partner(http.Controller):

    @http.route([
    MODULE_BASE_PATH + '<model("res.partner"):partner>',
    MODULE_BASE_PATH,
    MODULE_BASE_PATH + 'add',
    MODULE_BASE_PATH + 'delete',
    MODULE_BASE_PATH + '<model("res.partner"):partner>/edit',
    MODULE_BASE_PATH + 'set_login',
    ], type='http', auth="public", website=True)
    def get_partner(self, partner=False, **post):
        if request.httprequest.url[-4:] == 'edit': #edit form
            return request.render('website_crm_partner.partner_edit', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'edit'})
        if request.httprequest.url[-3:] == 'add': #add form
            return request.render('website_crm_partner.partner_edit', {'partner': None, 'root': MODULE_BASE_PATH, 'db': request.db,})
        if request.httprequest.url[-9:] == 'set_login': #set login form
            if request.httprequest.method == 'POST':
                return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
            return request.render('website_crm_partner.set_login', {'partner': None, 'root': MODULE_BASE_PATH, 'db': request.db,})
        if request.httprequest.method == 'POST':
            if post.get('id') == '' and post.get('btn-save') == 'btn-save': #new partner
                partner = request.env['res.partner'].create({
                    'name': post.get('name'),
                    'type': post.get('type'),
                    'comment': post.get('comment', ''),
                })
                return request.render('website_crm_partner.partner_detail', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db,})
            elif post.get('id') != '' and post.get('btn-save') == 'btn-save': #exist partner
                partner = request.env['res.partner'].browse(int(post.get('id')))
                partner.write({
                    'name': post.get('name'),
                    'comment': post.get('comment', ''),
                })
                return request.render('website_crm_partner.partner_detail', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db,})
            elif post.get('search_words') != '' and post.get('btn-search') == 'btn-search': #search
                partners = request.env['res.partner'].search(['&', ('name', 'ilike', post['search_words']), ('type', '=', 'contact')], order='name',limit=25)
                return request.render('website_crm_partner.partner_list', {'partners': partners, 'root': MODULE_BASE_PATH, 'db': request.db,})
            return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
        else:
            if partner:
                if partner and post.get('btn-delete') == 'btn-delete': #delete
                    partner.unlink()
                    return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
                return request.render('website_crm_partner.partner_edit', {'partner': partner, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'view'})
            else:
                partners = request.env['res.partner'].search([('type', '=', 'contact')], order='name',limit=25)
                return request.render('website_crm_partner.partner_list', {'partners': partners, 'root': MODULE_BASE_PATH, 'db': request.db,})


    @http.route([
    MODULE_BASE_PATH + '<model("res.partner"):partner>',
    MODULE_BASE_PATH,
    MODULE_BASE_PATH + 'add',
    MODULE_BASE_PATH + 'delete',
    MODULE_BASE_PATH + '<model("res.partner"):partner>/edit',
    MODULE_BASE_PATH + '<string:search>/search',
    MODULE_BASE_PATH + 'set_login',
    ], type='http', auth="public", website=True)
    def get_partner(self, partner=None, search='',**post):
        
        search_domain = [('type','=','contact')]
        fields =  ['name','phone','email']
        template = {'list': 'website_crm_partner.partner_list', 'detail': 'website_crm_partner.partner_detail'}
        
        if request.httprequest.url[-4:] == 'edit': #Edit
            if request.httprequest.method == 'GET':
                return request.render(template['detail'], {'partner': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'edit'})            
            else:
                partner.write({
                    'name': post.get('name'),
                    'comment': post.get('comment', ''),
                })
                return request.render(template['detail'], {'partner': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'view'})         
        elif request.httprequest.url[-3:] == 'add': #Add
            if request.httprequest.method == 'GET':
                return request.render(template['detail'], {'partner': None, 'root': MODULE_BASE_PATH, 'db': request.db,'mode': 'edit'})
            else:
                partner = request.env['res.partner'].create({
                    'name': post.get('name'),
                    'type': post.get('type'),
                    'comment': post.get('comment', ''),
                })
                return request.render(template['detail'], {'partner': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'view'})         
        elif request.httprequest.url[-6:] == 'delete': #Delete
            partner.unlink()
        elif request.httprequest.url[-6:] == 'search': #Search
            if request.httprequest.method == 'POST':
                search = post.get('search')
            search_domain.append(('name','like',search))
        elif partner:  # Detail
            return request.render(template['detail'], {'partner': partner, 'fields': fields, 'root': MODULE_BASE_PATH, 'db': request.db, 'mode': 'view'}) 
        
        return request.render(template['list'], {
            'partners': request.env['res.partner'].search(search_domain, order='name',limit=25), 
            'root': MODULE_BASE_PATH, 
            'db': request.db,
        })
        
#######################
        
        if request.httprequest.url[-9:] == 'set_login': #set login form
            if request.httprequest.method == 'POST':
                return werkzeug.utils.redirect(MODULE_BASE_PATH, 302)
            return request.render('website_crm_partner.set_login', {'partner': None, 'root': MODULE_BASE_PATH, 'db': request.db,})
        


    @http.route(['/mobile/security/<model("res.partner"):partner>', '/mobile/security'], type='http', auth="user", website=True)
    def mobile_security(self, partner=False, **post):
        partners = request.env['res.partner'].search([('type', '=', 'contact')], order='name',limit=25)
        return request.render('website_crm_partner.partner_list', {'partners': partners, 'root': MODULE_BASE_PATH, 'db': request.db,})

    #~ @http.route(['/allcategory/<model("product.category"):category>', ], type='http', auth="public", website=True)
    #~ def get_category(self, parent_id=1, **post):
        #~ cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #~ categories = request.env['product.category'].sudo().search([('parent_id', '=', parent_id)], order='id')
        #~ #categories.filtered("category.is_translated(lang)")
        #~ return request.render('website_product_category.page_allcategories', {'categories': categories})



