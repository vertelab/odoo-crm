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

    # name = fields.Char(string="Name", required=True)
    company_name = fields.Char(string="Company")

    res_id = fields.Char(string="Rec", required=True)
    res_model = fields.Char(string="Model", required=True)
    resource_ref = fields.Reference('_selection_target_model', 'Related Document', compute='_compute_resource_ref')
    line_ids = fields.One2many("linkedin.employee.wizard.line", "wizard_id", string="LinkedIn Employees")

    def _serialize_leads_vals(self, linked_employee):
        return {
            'name': linked_employee.name,
            'urn_id': linked_employee.profile_urn,
            'public_profile': linked_employee.public_profile,
            'function': linked_employee.position,
            'street': linked_employee.location,
            'contact_name': linked_employee.name,
            'parent_lead_id': self.resource_ref.id,
        }

    def _serialize_contact_vals(self, linked_employee):
        return {
            'name': linked_employee.name,
            'urn_id': linked_employee.profile_urn,
            'public_profile': linked_employee.public_profile,
            'function': linked_employee.position,
            'street': linked_employee.location,
            'parent_id': self.resource_ref.id,
        }

    def _selected_active_records(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError("Select one or more record!")
        return active_ids

    def action_create_employee_leads(self):
        vals = []
        for rec in self.line_ids:
            vals.append(self._serialize_leads_vals(rec))
        return self._process_record(vals)

    def action_create_contact(self):
        vals = []
        for rec in self.line_ids:
            vals.append(self._serialize_contact_vals(rec))
        return self._process_record(vals)

    def _process_record(self, vals, res_model=None):
        if not res_model:
            res_model = self.res_model
        for val in vals:
            rec_id = self.env[res_model].search([('urn_id', '=', val.get('urn_id'))])
            if not rec_id:
                rec_id = self.env[res_model].create(val)
            else:
                rec_id.write(val)

            if res_model == 'hr.employee':
                rec_id.work_contact_id.write({
                    'parent_id': self.resource_ref.id,
                    'urn_id': rec_id.urn_id,
                    'function': rec_id.job_title,

                })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self.res_model,
            'res_id': self.resource_ref.id
        }

    def action_create_employee(self):
        vals = []
        for rec in self.line_ids:
            vals.append(self._serialize_hr_vals(rec))
        return self._process_record(vals, res_model="hr.employee")

    def _serialize_hr_vals(self, linked_employee):
        return {
            'name': linked_employee.name,
            'urn_id': linked_employee.profile_urn,
            'job_title': linked_employee.position,
            'public_profile': linked_employee.public_profile
        }


class LinkedInEmployeeWizardLines(models.TransientModel):
    _name = 'linkedin.employee.wizard.line'
    _description = 'LinkedIn Employee Wizard Lines'

    name = fields.Char(string="Name")
    position = fields.Char(string="Position")
    public_profile = fields.Char(string="Public Profile")
    profile_urn = fields.Char(string="Public URN")
    profile_url = fields.Char(string="Public URL")
    email = fields.Char(string="Email")
    location = fields.Char(string="Location")
    wizard_id = fields.Many2one('linkedin.employee.wizard', string="Wizard")
