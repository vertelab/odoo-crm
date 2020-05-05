# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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

class res_partner(models.Model):
    _inherit = 'res.partner'

    is_fellowship = fields.Boolean(string = 'Fellowship', help = 'This is fellowship of companies.')
    # ~ is_company = fields.Boolean(string = 'Company', help = 'This is a companies')
    is_accommodator = fields.Boolean(string = 'Accommodator', help = 'This is an accommodator')
    have_liability_insurance = fields.Boolean(string = 'Liability insurance', help = 'true if the company have a liability insurance, else false')
    
    # ~ company_type = fields.Selection(selection_add=[('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')])
    
    # ~ company_type = fields.Selection(string='Company Type',
        # ~ selection=[('person', 'Individual'), ('company', 'Company'), ('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')],
        # ~ compute='_compute_insurance_company_type', inverse='_write_insurance_company_type')
        
    # ~ fellowship_id = fields.Many2one('res.fellowship', 'Fellowship', index=True, default=_default_fellowship)
    
    
    
    
    
    # ~ company_type = fields.Selection(string='Company Type',
        # ~ selection=[('person', 'Individual'), ('company', 'Company')],
        # ~ compute='_compute_company_type', inverse='_write_company_type')
        
    """@api.depends('is_company','is_fellowship','is_accommodator')
    def _compute_insurance_company_type(self):
        # ~ for partner in self:
            # ~ partner.company_type = 'company' if partner.is_company else 'person'
        # ~ raise Warning('Haze')
        for partner in self:
            if partner.is_company:
                partner.company_type = 'company'
            elif partner.is_fellowship:
                partner.company_type = 'fellowship'
            elif partner.is_accommodator:
                partner.company_type = 'accommodator'
            else:
                partner.company_type = 'person'
    #TODO does not work yet 
    def _write_insurance_company_type(self):
        raise Warning('Haze write')
        # ~ for partner in self:
            # ~ partner.is_company = partner.company_type == 'company'
        for partner in self:
            partner.is_company = (partner.company_type == 'company')
            partner.is_fellowship = (partner.company_type == 'fellowship')
            partner.is_accommodator = (partner.company_type == 'accommodator')
            
            

    @api.onchange('company_type')
    def onchange_insurance_company_type(self):
        # ~ self.is_company = (self.company_type == 'company')
        # ~ raise Warning('Haze onchange')
        self.is_company = (self.company_type == 'company')
        self.is_fellowship = (self.company_type == 'fellowship')
        self.is_accommodator = (self.company_type == 'accommodator')"""
        
    # ~ company_type = fields.Selection(selection_add=[('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')], 
    # ~ compute='_compute_insurance_company_type', inverse='_write_insurance_company_type')
    
    def _count_accommodator(self):
        self.count_accommodator = len(self.env['res.partner'].search([('parent_id', '=', self.id),('is_accommodator', '=', True)]))
        
    count_accommodator = fields.Integer(string = 'Count of accommodators',compute = '_count_accommodator')
    
    def _count_life_insurance(self):
        self.count_life_insurance = len(self.env['res.partner'].search([('parent_id', '=', self.id)]))
    count_life_insurance = fields.Integer(string = 'Count life insurance',compute = '_count_life_insurance')
    
    def _count_property_insurance(self):
        self.count_property_insurance = len(self.env['res.partner'].search([('parent_id', '=', self.id)]))
    count_property_insurance = fields.Integer(string = 'Count property insurance',compute = '_count_property_insurance')
        
    def _count_company(self):
        self.count_company = len(self.env['res.partner'].search([('parent_id', '=', self.id),('is_company','=', True)]))
    count_company = fields.Integer(string = 'Count company',compute = '_count_company') 
        
    
    # ~ date_entry = fields.Date(string='Date entry', required=True, help="Computed loggning membership")
    # ~ date_exit = fields.Date(string='Date exit', required=True, help="Computed membership")

