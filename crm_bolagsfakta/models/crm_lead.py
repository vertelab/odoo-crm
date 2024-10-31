from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)

class CRMLead(models.Model):
    _description = 'scaffold_test.scaffold_test'
    _inherit = 'crm.lead'

    crm_bolagsfakta_id = fields.Many2one(comodel_name="crm.bolagsfakta")
    bolagsfakta_company_link = fields.Char(default=False)
    bolagsfakta_address = fields.Char()
    bolagsfakta_org_number = fields.Char()
    bolagsfakta_corporate_form = fields.Char()
    bolagsfakta_industry = fields.Char()
    bolagsfakta_municipality = fields.Char()
