from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    linkedin_url = fields.Char(string="LinkedIn URL", readonly=True)

    urn_id = fields.Char(string="LinkedIn URN ID", readonly=True)

    employee_leads = fields.One2many('crm.lead', 'parent_lead_id', string="Employee Leads")

    def _linkedin_client(self):
        client = self.env.user._linkedin_client()
        return client

    def linkedin_enrich(self):
        client = self._linkedin_client()
        active_ids = self.env.context.get('active_ids')
        partner_ids = self.env['res.partner'].browse(active_ids).exists()
        for partner in partner_ids:
            if vals := self._search_company(client, partner):
                partner.write(vals)

    def _search_company(self, client, rec):
        result = client.search_companies(rec.name, limit=1)
        if result:
            company_details = client.get_company(result[0].get('urn_id'))
            address = company_details.get('headquarter', {})
            if address.get('country') in ['SE', 'Sweden']:
                vals = {
                    'urn_id': result[0].get('urn_id'),
                    'linkedin_url': company_details.get('url'),
                    'street': address.get('line1'),
                    'zip': address.get('postalCode'),
                    'city': address.get('city'),
                    'country_id': self._get_country_record_by_code(address.get('country')),
                }
                return vals
        return {}

    def _get_country_record_by_code(self, country_code):
        return self.env['res.country'].search([('code', '=', country_code)]).id

    def fetch_company_employees(self):
        if not self.urn_id:
            raise ValidationError("Lead has no LinkedIn URN ID")
        client = self._linkedin_client()
        employees = client.search_people(
            current_company=[self.urn_id], limit=30, include_private_profiles=True
        )
        if not employees:
            raise UserError(f"No Employee Found for {self.name}")
        return self._serialize_employees(employees)

    def _serialize_employees(self, employees):
        wizard_id = self.env['linkedin.employee.wizard'].create({
            'res_id': self.id,
            'res_model': self._name,
            'company_name': self.name,
            'line_ids': [(0, 0, {
                'name': linked_employee.get('name'),
                'profile_urn': linked_employee.get('urn_id'),
                'position': linked_employee.get('jobtitle'),
                'location': linked_employee.get('location'),
            }) for linked_employee in employees]
        })

        return self.view_linkedin_company_employee_wizard(wizard_id)

    def view_linkedin_company_employee_wizard(self, wizard_id):
        view_id = self.env.ref('crm_linkedin.linkedin_company_employee_wizard_form_view2')
        return {
            'type': 'ir.actions.act_window',
            'name': f"{self.name} Employees",
            'view_mode': 'tree',
            'res_model': 'linkedin.employee.wizard',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'res_id': wizard_id.id,
        }
