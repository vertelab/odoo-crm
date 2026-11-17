# -*- coding: utf-8 -*-
from dateutil import tz as timezone
from odoo import api, fields, models
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
import datetime
import logging
import time

_logger = logging.getLogger(__name__)

DEFAULT_CODE = """
# Available variables:
#  - env: environment on which the action is triggered
#  - crm: record on which the action is triggered
#  - stage: record on which the action is triggered
#  - self: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - _logger: _logger.info(message): logger to emit messages in server logs
#  - post_message: post_message('Message in chatter')
#  - UserError: exception class for raising user-facing warning messages
# To return an action, assign: action = {...}

"""

_logger = logging.getLogger(__name__)

def log(message, level="info", env=None):
    # Spara log i ir.logging-tabellen
    env = env or None
    if env:
        env['ir.logging'].create({
            'name': 'stage_code',
            'type': level,
            'dbname': env.cr.dbname,
            'level': level,
            'message': message,
            'path': 'crm.lead',
            'func': 'stage_code',
            'line': '0',
        })
    _logger.log(getattr(logging, level.upper(), logging.INFO), message)


class CrmStageMonitor(models.Model):
    _name = "crm.stage.monitor"
    _description = "CRM Stage Monitor"
    _order = "sequence desc"

    activity_type = fields.Many2one('mail.activity.type', string="Activity Type", help="")
    activity_user = fields.Selection(
        selection=[
            ('create_uid', 'Created by'),
            ('write_uid', 'Last Updated by'),
            ('team_id.user_id', 'Team Leader'),
            ('user_id', 'Sale Person'),
        ], 
        string='User'
    )
    code = fields.Text(string='Code', default=DEFAULT_CODE)
    esc_user = fields.Selection(
        selection=[
            ('create_uid', 'Created by'),
            ('write_uid', 'Last Updated by'),
            ('team_id.user_id', 'Team Leader'),
        ], 
        string='User'
    )
    message = fields.Char(string='Message')
    new_stage_id = fields.Many2one('project.task.type', string="New Stage", help="")
    sequence = fields.Integer(string='Sequence')
    stage_id = fields.Many2one('crm.stage', string="Stage", help="")
    summary = fields.Char(string='Summary', size=64)
    trigger_date = fields.Selection(
        selection=[
            ('date_open', 'Assignment Date'),
            ('create_date', 'Created On'),
            ('date_closed', 'Closed Date'),
            ('date_conversion', 'Conversion Date'),
            ('date_deadline', 'Deadline'),
            ('date_automation_last', 'Last Action'),
            ('date_last_stage_update', 'Last Stage Update'),
            ('remarkDate', 'Remark Date'),
            ('write_date', 'Last Updated On'),
        ], 
        string='Date'
    )
    trigger_days = fields.Integer(string='Days')
    trigger_type = fields.Selection(
        selection=[
            ('stage', 'Stage'),
            ('activity', 'Activity'),
            ('archive', 'Archive'),
            ('code', 'Code'),
            ('esc', 'Escalate'),
            ('message', 'Message'),
            ('unlink', 'Remove'),
        ], 
        string='Type'
    )

    @api.depends('trigger_days', 'trigger_type', 'activity_type', 'activity_user', 'summary', 'esc_user', 'message', 'new_stage_id', 'trigger_date')
    def _compute_trigger_info(self):
        for monitor in self:
            selection = dict(self.fields_get(allfields=['trigger_date'])['trigger_date']['selection'])
            display_value = selection.get(monitor.trigger_date, monitor.trigger_date or '')
            monitor.trigger_date_info = _(
                f"{abs(int(monitor.trigger_days)):>10} Days {'before' if monitor.trigger_days < 0 else 'after'} {display_value}"
            )
            if monitor.trigger_type == 'activity':
                monitor.trigger_info = _(f"{monitor.activity_type.name or ''} User {monitor.activity_user or ''} {monitor.summary or ''}".strip())
            elif monitor.trigger_type == 'esc':
                monitor.trigger_info = _(f"User {monitor.esc_user or ''}".strip())
            elif monitor.trigger_type == 'message':
                monitor.trigger_info = _(f"Message {monitor.message or ''}").strip()
            elif monitor.trigger_type == 'stage':
                monitor.trigger_info = monitor.new_stage_id.name or ''
            else:
                monitor.trigger_info = ''
    trigger_info = fields.Char(string='Info', size=20, trim=True, compute=_compute_trigger_info)
    trigger_date_info = fields.Char(string='Info', size=50, trim=True, compute=_compute_trigger_info)
    
    def monitor_trigger(self,crm):
        for monitor in self:
            if hasattr(stage, 'code') and monitor.code and monitor.trigger_type == 'code':
                self._execute_stage_code(monitor, crm)
            elif monitor.trigger_type == 'activity':
                user_id = getattr(crm, monitor.activity_user, None)
                if user_id:
                    self.env['mail.activity.schedule'].create({
                        'activity_type_id': monitor.trigger_activity_type.id,
                        'activity_user_id': user_id.id,
                        'summary': monitor.summary,
                        })
            elif monitor.trigger_type == 'esc':
                user_id = getattr(crm, monitor.esc_user, None)
                if user_id:
                    crm.user_id = user_id
            elif monitor.trigger_type == 'archive':
                crm.active = False
            elif monitor.trigger_type == 'unlink':
                crm.unlink()
            elif monitor.trigger_type == 'message':
                crm.message_post(body=monitor.message)
            elif monitor.trigger_type == 'stage':
                crm.stage_id = monitor.onchange_new_stage_id
                
 

class Stage(models.Model):
    _inherit = "crm.stage"

    stage_monitor_ids = fields.One2many(comodel_name='crm.stage.monitor', inverse_name='stage_id', string="Stage Monitor", help="")

    onchange_activity_type = fields.Many2one(
            comodel_name='mail.activity.type', 
            string="Activity Type", 
            help=""
        )
    onchange_activity_user = fields.Selection(
        selection=[
            ('create_uid', 'Created by'),
            ('write_uid', 'Last Updated by'),
            ('team_id.user_id', 'Team Leader'),
            ('user_id', 'Sale Person'),
        ], 
        string='User'
    )
    onchange_code = fields.Text(string='Code',default=DEFAULT_CODE)
    onchange_esc_user = fields.Selection(
            selection=[
                ('create_uid', 'Created by'),
                ('write_uid', 'Last Updated by'),
                ('team_id.user_id', 'Team Leader'),
            ], 
            string='User'
        )
    onchange_message = fields.Char(string='Message')
    onchange_new_stage_id = fields.Many2one(
            "project.task.type", 
            string="New Stage", 
            help=""
        )
    onchange_summary = fields.Char(string='Summary', size=64, trim=True)
    onchange_type = fields.Selection(
            selection=[
                ('stage', 'Stage'),
                ('activity', 'Activity'),
                ('archive', 'Archive'),
                ('code', 'Code'),
                ('esc', 'Escalate'),
                ('message', 'Message'),
                ('unlink', 'Remove'),
            ], 
            string='Type'
        )
        
    def _execute_stage_code(self,crm,code):
        for stage in self:
            if not code:
                return

            def post_message(body, **kwargs):
                """
                    Writes an entry in the chatter/log directly on the task.
                    Parameters:
                      - body: text for the message (str)
                      - subject, subtype_xmlid, message_type etc can be specified via kwargs.
                """
                task.message_post(body=body, **kwargs)

            local_ctx = {
                'env': self.env,
                'crm': crm,
                'stage': crm.stage_id,
                'self': self,
                'time': time,
                'datetime': datetime,
                'dateutil': timezone,
                'timezone': timezone,
                'log': lambda message, level='info': log(message, level, self.env),
                '_logger': _logger,
                'UserError': UserError,
                'post_message': post_message,
                'action': None,
            }

            try:
                _logger.debug(f"Before eval: {local_ctx=}")
                eval(code, {}, local_ctx)
                if local_ctx.get('action'):
                    return local_ctx['action']
            except Exception as e:
                _logger.error(f"Stage code execution failed: {e}")
                raise UserError(f"Error running code in stage: {e}")

    def onchange_trigger(self,crm):
        for stage in self:
            if hasattr(stage, 'code') and stage.onchage_code and stage.onchange_type == 'code':
                self._execute_stage_code(stage, crm,stage.onchange_code)
            elif stage.onchange_type == 'activity':
                user_id = getattr(crm, stage.onchange_activity_user, None)
                if user_id:
                    self.env['mail.activity.schedule'].create({
                        'activity_type_id': stage.onchange_activity_type.id,
                        'activity_user_id': user_id.id,
                        'summary': stage.onchage_summary,
                        })
            elif stage.onchange_type == 'esc':
                user_id = getattr(crm, stage.onchange_esc_user, None)
                if user_id:
                    crm.user_id = user_id
            elif stage.onchange_type == 'archive':
                crm.active = False
            elif stage.onchange_type == 'unlink':
                crm.unlink()
            elif stage.onchange_type == 'message':
                crm.message_post(body=stage.onchange_message)
            elif stage.onchange_type == 'stage':
                crm.stage_id = monitor.onchange_new_stage_id
