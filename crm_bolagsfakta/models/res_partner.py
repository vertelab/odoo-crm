import logging
import requests

from bs4 import BeautifulSoup

from odoo import models, fields
from odoo.exceptions import UserError
from .utils import extract_financial_statements, extract_arbetsstallen, extract_company_info

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    bolagsfakta_company_link = fields.Char(default=False)
    org_number = fields.Char()
    corporate_form = fields.Char()
    industry = fields.Char()
    municipality = fields.Many2one('res.kommun')
    employee_range = fields.Char(string="Employee Range", readonly=True)

    omsattning = fields.Float(string="Omsattning")
    arets_resultat = fields.Float(string="Arets Resultat")
    ebitda = fields.Float(string="Ebitda")
    utdelning = fields.Float(string="Utdelning")

    def bolagsfakta_enrich(self):
        vals = {}
        if not self.bolagsfakta_company_link:
            raise UserError("Bolagsfakta Company URL not set")
        response = requests.get(self.bolagsfakta_company_link)
        soup = BeautifulSoup(response.content, 'html.parser')
        financial_statements = extract_financial_statements(soup)
        vals.update(**financial_statements)
        _logger.info(f"financial info - {financial_statements}")
        arbetsstallen_data = extract_arbetsstallen(soup)
        vals.update({
            'employee_range': arbetsstallen_data.get('Antal anställda', False),
            'phone': arbetsstallen_data.get('Telefonnummer', False),
            'industry': arbetsstallen_data.get('SNI-kod', False),
        })
        more_company_info = extract_company_info(soup)
        vals.update({
            'org_number': more_company_info.get('org_number'),
            'corporate_form': more_company_info.get('company_type'),
            'vat': more_company_info.get('vat_number'),
        })
        self.write(vals)

