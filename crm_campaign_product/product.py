# Copyright (C) 2017-2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class CrmCampaignProduct(models.Model):
    _name = 'crm.campaign.product'
    _description = 'CRM Campaign Product'
    _order = 'sequence'

    sequence = fields.Integer()
    campaign_id = fields.Many2one(comodel_name="crm.tracking.campaign")
    product_id = fields.Many2one(comodel_name="product.product")
    name = fields.Char(related='product_id.name')
    default_code = fields.Char(related='product_id.default_code')
    type = fields.Selection(related='product_id.type')
    list_price = fields.Float(related='product_id.list_price')
    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')


class CrmTrackingCampaign(models.Model):
    _inherit = 'crm.tracking.campaign'

    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="crm_campaign_product_rel",
        column1='campaign_id', column2='product_id',
        string='Products',
    )
    campaign_product_ids = fields.One2many(
        comodel_name='crm.campaign.product',
        inverse_name='campaign_id',
        string='Campaign Products',
    )

    def update_campaign_product_ids(self):
        for rec in self:
            self.env['crm.campaign.product'].search([
                ('campaign_id', '=', rec.id)
            ]).unlink()
            for o in rec.object_ids.sorted(lambda o: o.sequence):
                if hasattr(o, 'create_campaign_product') and callable(o.create_campaign_product):
                    o.create_campaign_product(rec)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    campaign_ids = fields.Many2many(
        comodel_name='crm.tracking.campaign',
        relation="crm_campaign_product_rel",
        column1='product_id', column2='campaign_id',
        string='Campaigns',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    campaign_ids = fields.Many2many(
        comodel_name='crm.tracking.campaign',
        relation="crm_campaign_product_rel",
        column1='product_id', column2='campaign_id',
        string='Campaigns',
    )


class CrmCampaignObject(models.Model):
    _inherit = 'crm.campaign.object'

    @api.model
    def _selection_object_id(self):
        return super()._selection_object_id() + [
            ('product.template', 'Product Template'),
            ('product.product', 'Product Variant'),
            ('product.public.category', 'Product Category'),
        ]

    @api.onchange('object_id')
    def _onchange_object_id(self):
        res = super()._onchange_object_id()
        if self.object_id:
            if self.object_id._name in ('product.template', 'product.product'):
                self.name = self.object_id.name
                self.description = self.object_id.description_sale
                self.image = self.object_id.image
        return res

    def _create_campaign_variant(self, campaign, variant):
        self.env['crm.campaign.product'].create({
            'campaign_id': campaign.id,
            'product_id': variant.id,
            'sequence': len(campaign.product_ids) + 1,
        })

    def create_campaign_product(self, campaign):
        for rec in self:
            if not rec.object_id:
                continue
            obj = rec.object_id
            if obj._name == 'product.product':
                rec._create_campaign_variant(campaign, obj)
            elif obj._name == 'product.template':
                for variant in obj.product_variant_ids:
                    rec._create_campaign_variant(campaign, variant)
            elif obj._name == 'product.public.category':
                templates = self.env['product.template'].search([
                    ('public_categ_ids', 'in', obj.id)
                ])
                for tmpl in templates:
                    for variant in tmpl.product_variant_ids:
                        rec._create_campaign_variant(campaign, variant)
            else:
                super(CrmCampaignObject, rec).create_campaign_product(campaign)
