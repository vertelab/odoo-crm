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
import logging

_logger = logging.getLogger(__name__)


class CRMCampaignObject(models.Model):
    _inherit = 'crm.campaign.object'

    def _selection_target_model(self):
        target_model = super()._selection_target_model()
        return [*target_model, ('res.partner', 'Supplier')]

    object_id = fields.Reference(selection=_selection_target_model)

    def get_object_value(self):
        print("----")
        for objects in self.object_id:
            if objects and objects._name == 'res.partner':
                # objects = my_object.name
                self.description = objects.comment
                self.image = objects.image
        return super(CRMCampaignObject, self).get_object_value()

    def create_campaign_product(self, campaign):
        for objects in self.object_id:
            if objects._name == 'res.partner':
                for product in self.env['product.template'].search([('seller_ids.partner_id', '=', objects.id)]):
                    self.env['crm.campaign.product'].create({
                        'campaign_id': campaign.id,
                        'product_id': product.id,
                        'sequence': len(campaign.product_ids) + 1,
                    })
            else:
                super(CRMCampaignObject, self).create_campaign_product(campaign)
