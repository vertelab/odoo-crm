from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)

    linkedin_client_id = fields.Char(
        string='Client ID',
        config_parameter='linkedin_client_id',
        readonly=False
    )
    linkedin_client_secret = fields.Char(
        string='Client Secret',
        config_parameter='linkedin_client_secret',
        readonly=False
    )
