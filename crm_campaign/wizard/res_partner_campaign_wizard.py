from openerp import models, fields, api, _

class res_partner_note_wizard(models.TransientModel):
    _name = 'res.partner.note.wizard'
    _description = 'Res Partner Note Wizard'

    memo = fields.Html(string='Note Content')
    partner_ids = fields.One2many(comodel_name='res.partner', compute='_get_partner_ids')

    def _get_partner_ids(self):
        self.partner_ids = self._context.get('active_ids', [])

    @api.multi
    def create_note(self):
        for n in self:
            for p in n.partner_ids:
                n.env['note.note'].create({
                    'memo': n.memo,
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

    @api.multi
    def create_campaign(self):
        for c in self:
            for p in c.partner_ids:
                c.env['crm.lead'].create({
                    'name': '[' + c.name + '] - ' + p.name,
                    'email_from': p.email,
                    'phone': p.phone,
                    'partner_id': p.id,
                    'campaign_id': c.campaign_id.id,
                    'description': c.description,
                    'type': 'opportunity',
                })
