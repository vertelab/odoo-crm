# -*- coding: utf-8 -*-
"""CRM lead enrichment via the crawlai pi-agent tool.

The button on crm.lead builds a prompt from the record and runs the
"Lead Enricher" agent (pi-python, runtime=external) through the AI
coworker "Allman assistent". The heavy web work is delegated to the
pi-agent via the crawlai tool (executor="nats").

Nothing is written to the lead by this module directly — the pi-agent
proposes values and every write is gated by HITL (risk_level="write" on
the tool). The helper methods below only *read* the lead to build the
prompt and to expose the current state to the agent.
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# The three enrichment steps, selectable from the button.
ENRICH_STEPS = [
    ("website", "Find website (name / company registry)"),
    ("description", "Crawl site: description + contact person"),
    ("linkedin", "Check company LinkedIn"),
]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # ── Stored enrichment result (audit trail) ──────────────────────
    crawlai_last_run = fields.Datetime(
        "CrawlAI Last Run", readonly=True, copy=False,
        help="When the CrawlAI enrichment was last run for this lead.")
    crawlai_session_id = fields.Many2one(
        "ai.coworker.session", "CrawlAI Session", readonly=True, copy=False,
        help="The AI session produced by the last enrichment run.")
    crawlai_status = fields.Selection(
        [
            ("draft", "Not run"),
            ("running", "Running"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        string="CrawlAI Status", default="draft", readonly=True, copy=False,
        help="Status of the last CrawlAI enrichment run.")
    crawlai_result = fields.Text(
        "CrawlAI Result", readonly=True, copy=False,
        help="The agent's report from the last enrichment run.")
    linkedin = fields.Char(
        "LinkedIn", copy=False,
        help="Company LinkedIn page, discovered by the CrawlAI agent.")

    # ── Agent / coworker lookup ─────────────────────────────────────

    def _crawlai_agent(self):
        """Return the Lead Enricher agent, or raise a clear error."""
        agent = self.env.ref(
            "crm_enrich_crawlai.agent_crawlai_lead_enricher",
            raise_if_not_found=False)
        if not agent:
            agent = self.env["ai.agent"].search(
                [("name", "=", "CrawlAI Lead Enricher")], limit=1)
        if not agent:
            raise UserError(_(
                "The CrawlAI Lead Enricher agent is missing. "
                "Re-install or update the crm_enrich_crawlai module."))
        return agent

    def _crawlai_coworker(self):
        """Return the coworker that should own the session.

        Preference order: the agent's own coworker (if it is attached to
        exactly one), then the default "Allman assistent" coworker.
        """
        self.ensure_one()
        agent = self._crawlai_agent()
        link = self.env["ai.coworker.agent"].search(
            [("agent_id", "=", agent.id)], limit=1)
        if link and link.coworker_id:
            return link.coworker_id
        coworker = self.env.ref(
            "ai_agent_core.coworker_default_assistent",
            raise_if_not_found=False)
        if not coworker:
            coworker = self.env["ai.coworker"].search(
                [("is_default", "=", True)], limit=1)
        if not coworker:
            raise UserError(_(
                "No AI coworker found to run the CrawlAI enrichment. "
                "Attach the agent to a coworker first."))
        return coworker

    # ── Prompt construction ─────────────────────────────────────────

    def _crawlai_build_prompt(self, steps):
        """Build the agent prompt from the lead and the selected steps."""
        self.ensure_one()
        company = self.partner_name or self.name or ""
        lines = [
            "Enrich this CRM lead using the crawlai_lead_enricher tool.",
            "",
            "Lead: %s (id %s)" % (company, self.id),
            "Contact name: %s" % (self.contact_name or "(none)"),
            "Company registry (org.nr): %s" % (
                self.partner_id.company_registry or "(none)"),
            "Website: %s" % (self.website or "(none)"),
            "Email: %s" % (self.email_from or "(none)"),
            "Phone: %s" % (self.phone or "(none)"),
            "LinkedIn: %s" % (self.linkedin or "(none)"),
            "",
            "Steps to perform:",
        ]
        labels = dict(ENRICH_STEPS)
        for step in steps:
            lines.append("- %s: %s" % (step, labels.get(step, step)))
        lines += [
            "",
            "Use the tool with lead_id=%s and domains=%s." % (
                self.id, steps),
            "Present every proposed value with a short motivation and wait "
            "for approval before anything is written to the lead.",
        ]
        return "\n".join(lines)

    # ── Button actions ──────────────────────────────────────────────

    def action_crawlai_enrich(self, steps=None):
        """Run the CrawlAI enrichment agent for this lead.

        Called from the form button (all three steps) or from the wizard
        (individual steps). Returns an ir.actions.client notification so
        the user gets feedback without a full reload.
        """
        self.ensure_one()
        if not (self.partner_name or self.name):
            raise UserError(_(
                "The lead needs a company name before it can be enriched."))

        steps = steps or [s[0] for s in ENRICH_STEPS]
        agent = self._crawlai_agent()
        coworker = self._crawlai_coworker()
        prompt = self._crawlai_build_prompt(steps)

        self.write({
            "crawlai_status": "running",
            "crawlai_last_run": fields.Datetime.now(),
        })

        try:
            result = coworker.run(
                prompt,
                force_agent=agent,
                record=self,
            )
        except Exception as e:  # noqa: BLE001 — surfaced to the user
            _logger.exception("CrawlAI enrichment failed for lead %s", self.id)
            self.write({
                "crawlai_status": "error",
                "crawlai_result": str(e),
            })
            raise UserError(_("CrawlAI enrichment failed: %s") % e)

        session = self.env["ai.coworker.session"].search(
            [("coworker_id", "=", coworker.id)],
            order="create_date desc", limit=1)
        self.write({
            "crawlai_status": "done",
            "crawlai_result": result,
            "crawlai_session_id": session.id if session else False,
        })
        self.message_post(
            body=_("CrawlAI enrichment completed. %s") % (result or ""),
            message_type="notification",
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CrawlAI"),
                "message": _("Enrichment finished — review the proposals."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_crawlai_find_website(self):
        """Step a — find the company website."""
        return self.action_crawlai_enrich(steps=["website"])

    def action_crawlai_crawl_site(self):
        """Step b — crawl the site: description + contact person."""
        return self.action_crawlai_enrich(steps=["description"])

    def action_crawlai_check_linkedin(self):
        """Step c — check the company LinkedIn."""
        return self.action_crawlai_enrich(steps=["linkedin"])

    def action_crawlai_open_session(self):
        """Open the AI session produced by the last run."""
        self.ensure_one()
        if not self.crawlai_session_id:
            raise UserError(_("No CrawlAI session has been created yet."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "ai.coworker.session",
            "res_id": self.crawlai_session_id.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }
