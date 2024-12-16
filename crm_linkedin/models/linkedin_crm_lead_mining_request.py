# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)


class CRMLeadMiningRequest(models.Model):
    _name = 'crm.lead.linkedin.mining.request'
    _description = 'Linkedin CRM Lead Mining Request'

    def _default_lead_type(self):
        if self.env.user.has_group('crm.group_use_lead'):
            return 'lead'
        else:
            return 'opportunity'

    def _default_country_id(self):
        return self.env.user.company_id.country_id

    name = fields.Char(string='Request Number', required=True, readonly=True, default=lambda self: _('New'), copy=False)
    state = fields.Selection([('draft', 'Draft'), ('error', 'Error'), ('done', 'Done')], string='Status', required=True,
                             default='draft')

    # Request Data
    lead_number = fields.Integer(string='Number of Leads', required=True, default=10)
    search_type = fields.Selection([('companies', 'Companies and their Contacts'),
                                    ('people', 'People and their Contacts')],
                                   string='Target', required=True, default='companies')

    # Lead / Opportunity Data

    lead_type = fields.Selection([('lead', 'Leads'), ('opportunity', 'Opportunities')], string='Type', required=True,
                                 default=_default_lead_type)

    display_lead_label = fields.Char(compute='_compute_display_lead_label')
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', ondelete="set null",
        domain="[('use_opportunities', '=', True)]", readonly=False, compute='_compute_team_id', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    lead_ids = fields.One2many('crm.lead', 'linkedin_lead_mining_request_id', string='Generated Lead / Opportunity')
    lead_count = fields.Integer(compute='_compute_lead_count', string='Number of Generated Leads')

    # Company Criteria Filter
    filter_on_size = fields.Boolean(string='Filter on Size', default=False)
    company_size_min = fields.Integer(string='Size', default=1)
    company_size_max = fields.Integer(default=1000)
    # country_ids = fields.Many2many('res.country', string='Countries', default=_default_country_ids)
    country_id = fields.Many2one('res.country', string='Country', default=_default_country_id)
    state_ids = fields.Many2many('res.country.state', string='States')

    keywords = fields.Char(string="Keywords")
    linkedin_profile = fields.Char(string="LinkedIn Profile")

    @api.depends('lead_type', 'lead_number')
    def _compute_display_lead_label(self):
        selection_description_values = {
            e[0]: e[1] for e in self._fields['lead_type']._description_selection(self.env)}
        for request in self:
            lead_type = selection_description_values[request.lead_type]
            request.display_lead_label = '%s %s' % (request.lead_number, lead_type)

    @api.depends('lead_ids.linkedin_lead_mining_request_id')
    def _compute_lead_count(self):
        leads_data = self.env['crm.lead']._read_group(
            [('linkedin_lead_mining_request_id', 'in', self.ids)],
            ['linkedin_lead_mining_request_id'], ['__count'])
        mapped_data = {
            lead_mining_request.id: count
            for lead_mining_request, count in leads_data}
        for request in self:
            request.lead_count = mapped_data.get(request.id, 0)

    @api.depends('user_id', 'lead_type')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for mining in self:
            # setting user as void should not trigger a new team computation
            if not mining.user_id:
                continue
            user = mining.user_id
            if mining.team_id and user in mining.team_id.member_ids | mining.team_id.user_id:
                continue
            team_domain = [('use_leads', '=', True)] if mining.lead_type == 'lead' else [
                ('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            mining.team_id = team.id

    @api.model
    def get_empty_list_help(self, help_message):
        if not is_html_empty(help_message):
            return help_message

        help_title = _('Create a Lead Mining Request')
        sub_title = _('Generate new leads based on their country, industry, size, etc.')
        return super().get_empty_list_help(
            f'<p class="o_view_nocontent_smiling_face">{help_title}</p><p class="oe_view_nocontent_alias">{sub_title}</p>'
        )

    def _linkedin_client(self):
        client = self.env.user._linkedin_client()
        return client

    def _enrich_profile(self, client, basic_profile_data):
        enriched_profile_data = client.get_profile(urn_id=basic_profile_data.get('urn_id'))
        if enriched_profile_data:
            return self._get_important_profile_data(enriched_profile_data)
        return False

    def _enrich_company(self, client, basic_company_data):
        enriched_company_data = client.get_company(basic_company_data.get('urn_id'))
        if enriched_company_data:
            return self._get_important_company_data(basic_company_data, enriched_company_data)
        return False

    def _perform_request(self):
        client = self._linkedin_client()

        if self.search_type == 'people':
            profile = client.get_profile(
                self.linkedin_profile).get('urn_id') if self.linkedin_profile else False
            data = client.search_people(keywords=self.keywords, limit=self.lead_number, connection_of=profile)
        else:
            data = client.search_companies(limit=self.lead_number)
        return client, data

    def _get_important_company_data(self, basic_company_data, enriched_company_data):
        address = enriched_company_data.get('headquarter', {})
        return {
            'website': enriched_company_data.get('companyPageUrl'),
            'linkedin_url': enriched_company_data.get('url'),
            'description': enriched_company_data.get('description'),
            'name': f"{enriched_company_data.get('name')}: {basic_company_data.get('headline')}",
            'urn_id': basic_company_data.get('urn_id'),
            'street': address.get('line1'),
            'zip': address.get('postalCode'),
            'city': address.get('city'),
            'country_id': self._get_country_record_by_code(address.get('country')),
            'linkedin_lead_mining_request_id': self.id
        }

    def _get_country_record_by_code(self, country_code):
        return self.env['res.country'].search([('code', '=', country_code)]).id

    def _get_country_record_by_name(self, country_name):
        return self.env['res.country'].search([('name', '=', country_name)]).id

    def _get_important_profile_data(self, enriched_profile_data):
        name = (f"{enriched_profile_data.get('firstName')} "
                f"{enriched_profile_data.get('lastName')}: {enriched_profile_data.get('headline')}")
        return {
            'linkedin_url': enriched_profile_data.get('url'),
            'description': enriched_profile_data.get('summary'),
            'name': name,
            'urn_id': enriched_profile_data.get('urn_id'),
            'street': enriched_profile_data.get('geoLocationName'),
            'country_id': self._get_country_record_by_name(enriched_profile_data.get('geoCountryName')),
            'linkedin_lead_mining_request_id': self.id
        }

    def _create_leads_from_response(self, client, result):
        """ This method will get the response from the service and create the leads accordingly """
        self.ensure_one()
        lead_vals_list = []
        messages_to_post = {}
        for data in result:
            if self.search_type == 'people':
                lead_vals = self._enrich_profile(client, data)
            else:
                lead_vals = self._enrich_company(client, data)

            if lead_vals:
                lead_vals_list.append(lead_vals)

        self.env['crm.lead'].create(lead_vals_list)

    # Methods responsible for format response data into valid odoo lead data
    # @api.model
    # def _lead_vals_from_response(self, data):
    #     self.ensure_one()
    #     lead_vals = self.env['crm.lead.linkedin.helpers'].lead_vals_from_response(
    #         self.lead_type, self.team_id.id, self.tag_ids.ids,
    #         self.user_id.id, data
    #     )
    #     lead_vals['linkedin_lead_mining_request_id'] = self.id
    #     return lead_vals

    # def action_draft(self):
    #     self.ensure_one()
    #     self.name = _('New')
    #     self.state = 'draft'

    def action_mine_leads(self):
        self.ensure_one()
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('crm.lead.linkedin.mining.request') or _('New')
        client, results = self._perform_request()

        if results:
            self._create_leads_from_response(client, results)
            self.state = 'done'
            if self.lead_type == 'lead':
                return self.action_get_lead_action()
            elif self.lead_type == 'opportunity':
                return self.action_get_opportunity_action()
        elif self.env.context.get('is_modal'):
            # when we are inside a modal already, we re-open the same record
            # that way, the form view is updated and the correct error message appears
            # (sadly, there is no way to simply 'reload' a form view within a modal)
            return {
                'name': _('Generate Leads'),
                'res_model': 'crm.lead.linkedin.mining.request',
                'views': [[False, 'form']],
                'target': 'new',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'context': dict(self.env.context, edit=True)
            }
        else:
            # will reload the form view and show the error message on top
            return False

    def action_get_lead_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'lead')]
        return action

    def action_get_opportunity_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
        action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'opportunity')]
        return action

