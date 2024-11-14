from odoo import models, fields, api, _

import logging, requests
from bs4 import BeautifulSoup
from .constant import MUNICIPALITY, INDUSTRY

_logger = logging.getLogger(__name__)


class CRMBolagsfakta(models.Model):
    _name = 'crm.bolagsfakta'
    _description = 'scaffold_test.scaffold_test'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=False)
    information = fields.Text(default=False)
    company_link = fields.Char(default=False)
    crm_lead_ids = fields.One2many(comodel_name="crm.lead", inverse_name="crm_bolagsfakta_id")
    leads_count = fields.Integer(compute="compute_leads_count")
    is_1000 = fields.Boolean()  # compute="compute_check_1000"

    municipality = fields.Selection(selection=MUNICIPALITY)

    industry = fields.Selection(selection=INDUSTRY)

    def action_submit(self):

        url = "https://www.bolagsfakta.se/"

        if self.is_1000 == False:
            action_or_request = self.check_1000()

        self.get_companies(url)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Warning head"),
                'type': 'warning',
                'message': _("This is the detailed warning"),
                'sticky': True,
            },
        }

    def get_companies_request(self, url, detailed_category_name="", full_sni=""):

        sni = self.industry[:2]
        category_name = self.industry[3:]

        _logger.error(f"{url}bransch/{self.municipality}/{category_name}/{sni}/{detailed_category_name}/{full_sni}")

        response = requests.get(f"{url}bransch/{self.municipality}/{category_name}/{sni}")

        soup = BeautifulSoup(response.content, 'html.parser')

    def get_companies_data(self, soup):

        a_tags = self.extract_links(
            list(map(lambda div: div.find("a"), soup.find_all("div", class_="content-box content-box--no-hover mt-2"))))
        names = self.extract_content(soup.find_all("h2", class_="mt-0 site-h3"))
        addresses = self.extract_content(soup.find_all("div", class_="mt-0 bolagsfakta-color--charcole-black"))
        org_numbers = self.extract_content(soup.find_all("span", class_="mt-1 bolagsfakta-color--charcole-black"))
        corporate_forms = self.extract_content(
            list(map(lambda div: div.find("span"), soup.find_all("div", class_="col-sm-6 text-sm-right"))))

        for company_num in range(len(a_tags)):
            _logger.error(a_tags[company_num])
            _logger.error(names[company_num])
            _logger.error(addresses[company_num])
            _logger.error(org_numbers[company_num])
            _logger.error(corporate_forms[company_num])
            _logger.error("-" * 100)

            record = {
                "name": names[company_num],
                "crm_bolagsfakta_id": self.id,
                "bolagsfakta_company_link": a_tags[company_num],
                "bolagsfakta_address": addresses[company_num],
                "bolagsfakta_org_number": org_numbers[company_num],
                "bolagsfakta_corporate_form": corporate_forms[company_num],
                "bolagsfakta_industry": self.industry,
                "bolagsfakta_municipality": self.municipality,
            }

            self.create_lead(record)

    def check_1000(self, soup):

        count_companies = soup.find("h1", class_="site-h2")

        _logger.error(f"{count_companies=}")

        count_companies = int(count_companies.text.split("(")[1].split(" st")[0].replace("\xa0", ""))

        _logger.error(f"{count_companies=}")

        if count_companies >= 1000:

            _logger.error("running??????" * 50)

            self.check_1000 = True

        elif count_companies < 1000:

            pass

    def create_lead(self, record):
        self.env["crm.lead"].create(record)

    def extract_content(self, element_list):
        return list(map(lambda element: element.text.strip(), element_list))

    def extract_links(self, a_element_list):
        return list(map(lambda element: element['href'], a_element_list))

    def get_leads(self):
        return {
            'name': 'Leads',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,form',
            "domain": [("crm_bolagsfakta_id", "=", self.id)],
            "context": {"default_crm_bolagsfakta_id": self.id},
        }

    # @api.depends("asd")
    # def compute_check_1000(self):
    #     pass

    @api.depends("crm_lead_ids")
    def compute_leads_count(self):
        for rec in self:
            rec.leads_count = len(rec.crm_lead_ids)
