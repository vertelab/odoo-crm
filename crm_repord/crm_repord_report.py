# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution, third party addon
# Copyright (C) 2016- Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class crm_repord_report(models.Model):
    _name = "rep.order.report"
    _description = "Rep Order Statistics"
    _auto = False
    _rec_name = 'date'

    date = fields.Datetime(string='Date Created', readonly=True)
    date_confirm = fields.Datetime(string='Date Confirm', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product',string='Product', readonly=True)
    product_uom = fields.Many2one(comodel_name='product.uom', string='Unit of Measure', readonly=True)
    product_uom_qty = fields.Float(string='# of DFP', readonly=True)
    product_uom_kfp = fields.Float(string='# of KFP', readonly=True)

    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True)
    parent_id = fields.Many2one(comodel_name='res.partner', string='Parent', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', readonly=True)
    section_id = fields.Many2one(comodel_name='crm.case.section', string='Sales Team', readonly=True)
    price_total = fields.Float(string='Total Price', readonly=True)
    delay = fields.Float(string='Commitment Delay', digits=(16,2),readonly=True)
    categ_id = fields.Many2one(comodel_name="product.category",string='Category of Product',readonly=True)
    nbr = fields.Integer(string='# of Lines', readonly=True)
    state = fields.Selection([
            ('cancel', 'Cancelled'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('exception', 'Exception'),
            ('done', 'Done')], 'Order Status', readonly=True)
    pricelist_id = fields.Many2one(comodel_name="product.pricelist",string='Pricelist',readonly=True)
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account",string='Analytic Account',readonly=True)
            
        
    order_type = fields.Selection([('scrap', 'Scrap'), ('order', 'Order'), ('reminder', 'Reminder'), ('discount', 'Discount'), ('direct', 'Direct'), ('3rd_party', 'Third Party Order')], string="Order Type", readonly=True)
    order_id = fields.Many2one('sale.order', 'Sale Order',readonly=True)
#    amount_discount = fields.Float(string='Total Discount',digits=(16,2),readonly=True)
    campaign = fields.Many2one(comodel_name='marketing.campaign', string='Campaign',readonly=True)
    third_party_supplier = fields.Many2one('res.partner', 'Third Party Supplier',  readonly=True)
    
    role    =   fields.Char(string="Role",readonly=True)
    store_class = fields.Selection([('A', 'A'),('B', 'B'),('C', 'C'),('D', 'D'),('E', 'E')],string='Store Class',readonly=True)
    areg =      fields.Selection([
    ('1', u'Stockholm'),
    ('2', u'Norrtälje'),
    ('3', u'Enköping'),
    ('4', u'Uppsala'),
    ('5', u'Nyköping'),
    ('6', u'Katrineholm'),
    ('7', u'Eskilstuna'),
    ('8', u'Mjölby/Motala'),
    ('9', u'Linköping'),
    ('10', u'Norrköping'),
    ('11', u'Jönköping'),
    ('12', u'Tranås'),
    ('13', u'Eksjö/Nässjö/Vetlanda'),
    ('14', u'Värnamo'),
    ('15', u'Ljungby'),
    ('16', u'Växjö'),
    ('17', u'Västervik'),
    ('18', u'Hultsfred/Vimmerby'),
    ('19', u'Oskarshamn'),
    ('20', u'Kalmar/Nybro'),
    ('21', u'Visby'),
    ('22', u'Karlskrona'),
    ('23', u'Karlshamn'),
    ('24', u'Kristianstad'),
    ('25', u'Hässleholm'),
    ('26', u'Ängleholm'),
    ('27', u'Helsingborg/Landskrona'),
    ('28', u'Malmö/Lund/Trelleborg'),
    ('29', u'Ystad/Simrishamn'),
    ('30', u'Eslöv'),
    ('31', u'Halmstad'),
    ('32', u'Falkenberg/Varberg'),
    ('33', u'Göteborg'),
    ('34', u'Uddevalla'),
    ('35', u'Trollhättan/Vänersborg'),
    ('36', u'Borås'),
    ('37', u'Lidköping/Skara'),
    ('38', u'Falköping'),
    ('39', u'Skövde'),
    ('40', u'Mariestad'),
    ('41', u'Kristinehamn'),
    ('42', u'Karlstad'),
    ('43', u'Säffle/Åmål'),
    ('44', u'Arvika'),
    ('45', u'Örebro'),
    ('46', u'Karlskoga'),
    ('47', u'Lindesberg'),
    ('48', u'Västerås'),
    ('49', u'Köping'),
    ('50', u'Fagersta'),
    ('51', u'Sala'),
    ('52', u'Borlänge/Falun'),
    ('53', u'Avesta/Hedemora'),
    ('54', u'Ludvika'),
    ('55', u'Mora'),
    ('56', u'Gävle/Sandviken'),
    ('57', u'Bollnäs/Söderhamn'),
    ('58', u'Hudiksvall/Ljusdal'),
    ('59', u'Sundsvall'),
    ('60', u'Härnösand/Kramfors'),
    ('61', u'Sollefteå'),
    ('62', u'Örnsköldsvik'),
    ('63', u'Östersund'),
    ('64', u'Umeå'),
    ('65', u'Skellefteå'),
    ('66', u'Lycksele'),
    ('67', u'Piteå'),
    ('68', u'Luleå/Boden'),
    ('69', u'Haparanda/Kalix'),
    ('70', u'Kiruna/Gällivare'),
    ],
    string='Areg',
    readonly=True)
    rangebox =  fields.Char(string='Rangebox',readonly=True)
    zip      =  fields.Char(string='Zip',readonly=True)
    city     =  fields.Char(string='City',readonly=True)

    _order = 'date desc'

#~ (select count(*) from stock_pack_operation where picking_id = sp.id) as nbr_lines,
# sum(s.amount_discount) as amount_discount,
    def _select(self):
        select_str = """
        SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty / u.factor * u2.factor * pack.qty) as product_uom_kfp,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                    count(*) as nbr,
                    s.date_order as date,
                    s.date_confirm as date_confirm,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    l.state,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.section_id as section_id,
                    s.order_type as order_type,
                    s.order_id as order_id,
                    
                    s.campaign as campaign,
                    s.third_party_supplier as third_party_supplier,
                    s.role as role,
                    s.store_class as store_class,
                    s.areg as areg,
                    s.rangebox as rangebox,
                    s.zip as zip,
                    s.city as city
        """
        return select_str
    def _from(self):
        from_str = """
               rep_order_line  l
                      join rep_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_packaging pack on (pack.product_tmpl_id=t.id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
        """
        return from_str


    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.company_id,
                    l.state,
                    s.pricelist_id,
                    s.project_id,
                    s.section_id,
                    s.order_type,
                    s.order_id,
                    s.campaign,
                    s.third_party_supplier,
                    s.role,
                    s.store_class,
                    s.areg,
                    s.rangebox,
                    s.zip,
                    s.city
        """
        return group_by_str



    def init(self, cr):
        # self._table = sale_report
        #~ raise Warning("""CREATE or REPLACE VIEW %s as (
            #~ %s
            #~ FROM ( %s )
            #~ %s
            #~ )""" % (self._table, self._select(), self._from(), self._group_by()))
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
