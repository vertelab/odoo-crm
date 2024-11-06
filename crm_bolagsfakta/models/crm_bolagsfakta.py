from odoo import models, fields, api, _

import re
import logging, requests
from bs4 import BeautifulSoup
from .constant import MUNICIPALITY, INDUSTRY

_logger = logging.getLogger(__name__)

reqex_site_header = re.compile(r"\(([\d,]+)")


class CRMBolagsfakta(models.Model):
    _name = 'crm.bolagsfakta'
    _description = 'Bolagsfakta'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.depends('municipality', 'industry')
    def _compute_name(self):
        for rec in self:
            if rec.municipality and rec.industry:
                rec.name = f"{rec.municipality} - {rec.industry}"
            else:
                rec.name = False

    name = fields.Char(compute=_compute_name)
    information = fields.Text(default=False)
    company_link = fields.Char(default=False)
    crm_lead_ids = fields.One2many(comodel_name="crm.lead", inverse_name="crm_bolagsfakta_id")
    leads_count = fields.Integer(compute="compute_leads_count")
    municipality = fields.Selection(selection=MUNICIPALITY, required=True)
    industry = fields.Selection(selection=INDUSTRY, required=True)

    sni_id = fields.Many2one('res.sni', string="SNI")

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
        match = reqex_site_header.search(site_h2)

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

    def get_companies_data(self, base_url, detailed_category_name="", full_sni=""):
        sni = self.industry[:2]
        category_name = self.industry[3:]

        response = requests.get(f"{base_url}bransch/{self.municipality}/{category_name}/{sni}")
        soup = BeautifulSoup(response.content, 'html.parser')

        if self._has_over_1000(soup=soup):
            companies_data = self.process_sub_categories(soup=soup)
        else:
            companies_data = self.process_companies_data(soup=soup)

        self.create_leads(companies_data)

    def get_sub_categories_links(self, soup) -> list:
        """Extracts and returns links to subcategories."""
        return self.extract_links(
            list(
                map(lambda div: div.find("a"),
                    soup.find_all("div", class_="content-box content-box--no-hover mt-2"))
            )
        )

    def process_sub_categories(self, soup):
        """Process each subcategory if more than 1000 companies."""
        sub_categories_links = self.get_sub_categories_links(soup)

        companies_data = []

        for sub_category_link in sub_categories_links:
            sub_response = requests.get(sub_category_link)
            sub_soup = BeautifulSoup(sub_response.content, 'html.parser')

            companies_data.extend(self.process_companies_data(soup=sub_soup))
        return companies_data

    def process_companies_data(self, soup):
        # Find all company content-boxes on the current page
        company_boxes = soup.find_all("div", class_="content-box content-box--no-hover mt-2")
        companies_data = []

        for box in company_boxes:
            # Extract the link from the <a> tag
            a_tag = box.find("a")
            link = a_tag['href'] if a_tag else None

            # Extract content inside the inner content box
            inner_box = box.find("div", class_="content-box-inner content-box--no-hover")
            if inner_box:
                # Extract the name and address from the left column
                left_column = inner_box.find("div", class_="col-sm-6")
                name = left_column.find("h2", class_="mt-0 site-h3").get_text(strip=True) if left_column else None

                # Safely extract address, checking if it's None
                address = None
                if left_column:
                    address_element = left_column.find("div", class_="mt-1 bolagsfakta-color--charcole-black")
                    address = address_element.get_text(strip=True) if address_element else None

                # Initialize right_column as None
                right_column = None
                # Check for org number in both left and right columns
                org_number = None
                org_number_element = left_column.find(
                    "span", class_="mt-1 bolagsfakta-color--charcole-black"
                ) if left_column else None
                if not org_number_element:
                    right_column = inner_box.find("div", class_="col-sm-6 text-sm-right")
                    org_number_element = right_column.find(
                        "span", class_="mt-1 bolagsfakta-color--charcole-black"
                    ) if right_column else None

                if org_number_element:
                    org_number = org_number_element.get_text(strip=True) if org_number_element else None

                # Extract corporate form from the right column
                corporate_form = None
                if right_column:
                    corporate_form_elements = right_column.find_all("span")
                    if corporate_form_elements:
                        corporate_form = corporate_form_elements[-1].get_text(strip=True)

                # Create a dictionary for each company
                company_record = {
                    "name": name,
                    "partner_name": name,
                    "street": address,
                    "org_number": org_number,
                    "corporate_form": corporate_form,
                    "bolagsfakta_company_link": link,
                    "crm_bolagsfakta_id": self.id,
                    "industry": self.industry,
                    "municipality": self.municipality,
                    "type": self.type,
                    "tag_ids": self.tag_ids.ids,
                    "user_id": self.user_id.id,
                    "team_id": self.team_id.id,
                    "campaign_id": self.campaign_id.id,
                    "source_id": self.source_id.id,
                    "medium_id": self.medium_id.id,
                }
                companies_data.append(company_record)

        # Check for pagination
        pagination = soup.find("div", class_="pagination-standard")
        if pagination:
            next_page_link = self.get_next_page_link(pagination)
            if next_page_link:
                next_page_response = requests.get(next_page_link)
                next_page_soup = BeautifulSoup(next_page_response.content, 'html.parser')
                companies_data.extend(self.process_companies_data(soup=next_page_soup))

        return companies_data

    def get_next_page_link(self, pagination):
        """Extracts the link to the next page from the pagination."""
        next_page_link = None
        next_page = pagination.find("li", class_="pagination-standard-list__item--active").find_next_sibling("li")
        if next_page:
            next_page_link = next_page.find("a")['href'] if next_page.find("a") else None
        return next_page_link

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
