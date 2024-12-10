from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        campaign = self.env['utm.campaign'].get_campaigns()
        if len(campaign):
            if not vals.get('campaign_id'):
                vals['campaign_id'] = campaign[0].id
        return super(SaleOrder, self).create(vals)
