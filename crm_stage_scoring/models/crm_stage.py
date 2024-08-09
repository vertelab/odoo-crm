from odoo import models, fields, api
from odoo.exceptions import UserError

class Lead(models.Model):
        
    _inherit = "crm.stage" 
    _description = 'Add manual_percentage field'

    manual_probability = fields.Float("Manual Precentage")
    is_zero_stage = fields.Boolean("Zero Stage")

    @api.onchange('is_won', 'is_zero_stage')
    def _reset_zero_and_won(self):

        for stage in self:

            if stage.is_won and stage.is_zero_stage:

                raise UserError("A stage can't be both zero and won at the same time!")