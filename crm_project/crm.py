# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class crm_team(models.Model):
    _inherit = 'crm.team'

    project_id = fields.Many2one(comodel_name='project.project',string="Project",)

class crm_lead(models.Model):
    _inherit = 'crm.lead'

    project_id = fields.Many2one(comodel_name='project.project',related='team_id.project_id',string="Project",)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    project_id = fields.Many2one(comodel_name='project.project',string="Project",)
    
class project_project(models.Model):
    _inherit = 'project.project'

    lead_ids = fields.One2many(comodel_name='crm.lead',inverse_name='project_id',string='Leads')
    partner_ids = fields.One2many(comodel_name='res.partner',inverse_name="project_id",string='Leads')
    partner_count = fields.Integer("# Partners", compute='_compute_partner_count')
    lead_count = fields.Integer("# Leads", compute='_compute_partner_count')

    @api.multi
    def _compute_partner_count(self):
        for partner in self:
            partner.partner_count = len(partner.partner_ids)
            partner.lead_count = len(partner.lead_ids)

