from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    linkedin_url = fields.Char(string="LinkedIn URL", readonly=True)

    urn_id = fields.Char(string="LinkedIn URN ID", readonly=True)

    # parent_lead_id = fields.Many2one('crm.lead', string="Parent Lead")

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

    def fetch_company_employees(self):
        if not self.urn_id:
            raise ValidationError("Lead has no LinkedIn URN ID")
        client = self._linkedin_client()
        employees = client.search_people(
            current_company=[self.urn_id], limit=30, include_private_profiles=True
        )
        return self._serialize_employees(employees)

    def _serialize_employees(self, employees):
        vals = []
        for linked_employee in employees:
            vals.append({
                'name': linked_employee.get('name'),
                'company_name': self.name,
                'profile_urn': linked_employee.get('urn_id'),
                'position': linked_employee.get('jobtitle'),
                'location': linked_employee.get('location'),
                'res_id': self.id,
                'res_model': self._name,
            })
        linkedin_employee_ids = self.env['linkedin.employee.wizard'].create(vals)
        print(linkedin_employee_ids)
        return self.view_linkedin_company_employee_wizard(linkedin_employee_ids)

    def view_linkedin_company_employee_wizard(self, linkedin_employee_ids):
        view_id = self.env.ref('crm_linkedin.linkedin_company_employee_wizard_tree_view2')
        return {
            'type': 'ir.actions.act_window',
            'name': f"{self.name} Employees",
            'view_mode': 'tree',
            'res_model': 'linkedin.employee.wizard',
            'views': [(view_id.id, 'tree'), (False, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'domain': [('id', 'in', linkedin_employee_ids.ids)],
            'context': {
                'create': False,
                'default_parent_lead_id': self.id,
                'default_res_id': self.id,
                'default_res_model': self._name
            }
        }
