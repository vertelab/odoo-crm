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
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class reporder_make_invoice(models.TransientModel):
    _name = 'reporder.make.invoice'
    _description = 'Reporder Make Invoice'

    grouped = fields.Boolean(string='Group the invoices', default=False ,help='Check the box to group the invoices for the same customers')
    invoice_date = fields.Date(string='Inovice Date')

    @api.multi
    def make_invoices(self):
        form = self[0]
        newinv = []
        for order in self.env['rep.order'].browse(self.env.context.get('active_ids', [])):
            if not order.invoice_id:
                order.action_invoice_create2(self.env.context.get('active_ids', []), form.grouped, date_invoice=form.invoice_date)
                order.invoice_id.type = 'in_invoice'
                newinv.append(order.invoice_id.id)
        act_window = self.env['ir.model.data'].get_object_reference('account', 'action_invoice_tree2')
        act_window = self.env[act_window[0]].browse(act_window[1])
        result = act_window.read()[0]
        result['domain'] = "[('id','in', %s)]" %newinv

        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
