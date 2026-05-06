import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_force_fetch_mail(self):
        mail_servers = self.env['fetchmail.server'].search([('state', '=', 'done')])
        for server in mail_servers:
            server.sudo().fetch_mail()
        return True
