from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    linkedin_client_id = fields.Char(string='Client ID')
    linkedin_client_secret = fields.Char(string='Client Secret')
