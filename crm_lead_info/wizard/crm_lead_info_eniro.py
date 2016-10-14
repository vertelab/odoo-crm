from openerp import models, fields, api, _
import urllib2
import re
import logging
_logger = logging.getLogger(__name__)

class crm_lead_info_eniro_wizard(models.TransientModel):
    _name = 'crm.lead.info.eniro.wizard'
    _description = 'Export CRM-lead information from wizard'

    company_registries = fields.Char(string='Company Registries')
    categ_ids = fields.Many2many(comodel_name='crm.case.categ', string='Categories')

    @api.multi
    def create_crm_leads(self):
        api_profile = self.env['ir.config_parameter'].sudo().get_param('eniro_api_profile')
        api_key = self.env['ir.config_parameter'].sudo().get_param('eniro_api_key')
        if not (api_key or api_profile):
            raise Warning('Please configurate Eniro api account')

        leads = self.env['crm.lead'].search([])
        regs = [l.company_registry_no for l in leads]

        if len(self.company_registries) > 0:
            for reg in self.company_registries.split(','):
                if reg not in regs:
                    try:
                        res = urllib2.urlopen('http://api.eniro.com/partnerapi/cs/search/basic?profile=%s&key=%s&country=se&version=1.1.3&search_word=%s' % (api_profile, api_key, reg)).read()
                        (true,false,null) = (True,False,None)
                    except urllib2.HTTPError as e:
                        _logger.error('api.eniro error: %s %s' % (e.code, e.reason))
                        if e.code == 401:
                            _logger.error('Eniro API %s %s (wrong profile/key)' % (e.code, e.reason))
                            raise Warning('Eniro API %s %s (wrong profile/key)' % (e.code, e.reason))
                        return False
                    except urllib2.URLError as e:
                        _logger.error('api.eniro url error: %s %s' % (e.code, e.reason))
                        return False

                    json = eval(res)
                    #~ _logger.info('<<<<<< API Eniro Result: %s >>>>>' % json)

                    if not json or len(json['adverts']) == 0 or json['totalHits'] == 0:
                        return False

                    adverts = json['adverts'][json['totalHits']-1]
                    #~ _logger.debug('<<<<<< Adverts: %s >>>>>' % adverts)
                    companyInfo = adverts['companyInfo']
                    address = adverts['address']
                    phoneNumbers = adverts['phoneNumbers']

                    lead_info = {
                        'name': companyInfo['companyName'],
                        'partner_name': companyInfo['companyName'],
                        'company_registry_no': reg,
                        'street': address['streetName'],
                        'street2': address['postBox'] or '',
                        'zip': address['postCode'],
                        'city': address['postArea'],
                        'phone': [pn['phoneNumber'] for pn in phoneNumbers if pn['type'] == 'std'][0] if len(phoneNumbers)>0 else '',
                        'country_id': self.env['res.country'].search([('code','=','SE')])[0].id,
                        'categ_ids': [(6, 0, [c.id for c in self.categ_ids])],
                    }

                    self.env['crm.lead'].create(lead_info)


