# Copyright (C) 2017-2025 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from babel.dates import format_date

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class CrmTrackingCampaign(models.Model):
    _inherit = 'crm.tracking.campaign'

    phase_ids = fields.One2many(
        comodel_name='crm.tracking.phase',
        inverse_name='campaign_id',
        string='Phases',
    )
    country_ids = fields.Many2many(
        comodel_name='res.country', string='Country')

    def get_phase(self, date, is_reseller):
        self.ensure_one()
        return self.phase_ids.filtered(
            lambda p: (p.end_date >= date or not p.end_date)
            and p.reseller_pricelist == is_reseller
        )

    def get_current_phase(self, is_reseller):
        self.ensure_one()
        return self.get_phase(fields.Date.today(), is_reseller)

    def is_current(self, date, is_reseller):
        self.ensure_one()
        if is_reseller:
            if not self.country_ids or (
                self.env.user.partner_id.commercial_partner_id.country_id
                in self.country_ids
            ):
                phases = self.phase_ids.filtered(
                    lambda p: p.start_date <= date
                    and (p.end_date >= date if p.end_date else True)
                    and p.reseller_pricelist == is_reseller
                )
                return bool(phases)
            return False
        if self.date_stop:
            return self.date_start <= date <= self.date_stop
        return self.date_start <= date

    def check_product(self, prod_id):
        self.ensure_one()
        product = self.env['product.product'].browse(prod_id)
        template = product.product_tmpl_id
        return template.id in self.product_ids.mapped('id')

    def get_period(self, is_reseller):
        self.ensure_one()

        def pretty_date(d):
            return format_date(
                d, 'd MMM',
                locale=self.env.context.get('lang', 'sv_SE')
            ).replace('.', '')

        phase = self.get_phase(fields.Date.today(), is_reseller)
        if not phase:
            return ''
        date_start = phase.start_date
        date_stop = phase.end_date
        if not date_stop:
            return _('until further notice')
        if date_start:
            return '%s - %s' % (pretty_date(date_start), pretty_date(date_stop))
        return '- %s' % pretty_date(date_stop)

    @api.model
    def get_campaigns(self):
        campaigns = super().get_campaigns()
        country = self.env.user.partner_id.commercial_partner_id.country_id
        return campaigns.filtered(
            lambda c: not c.country_ids or country in c.country_ids
        )


class CrmTrackingPhase(models.Model):
    _name = "crm.tracking.phase"
    _description = "CRM Tracking Phase"
    _order = 'campaign_id, sequence, name'

    campaign_id = fields.Many2one(
        comodel_name='crm.tracking.campaign', string='Campaign')
    name = fields.Char(string='Name')
    phase_type = fields.Many2one(
        comodel_name="crm.tracking.phase.type", string="Type")
    sequence = fields.Integer()

    start_date = fields.Date(compute='_compute_dates', store=True)
    end_date = fields.Date(compute='_compute_dates', store=True)

    reseller_pricelist = fields.Boolean(
        string="Reseller",
        help="Use this pricelist for resellers")
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist", string="Pricelist")

    @api.depends('phase_type.start_days', 'phase_type.start_days_from_start',
                 'phase_type.end_days', 'phase_type.end_days_from_start',
                 'campaign_id.date_start', 'campaign_id.date_stop')
    def _compute_dates(self):
        for rec in self:
            pt = rec.phase_type
            campaign = rec.campaign_id
            if not pt or not campaign:
                rec.start_date = False
                rec.end_date = False
                continue

            base_start = campaign.date_start if pt.start_days_from_start else campaign.date_stop
            if base_start and pt.start_days is not None:
                rec.start_date = base_start + timedelta(days=pt.start_days)
            else:
                rec.start_date = False

            base_end = campaign.date_start if pt.end_days_from_start else campaign.date_stop
            if base_end and pt.end_days is not None:
                rec.end_date = base_end + timedelta(days=pt.end_days)
            else:
                rec.end_date = campaign.date_stop or False

    def get_pricelist(self, date, prod_id, is_reseller):
        for phase in self:
            if (date >= phase.start_date and date <= phase.end_date
                and phase.campaign_id.check_product(prod_id)
                and phase.pricelist_id
                and phase.reseller_pricelist == is_reseller):
                return phase.pricelist_id
        return self.env['product.pricelist'].browse()

    def get_phase(self, date, is_reseller):
        self.ensure_one()
        if (date >= self.start_date and date <= self.end_date
                and is_reseller == self.reseller_pricelist):
            return self


class CrmTrackingPhaseType(models.Model):
    _name = "crm.tracking.phase.type"
    _description = "CRM Tracking Phase Type"

    name = fields.Char(string='Name', required=True)
    start_days = fields.Integer()
    start_days_from_start = fields.Boolean(
        help="Checked: days counted from campaign start, otherwise from end")
    end_days = fields.Integer()
    end_days_from_start = fields.Boolean(
        help="Checked: days counted from campaign start, otherwise from end")

    @api.onchange('end_days')
    def _onchange_end_days(self):
        if (self.start_days_from_start and self.end_days_from_start
                and self.end_days and self.start_days
                and self.end_days < self.start_days):
            raise UserError(_(
                'End days must be greater than or equal to start days'))


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def price_get(self, prod_id, qty, partner=None):
        self.ensure_one()
        if isinstance(partner, models.BaseModel):
            partner = partner.id
        if not partner:
            partner = self.env.ref('base.public_partner').id

        partner_obj = self.env['res.partner'].sudo().browse(partner)
        is_reseller = (
            self.env.ref('base.public_user').property_product_pricelist
            != partner_obj.property_product_pricelist
        )

        price = super().price_get(prod_id, qty, partner=partner_obj)[self.id]
        campaign_price = float('inf')
        date = self.env.context.get('date') or fields.Date.today()

        campaigns = self.env['crm.tracking.campaign'].search([
            ('state', '=', 'open')
        ])
        for phase in campaigns.mapped('phase_ids'):
            pl = phase.get_pricelist(date, prod_id, is_reseller)
            if pl:
                try:
                    cp = pl.price_get(prod_id, qty, partner=partner_obj)[pl.id]
                    campaign_price = min(campaign_price, cp)
                except Exception:
                    pass

        return {self.id: campaign_price if campaign_price < price else price}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def get_campaign_products(self, for_reseller=False):
        products = self.env['product.template'].browse()
        domain = [('state', '=', 'open')]
        if not for_reseller:
            domain.append(('website_published', '=', True))
        campaigns = self.env['crm.tracking.campaign'].search(domain)
        for campaign in campaigns:
            if campaign.is_current(fields.Date.today(), for_reseller):
                products |= campaign.product_ids
        return products

    def get_campaign_image(self, for_reseller=False):
        self.ensure_one()
        domain = [('state', '=', 'open')]
        if not for_reseller:
            domain.append(('website_published', '=', True))
        campaigns = self.env['crm.tracking.campaign'].search(domain).filtered(
            lambda c: self.id in c.product_ids.mapped('id'))
        for campaign in campaigns:
            phase = campaign.get_phase(fields.Date.today(), for_reseller)
            if phase:
                return campaign.image
        return None

    def get_campaign_date(self, for_reseller=False):
        self.ensure_one()
        date = None
        if for_reseller:
            campaigns = self.env['crm.tracking.campaign'].search([
                ('state', '=', 'open')
            ]).filtered(lambda c: self.id in c.product_ids.mapped('id'))
            for campaign in campaigns:
                phase = campaign.get_phase(fields.Date.today(), for_reseller)
                if phase and phase.end_date and (
                    not date or phase.end_date > date):
                    date = phase.end_date
        else:
            campaigns = self.env['crm.tracking.campaign'].search([
                ('state', '=', 'open'),
                ('website_published', '=', True),
            ]).filtered(lambda c: self.id in c.product_ids.mapped('id'))
            for campaign in campaigns:
                if campaign.date_stop and (not date or campaign.date_stop > date):
                    date = campaign.date_stop
        return date


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_offer_product_consumer = fields.Boolean(
        compute='_compute_is_offer_product')
    is_offer_product_reseller = fields.Boolean(
        compute='_compute_is_offer_product')

    def _compute_is_offer_product(self):
        for rec in self:
            rec.is_offer_product_consumer = bool(
                rec._get_campaign_products(for_reseller=False) & rec)
            rec.is_offer_product_reseller = bool(
                rec._get_campaign_products(for_reseller=True) & rec)

    @api.model
    def _get_campaign_products(self, for_reseller=False):
        domain = [('state', '=', 'open')]
        if not for_reseller:
            domain.append(('website_published', '=', True))
        campaigns = self.env['crm.tracking.campaign'].search(domain)
        products = self.env['product.product'].browse()
        for campaign in campaigns:
            if campaign.is_current(fields.Date.today(), for_reseller):
                products |= self.env['product.product'].search([
                    ('product_tmpl_id', 'in', campaign.product_ids.mapped('id'))
                ])
        return products

    def get_campaign_image(self, for_reseller=False):
        return self.product_tmpl_id.get_campaign_image(for_reseller=for_reseller)

    def get_campaign_date(self, for_reseller=False):
        return self.product_tmpl_id.get_campaign_date(for_reseller=for_reseller)
