from odoo import fields, models, api, _
from odoo.exceptions import UserError


class LinkedInEmployeeWizard(models.TransientModel):
    _name = 'linkedin.employee.wizard'
    _description = 'LinkedIn Employee Wizard'

    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    @api.depends('res_model', 'res_id')
    def _compute_resource_ref(self):
        for wizard in self:
            if wizard.res_model and wizard.res_model in self.env:
                wizard.resource_ref = '%s,%s' % (wizard.res_model, wizard.res_id or 0)
            else:
                wizard.resource_ref = None

    name = fields.Char(string="Name")
    company_name = fields.Char(string="Company")
    position = fields.Char(string="Position")
    public_profile = fields.Char(string="Public Profile")
    profile_urn = fields.Char(string="Public URN")
    profile_url = fields.Char(string="Public URL")
    email = fields.Char(string="Email")
    location = fields.Char(string="Location")
    res_id = fields.Char(string="Rec", required=True)
    res_model = fields.Char(string="Model", required=True)
    resource_ref = fields.Reference('_selection_target_model', 'Related Document', compute='_compute_resource_ref')

    def action_create_leads(self):
        parent_lead_id = self.env.context.get('default_parent_lead_id')
        if not parent_lead_id:
            raise UserError("Employees needs to be linkedin to a Company")
        active_ids = self.env.context.get('active_ids')

        vals = []
        for employee in self.env['linkedin.employee.wizard'].browse(active_ids).exists():
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
        }

    def _serialize_contact_vals(self, linked_employee):
        return {
            'name': linked_employee.name,
            'urn_id': linked_employee.profile_urn,
            'function': linked_employee.position,
            'street': linked_employee.location,
            'parent_id': linked_employee.resource_ref.id,
        }

    def _selected_active_records(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError("Select one or more record!")

        return active_ids

    def action_create_contact(self):
        active_ids = self._selected_active_records()
        vals = []
        for rec in self.env['linkedin.employee.wizard'].browse(active_ids).exists():
            vals.append(self._serialize_contact_vals(rec))
        return self._process_record(vals)

    def _process_record(self, vals):
        for val in vals:
            print(vals)
            rec_id = self.env[self.res_model].search([('urn_id', '=', val.get('urn_id'))])
            if not rec_id:
                rec_id = self.env[self.res_model].create(val)
            if self.res_model == 'hr.employee':
                print(val)
                rec_id.work_contact_id.write({
                    'parent_id': val.get('parent_id'),
                    'urn_id': rec_id.profile_urn,
                    'function': rec_id.position,

                })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self.res_model,
            'res_id': self.resource_ref.id
        }

    def action_create_employee(self):
        active_ids = self._selected_active_records()
        vals = []
        for rec in self.env['linkedin.employee.wizard'].browse(active_ids).exists():
            vals.append(self._serialize_hr_vals(rec))
        return self._process_record(vals)

    def _serialize_hr_vals(self, linked_employee):
        return {
            'name': linked_employee.name,
            'urn_id': linked_employee.profile_urn,
            'job_title': linked_employee.position,
            'street': linked_employee.location,
            'parent_id': linked_employee.resource_ref.id,
        }