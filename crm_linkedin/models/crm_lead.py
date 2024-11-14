# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class Lead(models.Model):
    _inherit = 'crm.lead'

    linkedin_lead_mining_request_id = fields.Many2one(
        'crm.lead.linkedin.mining.request', string='Lead Mining Request', index='btree_not_null'
    )
    linkedin_url = fields.Char(string="LinkedIn URL")
    urn_id = fields.Char(string="LinkedIn URN ID")

    def _merge_get_fields(self):
        return super(Lead, self)._merge_get_fields() + ['linkedin_lead_mining_request_id']

    def action_generate_linkedin_leads(self):
        return {
            "name": _("Need help reaching your target?"),
            "type": "ir.actions.act_window",
            "res_model": "crm.lead.linkedin.mining.request",
            "target": "new",
            "views": [[False, "form"]],
            "context": {"is_modal": True},
        }
