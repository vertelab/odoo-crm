# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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
from odoo import models, fields, api,SUPERUSER_ID, _
import logging

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = "res.partner"
    
    def _get_default_status_id(self):
        """ Gives default stage_id """
        partner_id = self.env.context.get('default_partner_id')
        if not partner_id:
            return False
        return self.env['membership.recruitment.status'].search([('found','=',False)])[0]

    @api.model
    def _read_group_status_ids(self, stages, domain, order):
        return self.env['membership.recruitment.status'].search([])
        search_domain = [('id', 'in', stages.ids)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    
    membership_recruitment_status_id = fields.Many2one(comodel_name = "membership.recruitment.status",
                                                        ondelete='restrict', track_visibility='onchange', index=True,
                                                        default=_get_default_status_id, group_expand='_read_group_status_ids', copy=False)
    
    @api.multi
    def start_admission(self):
        for partner in self:
            partner.membership_recruitment_status_id = self.env['membership.recruitment.status'].search([])[0]
        action = self.env.ref("membership_status.action_admission_form")
        return action
 
 
class membership_recruitment_status(models.Model):
    _name = "membership.recruitment.status"
    
    name = fields.Char()
    _description = "Recruitment Stages"
    _order = 'sequence'
    	
    name = fields.Char("Stage name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")

    template_id = fields.Many2one(
        'mail.template', "Automated Email",
        help="If set, a message is posted on the applicant using the template when the applicant is set to the stage.")
    fold = fields.Boolean(
        "Folded in Recruitment Pipe",
        help="This stage is folded in the kanban view when there are no records in that stage to display.")
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda self: _('Blocked'), translate=True, required=True)
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda self: _('Ready for Next Stage'), translate=True, required=True)
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda self: _('In Progress'), translate=True, required=True)
