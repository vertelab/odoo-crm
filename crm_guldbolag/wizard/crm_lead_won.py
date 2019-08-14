# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadWon(models.TransientModel):
    _name = 'crm.lead.won'
    _description = 'Create Object'
    
    @api.model
    def _default_project_id(self):
        project_ids = self.env['project.project'].search([('label_tasks','=','objekt')])
        if len(project_ids)>0:
            return project_ids[0].id
    project_id = fields.Many2one(comodel_name='project.project', string='Object',domain="[('label_tasks','=','objekt')]",default=_default_project_id,required=True)
    @api.model
    def _default_lead_id(self):
        if self._context.get('active_model') == 'crm.lead':
            return self._context.get('active_id',None)
    lead_id = fields.Many2one(comodel_name='crm.lead', string='Opportunity',default=_default_lead_id)

    @api.multi
    def action_won_apply(self):
        tasks = self.env['project.task'].search([('lead_id','=',self.lead_id.id)])
        if len(tasks) > 0:
            task = tasks[0]
        else:
            tags = []
            for tag_name in self.lead_id.tag_ids.mapped('name'):
                tag = self.env['project.tags'].search([('name','=',tag_name)])
                if len(tag)>0:
                    tags.append(tag[0].id)
                else:
                    tags.append(self.env['project.tags'].create({'name': tag_name}).id)
            task = self.env['project.task'].create({
                 'name': self.lead_id.name,
                 'project_id': self.project_id.id,
                 'partner_id': self.lead_id.partner_id.id,
                 'region_id': self.lead_id.team_id.id,
                 'lead_id': self.lead_id.id,
                 'user_id': self.lead_id.user_id.id,
                 'expected_income': self.lead_id.planned_revenue,
                 'tag_ids': [(6,0,tags)] if tags else None,
                 # ~ 'industry_id': self.lead_id.industry_id,
                 })
        action = self.env.ref('project.action_view_task').read()[0]
        action.update({'res_id': task.id, 'context': {'default_project_id': self.project_id.id, }})
        # ~ raise Warning(action)
        return action
