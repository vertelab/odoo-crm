# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from allabolag import Company
from .constants import (
    SNI_MAPPED, SNI_MAIN, SNI_TWO, MINING_CORPORATE_FORM,
    MINING_KOMMUN, MINING_INDUSTRY_XV, MINING_LAN, SORT_OPTIONS
)
import traceback
from bs4 import BeautifulSoup
import json


import logging

_logger = logging.getLogger(__name__)


class CrmAllabolagMining(models.Model):
    _name = "crm.allabolag.mining"
    _inherit = ["mail.thread", "mail.activity.mixin", "utm.mixin"]
    _description = "CRM Allabolag Mining"
    _order = "date desc"

    def dynamic_industry_sub(self):
        _logger.warning(f"dynamic_industry_sub {self=}")
        result = []
        for main_code, main_name in SNI_MAIN:
            result.append((main_code, f"{main_code}  {main_name}"))
            for sub_code in SNI_MAPPED.get(main_code, []):
                sub_name = SNI_TWO.get(sub_code, "Okänt")
                result.append((sub_code, f"{sub_code} {sub_name}"))
        return result

    company_currency = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company.id,
    )
    corporate_form = fields.Selection(
        selection=MINING_CORPORATE_FORM, string="Company form"
    )
    date = fields.Date(
        string="Date", default=fields.Date.today()
    )
    description = fields.Text("Notes")
    expected_revenue = fields.Monetary(
        "Expected Revenue", currency_field="company_currency", tracking=True
    )
    employees_from = fields.Integer("Revenue From")
    employees_to = fields.Integer("Revenue To")
    industry = fields.Selection(
        selection=dynamic_industry_sub, string="Industry", required=False
    )
    industry_xv = fields.Selection(selection=MINING_INDUSTRY_XV, string="Industry")
    lan = fields.Selection(selection=MINING_LAN, string="County")
    lead_count = fields.Integer(
        string="Number of Leads", compute="_compute_lead_count", readonly=True
    )
    lead_ids = fields.One2many(
        comodel_name="crm.lead", inverse_name="mining_id", string="Leads", help=""
    )
    leads_url = fields.Char(string="Url", compute="_compute_leads_url")
    max_no_leads = fields.Integer(string="Number of Wanted Leads", default=50)
    name = fields.Char(
        "Request",
        index=True,
        required=True,
        compute="_compute_name",
        readonly=False,
        store=True,
        default=lambda self: _('New')
    )
    no_employees = fields.Selection(
        selection=[
            ("0-0", "0"),
            ("1-4", "1 - 4"),
            ("5-9", "5 - 9"),
            ("10-19", "10 - 19"),
            ("20-49", "20 - 49"),
            ("50-99", "50 - 99"),
            ("100-199", "100 - 199"),
            ("200-999", "200 - 999"),
            ("1000-1000000", "> 1000"),
        ],
        string="Number of Employees",
    )
    sort_option = fields.Selection(SORT_OPTIONS, string="Sortering", default='revenueDesc')
    kommun = fields.Selection(selection=MINING_KOMMUN, string="Municipality")
    recurring_plan = fields.Many2one(
        "crm.recurring.plan",
        string="Recurring Plan",
        groups="crm.group_use_recurring_revenues",
    )
    recurring_revenue = fields.Monetary(
        "Recurring Revenues",
        currency_field="company_currency",
        groups="crm.group_use_recurring_revenues",
    )

    revenue_from = fields.Float(string="Revenue")
    revenue_to = fields.Float(string="Revenue")
    profit_from = fields.Float(string="Profit")
    profit_to = fields.Float(string="Profit")
    selected_count = fields.Integer(string="Max Number of Leads")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("list", "List"),
            ("done", "Done"),
            ("error", "Error"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        tracking=True,
    )
    tag_ids = fields.Many2many(
        comodel_name="crm.tag", string="Tags", help="Set this tags to created leads"
    )  # relation|column1|column2
    type = fields.Selection(
        selection=[("lead", "Lead"), ("opportunity", "Opportunity")],
        string="Lead Type",
        default="lead",
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        index=True,
        compute="_compute_team_id",
        readonly=False,
        store=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        index=True,
        tracking=True,
        default=lambda self: self.env.user,
    )

    def _get_selection_label(self, field_name, field_key):
        """Get the label for a selection field key"""
        selection = self.fields_get(allfields=[field_name])[field_name]["selection"]
        return next((label for key, label in selection if key == field_key), field_key)

    @api.depends("user_id", "industry", "lan")
    def _compute_name(self):
        for s in self:
            industry_name = s._get_selection_label("industry", s.industry)
            s.name = f"{industry_name} {' - ' + s.lan if s.lan else ''} {' - ' + s.user_id.name if s.user_id else ''}"

    @api.depends("lead_ids")
    def _compute_lead_count(self):
        for s in self:
            s.lead_count = len(s.lead_ids)

    @api.depends(
        "corporate_form",
        "no_employees",
        "lan",
        "industry",
        "revenue_from",
        "revenue_to",
        "industry_xv",
        "sort_option"
    )
    def _compute_leads_url(self):
        """When changing the request info also update url"""
        for lead in self:
            segment = []
            if lead.industry:
                segment.append("naceIndustry=" + lead.industry)
            if lead.corporate_form:
                segment.append("companyType=" + lead.corporate_form)

            if lead.no_employees:
                (lead.employees_from, lead.employees_to) = lead.no_employees.split("-")
            if lead.employees_from:
                segment.append(f"numEmployeesFrom={lead.employees_from}")
            if lead.employees_to:
                segment.append(f"numEmployeesTo={lead.employees_to}")

            if lead.revenue_from:
                segment.append(f"revenueFrom={lead.revenue_from}")
            if lead.revenue_to:
                segment.append(f"revenueTo={lead.revenue_to}")
            if lead.profit_from:
                segment.append(f"profitFrom={lead.profit_from}")
            if lead.profit_to:
                segment.append(f"profitTo={lead.profit_to}")
            if lead.kommun and lead.lan:
                segment.append(f"location={lead.kommun},{lead.lan}")
            elif lead.kommun:
                segment.append("location=" + lead.kommun)
            elif lead.lan:
                segment.append("location=" + lead.lan)

            if lead.sort_option:
                segment.append("sort=" + lead.sort_option)

            lead.leads_url = "segmentering?" + "&".join(segment)

    @api.depends("user_id", "type")
    def _compute_team_id(self):
        """When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of."""
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
                continue
            team_domain = (
                [("use_leads", "=", True)]
                if lead.type == "lead"
                else [("use_opportunities", "=", True)]
            )
            team = self.env["crm.team"]._get_default_team_id(
                user_id=user.id, domain=team_domain
            )
            lead.team_id = team.id

    def action_get_lead_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action["domain"] = [("id", "in", self.lead_ids.ids), ("type", "=", "lead")]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No leads found
        </p><p>
            No leads could be generated according to your search criteria
        </p>"""
        )
        return action

    def action_get_opportunity_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "crm.crm_lead_opportunities"
        )
        action["domain"] = [
            ("id", "in", self.lead_ids.ids),
            ("type", "=", "opportunity"),
        ]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>"""
        )
        return action

    def action_draft(self):
        self.ensure_one()
        self.lead_ids.unlink()
        self.state = "draft"
        return None

    def action_enrich(self):
        self.ensure_one()
        for lead in self.lead_ids:
            if lead.summary_revenue == 0.0:
                try:
                    lead._enrich_lead()
                except Exception as e:
                    _logger.warning(f"Allabolag: An unexpected error occurred: {e}")
                    self.state = "error"
                    self.message_post(
                        body=_(f"An unexpected error occurred for {lead.name}: {e}")
                    )
                    return None

        self.state = "done"
        if self.type == "lead":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "crm.crm_lead_all_leads"
            )
            action["domain"] = [("id", "in", self.lead_ids.ids), ("type", "=", "lead")]
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "crm.crm_lead_opportunities"
            )
            action["domain"] = [
                ("id", "in", self.lead_ids.ids),
                ("type", "=", "opportunity"),
            ]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>"""
        )
        return action

    def allabolag_search_result(self, page=None):
        if not self.leads_url:
            return None  # Return None instead of 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        url_path = self.leads_url
        if page and page > 1:
            url_path = f"{self.leads_url}&page={page}"

        url = f"https://allabolag.se/{url_path}"
        _logger.info(f"Scraping: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")

        except Exception as e:
            _logger.error(f"Failed to scrape {url}: {e}")
            return None  # Return None instead of 0

    def scrape_traffar_number(self):
        """Scrape number of companies from Allabolag search results."""
        self.ensure_one()

        search_result = self.allabolag_search_result()
        if not search_result:  # Check if we got a valid result
            return 0

        header = search_result.find(class_="SearchResultList-listHeader")
        if header:
            digits = "".join(filter(lambda c: c.isdigit(), header.get_text(strip=True)))
            return int(digits) if digits else 0
        return 0

    def action_check(self):
        self.ensure_one()
        self.selected_count = self.scrape_traffar_number()
        if self.max_no_leads > self.selected_count:
            self.max_no_leads = self.selected_count

    def _get_search_except(self, search_result):
        """Extract organization numbers and URLs from search results."""
        if not search_result:
            return []

        results = []

        # Find all company cards
        company_cards = search_result.find_all(
            class_="SegmentationSearchResultCard-card"
        )

        for card in company_cards:
            try:
                # Extract company name and URL from the h2 link
                name_link = card.find("h2").find("a")
                if name_link:
                    company_name = name_link.get_text(strip=True)
                    company_url = name_link.get("href")

                    # Find the span containing "Org.nr" text
                    org_nr = None
                    property_spans = card.find_all(
                        "span", class_="CardHeader-propertyList"
                    )

                    for prop_span in property_spans:
                        # Check if this span contains the Org.nr
                        inner_spans = prop_span.find_all("span")
                        for inner_span in inner_spans:
                            if inner_span.get_text(strip=True) == "Org.nr":
                                # Get the next sibling text (the actual org number)
                                org_nr = inner_span.next_sibling
                                if org_nr:
                                    org_nr = str(org_nr).strip()
                                break
                        if org_nr:
                            break

                    if org_nr and company_url:
                        results.append(
                            {"name": company_name, "org_nr": org_nr, "url": company_url}
                        )

            except Exception as e:
                _logger.error(f"Failed to extract company data: {e}")
                continue
        return results

    def _get_max_companies_from_search(self):
        """Collect all companies up to max_no_leads by paginating through results."""
        all_companies = []
        page = 1

        while len(all_companies) < self.max_no_leads:
            # Get search results for current page
            search_result = self.allabolag_search_result(page=page)

            if not search_result:
                break

            # Extract companies from this page
            page_companies = self._get_search_except(search_result)

            if not page_companies:
                _logger.info(f"No more results found on page {page}")
                break

            # Add only what we need
            remaining = self.max_no_leads - len(all_companies)
            all_companies.extend(page_companies[:remaining])

            _logger.info(
                f"Page {page}: found {len(page_companies)} companies, total collected: {len(all_companies)}"
            )

            # Check if this was the last page (less than 10 results)
            if len(page_companies) < 10:
                break

            page += 1

            # Safety limit to prevent infinite loops
            if page > 100:
                _logger.warning("Reached maximum page limit (100)")
                break

        _logger.info(
            f"Collected {len(all_companies)} companies out of {self.max_no_leads} requested"
        )
        return all_companies

    def action_submit(self):
        self.ensure_one()
        search_data = self._get_max_companies_from_search()
        try:
            for data in search_data:
                if company_data := self._get_company_details(data.get("org_nr", False)):
                    company_vals = self._set_company_details(company_data)
                    company_vals["linkTo"] = f"https://allabolag.se{data['url']}"
                    self._sync_lead(company_vals=company_vals)
                    # self.env['crm.lead'].create(company_vals)
                    self.env.cr.commit()
        except Exception as e:
            tb_str = traceback.format_exc()
            _logger.warning(f"Allabolag: An unexpected error occurred: {e}, {tb_str}")
            self.message_post(
                body=_(f"An unexpected error occurred: {e}"),
                message_type="notification",
            )
            self.state = "error"

        self.state = "list"
        if self.type == "lead":
            return self.action_get_lead_action()
        elif self.type == "opportunity":
            return self.action_get_opportunity_action()
        return None

    def _sync_lead(self, company_vals):
        crm_lead = self.env["crm.lead"]
        lead_id = crm_lead.search(
            [("company_registry", "=", company_vals.get("company_registry"))]
        )
        if not lead_id:
            self.env["crm.lead"].create(company_vals)

    def _set_company_details(self, company_data):
        employee = company_data.get("employees", 0)
        return {
            "name": company_data.get("name"),
            "partner_name": company_data.get("name", False),
            "company_registry": company_data.get("orgnr", False),
            "mining_id": self.id,
            "city": company_data.get("postalAddress").get("postPlace") if company_data.get("postalAddress") else False,
            "tag_ids": self.tag_ids,
            "type": self.type,
            "user_id": self.user_id.id if self.user_id else None,
            "description": self.description,
            "team_id": self.team_id.id if self.team_id else None,
            "campaign_id": self.campaign_id.id if self.campaign_id else None,
            "source_id": self.source_id.id if self.source_id else None,
            "medium_id": self.medium_id.id if self.medium_id else None,
            "expected_revenue": self.expected_revenue,
            "summary_parent_company": company_data.get("foundationYear"),
            "summary_state": company_data.get("status", {}).get("status"),
            "kpi_no_employees": employee,
            "allabolag_json_data": company_data,
            "linkTo": company_data.get("linkTo")
        }

    def _get_company_details(self, org_nr):
        if data := Company(org_nr).data:
            return data.get("company")
        return {}

    def action_allabolag_url(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"https://allabolag.se/{self.leads_url}",
            "target": "new",
        }
