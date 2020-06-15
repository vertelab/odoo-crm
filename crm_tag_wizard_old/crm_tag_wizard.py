# -*- coding: utf-8 -*-
from odoo import api, fields, models

class crm_tag_wizard(models.TransientModel):
    _name = 'crm.tag.wizard'
    _description = 'Create Wondertags'

    @api.model
    def _default_lead_ids(self):
        return self._context.get('active_ids')
    lead_ids = fields.Many2many(comodel_name='crm.lead', default=_default_lead_ids)
    tag_ids = fields.Many2many(comodel_name='crm.lead.tag', string='Tag', required=True)

    @api.multi
    def action_tag_apply(self):
        
        for lead in self.lead_ids:
            for tag in self.tag_ids:
                lead.tag_ids = [(4, tag.id, 0)]
        action = self.env.ref('crm.crm_lead_all_leads').read()[0]
        # ~ action.update({'res_id': task.id, 'context': {'default_project_id': self.project_id.id, }})
        # ~ raise Warning(action)
        return action
