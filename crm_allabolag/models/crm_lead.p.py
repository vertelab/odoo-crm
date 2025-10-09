from odoo import models, fields
from .constants import (
    SNI_MAIN, MINING_CORPORATE_FORM,
    MINING_KOMMUN, MINING_INDUSTRY_XV, MINING_LAN
)


class CRMLead(models.Model):
    _inherit = "crm.lead"

    mining_id = fields.Many2one(comodel_name="crm.allabolag.mining")

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

    allabolag_json_data = fields.Json()
