# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2019 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

    
class Survey(models.Model):
    _inherit = 'survey.survey'
    
    def _default_department_ids(self):
        # ~ _logger.warn('\n\n_default_departments_ids\n%s\n' % self.env.context)
        return self.env.user.employee_ids.mapped('department_id')
    
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', default=_default_department_ids)
    department_restrict = fields.Boolean(string='Department Restrict', compute='_department_restrict', search='_search_department_restrict', help="Dummy field to restrict resources depending on user department.")
    
    def _department_restrict(self):
        pass
    
    def _search_department_restrict(self, op, value):
        return self.get_department_restrict_domain()
    
    def get_department_restrict_domain(self, field_name='department_id'):
        """Calculate which resources should be allowed depending on user groups and sales team.
        
        :param field_name: The name of the sales team field for the given model.
        :returns: A search domain expressing the users security restrictions.
        """
        # Seems like this is run as admin. Fetch user from uid.
        user = self.env['res.users'].browse(self.env.context.get('uid'))
        if not user:
            return []
        # ~ _logger.warn('\n\nget_departments_restrict_domain\n%s\n%s\n' % (self.env.context, self.env.user))
        if user._is_admin():
            # Don't apply restriction to admin.
            # ~ _logger.warn('\n\nadmin\n')
            return []
        if not user._has_group('base.group_user'):
            # Only apply this restriction to internal users.
            # ~ _logger.warn('\n\nnot employee\n')
            return []
        if user._has_group('crm_survey_department.group_all_departments'):
            # This user has cross team access.
            # ~ _logger.warn('\n\ncross team access\n')
            return []
        # Restrict to own sales teams, or no sales team.
        department_id = user.department_ids.mapped('id')
        # ~ if user.sale_team_id:
            # ~ team_ids.append(user.sale_team_id.id)
        # ~ _logger.warn('\n\nteam_ids: %s\n' % team_ids)   
        if department_id:
            domain = [(field_name, '=', False)]
            for id in department_id:
                domain.append((field_name, 'child_of', id))
            return ['|' for x in range(len(domain) - 1)] + domain
        return [(field_name, '=', False)]

# class CrmLead(models.Model):
#     _inherit = "crm.lead"
    
#     departments_restrict = fields.Boolean(string='Sales Team Restrict', compute='_departments_restrict', search='_search_departments_restrict', help="Dummy field to restrict resources depending on user sales team.")
    
#     def _departments_restrict(self):
#         pass
    
#     def _search_departments_restrict(self, op, value):
#         return self.env['res.partner'].get_departments_restrict_domain('team_id')

class res_users(models.Model):
    _inherit = 'res.users'
    
    def _default_department_ids(self):
        # ~ _logger.warn('\n\n_default_departments_ids\n%s\n' % self.env.context)	
        return self.env.user.employee_ids.mapped('department_id')
        
    department_ids = fields.Many2many(comodel_name='hr.department', string='Department', default=_default_department_ids)
    
    
    
    
    
    
    
