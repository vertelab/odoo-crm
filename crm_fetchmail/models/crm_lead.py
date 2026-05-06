from odoo import models, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_force_fetch_mail(self):
        # Hämtar alla konfigurerade inkommande e-postservrar
        mail_servers = self.env['fetchmail.server'].search([('state', '=', 'done')])
        for server in mail_servers:
            server.sudo().fetch_mail()
        return True
