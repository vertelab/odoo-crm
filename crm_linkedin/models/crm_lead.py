# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, tools, api
from odoo.exceptions import ValidationError, UserError
from ast import literal_eval
from linkedin_api import Linkedin
from linkedin_api.utils import helpers
from odoo.addons.crm.models.crm_lead import CRM_LEAD_FIELDS_TO_MERGE

CRM_LEAD_FIELDS_TO_MERGE.extend(['linkedin_url', 'urn_id'])


class Lead(models.Model):
    _inherit = 'crm.lead'

    linkedin_lead_mining_request_id = fields.Many2one(
        'crm.lead.linkedin.mining.request', string='LinkedIn Lead Mining Request', index='btree_not_null'
    )
    linkedin_url = fields.Char(string="LinkedIn URL", readonly=True)

    urn_id = fields.Char(string="LinkedIn URN ID", readonly=True)

    parent_lead_id = fields.Many2one('crm.lead', string="Parent Lead")

    employee_leads = fields.One2many('crm.lead', 'parent_lead_id', string="Employee Leads")

    # def linkedin_user_profile(self):
    #     client = self._linkedin_client()
    #     urn = helpers.get_id_from_urn(
    #         client.get_user_profile().get('miniProfile', {}).get('entityUrn')
    #     )
    #     return client, urn

    @api.depends('employee_leads')
    def _compute_employee_leads_count(self):
        for rec in self:
            rec.employee_leads_count = len(rec.employee_leads)

    employee_leads_count = fields.Float(string="Employee Count", compute=_compute_employee_leads_count)

    def _merge_get_fields(self):
        return super(Lead, self)._merge_get_fields() + ['linkedin_lead_mining_request_id']

    def action_generate_linkedin_leads(self):
        return {
            "name": _("Need help reaching your target?"),
            "type": "ir.actions.act_window",
            "res_model": "crm.lead.linkedin.mining.request",
            "target": "new",
            "views": [[False, "form"]],
            "context": {"is_modal": True},
        }

    def _linkedin_client(self):
        client = self.env.user._linkedin_client()
        return client

    def linkedin_enrich(self):
        client = self._linkedin_client()
        active_ids = self.env.context.get('active_ids')
        lead_ids = self.env['crm.lead'].browse(active_ids).exists()
        for lead in lead_ids:
            if vals := self._search_company(client, lead):
                lead.write(vals)

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

    def _split_batch(self):
        batch_size = 100
        for batch_rec in tools.split_every(batch_size, self.ids):
            yield batch_rec

    def fetch_company_employees(self):
        if not self.urn_id:
            raise ValidationError("Lead has no LinkedIn URN ID")
        client = self._linkedin_client()
        employees = client.search_people(
            current_company=[self.urn_id], limit=30, include_private_profiles=True
        )
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
        view_id = self.env.ref('crm_linkedin.linkedin_company_employee_wizard_form_view')
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

    def action_view_employees(self):
        view_id = self.env.ref('crm_linkedin.linkedin_company_employee_tree_view_leads')
        return {
            'type': 'ir.actions.act_window',
            'name': f"{self.name} Employees",
            'view_mode': 'tree',
            'res_model': 'crm.lead',
            'views': [(view_id.id, 'tree'), (False, 'form')],
            'view_id': view_id.id,
            'target': 'self',
            'domain': [('parent_lead_id', '=', self.id)]
        }

    def _cron_send_linkedin_invitation(self):
        client = self._linkedin_client()

        self._send_linkedin_messages(client)

    def _send_connection(self, client, lead):
        client.add_connection()

    def _send_linkedin_messages(self, client):
        crm_lead_urns = self._crm_leads().mapped('urn_id')
        client.send_message(
            message_body="",
            recipients=crm_lead_urns
        )

    # def _check_who_accepted_connection(self):
    #     # def _cron_send_linkedin_invitation(self):
    #     crm_lead_urns = self._crm_leads().mapped('urn_id')
    #     client, urn = self.linkedin_user_profile()
    #     connections = client.get_profile_connections(urn)
    #     connected_persons = list(filter(lambda connection: connection.get('urn_id') not in crm_lead_urns, connections))

    def _crm_leads(self):
        config_id = self.env['automation.configuration'].search([('model_id.model', '=', 'crm.lead')])
        crm_ids = self.env['crm.lead'].search(literal_eval(config_id.editable_domain))
        leads = crm_ids.mapped('employee_leads')
        return leads

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        vals = super(Lead, self)._prepare_customer_values(partner_name, is_company=is_company, parent_id=parent_id)
        vals.update({
            'linkedin_url': self.linkedin_url,
            'urn_id': self.urn_id,
        })
        return vals
