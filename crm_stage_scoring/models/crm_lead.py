from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class Lead(models.Model):
        
    _inherit = "crm.lead" 
    _description = 'scaffold_test.scaffold_test'

    @api.depends(lambda self: ['stage_id', 'team_id'] + self._pls_get_safe_fields())
    def _compute_probabilities(self):
        lead_probabilities = self._pls_get_naive_bayes_probabilities()
        for lead in self:
            if lead.id in lead_probabilities:
                was_automated = lead.active and lead.is_automated_probability
                lead.automated_probability = lead_probabilities[lead.id]

                if lead.stage_id.is_zero_stage:
                    lead.probability = 0

                elif was_automated:
                    lead.probability = lead.automated_probability
                
                elif lead.stage_id.manual_probability:
                    lead.probability = lead.stage_id.manual_probability

    
