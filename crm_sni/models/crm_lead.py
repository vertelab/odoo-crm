from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sni_ids = fields.Many2many(comodel_name='res.sni', string='SNI')
    sni_id = fields.Many2one(comodel_name='res.sni', string="Primary SNI")
