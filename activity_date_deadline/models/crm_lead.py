from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'crm.lead'
  
    active_date_deadline = fields.Date().stored = True
    #linkedin_client_id = fields.Char(string='Client ID')
    #linkedin_client_secret = fields.Char(string='Client Secret')
