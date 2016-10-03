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
import time
import logging
import base64
import werkzeug
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)
from openerp.exceptions import Warning

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
    repord_3p_supplier = fields.Boolean('Handle reporders for this partner')

class res_partner_listing(models.Model):
    _name = 'res.partner.listing'

    name = fields.Char(string='Name')
    product_ids = fields.Many2many(comodel_name='product.product', string='Products')

class MobileSaleView(http.Controller):
    @http.route(['/crm/<model("res.partner"):partner>/repord'], type='http', auth="user", website=True)
    def repord(self, partner=None, **post):
        products = request.env['res.partner'].browse(partner.id).product_ids
        parent_products = request.env['res.partner'].browse(partner.id).listing_id.product_ids
        rep_order = request.env['rep.order'].search([('partner_id', '=', partner.id), ('state', '=', 'draft')])
        if not rep_order:
            rep_order = request.env['rep.order'].create({
                'partner_id': partner.id
            })
        else:
            rep_order = rep_order[0]
        return request.website.render("crm_repord.mobile_order_view", {'partner': partner, 'products': products, 'parent_products': parent_products, 'order': rep_order,})

    @http.route(['/crm/<model("res.partner"):partner>/image_upload'], type='http', auth="user", website=True)
    def image_upload(self, partner=None, **post):
        if request.httprequest.method == 'POST':
            if post['ufile']:
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
        return werkzeug.utils.redirect('/crm/%s/repord' %partner.id, 302)

    @http.route(['/crm/delete/image'], type='json', auth="user", website=True)
    def image_delete(self, attachment_id=None, **kw):
        image = request.env['ir.attachment'].browse(int(attachment_id))
        image.unlink()
        return 'image_deleted'

    @http.route(['/crm/send/repord'], type='json', auth="user", methods=['POST'], website=True)
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

    @http.route(['/crm/add/product'], type='json', auth="user", methods=['POST'], website=True)
    def add_product(self, res_partner, product_id, **kw):
        partner = request.env['res.partner'].search([('id', '=', int(res_partner))])
        for p in partner.listing_id.product_ids:
            if int(product_id) != p.id:
                partner.write({
                    'product_ids': [(4, int(product_id), 0)]
                })
        return 'added'

    @http.route(['/crm/remove/product'], type='json', auth="user", methods=['POST'], website=True)
    def remove_product(self, res_partner, product_id, **kw):
        partner = request.env['res.partner'].search([('id', '=', int(res_partner))])
        for p in partner.listing_id.product_ids:
            if int(product_id) == p.id:
                partner.write({
                    'product_ids': [(3, int(product_id), 0)]
                })
        return 'removed'

    @http.route(['/crm/todo/done'], type='json', auth="user", methods=['POST'], website=True)
    def todo_done(self, note_id, **kw):
        note = request.env['note.note'].search(['&', '&', ('id', '=', int(note_id)), ('open', '=', True), ('stage_id', '!=', request.env.ref('note.note_stage_04').id)])
        note.write({
            'open': False,
            'stage_id': request.env.ref('note.note_stage_04').id,
            'date_done': datetime.date.today(),
        })
        return 'note_done'

    @http.route(['/crm/meeting/visited'], type='json', auth="user", methods=['POST'], website=True)
    def customer_visited(self, partner_id, **kw):
        meetings = request.env['calendar.event'].search([])
        partner = request.env['res.partner'].search([('id', '=', int(partner_id))])
        for m in meetings:
            if partner in m.partner_ids:
                m.write({
                    'categ_ids': [(4, request.env.ref('crm_repord.categ_meet6').id, _)],
                })
        return 'meeting_done'

    @http.route(['/crm/presentation/done'], type='json', auth="user", methods=['POST'], website=True)
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

    @http.route(['/crm/repord/type'], type='json', auth="user", methods=['POST'], website=True)
    def change_order_type(self, order, order_type, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        order.write({
            'order_type': order_type,
        })
        return 'order_type_changed'

    @http.route(['/crm/repord/campaign'], type='json', auth="user", methods=['POST'], website=True)
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

    @http.route(['/crm/repord/deliverydate'], type='json', auth="user", methods=['POST'], website=True)
    def change_delivery_date(self, order, date_order, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        order.write({
            'date_order': date_order,
        })
        return 'delivery_date_changed'

    @http.route(['/crm/repord/confirm'], type='json', auth="user", methods=['POST'], website=True)
    def order_confirm(self, order, send_mail, **kw):
        order = request.env['rep.order'].search([('id', '=', int(order))])
        if send_mail == True:
            if not order.partner_id.email:
                return 'no_email'
            else:
                order.force_quotation_send()
        order.action_convert_to_sale_order()
        return 'repord_confirmed'

    # store list
    @http.route(['/crm/mystores'], type='http', auth="user", website=True)
    def mystores(self, **post):
        my_stores = request.env['res.partner'].search([('is_company', '=', True), ('customer', '=', True), ('user_id', '=', request.env.uid)], order='store_class, name')
        my_coops = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_coop.coop'))
        my_icas = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_ica.ica_gruppen'))
        my_axfoods = my_stores.filtered(lambda s: s.parent_id == request.env.ref('edi_gs1_axfood.axfood_group'))
        return request.website.render("crm_repord.mystores", {'my_coops': my_coops, 'my_icas': my_icas, 'my_axfoods': my_axfoods,})

    @http.route(['/crm/search/stores'], type='http', auth="user", website=True)
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

    @http.route(['/crm/<model("res.partner"):partner>/store_info_update'], type='http', auth="user", website=True)
    def store_info_update(self, partner=None, **post):
        if request.httprequest.method == 'POST':
            partner.write({
                'name': post['name'],
                'gs1_gln': post['gs1_gln'],
                'phone': post['phone'],
                'mobile': post['mobile'],
                'email': post['email'],
                'ref': post['ref'],
                'street': post['street'],
                'zip': post['zip'],
                'city': post['city'],
                'store_class': post['store_class'],
                'size': post['size'],
            })
            return werkzeug.utils.redirect('/crm/%s/repord' % partner.id, 302)
        return request.website.render("crm_repord.store_info_update", {'partner': partner})

    @http.route([
        '/crm/<model("res.partner"):partner>/company',
        '/crm/<model("res.partner"):partner>/company/edit',
    ], type='http', auth="user", website=True)
    def company_info_update(self, partner=None, **post):
        model = 'res.partner'
        fields =  ['name','store_class','size','vat','email','phone']
        if request.httprequest.url[-4:] == 'edit': #Edit
            if request.httprequest.method == 'GET':
                return request.render('crm_repord.company_detail', {'model': model, 'object': partner, 'fields': fields, 'title': partner.name ,'mode': 'edit'})
            else:
                partner.write({ f: post.get(f) for f in fields })
                return werkzeug.utils.redirect('/crm/%s/repord' % partner.id, 302)
        return request.render('crm_repord.company_detail', {'model': model, 'object': partner, 'fields': fields, 'title': partner.name , 'mode': 'view'})


    @http.route([
        '/crm/<model("res.partner"):partner>/contact',
        '/crm/<model("res.partner"):partner>/contact/edit',
        '/crm/<model("res.partner"):partner>/contact/add',
        '/crm/<model("res.partner"):partner>/contact/delete',
    ], type='http', auth="user", website=True)
    def contact_info_update(self, partner=None, **post):
        model = 'res.partner'
        fields =  ['name','phone','email','type']
        if request.httprequest.url[-4:] == 'edit': #Edit
            if request.httprequest.method == 'GET':
                return request.render('crm_repord.object_detail', {'model': model, 'object': partner, 'partner': partner.parent_id, 'fields': fields, 'title': partner.name ,'mode': 'edit'})
            else:
                partner.write({ f: post.get(f) for f in fields })
                return request.render('crm_repord.object_detail', {'model': model, 'object': partner, 'partner': partner.parent_id, 'fields': fields, 'title': partner.name , 'mode': 'view'})
        elif request.httprequest.url[-3:] == 'add': #Add
            if request.httprequest.method == 'GET':
                return request.render('crm_repord.object_detail', {'model': model, 'object': None, 'partner': partner.parent_id, 'fields': fields, 'title': partner.name , 'mode': 'add'})
            else:
                partner = request.env['res.partner'].create({ f: post.get(f) for f in fields })
                return request.render('crm_repord.object_detail', {'model': model, 'object': partner, 'partner': partner.parent_id, 'fields': fields, 'title': partner.name , 'mode': 'view'})
        elif request.httprequest.url[-6:] == 'delete': #Delete
            if partner:
                partner.unlink()
                return werkzeug.utils.redirect('/crm/%s/repord' % partner.parent_id.id, 302)
        return request.render('crm_repord.object_detail', {'model': model, 'object': partner, 'partner': partner.parent_id, 'fields': fields, 'title': partner.name , 'mode': 'view'})

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
    order_type = fields.Selection([('scrap', 'Scrap'), ('order', 'Order'), ('reminder', 'Reminder'), ('discount', 'Discount'), ('direct', 'Direct'), ('3rd_party', 'Third Party Order')], default='order', string="Order Type")
    order_line = fields.One2many('rep.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True)
    order_id = fields.Many2one('sale.order', 'Sale Order')
    amount_untaxed = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    amount_tax = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    amount_total = fields.Float(compute='_repord_amount_all_wrapper', digits=dp.get_precision('Account'), store=True)
    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Invoice')
    invoice_ids = None
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    amount_discount = fields.Float(compute='_amount_discount', string='Total Discount')
    procurement_group_id = None
    campaign = fields.Many2one(comodel_name='marketing.campaign', string='Campaign')

    third_party_supplier = fields.Many2one('res.partner', 'Third Party Supplier', compute='repord_set_3p_supplier', store=True, readonly=False)

    @api.one
    @api.depends('order_type', 'order_line', 'order_line.product_id')
    def repord_set_3p_supplier(self):
        if self.order_type == '3rd_party':
            for line in self.order_line:
                if line.product_id and line.product_id.categ_id and line.product_id.categ_id.repord_3p_supplier:
                    self.third_party_supplier = line.product_id.categ_id.repord_3p_supplier
                    return
        self.third_party_supplier = None

    @api.one
    def action_view_sale_order_line_make_invoice(self):
        pass

    @api.one
    def _amount_discount(self):
        self.amount_discount = sum((l.price_unit - l.price_reduce) * l.product_uom_qty for l in self.order_line)

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
        #Fix line numbers
        sequence = 1
        for line in self.order_line:
            line.sequence = sequence
            sequence += 1
        if self.order_type in ['direct'] and self.state == 'draft':
            order  = self.env['sale.order'].create({
                'name': '/',
                'rep_order_id': self.id,
                'partner_id': self.partner_id.id,
                'pricelist_id': self.pricelist_id.id,
                'campaign_id': self.campaign.id,
                'project_id': self.campaign.account_id.id if self.campaign.account_id else None,
                'order_line': [(0, 0, {
                    'sequence': l.sequence,
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

    @api.v7
    def action_quotation_send(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_repord', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'rep.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.v7
    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return self.pool['report'].get_action(cr, uid, ids, 'crm_repord.report_reporder', context=context)

    @api.model
    def action_invoice_create(self, orders, grouped=False, date_invoice=False):
        invoices = {}
        partner_currency = {}
        res = False
        for o in self.browse(orders):
            currency_id = o.pricelist_id.currency_id.id
            if (o.partner_id.id in partner_currency) and (partner_currency[o.partner_id.id] <> currency_id):
                raise Warning('Error! You cannot group sales having different currencies for the same partner.')
            partner_currency[o.partner_id.id] = currency_id
            #if repord type is scrap or discount. make supplier invoices from each order line
            if o.order_type in ['scrap', 'discount']:
                lines = []
                for line in o.order_line:
                    if line.invoiced:
                        continue
                    elif (line.state in ['draft', 'confirmed', 'done', 'exception']):
                        lines.append(line.id)
                created_lines = self.pool.get('rep.order.line').invoice_line_create(self._cr, self._uid, lines, context=self._context)
                if created_lines:
                    invoices.setdefault(o.partner_invoice_id.id or o.partner_id.id, []).append((o, created_lines))
            #if reporder type is order or reminder. make supplier invoices from order. order line will be total discount from the orders
            elif o.order_type in ['order', 'reminder']:
                discount_product = o.env.ref('crm_repord.discount_product')
                created_lines = []
                created_lines.append(self.env['account.invoice.line'].create({
                    #~ 'product_id': discount_product.id or False,
                    'name': discount_product.name % o.name,
                    'quantity': 1,
                    'account_id': discount_product.property_account_expense.id,
                    'price_unit': o.amount_discount,
                    'invoice_line_tax_id': [(6, 0, [discount_product.supplier_taxes_id.id])],
                }).id)
                if created_lines:
                    invoices.setdefault(o.partner_invoice_id.id or o.partner_id.id, []).append((o, created_lines))
            elif o.order_type in ['direct', '3rd_party']:
                raise Warning('Error! You cannot create invoice for a direct order.')
        for val in invoices.values():
            if grouped:
                res = self.pool.get('rep.order')._make_invoice(self._cr, self._uid, val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []), context=self._context)
                invoice_ref = ''
                origin_ref = ''
                for o, l in val:
                    invoice_ref += (o.client_order_ref or o.name) + '|'
                    origin_ref += (o.origin or o.name) + '|'
                    o.write({'state': 'progress', 'invoice_id': res})
                #remove last '|' in invoice_ref
                if len(invoice_ref) >= 1:
                    invoice_ref = invoice_ref[:-1]
                if len(origin_ref) >= 1:
                    origin_ref = origin_ref[:-1]
                invoice = self.env['account.invoice'].browse(res)
                invoice.write({'origin': origin_ref, 'name': invoice_ref, 'type': 'in_invoice'})
            else:
                for o, l in val:
                    res = self.pool.get('rep.order')._make_invoice(self._cr, self._uid, o, l, context=self._context)
                    o.write({'state': 'progress', 'invoice_id': res})
                    invoice = self.env['account.invoice'].browse(res)
                    invoice.write({'type': 'in_invoice'})
        return res

    @api.v7
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}
        invoiced_sale_line_ids = self.pool.get('rep.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('rep.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        #~ for preinv in order.invoice_ids:
            #~ if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                #~ for preline in preinv.invoice_line:
                    #~ inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    #~ lines.append(inv_line_id)
        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id


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

class product_category(models.Model):
    _inherit = 'product.category'

    repord_3p_supplier = fields.Many2one('res.partner', 'Resell for', inverse='_repord_set_3p_supplier', readonly=False, domain=[('repord_3p_supplier', '=', True)])

    @api.one
    def _repord_set_3p_supplier(self):
        for category in self.child_id:
            category.repord_3p_supplier = self.repord_3p_supplier

