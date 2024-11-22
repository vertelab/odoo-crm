import logging
import re
import requests

from bs4 import BeautifulSoup

from odoo import models, fields, api, _
from .constant import INDUSTRY
from .utils import extract_companies

_logger = logging.getLogger(__name__)

regex_site_header = re.compile(r"\(([\d,]+)")


class CRMBolagsfakta(models.Model):
    _name = 'crm.bolagsfakta'
    _description = 'Bolagsfakta'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Name")
    information = fields.Text(default=False)
    company_link = fields.Char(default=False)
    crm_lead_ids = fields.One2many(comodel_name="crm.lead", inverse_name="crm_bolagsfakta_id")
    leads_count = fields.Integer(compute="compute_leads_count")
    municipality_ids = fields.Many2many('res.kommun', required=True)
    industry = fields.Selection(selection=INDUSTRY, required=True)
    number_of_result = fields.Integer(string="Number of Result")
    turn_over = fields.Float(string="Turnover")
    number_of_employees = fields.Integer(string="Number of Employees")

    # sni_id = fields.Many2one('res.sni', string="SNI")

    user_id = fields.Many2one("res.users", string="Salesperson")
    team_id = fields.Many2one("crm.team", string="Team")
    type = fields.Selection([('opportunity', 'Opportunity'), ('lead', 'Lead')])
    tag_ids = fields.Many2many('crm.tag', string="Tags")
    description = fields.Text('Notes')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('list', 'List'), ('done', 'Done'), ('error', 'Error'), ('cancel', 'Cancel')],
        default='draft', tracking=True)

    def action_submit(self):
        base_url = "https://www.bolagsfakta.se/"
        self.get_companies_data(base_url)

    def _has_over_1000(self, soup) -> bool:
        """Check if the number of companies is over 1000."""
        site_h2 = soup.find("h1", {"class": "site-h2"}).text
        match = regex_site_header.search(site_h2)

        if match:
            # Remove commas and convert to an integer
            number_of_companies = int(match.group(1).replace(',', ''))
            # Check if the number is greater than or equal to 1000
            return number_of_companies >= 1000
        return False

    def create_leads(self, companies_data: list):
        self.env['crm.lead'].create(companies_data)

    def get_leads(self):
        return {
            'name': 'Leads',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,form',
            "domain": [("crm_bolagsfakta_id", "=", self.id)],
            "context": {"default_crm_bolagsfakta_id": self.id},
        }

    def get_companies_data(self, base_url):
        sni = self.industry[:2]
        category_name = self.industry[3:]
        for municipality in self.municipality_ids:
            response = requests.get(f"{base_url}bransch/{municipality.code}/{category_name}/{sni}")
            soup = BeautifulSoup(response.content, 'html.parser')

            if self._has_over_1000(soup=soup):
                companies_data = self.process_sub_categories(soup=soup, municipality=municipality)
            else:
                companies_data = extract_companies(
                    soup=soup,
                    municipality=municipality,
                    crm_data=self._base_metadata(),
                    filter_params=self._filter_params()
                )
            self.create_leads(companies_data)

    def get_sub_categories_links(self, soup) -> list:
        """Extracts and returns links to subcategories."""
        return self.extract_links(
            list(
                map(lambda div: div.find("a"),
                    soup.find_all("div", class_="content-box content-box--no-hover mt-2"))
            )
        )

    def _base_metadata(self):
        return {
            "type": self.type,
            "crm_bolagsfakta_id": self.id,
            "industry": self.industry,
            "tag_ids": self.tag_ids.ids,
            "user_id": self.user_id.id,
            "team_id": self.team_id.id,
            "campaign_id": self.campaign_id.id,
            "source_id": self.source_id.id,
            "medium_id": self.medium_id.id,
        }

    def _filter_params(self):
        return {
            "turn_over": self.turn_over,
            "number_of_employees": self.number_of_employees,
        }

    def process_sub_categories(self, soup, municipality):
        """Process each subcategory if more than 1000 companies."""
        sub_categories_links = self.get_sub_categories_links(soup)

        companies_data = []

        for sub_category_link in sub_categories_links:
            sub_response = requests.get(sub_category_link)
            sub_soup = BeautifulSoup(sub_response.content, 'html.parser')

            companies_data.extend(extract_companies(
                soup=sub_soup,
                municipality=municipality,
                crm_data=self._base_metadata(),
                filter_params=self._filter_params()
            ))
        return companies_data

    def create_lead(self, record):
        self.env["crm.lead"].create(record)

    def extract_content(self, element_list):
        return list(map(lambda element: element.text.strip(), element_list))

    def extract_links(self, a_element_list):
        return list(map(lambda element: element['href'], a_element_list))

    @api.depends("crm_lead_ids")
    def compute_leads_count(self):
        for rec in self:
            rec.leads_count = len(rec.crm_lead_ids)

    def check_leads_count(self):
        base_url = "https://www.bolagsfakta.se/"
        sni = self.industry[:2]
        category_name = self.industry[3:]
        count = 0
        for municipality in self.municipality_ids:
            response = requests.get(f"{base_url}bransch/{municipality.code}/{category_name}/{sni}")
            soup = BeautifulSoup(response.content, 'html.parser')

            site_h2 = soup.find("h1", {"class": "site-h2"}).text
            match = regex_site_header.search(site_h2)

            if match:
                # Remove commas and convert to an integer
                count += int(match.group(1).replace(',', ''))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Number of Leads"),
                'type': "success",
                'message': f"The number of leads is {count}",
                'sticky': True,
            }
        }
