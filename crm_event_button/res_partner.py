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

import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    @api.one
    def _get_event_attendances(self):
        self.event_attendances = len(self.env['event.registration'].search_read([('partner_id', '=', self.id), ('state', '=', 'done')], []))
    
    event_attendances = fields.Integer('Events', compute='_get_event_attendances') 
    
    @api.multi
    def action_view_event_attendances(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('event', 'action_registration')
        res['context'] = {
            'search_default_partner_id': self.id,
            'search_default_state': 'done',
            'default_partner_id': self.id,
        }
        return res
        

