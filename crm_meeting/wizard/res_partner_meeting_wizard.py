from openerp import models, fields, api, _

class res_partner_meeting_wizard(models.TransientModel):
    _name = 'res.partner.meeting.wizard'
    _description = 'Res Partner Meeting Wizard'

    description = fields.Text(string='Description')
    add_repord = fields.Boolean(string='Add link to repord')

    partner_ids = fields.One2many(comodel_name='res.partner', compute='_get_partner_ids')

    def _get_partner_ids(self):
        self.partner_ids = self._context.get('active_ids', [])

    @api.multi
    def create_meeting_summary(self):
        for r in self:
            for p in r.partner_ids:
                add_repord = r.add_repord and '%s/crm/%s/repord' % (self.env['ir.config_parameter'].get_param('web.base.url'),p.id) or ''
                self.env['calendar.event'].create({
                    'name': p.name,
                    'start_datetime': '2010-01-01 00:00:00',
                    'stop_datetime': '2010-01-01 00:00:00',
                    'allday': False,
                    'week_number': 'Undefined',
                    'weekday': 'friday',
                    'location': p.city,
                    'description': r.description + '\n' + add_repord if r.description else add_repord,
                    'partner_ids': [(6, 0, [p.user_id.partner_id.id if p.user_id else self.env['res.users'].browse(self.env.uid).partner_id.id, p.id])],
                    })
        return{
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_type': 'kanban',
            'view_mode': 'calendar,kanban,tree,form,gantt',
            #~ 'views': [(False, 'kanban')],
            #~ 'view_id': 'calendar_kanban.view_calendar_event_kanban',
            'target': 'current',
        }
