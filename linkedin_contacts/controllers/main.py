# -*- coding: utf-8 -*-

import collections
import babel.dates
import re
import json
import requests
import werkzeug
from werkzeug.datastructures import OrderedMultiDict
from werkzeug.exceptions import NotFound
from odoo.http import request

from ast import literal_eval
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import fields, http, _


class LinkedInController(http.Controller):
    _callback_url = '/api/linkedin/auth/callback'

    @http.route('/api/linkedin/auth/callback', type='http', methods=['GET', 'POST'], auth="user", csrf=False)
    def linkedin_auth_callback(self, **kwargs):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        linkedin_client_id = request.env['ir.config_parameter'].sudo().get_param('linkedin_client_id')
        linkedin_client_secret = request.env['ir.config_parameter'].sudo().get_param('linkedin_client_secret')

        data = {
            'grant_type': 'authorization_code',
            'code': kwargs.get('code'),
            'client_id': linkedin_client_id,
            'client_secret': linkedin_client_secret,
            'redirect_uri': f"{base_url}/api/linkedin/auth/callback",
        }
        access_token_req = requests.post('https://www.linkedin.com/oauth/v2/accessToken', data=data)
        user_id = request.env.user

        if access_token_req.status_code == 200:
            request.env.user.sudo().write({'access_token': access_token_req.json()['access_token']})

        menu_id = request.env.ref('base.menu_administration').id
        action_id = request.env.ref('base.action_res_users').id
        return werkzeug.utils.redirect(f"/web#id={user_id.id}&action={action_id}&model=res.users&view_type=form&cids=&menu_id={menu_id}")
