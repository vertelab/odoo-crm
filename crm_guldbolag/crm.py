# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2019 Vertel AB (<http://vertel.se>).
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
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    hogsta_vardetillvaxt = fields.Float(string = u"Högsta värdetillväxt")
    omsattnigstillvaxt = fields.Float(string = u"Omsättningstillväxt", help="Omsättningstillväxt föregående år")
    hogsta_rorelsemarginal = fields.Float(string = u"Högsta rörelsemarginal")
    hogst_avkastning = fields.Float(string = u"Högst avkastning")
    omsattning_per_anstalld = fields.Integer(string = u"Omsättning per anställd")
    resultat_per_anstalld = fields.Integer(string = u"Resultat per anställd")
    lon_per_anstalld = fields.Integer(strincg = u"Lön per anställd")
    nettoomsattning = fields.Integer(string = u"Nettoomsättning")
    antal_anstallda = fields.Integer(string = u"Antal anställda")
    
    @api.multi
    def merge_opportunity(self, user_id=False, team_id=False):
        from odoo.addons.crm.models.crm_lead import CRM_LEAD_FIELDS_TO_MERGE
        # ~ raise Warning(CRM_LEAD_FIELDS_TO_MERGE)
        CRM_LEAD_FIELDS_TO_MERGE += ['hogsta_vardetillvaxt', 'omsattnigstillvaxt', 'hogsta_rorelsemarginal',
        'hogst_avkastning', 'omsattning_per_anstalld', 'resultat_per_anstalld', 'nettoomsattning', 'antal_anstallda']
        return super(crm_lead, self).merge_opportunity(user_id, team_id)
        
        
        
