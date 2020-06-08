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


class insurance_permission(models.Model):
    _name = 'insurance.permission'
    
    name = fields.Char(string="Name")
    
class insurance_license(models.Model):
    _name = 'insurance.license'
    
    name = fields.Char(string="Name")

class res_partner(models.Model):
    _inherit = 'res.partner'

    is_fellowship = fields.Boolean(string='Fellowship', default=False, help='This is fellowship of companies.')
    # ~ is_company = fields.Boolean(string='Company', default=False, help='This is a companies')
    is_accommodator = fields.Boolean(string='Accommodator', default=False, help='This is an accommodator')
    liability_insurance = fields.Many2many(comodel_name='insurance.license', string='Insurance License')
    liability_insurance_permission = fields.Many2many(comodel_name='insurance.permission', string='Insurance Permission')
    
    # ~ have_life_insurance = fields.Boolean(string='Life Insurance', default=False, help='This is life insurance')
    # ~ have_property_insurance=fields.Boolean(string='Property Insurance', default=False, help='This is property insurance')
    # ~ insurance_permission_ids = fields.Many2many(comodel_name='res.partner', string='Permission')
    membership_ids = fields.Many2many(comodel_name='res.partner', relation='partner_member_rel', column1='parent_id',column2='member_id', string='Membership ID')
    count_fellowship = fields.Integer(string='Fellowship', compute ='_compute_count_fellowship')
    count_accommodator = fields.Integer(string='Accommodators', compute ='_compute_count_accommodator')
    count_life_insurance = fields.Integer(string='Life Insurance', compute ='_compute_count_life_insurance')
    count_property_insurance = fields.Integer(string='Property Insurance', compute ='_compute_count_property_insurance')
    count_life_protperty_insurance = fields.Integer(string='Life/Property Insurance', compute ='_compute_life_protperty_insurance')
    vat = fields.Char(string='Tax ID', help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    personnumber = fields.Char(string='Person Number', help="This is person number")
    org_prn = fields.Char(string="Org/Person Number", compute ='_compute_org_prn')
    # ~ company_type = fields.Selection(selection_add=[('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')])
    url_financial_supervisory = fields.Text(string = 'Finansinspektionen')
    
    @api.one
    def _compute_org_prn(self):
        if self.company_type == 'company':
            self.org_prn = self.vat
        elif self.company_type == 'person':
            self.org_prn = self.personnumber
            
    def _compute_count_fellowship(self):
        self.count_fellowship = self.env['res.partner'].search_count([('id', 'child_of', self.id),('is_fellowship', '=', True)])
    
    def _compute_count_accommodator(self):
        self.count_accommodator = self.env['res.partner'].search_count([('id', 'child_of', self.id),('is_accommodator', '=', True)])
    
    def _compute_count_life_insurance(self):
        self.count_life_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_life').id)])
    
    def _compute_count_property_insurance(self):
        self.count_property_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_property').id)])
    
    def _compute_life_protperty_insurance(self):
        self.count_life_protperty_insurance = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_life').id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_property').id)])
        
    def _compute_count_life_permission(self):
        self.count_life_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_life_permission').id)])
    
    def _compute_count_property_permission(self):
        self.count_property_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_property_permission').id)])
    
    def _compute_life_protperty_permission(self):
        self.count_life_protperty_insurance_permission = self.env['res.partner'].search_count([('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_life_permission').id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_property_permission').id)])
        
    @api.multi
    def fellowship_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('is_fellowship', '=', True)]
        return action
    
    @api.multi
    def accommodator_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('is_accommodator', '=', True)]
        return action
    
    @api.multi
    def life_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_life').id)]
        return action
        
    @api.multi
    def property_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_property').id)]
        return action
        
    @api.multi
    def life_protperty_insurance_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_life').id),('liability_insurance', '=', self.env.ref('crm_insurance.crm_insurance_property').id)]
        return action
        
    @api.multi
    def life_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_life_permission').id)]
        return action
        
    @api.multi
    def property_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_property_permission').id)]
        return action
        
    @api.multi
    def life_protperty_permission_button(self):
        partner_ids = self.ids
        partner_ids.append(self.env.user.partner_id.id)
        action = self.env['ir.actions.act_window'].for_xml_id('contacts', 'action_contacts')
        action['context'] = {
            'default_partner_ids': partner_ids,
        }
        action['domain'] = [('id', 'child_of', self.id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_life_permission').id),('liability_insurance_permission', '=', self.env.ref('crm_insurance.crm_insurance_property_permission').id)]
        return action
        
        
        

    
    # ~ company_type = fields.Selection(selection_add=[('fellowship', 'Fellowship'), ('accommodator', 'Accommodator')])
    # ~ fellowship_id = fields.Many2one('res.fellowship', 'Fellowship', index=True, default=_default_fellowship)
    # ~ company_type = fields.Selection(string='Company Type',
        # ~ selection=[('person', 'Individual'), ('company', 'Company')],
        # ~ compute='_compute_company_type', inverse='_write_company_type')
    #TODO: Added selection options show in the selection field but can not be clicked. 
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
    
    
    
    # ~ accommodator_ids = fields.Many2many(comodel_name='res.partner', relation='partner_accommodator_rel', column1='parent_id',column2='accommodator_id',domain='[("parent_id", "=", self.id)]', context='{"default_is_accommodator": True}')
    
    

    
    # ~ company_ids = fields.Many2many(comdoel_name='res.partner', realtion='partner_company_rel', column1='parent_id', column2='company_id', domain='[("parent_id", "=", self.id)]', context='{"default_is_company": True}')
    
    
    
    # ~ @api.multi
    # ~ def _compute_meeting_count(self):
        # ~ for partner in self:
            # ~ partner.meeting_count = len(partner.meeting_ids)
    # ~ meeting_ids = fields.Many2many('calendar.event', 'calendar_event_res_partner_rel', 'res_partner_id', 'calendar_event_id', string='Meetings', copy=False)
    # ~ meeting_count = fields.Integer("# Meetings", compute='_compute_meeting_count')
    
    #url_financial_supervisory = fields.Text(string = 'URL')
    

    # ~ revenue = fields.Float(string = 'Revenue')
    # ~ revenue_property = fields.Float(string = 'Revenue Property Insurance')
    # ~ revenue_life = fields.Float(string = 'Revenue Life Insurance')
    
    
# ~ class insurance_permissions(models.Model):
    # ~ _description = 'Permissions'
    # ~ _name = "res.insurance.permissions"
    # ~ _order = "display_name"
    
    # ~ date_entry = fields.Date(string='Date entry', required=True, index=True, help="Computed loggning membership")
    # ~ date_exit = fields.Date(string='Date exit', required=True, index=True, help="Computed membership")
    
    
    
class member(models.Model):
    _description = 'Member'
    _name = "res.member"
    _order = "display_name"
    
    active = fields.Boolean('Active', default=True)
    
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    # ~ parent_name = fields.Char(related='partner_id.name', readonly=True, string='Parent name')
    # ~ child_ids = fields.One2many('res.member', 'parent_id', string='Membership', domain=[('active', '=', True)])
    
    # ~ start_date = fields.Date(string='Start Date', required=True, index=True, help="Computed the date join membership")
    # ~ stop_date = fields.Date(string='Stop Date', required=True, index=True, help="Computed the date stop membmership")
    # ~ invoice_id = fields.Many2one(comodel_name = 'account.invoice', string='Invoice')
    
    
        


   
