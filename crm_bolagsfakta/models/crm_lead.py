from odoo import models, fields, api, _, tools

import re
import logging, requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    crm_bolagsfakta_id = fields.Many2one(comodel_name="crm.bolagsfakta")
    bolagsfakta_company_link = fields.Char(default=False)
    org_number = fields.Char()
    corporate_form = fields.Char()
    industry = fields.Char()
    municipality = fields.Many2one('res.kommun')
    fin_data = fields.Html(string="Fin Data", sanitize_attributes=False, translate=html_translate, sanitize_form=False)

    omsattning = fields.Float(string="Omsattning")
    arets_resultat = fields.Float(string="Arets Resultat")
    ebitda = fields.Float(string="Ebitda")
    utdelning = fields.Float(string="Utdelning")

    def _split_batch(self):
        batch_size = 100
        for sms_batch in tools.split_every(batch_size, self.ids):
            yield sms_batch

    def bolagsfakta_enrich(self):
        for batch_ids in self._split_batch():
            lead_ids = self.env['crm.lead'].browse(batch_ids).exists()

            for lead in lead_ids:
                response = requests.get(lead.bolagsfakta_company_link)
                soup = BeautifulSoup(response.content, 'html.parser')
                financial_statements = self.financial_statements(soup)
                _logger.info(f"financial info - {financial_statements}")
                lead.write(financial_statements)

    def financial_statements(self, soup) -> Dict[str, float]:
        metrics = {
            'omsattning': None,
            'arets_resultat': None,
            'ebitda': None,
            'utdelning': None
        }

        def safe_float_conversion(value):
            """Safely convert string to float, handling any errors"""
            if value is None:
                return None
            try:
                # Remove commas and convert to float
                return float(str(value).replace(',', ''))
            except (ValueError, TypeError, AttributeError):
                _logger.error(f"Could not convert value to float: {value}")
                return None

        try:
            # 1. Find EBITDA
            for row in soup.find_all('tr', class_='d-none d-lg-table-row'):
                tooltip = row.find('span', class_='tooltip__text')
                if tooltip and 'EBITDA' in tooltip.text:
                    value_text = row.find_all('td')[1].get_text(strip=True)
                    metrics['ebitda'] = safe_float_conversion(value_text)

            # 2. Find Rörelsens omsättning
            omsattning_row = soup.find('u', text='Rörelsens omsättning')
            if omsattning_row:
                row = omsattning_row.find_parent('tr')
                value_text = row.find_all('td')[1].get_text(strip=True)
                metrics['omsattning'] = safe_float_conversion(value_text)

            # 3. Find Årets resultat
            resultat_rows = soup.find_all('tr', class_='d-none d-lg-table-row table--bgcolor')
            for row in resultat_rows:
                tooltip = row.find('span', class_='tooltip__text')
                if tooltip and tooltip.text.strip() == 'Årets resultat':
                    value_text = row.find_all('td')[1].get_text(strip=True)
                    metrics['arets_resultat'] = safe_float_conversion(value_text)
                    break

        except Exception as e:
            _logger.error(f"Error parsing financial statements: {e}")

        # Final check to ensure all non-None values are floats
        for key in metrics:
            if metrics[key] is not None:
                metrics[key] = safe_float_conversion(metrics[key])

        return metrics


