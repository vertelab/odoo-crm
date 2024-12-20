# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2017- Vertel AB (<http://vertel.se>).
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
from odoo import models, fields, api, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class CrmTrackingCampaign(models.Model):
    _name = 'utm.campaign'
    _inherit = ['utm.campaign', 'mail.thread']

    color = fields.Integer('Color Index')
    date_start = fields.Date(string='Start Date', )
    date_stop = fields.Date(string='Start Stop', )
    image = fields.Binary(string='Image')
    description = fields.Text(string='Description', translate=True)
    campaign_id = fields.Many2one(comodel_name='utm.campaign', string='Campaign')

    name = fields.Char(string='Name')
    sequence = fields.Integer()
    object_id = fields.Reference(selection=[], string='Object')

    object_ids = fields.One2many(comodel_name='crm.campaign.object', inverse_name='campaign_id', string='Objects')
    kampanjer_ = fields.Char(string='Kampanjer')
    
    def _object_names(self):
        for obj in self:
            obj.object_names = ', '.join(obj.object_ids.mapped('name'))

    object_names = fields.Char(compute='_object_names')

    def _object_count(self):
        for obj in self:
            self.object_count = len(self.object_ids)

    object_count = fields.Integer(compute='_object_count')

    @api.model
    def get_campaigns(self):
        return self.env['utm.campaign'].search([
            ('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today())
        ])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=False, default='draft',
        copy=False,
        help=" * The 'Draft' status is used during planning.\n"
             " * The 'Open' status is used when the campaign are running.\n"
             " * The 'Closed' status is when the campaign is over.\n"
             " * The 'Cancelled' status is used when the campaign is stopped.")


class CrmCampaignObject(models.Model):
    _name = 'crm.campaign.object'
    _description = "CRM Campaign Object"

    _order = 'campaign_id,sequence,name'

    def _selection_target_model(self):
        return []

    name = fields.Char(string='Name')
    description = fields.Text(string='Description', translate=True)
    website_short_description = fields.Text(string='Website Short Description', translate=True)
    image = fields.Binary(string='Image')
    sequence = fields.Integer()
    color = fields.Integer('Color Index')
    campaign_id = fields.Many2one(comodel_name='utm.campaign', string='Campaign')
    object_id = fields.Reference(selection=_selection_target_model, string='Record Reference')

    @api.onchange('object_id')
    def get_object_value(self):
        pass

    @api.model
    def create_campaign_product(self, campaign):
        pass


class CampaignOverview(models.TransientModel):
    _name = 'campaign.overview'

    date = fields.Date(string='Date', required=True)

    @api.model
    def overview(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/?campaign_date=%s' % self.date,
            'target': 'new',
            'res_id': self.id,
        }
