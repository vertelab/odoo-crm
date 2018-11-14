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

    latest_activity = fields.Datetime(string="Latest activity",help="Last activity by this partner", select=True)

    @api.one
    def set_latest_activity(self):
        self.latest_activity = fields.Datetime.now()
        if self.parent_id:
            self.parent_id.set_latest_activity()


class sale_order(models.Model):
    _inherit='sale.order'

    @api.multi
    def action_button_confirm(self):
        self.partner_id.set_latest_activity()
        return super (sale_order,self).action_button_confirm()

class account_invoice(models.Model):
    _inherit='account.invoice'

    @api.multi
    def invoice_print(self):
        for invoice in self:
            invoice.partner_id.set_latest_activity()
        return super(account_invoice,self).invoice_print()

    @api.multi
    def action_invoice_sent(self):
        for invoice in self:
            invoice.partner_id.set_latest_activity()
        return super(account_invoice,self).action_invoice_sent()

class stock_picking(models.Model):
    _inherit='stock.picking'

    @api.one
    def action_done(self):
        self.partner_id.set_latest_activity()
        return super(stock_picking,self).action_done()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
