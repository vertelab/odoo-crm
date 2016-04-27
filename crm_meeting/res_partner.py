# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
from openerp.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit='res.partner'

    @api.one
    @api.depends('meeting_ids')
    def _last_meeting(self):
        if self.meeting_ids:
            self.last_meeting = self.meeting_ids.sorted(lambda m: m.start_date)[-1].start_date
        else:
            self.last_meeting = None
    last_meeting = fields.Date(string="Last meeting",compute='_last_meeting',store=True,help="Last meeting with this partner", select=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
