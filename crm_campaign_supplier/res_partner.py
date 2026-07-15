# Copyright (C) 2017-2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class CrmCampaignObject(models.Model):
    _inherit = 'crm.campaign.object'

    @api.model
    def _selection_object_id(self):
        return super()._selection_object_id() + [
            ('res.partner', 'Supplier'),
        ]

    @api.onchange('object_id')
    def _onchange_object_id(self):
        res = super()._onchange_object_id()
        if self.object_id and self.object_id._name == 'res.partner':
            self.name = self.object_id.name
            self.description = self.object_id.comment
            self.image = self.object_id.image
        return res

    def create_campaign_product(self, campaign):
        for rec in self:
            if rec.object_id and rec.object_id._name == 'res.partner':
                templates = self.env['product.template'].search([
                    ('seller_ids.name', '=', rec.object_id.id)
                ])
                for tmpl in templates:
                    self.env['crm.campaign.product'].create({
                        'campaign_id': campaign.id,
                        'product_id': tmpl.product_variant_ids[:1].id,
                        'sequence': len(campaign.product_ids) + 1,
                    })
            else:
                super(CrmCampaignObject, rec).create_campaign_product(campaign)
