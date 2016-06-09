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

class sale_cycle(models.Model):
    _name = 'sale.cycle'
    _description = 'Sales Cycle'

    name = fields.Char('Name', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    campaign_ids = fields.One2many(comodel_name='marketing.campaign', inverse_name='cycle_id',string='Campaigns')

    @api.model
    def _get_last_cycle_dates(self):
        last_cycle = self.search_read([('date_start', '<=', fields.Date.today())], ['date_start', 'date_end'], order='date_end DESC', limit=1)
        return last_cycle and (last_cycle[0]['date_start'], last_cycle[0]['date_end']) or ('', '')


class res_partner(models.Model):
    _inherit = 'res.partner'

    visited_last_cycle = fields.Boolean('Visited Last Cycle', compute='_compute_visited_last_cycle', search='_search_visited_last_cycle')

    @api.one
    @api.depends('last_meeting')
    def _compute_visited_last_cycle(self):
        last_date, foo = self.env['sale.cycle']._get_last_cycle_dates()
        self.visited_last_cycle = last_date == self.last_meeting

    def _search_visited_last_cycle(self, operator, value):
        _logger.warn("\n\n0\n\n")
        start_date, stop_date = self.env['sale.cycle']._get_last_cycle_dates()
        if (operator == '=' and value == False) or (operator == '!=' and value == True):
            if start_date and stop_date:
                _logger.warn("\n\n1\n\n")
                return ['|', '|', ('last_meeting', '<', start_date), ('last_meeting', '>', stop_date), ('last_meeting', '=', False)]
            else:
                _logger.warn("\n\n2\n\n")
                return []
            
        else:
            if start_date and stop_date:
                _logger.warn("\n\n3\n\n")
                return ['&', ('last_meeting', '>=', start_date), ('last_meeting', '<=', stop_date)]
            else:
                return [('id', '<', 1)]
                
class marketing_campaign(models.Model):
    _inherit = "marketing.campaign"

    cycle_id = fields.Many2one(comodel_name='sale.cycle', string='Sale cycle')


