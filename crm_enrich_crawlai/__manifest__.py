# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2026- Vertel AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "CRM: Enrich with CrawlAI",
    "version": "18.0.1.1.0",
    "summary": "AI-driven lead enrichment via a pi-python agent (website, "
               "description, contact person, LinkedIn)",
    "description": """
CRM: Enrich with CrawlAI
========================

Extends the AI coworker "Allman assistent" with a new ai.agent of
pi-python type and an ai.tool (crawlai) that is invoked from a button
on crm.lead.

The agent performs three steps:

a) If the lead has no website, search by company name / company registry
   number to find the company website and store it on the record.
b) Crawl the company website, fetch a company description, extend the
   lead description / note with it, and find a contact person.
c) Check the company's LinkedIn presence.

Design notes
------------
* The tool is executed by the pi-agent (executor="nats") so the heavy
  web work runs outside the Odoo worker. The agent itself is
  runtime="external" (a separate process).
* Every write to the lead goes through HITL: the tool returns a proposal
  and the write happens only after approval (risk_level="write").
* All three steps are individually selectable from the button.
""",
    "sequence": "999",
    "author": "Vertel AB",
    "category": "CRM",
    "website": "https://vertel.se/apps/odoo-crm/crm_enrich_crawlai",
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "maintainer": "Vertel AB",
    "repository": "https://github.com/vertelab/odoo-crm",
    "depends": [
        "crm",
        "ai_agent_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/crawlai_tool.xml",
        "data/crawlai_skill.xml",
        "data/crawlai_agent.xml",
        "views/crm_lead_views.xml",
        "wizard/crawlai_enrich_wizard_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
