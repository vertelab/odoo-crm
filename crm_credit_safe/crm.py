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

#TODO: Dela upp Credit Safe och BNI, SNI
#TODO: related-fält t ex vd-Namn -> kontaktperson, org_nr -> company_registry
#TODO: koncernbolag boolean  Ja/Nej -> computed field

class crm_lead(models.Model):
    _inherit = 'crm.lead'

    org_nr = fields.Char(string='Orgnr')
    bolagsform = fields.Char(string="Bolagdsform")
    kontor = fields.Char(string="Kontor")
    koncernbolag = fields.Boolean(string="Koncernbolag")
    reg_datum = fields.Date(string="Reg.Datum")
    vd_namn = fields.Char(string="VD Namn")
    branschkod = fields.Char(string="Branschkod")
    ant_anst_ab = fields.Integer(string="Antal Abst, AB")
    oms_intervall_scb = fields.Char(string="Oms. Intervall, SCB")
    resultat_fore_skatt = fields.Char(string="Resultat före skatt")

class res_partner(models.Model):
    _inherit = 'res.partner'

    is_bni = fields.Boolean(string="Is BNI")
    bni_state = fields.Selection([('member','Medlem'),('first','Första utbild'),('second','Andra utbild'),('former','Fd',)],string="BNI Status",  track_visibility='onchange')
    bni_partner = fields.Boolean(string="BNI Affärspartner", track_visibility='onchange',)
    bni_mentor = fields.Many2one(comodel_name='res.partner',string="BNI Mentor",  track_visibility='onchange')
    
    branschkod = fields.Char(string="Branschkod")
    ant_anst_ab = fields.Integer(string="Antal Anst, AB")
    oms_intervall_scb = fields.Char(string="Oms. Intervall, SCB")
