from odoo import models, fields, api, _

import re
import logging, requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    crm_bolagsfakta_id = fields.Many2one(comodel_name="crm.bolagsfakta")
    bolagsfakta_company_link = fields.Char(default=False)
    org_number = fields.Char()
    corporate_form = fields.Char()
    industry = fields.Char()
    municipality = fields.Char()

    def bolagsfakta_enrich(self):
        response = requests.get(self.bolagsfakta_company_link)
        soup = BeautifulSoup(response.content, 'html.parser')
        financial_statements = self.financial_statements(soup)
        print(financial_statements)

    def financial_statements(self, soup) -> Dict[str, List[Dict[str, Any]]]:
        data = {
            "nyckeltal": [],
            "bokslutsperiod": [],
            "resultatrakning": []
        }

        # Get all tables
        tables = soup.find_all('table')

        # Process each section based on table headers
        for table in tables:
            header = table.find('th')
            if not header:
                continue

            header_text = header.get_text(strip=True)

            if "Nyckeltal" in header_text:
                data["nyckeltal"] = self._process_nyckeltal(table)
            elif "Bokslutsperiod" in header_text:
                data["bokslutsperiod"] = self._process_bokslutsperiod(table)
            elif "Resultaträkning" in header_text:
                data["resultatrakning"] = self._process_resultatrakning(table)

        return data

    def _process_nyckeltal(self, table) -> List[Dict[str, Any]]:
        items = []
        years = self._get_years(table)

        for row in table.find_all('tr', class_='d-none d-lg-table-row'):
            tooltip = row.find('span', class_='tooltip')
            if not tooltip:
                continue

            name = tooltip.find('span', class_='tooltip__text').get_text(strip=True)
            description = tooltip.find('span', class_='tooltip__desc')
            description = description.get_text(strip=True) if description else ""

            values = {}
            for year, cell in zip(years, row.find_all('td')[1:]):
                try:
                    value = cell.get_text(strip=True)
                    values[year] = float(value.replace(',', '')) if value else None
                except (ValueError, AttributeError):
                    values[year] = None

            items.append({
                "name": name,
                "description": description,
                "values": values
            })

        return items

    def _process_bokslutsperiod(self, table) -> List[Dict[str, Any]]:
        items = []
        years = self._get_years(table)

        for row in table.find_all('tr', class_='d-none d-lg-table-row'):
            name = row.find('td').get_text(strip=True)

            values = {}
            for year, cell in zip(years, row.find_all('td')[1:]):
                value = cell.get_text(strip=True)
                try:
                    values[year] = int(value) if name == "Bokslutslängd" else value
                except (ValueError, AttributeError):
                    values[year] = value

            items.append({
                "name": name,
                "values": values
            })

        return items

    def _process_resultatrakning(self, table) -> List[Dict[str, Any]]:
        items = []
        years = self._get_years(table)

        for row in table.find_all('tr', class_='d-none d-lg-table-row'):
            tooltip = row.find('span', class_='tooltip')
            if not tooltip:
                continue

            name = tooltip.find('span', class_='tooltip__text').get_text(strip=True)
            description = tooltip.find('span', class_='tooltip__desc')
            description = description.get_text(strip=True) if description else ""

            values = {}
            for year in years:
                values[year] = None  # Initialize all values as None as per example

            items.append({
                "name": name,
                "description": description,
                "values": values
            })

        return items

    def _get_years(self, table) -> List[str]:
        """Extract years from table header."""
        header_row = table.find('tr')
        if not header_row:
            return []

        years = []
        for th in header_row.find_all('th')[1:]:  # Skip first column
            year = th.get_text(strip=True)
            if year.isdigit():
                years.append(year)

        return years

