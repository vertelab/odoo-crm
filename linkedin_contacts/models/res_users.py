from odoo import models, fields, api
import requests
import uuid
from werkzeug import urls
from odoo.addons.linkedin_contacts.controllers.main import LinkedInController


class Users(models.Model):
    _inherit = 'res.users'

    access_token = fields.Char(string="Access Token")

    def authorize_linkedin(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        linkedin_client_id = self.env['ir.config_parameter'].get_param('linkedin_client_id')
        authorization_url = 'https://www.linkedin.com/oauth/v2/authorization'
        callback_url = urls.url_join(base_url, LinkedInController._callback_url)

        linked_request_url = (f"{authorization_url}?response_type=code&client_id={linkedin_client_id}"
                              f"&redirect_uri={callback_url}&state={uuid.uuid4()}&scope=openid,profile,email")

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': linked_request_url,
        }

    def get_linkedin_connection(self):
        headers = {
            'Authorization': f"Bearer {self.access_token}"
        }
        min_profile = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        print(min_profile.text)
