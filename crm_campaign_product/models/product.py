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


class res_partner(models.Model):
    _inherit = 'res.partner'
    seller_ids = fields.One2many(string='Suppliers', comodel_name='product.supplierinfo', inverse_name='partner_id')

    def _product_ids(self):
    	for product in self:
        	product.product_ids = [(6, 0, [s.product_tmpl_id.id for s in product.seller_ids])]
    product_ids = fields.Many2many(string='Products', comodel_name='product.template', compute='_product_ids')

class CRMCampaignProduct(models.Model):
    _name = 'crm.campaign.product'
    _order = 'sequence'

    sequence = fields.Integer()
    campaign_id = fields.Many2one(comodel_name="utm.campaign")
    product_id = fields.Many2one(comodel_name="product.template")
    name = fields.Char(related='product_id.name')
    default_code = fields.Char(related='product_id.default_code')
    type = fields.Selection(related='product_id.type')
    list_price = fields.Float(related='product_id.list_price')
    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')


class CrmTrackingCampaign(models.Model):
    _inherit = 'utm.campaign'

    product_ids = fields.Many2many(comodel_name='product.template', relation="crm_campaign_product",
                                   column1='campaign_id', column2='product_id', string='Products')
    campaign_product_ids = fields.One2many(comodel_name='crm.campaign.product', inverse_name='campaign_id',
                                           string='Products')

    def update_campaign_product_ids(self):
        self.env['crm.campaign.product'].search([('campaign_id', '=', self.id)]).sudo().unlink()
        for o in self.object_ids.sorted(lambda seq: seq.sequence):
            _logger.error(getattr(o, 'create_campaign_product', False))
            if getattr(o, 'create_campaign_product', False):
                o.create_campaign_product(self)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    campaign_ids = fields.Many2many(comodel_name='utm.campaign', relation="crm_campaign_product", column1='product_id',
                                    column2='campaign_id', string='Campaigns')


class CRMCampaignObject(models.Model):
    _inherit = 'crm.campaign.object'

    def _selection_target_model(self):
        target_model = super()._selection_target_model()
        return [*target_model, ('product.template', 'Product Template'), ('product.product', 'Product Variant')]

    object_id = fields.Reference(selection=_selection_target_model)

    def get_object_value(self):
        if self.object_id:
            print("---jjjj-")
            if self.object_id._name == 'product.template' or self.object_id._name == 'product.product':
                self.res_id = self.object_id.id
                self.name = self.object_id.name
                self.description = self.object_id.description_sale
                self.image = self.object_id.image
        return super(CRMCampaignObject, self).get_object_value()

    def create_campaign_product(self, campaign):
        if self.object_id._name == 'product.template':
            self.env['crm.campaign.product'].create({
                'campaign_id': campaign.id,
                'product_id': self.object_id.id,
                'sequence': len(campaign.product_ids) + 1,
            })
        elif self.object_id._name == 'product.product':
            self.env['crm.campaign.product'].create({
                'campaign_id': campaign.id,
                'product_id': self.object_id.product_tmpl_id.id,
                'sequence': len(campaign.product_ids) + 1,
            })
        elif self.object_id._name == 'product.public.category':
            for product in self.env['product.template'].search([('public_categ_ids', 'in', self.object_id.id)]):
                self.env['crm.campaign.product'].create({
                    'campaign_id': campaign.id,
                    'product_id': product.id,
                    'sequence': len(campaign.product_ids) + 1,
                })
        else:
            super(CRMCampaignObject, self).create_campaign_product(campaign)
