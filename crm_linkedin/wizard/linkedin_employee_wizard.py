from odoo import fields, models, api, _
from odoo.exceptions import UserError


class LinkedInEmployeeWizard(models.TransientModel):
    _name = 'linkedin.employee.wizard'
    _description = 'LinkedIn Employee Wizard'

    name = fields.Char(string="Name")
    company_name = fields.Char(string="Company")
    position = fields.Char(string="Position")
    public_profile = fields.Char(string="Public Profile")
    profile_urn = fields.Char(string="Public URN")
    profile_url = fields.Char(string="Public URL")
    email = fields.Char(string="Email")
    location = fields.Char(string="Location")

    def action_create_leads(self):
        parent_lead_id = self.env.context.get('default_parent_lead_id')
        if not parent_lead_id:
            raise UserError("Employees needs to be linkedin to a Company")
        print(parent_lead_id)
        active_ids = self.env.context.get('active_ids')
        print("active_ids", active_ids)

        vals = []
        for employee in self.env['linkedin.employee.wizard'].browse(active_ids).exists():
            print(employee)
            vals.append(self._serialize_employee_vals(employee))
        return self.sync_leads(vals)

    def _serialize_employee_vals(self, linked_employee):
        return {
            'name': f"{linked_employee.name or False} - {linked_employee.company_name}",
            'urn_id': linked_employee.profile_urn,
            'function': linked_employee.position,
            'contact_name': linked_employee.name,
            'street': linked_employee.location,
            'parent_lead_id': self.env.context.get('default_parent_lead_id')
        }

    def sync_leads(self, leads):
        for lead_vals in leads:
            crm_lead_id = self.env['crm.lead'].search([('urn_id', '=', lead_vals.get('urn_id'))])
            if not crm_lead_id:
                self.env['crm.lead'].create(lead_vals)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.env.context.get('default_parent_lead_id')
            # 'view_id': view_id.id,
        }
