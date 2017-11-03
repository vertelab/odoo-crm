# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
from openerp import http
from openerp.http import request
import time
import uuid

import logging
_logger = logging.getLogger(__name__)

import tempfile

try:
    import xlsxwriter
except:
    _logger.info('XlsxWriter not installed. sudo pip install XlsxWriter')


class sale_order(models.Model):
    _inherit = 'sale.order'

    access_token = fields.Char(default=lambda self: str(uuid.uuid4()))



class sale_order_generator(models.TransientModel):
    _name = 'sale.order.generator'

    order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', required=True)
    categ_ids = fields.Many2many(comodel_name='crm.case.categ', string='Tags', required=True)
    @api.model
    def get_default_partner_ids(self):
        return self.env['res.partner'].browse(self._context.get('active_ids', []))
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', default=get_default_partner_ids)

    @api.one
    def generate_sale_orders(self):
        categs = self.categ_ids
        for p in self.partner_ids:
            values = self.order_id.onchange_partner_id(p.id)['value']
            values['partner_id'] = p.id
            order = self.order_id.copy(values)
            order.categ_ids = categs

class crm_tracking_campaign(models.Model):
    _inherit = 'crm.tracking.campaign'
    
    @api.model
    def excel_order_line(self,campaign):
        #~ raise Warning(campaign)
        # https://xlsxwriter.readthedocs.io/
        temp = tempfile.NamedTemporaryFile(mode='w+t',suffix='.xlsx')
        workbook = xlsxwriter.Workbook(temp.name)
        worksheet = workbook.add_worksheet()
        worksheet.write('A1', 'Ordernummer')
        worksheet.write('B1', 'Orderdatum')
        worksheet.write('C1', u'Leverantör')
        worksheet.write('D1', 'Vara')
        worksheet.write('E1', 'a pris')
        worksheet.write('F1', 'Antal')
        worksheet.write('G1', 'Totalt')
        worksheet.write('H1', 'Namn')
        worksheet.write('I1', 'Gata')
        worksheet.write('J1', 'Postnummer')
        worksheet.write('K1', 'Ort')
        worksheet.write('L1', 'e-post')
        worksheet.write('M1', 'kommentar')
        worksheet.write('N1', u'fraktsätt')
        
        row = 2
        #~ for i,line in self.env['sale.order.line'].search([('campaign_id','=',campaign.id)],order='supplier_id.name,product.name'):
        for i,line in self.env['sale.order.line'].search([]):
            for i in range(line.product_uom_qty):
                worksheet.write('A%d' % row, line.order_id.name)
                worksheet.write('B%d' % row, line.order_id.date_confirm)
                worksheet.write('C%d' % row, line.supplier_id.name)
                worksheet.write('D%d' % row, line.product_id.name)
                worksheet.write('E%d' % row, line.price_unit)
                worksheet.write('F%d' % row, 1.0)
                worksheet.write('G%d' % row, line.price_subtotal)
                worksheet.write('H%d' % row, line.order_id.partner_id.name)
                worksheet.write('I%d' % row, line.order_id.partner_id.street)
                worksheet.write('J%d' % row, line.order_id.partner_id.zip)
                worksheet.write('K%d' % row, line.order_id.partner_id.city)
                worksheet.write('L%d' % row, line.order_id.partner_id.mail)
                worksheet.write('M%d' % row, line.order_id.note)
                worksheet.write('N%d' % row, line.order_id.carrier_id.name + ' ' + line.order_id.cavarosa_box)
                row += 1
        workbook.close() 
        temp.seek(0)
        data = temp.read()
        _logger.warn(temp.name)
        _logger.warn(data)
        temp.close()
        return (data,'xlsx')


class response_sale_order(http.Controller):

    @http.route(['/order/<int:order_id>/accept/<token>'], type='http', auth='public', website=True)
    def accept(self, order_id=None, token=None, **post):
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if token:
            if token != order.access_token:
                return request.website.render('website.404')
            body=_('Quotation accpeted by customer')
            self.__message_post(body, order_id, type='comment')
            order.action_button_confirm()
        return request.website.render('crm_cavarosa.order_thanks_page', {'partner_name': order.partner_id.name})

    @http.route(['/order/<int:order_id>/reject/<token>'], type='http', auth='public', website=True)
    def reject(self, order_id=None, token=None, **post):
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if token:
            if token != order.access_token:
                return request.website.render('website.404')
            body=_('Quotation rejected by customer')
            self.__message_post(body, order_id, type='comment')
            order.action_cancel()
        return request.website.render('crm_cavarosa.order_response_page', {'partner_name': order.partner_id.name})

    def __message_post(self, message, order_id, type='comment', subtype=False, attachments=[]):
        user = request.env['res.users'].sudo().browse(request.context['uid'])
        #~ request.env['sale.order'].sudo().message_post(order_id,
                #~ body=message,
                #~ type=type,
                #~ subtype=subtype,
                #~ author_id=user.partner_id.id,
                #~ attachments=attachments
            #~ )
        request.env['mail.message'].create({
            'body': message,
            'subject': "Order status changed",
            'author_id': user.partner_id.id,
            'res_id': order_id,
            'model': 'sale.order',
            'type': type,
            })
        return True
