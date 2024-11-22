import requests
import rss_parser
import xmltodict
import base64
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class CRMTED(models.Model):
    _name = 'crm.ted'
    _description = ''

    name = fields.Char()
    crm_lead_ids = fields.One2many(comodel_name="crm.lead", inverse_name="crm_ted_id")
    crm_lead_count = fields.Integer(compute="_compute_crm_lead_count")

    ted_title = fields.Char()
    ted_tender_id = fields.Char()
    ted_description = fields.Text()
    ted_link = fields.Char()
    ted_publication_date = fields.Datetime()
    ted_pdf_name = fields.Char()
    ted_pdf = fields.Binary()
    ted_xml_name = fields.Char()
    ted_xml = fields.Binary()
    ted_cpv = fields.Char()
    ted_participation_period = fields.Datetime()
    ted_additional_information_period = fields.Datetime()
    ted_org_name = fields.Char()
    ted_address = fields.Char()
    ted_city = fields.Char()
    ted_zip = fields.Char()
    ted_country_code = fields.Char()
    ted_contact = fields.Char()
    ted_phone = fields.Char()
    ted_email = fields.Char()
    ted_country = fields.Many2one(comodel_name="res.country")
    ted_currency_id = fields.Many2one(comodel_name="res.currency")
    ted_estimated_value = fields.Monetary(currency_field='ted_currency_id')

    def create_lead(self):

        company_partner = self.get_res_partner_company()
        self.create_res_partner(company_partner)

        new_crm_lead = \
        {
            "name": self.ted_org_name,
            "expected_revenue": self.ted_estimated_value,
            "partner_id": company_partner.id,
            "email_from": self.ted_email,
            "phone": self.ted_phone,
            "date_deadline": self.ted_participation_period,
            "partner_name": self.ted_org_name,
            "contact_name": self.ted_contact,
            "street": self.ted_address,
            "zip": self.ted_zip,
            "city": self.ted_city,
            "country_id": self.ted_country.id,
        }

        crm_lead_id = self.env["crm.lead"].create(new_crm_lead)

        self.crm_lead_ids = [(4,crm_lead_id.id)]

    def get_res_partner_company(self):

        res_partner_company = self.env["res.partner"].search([("name", "=", self.ted_org_name)])

        if not res_partner_company:

            new_company_partner = \
            {
                "name": self.ted_org_name,
                "street": self.ted_address,
                "zip": self.ted_zip,
                "city": self.ted_city,
                "country_id": self.ted_country.id,
                "email": self.ted_email,
                "phone": self.ted_phone,
            }

            return self.env["res.partner"].create(new_company_partner)

        return res_partner_company


    def create_res_partner(self,company_partner):

        res_partner = self.env["res.partner"].search([("parent_id", "=", company_partner.id),("name", "=", self.ted_contact)])

        if not res_partner:

            new_partner = \
            {
                "name": self.ted_contact,
                "street": self.ted_address,
                "zip": self.ted_zip,
                "city": self.ted_city,
                "country_id": self.ted_country.id,
                "email": self.ted_email,
                "phone": self.ted_phone,
                "parent_id": company_partner.id,
            }

            self.env["res.partner"].create(new_partner)

    def get_record_list(self):

        url = "https://api.ted.europa.eu/private-search/api/v1/notices/rss?query=%28buyer-country+IN+%28SWE%29%29+AND+%28classification-cpv+IN+%28comp%29%29&channelTitle=TED&channelDescription=TED+%7C+Datatj%C3%A4nster+och+liknande+tj%C3%A4nster+%7C+EN&fields=publication-date,+deadline-receipt-request,+notice-type&language=SV"

        response = requests.get(url)

        rss = rss_parser.RSSParser.parse(response.text)

        record_list = []

        ted_tender_ids = list(map(lambda record: record.ted_tender_id,self.env["crm.ted"].search([])))
        
        for item in rss.channel.items:

            record = {}

            if len(item.links) > 1:
                raise ValidationError(_("Something that was believed to be impossible has happened. Please contact the developer."))
            
            record["ted_tender_id"] = item.title.content.split(":")[0]
            
            if record["ted_tender_id"] not in ted_tender_ids:

                record["ted_title"] = item.title.content.split(":")[1]
                record["ted_description"] = item.description.content
                record["ted_link"] = item.links[0].content
                record["ted_publication_date"] = datetime.strptime(item.pub_date.content,'%a, %d %b %Y %H:%M:%S %Z')
                record["ted_pdf"] = base64.b64encode(requests.get(f"https://ted.europa.eu/sv/notice/{record['ted_tender_id']}/pdfs").content)
                record["ted_pdf_name"] = f"{record['ted_tender_id']}.pdf"
                xml = requests.get(f"https://ted.europa.eu/sv/notice/{record['ted_tender_id']}/xml").content
                record["ted_xml"] = base64.b64encode(xml)
                record["ted_xml_name"] = f"{record['ted_tender_id']}.xml"
                soup = BeautifulSoup(xml, 'xml')
                record["ted_currency_id"] = self.get_ted_currency_id(soup.EstimatedOverallContractAmount)
                record["ted_estimated_value"] = int(soup.EstimatedOverallContractAmount.string) if soup.EstimatedOverallContractAmount else False
                record["ted_cpv"] = soup.ItemClassificationCode.string if soup.ItemClassificationCode else False
                record["ted_participation_period"] =  self.combine_date_and_time(soup.ParticipationRequestReceptionPeriod)
                record["ted_additional_information_period"] = self.combine_date_and_time(soup.AdditionalInformationRequestPeriod)
                record["ted_org_name"] = soup.PartyName.Name.string if soup.PartyName and soup.PartyName.Name else False
                record["ted_address"] = soup.StreetName.string if soup.StreetName else False
                record["ted_city"] = soup.CityName.string if soup.CityName else False
                record["ted_zip"] = soup.PostalZone.string if soup.PostalZone else False
                record["ted_country_code"] = soup.CountrySubentityCode.string[:2] if soup.CountrySubentityCode else False
                record["ted_country"] = self.get_country(record["ted_country_code"])
                record["ted_contact"] = soup.Contact.Name.string if soup.Contact and soup.Contact.Name else False
                record["ted_phone"] = soup.Contact.Telephone.string if soup.Contact and soup.Contact.Telephone else False
                record["ted_email"] = soup.Contact.ElectronicMail.string if soup.Contact and soup.Contact.ElectronicMail else False

                _logger.error(f"{record['ted_org_name']}")
                _logger.error(f"{record['ted_contact']}")
                _logger.error(f"{record['ted_phone']}")
                _logger.error(f"{record['ted_email']}")

                record_list.append(record)

        return record_list

    def combine_date_and_time(self,tag):
        if tag:
            return f"{tag.EndDate.string.split('+')[0]} {tag.EndTime.string.split('+')[0]}"
        return False

    def get_ted_currency_id(self,soup):
        if soup:
            currency = self.env["res.currency"].search([("name", "=", soup["currencyID"])])
            return currency.id if currency else False
        return False

    def get_country(self,country_code):
        if country_code:
            country = self.env["res.country"].search([("code", "=", country_code)])
            return country.id if country else False
        return Fasle

    def create_records(self):
        record_list = self.get_record_list()
        
        for record in record_list:

            self.create_record(record)

    def create_record(self,record):
        self.create(record)

    def go_to_leads_action(self):
        return {   
            'name': 'My Tree View',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,tree,form',
            'domain': [("id", "in", self.crm_lead_ids.ids)],
        }

    api.depends("crm_lead_count")
    def _compute_crm_lead_count(self):
        for record in self:
            record.crm_lead_count = len(record.crm_lead_ids)

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.ted_title

