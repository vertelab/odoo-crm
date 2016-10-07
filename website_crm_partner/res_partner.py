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

from openerp.addons.website_mobile.website_mobile import mobile_crud
#~ import openerp.addons.website_mobile as mobile

import logging
_logger = logging.getLogger(__name__)

MOBILE_BASE_PATH = '/mobile/contact/'

class website_crm_partner(mobile_crud,http.Controller):
#~ class website_crm_partner(website_mobile.mobile_crud):
        
    def __init__(self):
        super(website_crm_partner,self).__init__()
        self.search_domain = [('type','=','contact')]
        self.model = 'res.partner'
        self.load_fields(['name','is_company','phone','email','type'])
        self.root = MOBILE_BASE_PATH
        self.title = _('Contact')


    @http.route([MOBILE_BASE_PATH,MOBILE_BASE_PATH+'<model("res.partner"):partner>'],type='http', auth="user", website=True)
    def partner_list(self, partner=None, search='',**post):
        return self.do_list(obj=partner)

    @http.route([MOBILE_BASE_PATH+'<string:search>/search',MOBILE_BASE_PATH+'search'],type='http', auth="user", website=True)
    def partner_search(self, search=None,**post):
        return self.do_list(search=search or post.get('search'))

    @http.route([MOBILE_BASE_PATH+'add'],type='http', auth="user", website=True)
    def partner_add(self, partner=None, search='',**post):
        return self.do_add(**post)

    @http.route([MOBILE_BASE_PATH+'<model("res.partner"):partner>/edit'],type='http', auth="user", website=True)
    def partner_edit(self, partner=None, search='',**post):
        return self.do_edit(obj=partner,**post)

    @http.route([MOBILE_BASE_PATH+'<model("res.partner"):partner>/delete'],type='http', auth="user", website=True)
    def partner_delete(self, partner=None, search='',**post):
        return self.do_delete(obj=partner)


class website_crm_user(mobile_crud,http.Controller):
#~ class website_crm_partner(website_mobile.mobile_crud):
       
    def __init__(self):
        super(website_crm_user,self).__init__()
        self.model = 'res.users'
        self.load_fields(['name','phone','login'])
        self.root = '/mobile/user'

    @http.route(['/mobile/user','/mobile/user/<model("res.users"):partner>'],type='http', auth="user", website=True)
    def partner_list(self, partner=None, search='',**post):
        return self.do_list(obj=partner)

    @http.route(['/mobile/user/add'],type='http', auth="user", website=True)
    def partner_add(self, partner=None, search='',**post):
        return self.do_add(**post)

    @http.route(['/mobile/user/<model("res.users"):partner>/edit'],type='http', auth="user", website=True)
    def partner_edit(self, partner=None, search='',**post):
        return self.do_edit(obj=partner,**post)


