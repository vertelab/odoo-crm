import logging
import requests

from bs4 import BeautifulSoup

from odoo import models, fields, tools
from .utils import extract_financial_statements

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    crm_bolagsfakta_id = fields.Many2one(comodel_name="crm.bolagsfakta")
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

    def _split_batch(self):
        batch_size = 100
        for batch_rec in tools.split_every(batch_size, self.ids):
            yield batch_rec

    def bolagsfakta_enrich(self):
        for batch_ids in self._split_batch():
            lead_ids = self.env['crm.lead'].browse(batch_ids).exists()

            for lead in lead_ids:
                response = requests.get(lead.bolagsfakta_company_link)
                soup = BeautifulSoup(response.content, 'html.parser')
                financial_statements = extract_financial_statements(soup)
                _logger.info(f"financial info - {financial_statements}")
                lead.write(financial_statements)

