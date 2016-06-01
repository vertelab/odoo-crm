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

    role = fields.Char(string="Role",help="Chain or type of shop", select=True)
    store_class = fields.Selection([('A', 'A'),('B', 'B'),('C', 'C'),('D', 'D'),('E', 'E')], string='Store Class')
    areg = fields.Selection([
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
    ], string='Areg')
    size = fields.Float(string='Size')
    fsg_paolos = fields.Float(string=u'FSG PAOLOS')
    fsg_leroy = fields.Float(string=u'FSG LERÖY')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
