import os

from odoo import models, fields, api, _
from linkedin_api import Linkedin
from linkedin_api.settings import COOKIE_PATH
from linkedin_api.cookie_repository import CookieRepository

LINKEDIN_SESSION = False


class Company(models.Model):
    _inherit = "res.users"

    linkedin_email = fields.Char(string="LinkedIn Email")
    linkedin_password = fields.Char(string="LinkedIn Password")

    def _linkedin_client(self):
        api = Linkedin(self.linkedin_email, self.linkedin_password)
        return api

    def action_reset_cookie(self):
        cookie_path = "{}{}.jr".format(COOKIE_PATH, self.linkedin_email)
        try:
            if os.path.exists(cookie_path):
                os.remove(cookie_path)
                return self._cookie_operation_message(
                    title="Success", message="Cookie cleared Successfully"
                )
        except Exception as e:
            print(f"An error occurred while deleting the file {e}")
            return self._cookie_operation_message(
                title="Error", message=f"An error occurred while clearing cookie {e}"
            )

    def _cookie_operation_message(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'type': title.lower(),
                'message': message,
                'sticky': True,
            }
        }
