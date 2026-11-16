from odoo import models, fields
from .constants import (
    SNI_MAIN, MINING_CORPORATE_FORM,
    MINING_KOMMUN, MINING_INDUSTRY_XV, MINING_LAN
)


class CRMLead(models.Model):
    # The allabolag mixin supplies summary_* and kpi_* — the fields the form
    # view shows and the provider writes. Without it the view fails to load.
    _name = 'crm.lead'
    _inherit = ["crm.lead", "res.partner.allabolag.mixin"]

    mining_id = fields.Many2one(comodel_name="crm.allabolag.mining")

    # Declared here rather than in crm_allabolag.py: these are the fields the
    # provider writes and the view shows, and they belong next to the mining
    # fields they sit beside.
    company_registry = fields.Char(string='Company Registry', size=64, trim=True)
    vat = fields.Char(string='VAT', size=64, trim=True)
    linkTo = fields.Char(string='Link', help="Link to Allabolag")

    mining_corporate_form = fields.Selection(
        selection=MINING_CORPORATE_FORM,
        string="Company form",
        related="mining_id.corporate_form",
        readonly=True,
        store=True,
    )
    mining_industry = fields.Selection(
        selection=SNI_MAIN,
        string="industry",
        related="mining_id.industry",
        readonly=True,
        store=True,
    )
    mining_industry_xv = fields.Selection(
        selection=MINING_INDUSTRY_XV,
        string="industry",
        related="mining_id.industry_xv",
        readonly=True,
        store=True,
    )
    mining_lan = fields.Selection(
        selection=MINING_LAN,
        string="County",
        related="mining_id.lan",
        readonly=True,
        store=True,
    )
    mining_kommun = fields.Selection(
        selection=MINING_KOMMUN,
        string="Municipality",
        related="mining_id.kommun",
        readonly=True,
        store=True,
    )

    allabolag_json_data = fields.Text()
