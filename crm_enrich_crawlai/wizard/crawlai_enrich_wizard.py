# -*- coding: utf-8 -*-
"""Wizard: choose which enrichment steps to run on a crm.lead."""

from odoo import models, fields, api, _


class CrawlaiEnrichWizard(models.TransientModel):
    _name = "crm.crawlai.enrich.wizard"
    _description = "CrawlAI Lead Enrichment Wizard"

    lead_id = fields.Many2one(
        "crm.lead", string="Lead", required=True, ondelete="cascade")
    lead_name = fields.Char(related="lead_id.name", readonly=True)
    company_name = fields.Char(related="lead_id.partner_name", readonly=True)
    # company_registry lives on res.partner, not crm.lead.
    company_registry = fields.Char(
        related="lead_id.partner_id.company_registry", readonly=True)
    website = fields.Char(related="lead_id.website", readonly=True)

    step_website = fields.Boolean(
        "Find website", default=True,
        help="Search by company name / company registry number to find the "
             "company website and store it on the lead.")
    step_description = fields.Boolean(
        "Crawl site: description + contact person", default=True,
        help="Crawl the company website, fetch a company description, extend "
             "the lead description/note with it, and find a contact person.")
    step_linkedin = fields.Boolean(
        "Check company LinkedIn", default=True,
        help="Check the company's LinkedIn presence.")

    def action_run(self):
        self.ensure_one()
        steps = []
        if self.step_website:
            steps.append("website")
        if self.step_description:
            steps.append("description")
        if self.step_linkedin:
            steps.append("linkedin")
        if not steps:
            steps = ["website", "description", "linkedin"]
        return self.lead_id.action_crawlai_enrich(steps=steps)
