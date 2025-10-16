# -*- coding: utf-8 -*-
from dateutil import tz as timezone
from odoo import api, fields, models
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
import datetime
import logging
import time

_logger = logging.getLogger(__name__)



class Lead(models.Model):
    _inherit = "crm.lead"

    def cron_monitor(self):
        today = fields.Date.today(self)
        for crm in self.search([]):
            for monitor in crm._stage_id.stage_monitor_ids.filtered(lambda m: m.stage_id.id == crm.stage_id.id):
                crm_date = getattr(crm, monitor.trigger_date, None)
                if not crm_date:
                    continue
                # Convert task_date if it is string to date
                if isinstance(crm_date, str):
                    try:
                        crm_date = datetime.strptime(crm_date, '%Y-%m-%d').date()
                    except Exception as e:
                        _logger.warning(f"Failed to parse date {crm_date} for lead {crm.id}: {e}")
                        continue
                compare_date = crm_date + timedelta(days=monitor.trigger_days)
                #TODO We need a mecanism to do this just once and still catch up for old tasks or changes in monitor rules
                if today == compare_date:
                    monitor.monitor_trigger(crm)

    def action_monitor(self):
        today = fields.Date.today()
        for crm in self:
            for monitor in crm._stage_id.stage_monitor_ids.filtered(lambda m: m.stage_id.id == crm.stage_id.id):
                crm_date = getattr(crm, monitor.trigger_date, None)
                if not crm_date:
                    continue
                # Convert task_date if it is string to date
                if isinstance(crm_date, str):
                    try:
                        crm_date = datetime.strptime(crm_date, '%Y-%m-%d').date()
                    except Exception as e:
                        _logger.warning(f"Failed to parse date {crm_date} for lead {crm.id}: {e}")
                        continue
                compare_date = crm_date + timedelta(days=monitor.trigger_days)
                #TODO We need a mecanism to do this just once and still catch up for old tasks or changes in monitor rules
                if crm.stage_id.trigger_days > 0 and today >= compare_date:
                    monitor.monitor_trigger(crm)

    def write(self, vals):
        result = super().write(vals)
        if 'stage_id' in vals:
            for crm in self:
                crm.stage_id.onchange_trigger(crm)
        return result
        
    
