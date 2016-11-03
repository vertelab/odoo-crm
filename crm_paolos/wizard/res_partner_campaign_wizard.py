from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class res_partner_note_wizard(models.TransientModel):
    _name = 'res.partner.note.wizard'
    _description = 'Res Partner Note Wizard'

    memo = fields.Html(string='Note Content')
    partner_ids = fields.One2many(comodel_name='res.partner', compute='_get_partner_ids')
    stage_id = fields.Many2one(comodel_name='note.stage')
    tag_ids = fields.Many2many(string="Tags",comodel_name='note.tag')
    
    def _get_partner_ids(self):
        self.partner_ids = self._context.get('active_ids', [])

    @api.multi
    def create_note(self):
        for n in self:
            for p in n.partner_ids:
                n.env['note.note'].create({
                    'memo': n.memo,
                    'partner_id': p.id,
                    'tag_ids': [(6,0,[t.id for t in n.tag_ids])],
                    'message_follower_ids': [(6,0, [p.user_id.partner_id.id])] if p.user_id else None,
                })


class res_partner_campaign_wizard(models.TransientModel):
    _name = 'res.partner.campaign.wizard'
    _description = 'Res Partner Campaign Wizard'

    name = fields.Char(string='Name')
    partner_ids = fields.One2many(comodel_name='res.partner', compute='_get_partner_ids')
    description = fields.Text(string='Internal note')
    campaign_id = fields.Many2one(comodel_name='marketing.campaign', string='Campaign')

    def _get_partner_ids(self):
        self.partner_ids = self._context.get('active_ids', [])

    def _average_distribution(self, partners, budget):
        return budget / len(partners)

    def _procent_distribution(self, size, average_size, total_size, budget):
        if size == 0:
            size = average_size
        return size / total_size * budget

    @api.multi
    def create_campaign(self):
        for c in self:
            total_size = sum([p.size for p in c.partner_ids.filtered(lambda p: p.size > 0)])
            average_size = total_size / (len(c.partner_ids.filtered(lambda p: p.size > 0)) or 1)
            for p in c.partner_ids.filtered(lambda p: p.size == 0):
                total_size += average_size
            for p in c.partner_ids:
                c.env['crm.lead'].create({
                    'name': '[' + c.name + '] - ' + p.name,
                    'email_from': p.email,
                    'phone': p.phone,
                    'partner_id': p.id,
                    'campaign': c.campaign_id.id,
                    'description': c.description,
                    'planned_revenue': self._average_distribution(c.partner_ids, c.campaign_id.campaign_budget) if c.campaign_id.distribution == 'evenly' or total_size == 0 else self._procent_distribution(p.size, average_size, total_size, c.campaign_id.campaign_budget),
                    'type': 'opportunity',
                })
