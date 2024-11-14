from math import floor, log10
from odoo import api, models


class CRMLinkedInHelpers(models.Model):
    _name = 'crm.lead.linkedin.helpers'
    _description = 'Helper methods for crm_linkedin_mine modules'

    @api.model
    def lead_vals_from_response(self, lead_type, team_id, tag_ids, user_id, company_data, people_data):
        # country_id = self.env['res.country'].search([('code', '=', company_data['country_code'])]).id
        # website_url = 'https://www.%s' % company_data['domain'] if company_data['domain'] else False
        lead_vals = {
            # Lead vals from record itself
            'type': lead_type,
            'team_id': team_id,
            'tag_ids': [(6, 0, tag_ids)],
            'user_id': user_id,
            'reveal_id': company_data['clearbit_id'],
            # Lead vals from data
            'name': company_data['name'] or company_data['domain'],
            'partner_name': company_data['legal_name'] or company_data['name'],
            'email_from': next(iter(company_data.get('email', [])), ''),
            'phone': company_data['phone'] or (company_data['phone_numbers'] and company_data['phone_numbers'][0]) or '',
            # 'website': website_url,
            # 'street': company_data['location'],
            # 'city': company_data['city'],
            # 'zip': company_data['postal_code'],
            # 'country_id': country_id,
            # 'state_id': self._find_state_id(company_data['state_code'], country_id),
        }

        # If type is people then add first contact in lead data
        if people_data:
            lead_vals.update({
                'contact_name': people_data[0]['full_name'],
                'email_from': people_data[0]['email'],
                'function': people_data[0]['title'],
            })
        return lead_vals

    @api.model
    def _find_state_id(self, state_code, country_id):
        state_id = self.env['res.country.state'].search([('code', '=', state_code), ('country_id', '=', country_id)])
        if state_id:
            return state_id.id
        return False
