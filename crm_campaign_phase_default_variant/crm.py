# Copyright (C) 2017-2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_default_variant(self):
        """Return the first campaign variant if available, else default."""
        self.ensure_one()
        campaign_variants = self.product_variant_ids & (
            self.env['product.product'].browse()._get_campaign_products(
                for_reseller=self.env.user.partner_id.commercial_partner_id
                .property_product_pricelist.for_reseller
            )
        )
        if campaign_variants:
            return campaign_variants[0]
        return super().get_default_variant()
