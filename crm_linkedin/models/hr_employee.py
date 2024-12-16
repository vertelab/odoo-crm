from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = 'hr.employee'

    linkedin_url = fields.Char(string="LinkedIn URL", readonly=True)

    urn_id = fields.Char(string="LinkedIn URN ID", readonly=True)

    public_profile = fields.Char(string="LinkedIn Public Profile", readonly=True)
