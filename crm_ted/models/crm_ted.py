import requests
import rss_parser
import xmltodict
import base64
import logging
# import lxml
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
    ted_title = fields.Char()
    ted_tender_id = fields.Char()
    ted_description = fields.Text()
    ted_link = fields.Char()
    ted_publication_date = fields.Datetime()
    ted_pdf = fields.Binary()
    ted_xml = fields.Binary()
    ted_estimated_value = fields.Integer()
    ted_cpv = fields.Char()
    ted_participation_period = fields.Datetime()
    ted_additional_information_period = fields.Datetime()
    # ted_curency_id = fields.Many2one(comodel_name="res.curency")
    # ted_estimated_value = fields.Monetary(currency_field='ted_curency_id')

    def create_records(self):
    
        record_list = self.get_record_list()

        for record in record_list:

            self.create_record(record)

    def get_record_list(self):

        url = "https://api.ted.europa.eu/private-search/api/v1/notices/rss?query=%28buyer-country+IN+%28SWE%29%29+AND+%28classification-cpv+IN+%28comp%29%29&channelTitle=TED&channelDescription=TED+%7C+Datatj%C3%A4nster+och+liknande+tj%C3%A4nster+%7C+EN&fields=publication-date,+deadline-receipt-request,+notice-type&language=SV"

        response = requests.get(url)

        rss = rss_parser.RSSParser.parse(response.text)

        record_list = []
        
        for item in rss.channel.items:

            record = {}

            if len(item.links) > 1:
                raise ValidationError(_("Something that was believed to be impossible has happened. Please contact the developer."))

            # _logger.error(f"{item.title.content}")
            # _logger.error(f"{item.description.content}")
            # _logger.error(f"{item.links[0].content}")
            # _logger.error(f"{item.pub_date.content}")

            record["ted_title"] = item.title.content.split(":")[1]
            record["ted_tender_id"] = item.title.content.split(":")[0]
            record["ted_description"] = item.description.content
            record["ted_link"] = item.links[0].content
            record["ted_publication_date"] = datetime.strptime(item.pub_date.content,'%a, %d %b %Y %H:%M:%S %Z')
            record["ted_pdf"] = base64.b64encode(requests.get(f"https://ted.europa.eu/sv/notice/{record['ted_tender_id']}/pdfs").content)
            xml = requests.get(f"https://ted.europa.eu/sv/notice/{record['ted_tender_id']}/xml").content
            record["ted_xml"] = base64.b64encode(xml)
            soup = BeautifulSoup(xml, 'xml')
            # record["ted_curency_id"] = self.get_ted_curency_id(base64.b64decode(record["ted_xml"]))
            record["ted_estimated_value"] = int(soup.EstimatedOverallContractAmount.string) if soup.EstimatedOverallContractAmount else False
            record["ted_cpv"] = soup.ItemClassificationCode.string if soup.ItemClassificationCode else False
            record["ted_participation_period"] =  self.combine_date_and_time(soup.ParticipationRequestReceptionPeriod)
            record["ted_additional_information_period"] = self.combine_date_and_time(soup.AdditionalInformationRequestPeriod)

            record_list.append(record)

        return record_list
    def combine_date_and_time(self,tag):
        _logger.error(f"{tag}")
        if tag:
            _logger.error(f"{tag.EndDate.string.split('+')[0]} {tag.EndTime.string.split('+')[0]}")
            return f"{tag.EndDate.string.split('+')[0]} {tag.EndTime.string.split('+')[0]}"
        return False


    # def get_ted_curency_id(self,xml)
    #     soup = BeautifulSoup(xml, 'xml')
    #     estimated_value = soup.EstimatedOverallContractAmount.string if soup.EstimatedOverallContractAmount else False
    #     _logger.error(f"{test}")
    #     return estimated_value

    def create_record(self,record):

        self.create(record)

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.ted_title

