# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2017- Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
import werkzeug
import datetime
import logging

_logger = logging.getLogger(__name__)


class CRMTrackingCampaign(models.Model):
    _inherit = 'utm.campaign'

    website_description = fields.Html(string='Website Description')
    website_published = fields.Boolean(string='Available in the website', default=False, copy=False)
    website_url = fields.Char(string='Website url', compute='_website_url')

    def _website_url(self):
        self.website_url = '/campaign/%s' % self.id

    def get_campaigns(self):
        return super(CRMTrackingCampaign, self).get_campaigns().filtered(lambda c: c.website_published)


class CRMCampaignObject(models.Model):
    _inherit = 'crm.campaign.object'

    def _selection_target_model(self):
        target_model = super()._selection_target_model()
        return [*target_model, ('product.public.category', 'Product Category')]

    object_id = fields.Reference(selection=_selection_target_model)

    def get_object_value(self):
        for objects in self.object_id:
            if objects:
                if objects._name == 'product.public.category':
                    self.res_id = objects.id
                    self.name = objects.name
                    self.description = objects.description
                    self.image = objects.image
        return super(CRMCampaignObject, self).get_object_value()
    #


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    description = fields.Text(string='Description')
    mobile_icon = fields.Char(string='Mobile Icon', help='This icon will display on smaller devices')
