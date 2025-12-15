from odoo import models, fields, api, _
from datetime import date
import logging
from odoo.exceptions import ValidationError
import re

from allabolag import Company
from allabolag.liquidated_companies import iter_liquidated_companies
from allabolag.list import iter_list
from copy import deepcopy
from datetime import datetime

_logger = logging.getLogger(__name__)

##Dokumentera snikod,bolagsform,valuta
class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', "res.partner.allabolag.mixin"]

    company_registry = fields.Char(string='Company Registry', size=64, trim=True, )
    vat = fields.Char(string='VAT', size=64, trim=True, )
    linkTo = fields.Char(string='Link', help="Link to Allabolag")

    def _enrich_lead(self):
        if company_data := Company(self.company_registry).data:
            company_vals = self._set_company_details(company_data.get("company"))
            self.write(company_vals)

    def _set_company_details(self, company_data):
        revenue = int(company_data.get('revenue', 0))
        employees = int(company_data.get("employees", 0))

        # Estimate employees if missing but has revenue
        if employees == 0 and revenue > 0:
            employees = max(1, revenue // 200_000)

        # Calculate revenue per employee safely
        revenue_per_employee = round(revenue / employees, 2) if employees > 0 else 0

        res1 = {
            "name": company_data.get("name"),
            "partner_name": company_data.get("name", False),
            "company_registry": company_data.get("orgnr", False),
            "city": company_data.get("postalAddress",{}).get("postPlace",False) if company_data.get("postalAddress") else False,
            "summary_parent_company": company_data.get("foundationYear"),
            "summary_state": company_data.get("status", {}).get("status") if company_data.get("status") else False,
            "kpi_no_employees": employees,
            "summary_revenue": revenue,
            "kpi_revenue_employees": revenue_per_employee,
            "summary_purpose": company_data.get('purpose', ""),
            "summary_profit_ebit": company_data.get("profit", 0),
            "contact_name": company_data.get("contactPerson", {}).get('name', "") if company_data.get("contactPerson") else False,
            "function": company_data.get("contactPerson", {}).get('role', "") if company_data.get("contactPerson") else False,
            "summary_registry_year": company_data.get('registrationDate'),
            "email_from": company_data.get("email"),
            "phone": company_data.get("phone",False),
            "mobile": company_data.get("mobile",False),
            "website": company_data.get("homePage",False),
            "street": company_data.get("postalAddress", {}).get("addressLine",False) if company_data.get("postalAddress") else False, 
            "zip": company_data.get("postalAddress", {}).get("zipCode",False) if company_data.get("postalAddress") else False,
        }
        _logger.warning(f"{res1=}")
        return res1

        
        


    # def enrich_allabolag(self):
    #     for crm in self:
    #         _logger.warning('%s' % crm._fields['summary_revenue'])
    #         if not crm.company_registry:
    #             crm.company_registry, item=self.env['res.partner'].name2orgno(crm.partner_name or crm.name)
    #
    #         record = crm.env['res.partner'].partner_enrich_allabolag(crm.company_registry)
    #         crm.write(record)

    def crm_enrich(self):
        for crm in self:
            crm._enrich_lead()
            # crm.enrich_allabolag()
        super(CrmLead, self).crm_enrich()
