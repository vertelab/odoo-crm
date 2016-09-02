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
from openerp import http
from openerp.http import request
import datetime
import logging
import base64
_logger = logging.getLogger(__name__)

import openerp.addons.decimal_precision as dp

class sale_order(models.Model):
    _inherit = 'sale.order'

    rep_order_id = fields.Many2one('rep.order', 'Rep Order Reference')


class res_partner(models.Model):
    _inherit = 'res.partner'

    def _get_meeting(self):
        meetings = []
        for m in self.meeting_ids:
            if m.allday:
                if m.start_date == datetime.date.today():
                    meetings.append(m)
            if not m.allday:
                if m.start_datetime[0:10] == str(datetime.date.today()):
                    meetings.append(m)
        return meetings

    product_ids = fields.Many2many(comodel_name='product.product', string='Products')
    listing_id = fields.Many2one(comodel_name='res.partner.listing', string='Listing')


class res_partner_listing(models.Model):
    _name = 'res.partner.listing'

    name = fields.Char(string='Name')
    product_ids = fields.Many2many(comodel_name='product.product', string='Products')


class MobileSaleView(http.Controller):
    @http.route(['/crm/<model("res.partner"):partner>/repord'], type='http', auth="public", website=True)
    def repord(self, partner=None, **post):
        products = request.env['res.partner'].sudo().search([('id', '=', partner.id)]).product_ids
        parent_products = request.env['res.partner'].sudo().search([('id', '=', partner.id)]).listing_id.product_ids
        rep_order = request.env['rep.order'].search([('partner_id', '=', partner.id), ('state', '=', 'draft')])
        if request.httprequest.method == 'POST':
            request.env['ir.attachment'].create({
                'name': post['ufile'].filename,
                'res_model': 'res.partner',
                'res_name': partner.name,
                'partner_id': partner.id,
                'res_id': partner.id,
                'type': 'binary',
                'datas': base64.encodestring(post['ufile'].read()),
                'datas_fname': post['ufile'].filename,
            })
        if not rep_order:
            rep_order = request.env['rep.order'].create({
                'partner_id': partner.id
            })
        else:
            rep_order = rep_order[0]
        return request.website.render("crm_repord.mobile_order_view", {'partner': partner, 'products': products, 'parent_products': parent_products, 'order': rep_order,})

    @http.route(['/crm/send/repord'], type='json', auth="public", methods=['POST'], website=True)
    def send_rep_order(self, res_partner, product_id, product_uom_qty, discount, **kw):
        rep_order_ids = request.env['rep.order'].search([('partner_id', '=', int(res_partner)),('state','=','draft')])
        if len(rep_order_ids)>0:
            repord = rep_order_ids[0]
        else:
            repord = request.env['rep.order'].create({
                'partner_id': int(res_partner),
                'state': 'draft',
            })
        order_line = False
        product = request.env['product.product'].search([('id', '=', int(product_id))])
        for line in repord.order_line:
            if line.product_id.id == int(product_id):
                order_line = line
        if order_line:
            order_line = request.env['rep.order.line'].search([('product_id', '=', int(product_id))])
            if float(product_uom_qty) == 0.000:
                order_line.unlink()
            else:
                order_line.write({
                    'product_uom_qty': float(product_uom_qty),
                    'price_unit': product.lst_price,
                    'discount': float(discount) if discount != '' else 0.00,
                })
        elif product_uom_qty > 0.000:
            order_line = request.env['rep.order.line'].search([('order_id', '=', repord.id)])
            order_line.create({
                'order_id': rep_order_ids[0].id,
                'product_id': int(product_id),
                'name': product.name,
                'product_uom_qty': float(product_uom_qty),
                'product_uom': product.uom_id.id,
                'price_unit': product.lst_price,
                'tax_id': [(6, 0, [tax_id.id for tax_id in product.taxes_id])],
                'discount': float(discount) if discount != '' else 0.00,
            })

    @http.route(['/crm/add/product'], type='json', auth="public", methods=['POST'], website=True)
    def add_product(self, res_partner, product_id, **kw):
        partner = request.env['res.partner'].search([('id', '=', int(res_partner))])
        for p in partner.listing_id.product_ids:
            if int(product_id) != p.id:
                partner.write({
                    'product_ids': [(4, int(product_id), 0)]
                })
        return 'added'

    @http.route(['/crm/remove/product'], type='json', auth="public", methods=['POST'], website=True)
    def remove_product(self, res_partner, product_id, **kw):
        partner = request.env['res.partner'].search([('id', '=', int(res_partner))])
        for p in partner.listing_id.product_ids:
            if int(product_id) == p.id:
                partner.write({
                    'product_ids': [(3, int(product_id), 0)]
                })
        return 'removed'

    @http.route(['/crm/todo/done'], type='json', auth="public", methods=['POST'], website=True)
    def todo_done(self, note_id, **kw):
        note = request.env['note.note'].search(['&', '&', ('id', '=', int(note_id)), ('open', '=', True), ('stage_id', '!=', request.env.ref('note.note_stage_04').id)])
        note.write({
            'open': False,
            'date_done': datetime.date.today(),
        })
        return 'note_done'

    @http.route(['/crm/meeting/visited'], type='json', auth="public", methods=['POST'], website=True)
    def customer_visited(self, partner_id, **kw):
        meetings = request.env['calendar.event'].search([])
        partner = request.env['res.partner'].search([('id', '=', int(partner_id))])
        for m in meetings:
            if partner in m.partner_ids:
                m.write({
                    'categ_ids': [(4, request.env.ref('crm_repord.categ_meet6').id, _)],
                })
        return 'meeting_done'

    @http.route(['/crm/presentation/done'], type='json', auth="public", methods=['POST'], website=True)
    def presentation(self, partner_id, categ, **kw):
        partner = request.env['res.partner'].browse(int(partner_id))
        request.env['mail.message'].create({
            'body': 'Presentation done.',   #TODO: change message body
            'subject': 'Presentation to ' + categ + ' has be done',
            'author_id': request.env['res.users'].browse(request.env.uid).partner_id.id,
            'model': partner._name,
            'res_id': partner.id,
            'type': 'notification',
        })
        return 'presentation_done'

    @http.route(['/crm/repord/type'], type='json', auth="public", methods=['POST'], website=True)
    def change_order_type(self, order, order_type, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        order.write({
            'order_type': order_type,
        })
        return 'order_type_changed'

    @http.route(['/crm/repord/campaign'], type='json', auth="public", methods=['POST'], website=True)
    def change_campaign(self, order, campaign_id, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        if campaign_id != '':
            campaign = request.env['marketing.campaign'].search([('id', '=', int(campaign_id))])
            order.write({
                'campaign': campaign.id,
            })
        else:
            order.write({
                'campaign': None,
            })
        return 'campaign_changed'

    @http.route(['/crm/repord/deliverydate'], type='json', auth="public", methods=['POST'], website=True)
    def change_delivery_date(self, order, date_order, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        order.write({
            'date_order': date_order,
        })
        return 'delivery_date_changed'

    @http.route(['/crm/repord/confirm'], type='json', auth="public", methods=['POST'], website=True)
    def order_confirm(self, order, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        order.action_convert_to_sale_order()
        return 'repord_confirmed'

    # store list
    @http.route(['/crm/mystores'], type='http', auth="public", website=True)
    def mystores(self, **post):
        my_stores = request.env['res.partner'].search([('is_company', '=', True), ('customer', '=', True), ('user_id', '=', request.env.uid)], order='store_class, name')
        my_coops = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_coop.coop'))
        my_icas = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_ica.ica_gruppen'))
        my_axfoods = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_axfood.axfood_group'))
        return request.website.render("crm_repord.mystores", {'my_coops': my_coops, 'my_icas': my_icas, 'my_axfoods': my_axfoods,})

    @http.route(['/crm/search/stores'], type='http', auth="public", website=True)
    def search_stores(self, **post):
        if request.httprequest.method == 'POST':
            search_words = post.get('search_words').split(' ')
            if len(search_words) > 0:
                word = search_words[0]
                partners = request.env['res.partner'].search(['|','|',('name','ilike', word),('street','ilike',word),('city','ilike',word)], order='store_class, name')
                partners = partners.filtered(lambda p: p.is_company == True and p.customer == True)
                for w in search_words[1:]:
                    partners = partners.filtered(lambda p: (w.lower() in p.name.lower()) or (w.lower() in p.street.lower() if p.street else '') or (w.lower() in p.city.lower() if p.city else ''))
                #~ partners.sorted(lambda p: p.name and p.store_class)
                partners = partners.filtered(lambda p: not 'Maxi Special' in p.name)
                return request.website.render("crm_repord.search_result", {'partners': partners, 'search_words': ' '.join(search_words)})
            else:
                return request.website.render("crm_repord.search_stores", {})
        else:
            return request.website.render("crm_repord.search_stores", {})

class rep_order(models.Model):
    _name = "rep.order"
    _inherit = "sale.order"
    _description = "Representative Order"

    @api.multi
    @api.depends('order_line', 'order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _repord_amount_all_wrapper(self):
        values = self._amount_all_wrapper(None, None)
        _logger.warn(values)
        for order in self:
            order.amount_untaxed = values.get(order.id, {}).get('amount_untaxed', 0)
            order.amount_tax = values.get(order.id, {}).get('amount_tax', 0)
            order.amount_total = values.get(order.id, {}).get('amount_total', 0)

    #state = fields.Selection(selection_add = [('reminder', 'Reminder')])
    order_type = fields.Selection([('scrap','Scrap'),('order','Order'),('reminder','Reminder'),('discount','Discount'),('direct','Direct')],default='order',string="Order Type",)
    order_line = fields.One2many('rep.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True)
    order_id = fields.Many2one('sale.order', 'Sale Order')
    amount_untaxed = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    amount_tax = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    amount_total = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    invoice_ids = None
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    procurement_group_id = None
    campaign = fields.Many2one(comodel_name='marketing.campaign', string='Campaign')

    @api.one
    def action_view_sale_order_line_make_invoice(self):
        pass

    @api.v7
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(rep_order, self).onchange_partner_id(cr, uid, ids, part, context)
        if not part:
            return res
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        if part.property_product_pricelist and part.property_product_pricelist.id != self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'list0')[1]:
            res['value']['pricelist_id'] = part.property_product_pricelist.id
        else:
            res['value']['pricelist_id'] = part.parent_id.property_product_pricelist.id
        return res

    @api.one
    def action_convert_to_sale_order(self):
        if self.order_type in ['order', 'direct'] and self.state == 'draft':
            order  = self.env['sale.order'].create({
                'name': '/',
                'rep_order_id': self.id,
                'partner_id': self.partner_id.id if self.order_type in ['order', 'direct'] else self.partner_id.parent_id.id,
                'pricelist_id': self.pricelist_id.id,
                'campaign': self.campaign.id,
                'project_id': self.campaign.account_id.id if self.campaign.account_id else None,
                'client_order_ref': self.name,
                'route_id': self.env.ref('edi_gs1.route_esap20').id if self.order_type == 'order' else None,
                'nad_by': self.partner_id.id if self.order_type == 'order' else None,
                'nad_su': self.env.ref('base.main_partner').id if self.order_type == 'order' else None,
                'unb_sender': self.env.ref('base.main_partner').id if self.order_type == 'order' else None,
                'unb_recipient': self.partner_id.parent_id.id if self.order_type == 'order' else None,
                'order_line': [(0, 0, {
                    'name': l.name,
                    'product_id': l.product_id and l.product_id.id or None,
                    'product_uom_qty': l.product_uom_qty,
                    'product_uom': l.product_uom.id,
                    'price_unit': l.price_unit,
                    'tax_id': [(6, 0, [t.id for t in l.tax_id and l.tax_id or []])],
                    'discount': l.discount,
                }) for l in self.order_line],
            })
            self.state = 'progress'
            self.order_id = order.id
            #~ order.action_button_confirm()
        else:
            self.state = 'sent'

    @api.one
    def action_repord_done(self):
        self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_id(self.env.ref('crm_repord.sequence_repord').id) or '/'
        new_id = super(rep_order, self).create(vals)
        return new_id


class rep_order_line(models.Model):
    _name = "rep.order.line"
    _inherit = "sale.order.line"
    _description = "Representative Order Line"

    order_id = fields.Many2one('rep.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]})
    tax_id = fields.Many2many('account.tax', 'rep_order_tax', 'order_line_id', 'tax_id', string='Taxes', readonly=True, states={'draft': [('readonly', False)]})
    #Must overwrite invoice_lines, or invoice creation will cease to function!
    #Could quite possibly be true for other fields
    invoice_lines = None
    #Overwriting procurement_ids just to be safe. Don't need this for repord anyway.
    procurement_ids = None


