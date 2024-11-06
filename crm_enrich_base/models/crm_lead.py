from odoo import models, fields, api, _
from datetime import date
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    def crm_enrich(self):
        mro = self.__class__.__mro__
        _logger.warning(f'{self.__class__.__name__=}  {type(self).__mro__=}\n{mro=}')

        for crm in self:
            _logger.warning(f'crm_enrich_base {crm.name=}')
        if hasattr(super(CrmLead, self), 'crm_enrich'):
            super(CrmLead, self).crm_enrich()
        # ~ if hasattr(self.env['crm.lead'], 'crm_enrich'):
            # ~ super(CrmLead,self).crm_enrich()

        # ~ super(CrmLead,self).crm_enrich()
        
    @api.model
    def orgnr2vat(self,company_registry):
        if company_registry:
            return f"SE{company_registry.replace('-','')}01"
        else:
            return None
        
