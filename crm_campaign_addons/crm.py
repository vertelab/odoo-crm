# Copyright (C) 2017-2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class CrmTrackingCampaign(models.Model):
    _name = 'crm.tracking.campaign'
    _inherit = ['crm.tracking.campaign', 'mail.thread']

    color = fields.Integer('Color Index')
    date_start = fields.Date(string='Start Date', tracking=True)
    date_stop = fields.Date(string='End Date', tracking=True)
    image = fields.Binary(string='Image')

    object_ids = fields.One2many(
        comodel_name='crm.campaign.object',
        inverse_name='campaign_id',
        string='Objects',
    )
    object_names = fields.Char(compute='_compute_object_names')
    object_count = fields.Integer(compute='_compute_object_count')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, default='draft',
       tracking=True, copy=False,
       help=" * The 'Draft' status is used during planning.\n"
            " * The 'Open' status is used when the campaign is running.\n"
            " * The 'Closed' status is when the campaign is over.\n"
            " * The 'Cancelled' status is used when the campaign is stopped.")

    @api.depends('object_ids.name')
    def _compute_object_names(self):
        for rec in self:
            rec.object_names = ', '.join(rec.object_ids.mapped('name'))

    @api.depends('object_ids')
    def _compute_object_count(self):
        for rec in self:
            rec.object_count = len(rec.object_ids)

    @api.model
    def get_campaigns(self):
        return self.search([
            ('date_start', '<', fields.Date.today()),
            ('date_stop', '>', fields.Date.today()),
        ])


class CrmCampaignObject(models.Model):
    _name = 'crm.campaign.object'
    _description = 'CRM Campaign Object'
    _order = 'campaign_id, sequence, name'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description', translate=True)
    image = fields.Binary(string='Image')
    sequence = fields.Integer()
    color = fields.Integer('Color Index')
    campaign_id = fields.Many2one(
        comodel_name='crm.tracking.campaign', string='Campaign')
    object_id = fields.Reference(
        selection='_selection_object_id', string='Object')

    @api.model
    def _selection_object_id(self):
        return []

    @api.onchange('object_id')
    def _onchange_object_id(self):
        pass

    def create_campaign_product(self, campaign):
        pass


class CampaignOverview(models.TransientModel):
    _name = 'campaign.overview'
    _description = 'Campaign Overview'

    date = fields.Date(string='Date', required=True)

    def overview(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/?campaign_date=%s' % self.date,
            'target': 'new',
        }
