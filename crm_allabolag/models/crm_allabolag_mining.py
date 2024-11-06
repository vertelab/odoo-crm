# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from allabolag import Company, iter_liquidated_companies
from allabolag.list import iter_list
from bs4 import BeautifulSoup
import json


import logging
_logger = logging.getLogger(__name__)

MINING_LAN = [
            (('xl/10'),('Blekinge')),
            (('xl/20'),('Dalarna')),
            (('xl/9'),('Gotland')),
            (('xl/21'),('Gävleborg')),
            (('xl/13'),('Halland')),
            (('xl/23'),('Jämtland')),
            (('xl/6'),('Jönköping')),
            (('xl/8'),('Kalmar')),
            (('xl/7'),('Kronoberg')),
            (('xl/25'),('Norrbotten')),
            (('xl/12'),('Skåne')),
            (('xl/1'),('Stockholm')),
            (('xl/4'),('Södermanland')),
            (('xl/3'),('Uppsala')),
            (('xl/17'),('Värmland')),
            (('xl/24'),('Västerbotten')),
            (('xl/22'),('Västernorrland')),
            (('xl/19'),('Västmanland')),
            (('xl/14'),('Västra götaland')),
            (('xl/18'),('Örebro')),
            (('xl/5'),('Östergötland')),
    ]

MINING_INDUSTRY = [
            (("bransch/ambassader-internationella-org/29/_"),("Ambassader & Internationella Org.")),
            (("bransch/avlopp-avfall-el-vatten/5/_"),("Avlopp, Avfall, El & Vatten")),
            (("bransch/bank-finans-forsakring/14/_"),("Bank, Finans & Försäkring")),
            (("bransch/bemanning-arbetsformedling/23/_"),("Bemanning & Arbetsförmedling")),
            (("branschbransch-arbetsgivar-yrkesorg/27/_"),("Bransch-, Arbetsgivar- & Yrkesorg.")),
            (("bransch/bygg-design-inredningsverksamhet/6/_"),("Bygg-, Design- & Inredningsverksamhet")),
            (("bransch/data-it-telekommunikation/13/_"),("Data, It & Telekommunikation")),
            (("bransch/detaljhandel/9/_"),("Detaljhandel")),
            (("bransch/fastighetsverksamhet/15/_"),("Fastighetsverksamhet")),
            (("bransch/foretagstjanster/11/_"),("Företagstjänster")),
            (("bransch/hotell-restaurang/12/_"),("Hotell & Restaurang")),
            (("bransch/har-skonhetsvard/28/_"),("Hår & Skönhetsvård")),
            (("bransch/halsa-sjukvard/21/_"),("Hälsa & Sjukvård")),
            (("bransch/jordbruk-skogsbruk-jakt-fiske/0/_"),("Jordbruk, Skogsbruk, Jakt & Fiske")),
            (("bransch/juridik-ekonomi-konsulttjanster/16/_"),("Juridik, Ekonomi & Konsulttjänster")),
            (("bransch/kultur-noje-fritid/26/_"),("Kultur, Nöje & Fritid")),
            (("bransch/livsmedelsframstallning/2/_"),("Livsmedelsframställning")),
            (("bransch/media/3/_"),("Media")),
            (("bransch/motorfordonshandel/7/_"),("Motorfordonshandel")),
            (("bransch/offentlig-forvaltning-samhalle/25/_"),("Offentlig Förvaltning & Samhälle")),
            (("bransch/partihandel/8/_"),("Partihandel")),
            (("bransch/reklam-pr-marknadsundersokning/17/_"),("Reklam, Pr & Marknadsundersökning")),
            (("bransch/reparation-installation/4/_"),("Reparation & Installation")),
            (("bransch/resebyra-turism/24/_"),("Resebyrå & Turism")),
            (("bransch/teknisk-konsultverksamhet/18/_"),("Teknisk Konsultverksamhet")),
            (("bransch/tillverkning-industri/1/_"),("Tillverkning & Industri")),
            (("bransch/transport-magasinering/10/_"),("Transport & Magasinering")),
            (("bransch/utbildning-forskning-utveckling/19/_"),("Utbildning, Forskning & Utveckling")),
            (("bransch/uthyrning-leasing/22/_"),("Uthyrning & Leasing")),
            (("bransch/ovriga-konsumenttjanster/20/_"),("Övriga Konsumenttjänster")),
        ]
        
MINING_INDUSTRY_XV = [
                (('xv/PARTIHANDEL')                      ,('Partihandel')),
                (('xv/JORDBRUK, SKOGSBRUK, JAKT & FISKE'),('Jordbruk, skogsbruk, jakt & fiske' )),
                (('xv/FASTIGHETSVERKSAMHET')             ,('Fastighetsverksamhet')),
                (('xv/BRANSCH-, ARBETSGIVAR- & YRKESORG.'),('Bransch-, arbetsgivar- & yrkesorg.')),
                (('xv/BYGG-, DESIGN- & INREDNINGSVERKSAMHET'),('Bygg-, design- & inredningsverksamhet')),
                (('/xv/KULTUR, NÖJE & FRITID')            ,('Kultur, nöje & fritid')),
                (('/xv/JURIDIK, EKONOMI & KONSULTTJÄNSTER'),('Juridik, ekonomi & konsulttjänster')),
                (('/xv/DETALJHANDEL')                     ,('Detaljhandel')),
                (('/xv/DATA, IT & TELEKOMMUNIKATION')     ,('Data, it & telekommunikation')),
                (('xv/PARTIHANDEL')                       ,('Partihandel')),
                (('xv/HÄLSA & SJUKVÅRD')                  ,('Hälsa & sjukvård')),
                (('xv/TILLVERKNING & INDUSTRI')           ,('Tillverkning & industri')),
                (('xv/BANK, FINANS & FÖRSÄKRING')         ,('Bank, finans & försäkring')),
                (('xv/UTBILDNING, FORSKNING & UTVECKLING'),('Utbildning, forskning & utveckling')),
                (('xv/HOTELL & RESTAURANG')               ,('Hotell & restaurang')),
                (('/xv/TRANSPORT & MAGASINERING')         ,('Transport & magasinering')),
                (('xv/TEKNISK KONSULTVERKSAMHET')         ,('Teknisk konsultverksamhet')),
                (('xv/REPARATION & INSTALLATION')         ,('Reparation & installation')),
                (('xv/HÅR & SKÖNHETSVÅRD')                ,('Hår & skönhetsvård')),
                (('xv/ÖVRIGA KONSUMENTTJÄNSTER')          ,('Övriga konsumenttjänster')),
                (('xv/FÖRETAGSTJÄNSTER')                  ,('Företagstjänster')),
                (('xv/MEDIA')                             ,('Media')),
                (('xv/REKLAM, PR & MARKNADSUNDERSÖKNING') ,('Reklam, pr & marknadsundersökning')),
                (('xv/BEMANNING & ARBETSFÖRMEDLING'),('Bemanning & arbetsförmedling')),
                (('xv/MOTORFORDONSHANDEL'),('Motorfordonshandel')),
                (('/xv/UTHYRNING & LEASING'),('Uthyrning & leasing')),
                (('xv/AVLOPP, AVFALL, EL & VATTEN'),('Avlopp, avfall, el & vatten')),
                (('xv/LIVSMEDELSFRAMSTÄLLNING'),('Livsmedelsframställning')),
                (('xv/RESEBYRÅ & TURISM'),('Resebyrå & turism')),
                (('xv/OFFENTLIG FÖRVALTNING & SAMHÄLLE'),('Offentlig förvaltning & samhälle')),
                (('xv/AMBASSADER & INTERNATIONELLA ORG.'),('Ambassader & internationella org.'))
            ]

MINING_REQUEST_TYPE =[  ('industry','Industry'),
                        ('lista/omsatter-mest/11','Turns over the most'),
                        ('lista/hogst-resultat/12','Highest result'),('lista/storsta-arbetsgivarna/13','Largest employers'),
                        ('lista/flest-bilar/14','Most cars'),('lista/bolag-med-varumarken/15','Companies with brands'),
                        ('lista/bostads-och-bostadsrattfor/25','Housing Cooperatives'),('lista/statliga-och-kommunala-bolag/33','State and Municipal Companies')
                    ]

MINING_CORPORATE_FORM = [
        (('xb/EF'),('Enskild firma')),
        (('xb/AB'),('Aktiebolag')),
        (('xb/IF'),('Ideella föreningar')),
        (('xb/HK'),('Hb & Kb')),
        (('xb/OV'),('Övriga bolagsformer')),
        (('xb/SA'),('Samfälligheter')),
        (('xb/SF'),('Sambruksförening')),
        (('xb/FI'),('Filialer')),
        (('xb/EK'),('Ekonomisk förening')),
        (('xb/EB'),('Enkla bolag')),
        (('xb/SK'),('Statliga & kommunala')),
        (('xb/BF'),('Bostadsförening')),
        (('xb/VP'),('Värdepappersfonder')),
    ]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    mining_id = fields.Many2one(comodel_name='crm.allabolag.mining')

    mining_corporate_form = fields.Selection(selection=MINING_CORPORATE_FORM,string='Company form',related='mining_id.corporate_form', readonly=True,store=True)
    mining_industry = fields.Selection(selection=MINING_INDUSTRY,string='industry',related='mining_id.industry', readonly=True,store=True)
    mining_industry_xv = fields.Selection(selection=MINING_INDUSTRY_XV,string='industry',related='mining_id.industry_xv', readonly=True,store=True)
    mining_lan = fields.Selection(selection=MINING_LAN,string='County',related='mining_id.lan', readonly=True,store=True)
    mining_request_type = fields.Selection(selection=MINING_REQUEST_TYPE,string='Request Type',store=True,related='mining_id.request_type', readonly=True)


class CrmAllabolagMining(models.Model):
    _name = 'crm.allabolag.mining'
    _inherit = ['mail.thread', 'mail.activity.mixin','utm.mixin']
    _description = 'CRM Allabolag Mining'
    _order = "date desc"

    company_currency = fields.Many2one("res.currency", string='Currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    corporate_form = fields.Selection(selection=MINING_CORPORATE_FORM,string='Company form')
    date = fields.Date(string='Date',default=fields.Date.today()) # fields.date.add|context_today|end_of|start_of|substract|to_date|to_string|today
    description = fields.Text('Notes')
    expected_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency', tracking=True)
    industry = fields.Selection(selection=MINING_INDUSTRY,string='Industry',required=False)
    industry_xv = fields.Selection(selection=MINING_INDUSTRY_XV,string='Industry')
    lan = fields.Selection(selection=MINING_LAN,string='County')
    lead_count = fields.Integer(string='Number of Leads',compute='_compute_lead_count',readonly=True)
    lead_ids = fields.One2many(comodel_name='crm.lead',inverse_name='mining_id',string="Leads",help="") 
    leads_url = fields.Char(string='Url', trim=True, compute="_compute_leads_url")
    max_no_leads = fields.Integer(string='Number of Wanted Leads', default=50)
    name = fields.Char(
        'Request', index=True, required=True,
        compute='_compute_name', readonly=False, store=True)
    no_employees = fields.Selection(selection=[
            (('xe/1'),('0')),
            (('xe/2'),('1 - 4')),
            (('xe/3'),('5 - 9')),
            (('xe/4'),('10 - 19')),
            (('xe/5'),('20 - 49')),
            (('xe/6'),('50 - 99')),
            (('xe/7'),('100 - 199')),
            (('xe/8'),('200 - 999')),
            (('xe/9'),('> 1000')),
        ],string='Number of Employees')
    recurring_plan = fields.Many2one('crm.recurring.plan', string="Recurring Plan", groups="crm.group_use_recurring_revenues")
    recurring_revenue = fields.Monetary('Recurring Revenues', currency_field='company_currency', groups="crm.group_use_recurring_revenues")
    request_type = fields.Selection(selection=MINING_REQUEST_TYPE,string='Request Type',required=True,default='industry')
    revenue_from = fields.Integer(string='Revenue')
    revenue_to = fields.Integer(string='Revenue')
    selected_count = fields.Integer(string='Max Number of Leads')
    state = fields.Selection(selection=[('draft','Draft'),('list','List'),('done','Done'),('error','Error'),('cancel','Cancel')],default='draft',tracking=True)
    tag_ids = fields.Many2many(comodel_name='crm.tag',string='Tags',help="Set this tags to created leads") # relation|column1|column2
    type = fields.Selection(selection=[('lead','Lead'),('opportunity','Opportunity')],string='Lead Type',default='lead',required=True)
    team_id = fields.Many2one(
        comodel_name='crm.team', string='Sales Team', index=True,
        compute='_compute_team_id', readonly=False, store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True, default=lambda self: self.env.user)


    @api.depends('user_id','industry','request_type')
    def _compute_name(self):
        for s in self:
            if s.request_type != 'industry':
                # ~ raise UserError(f"{[a for a in s.fields_get(allfields=['request_type'])['request_type']['selection'] if a[0] == s.request_type][0][1]}")
                request_name = [a for a in s.fields_get(allfields=['request_type'])['request_type']['selection'] if a[0] == s.request_type][0][1]
                s.name = _(f"[{s.user_id.name}] {request_name}")
            else:
                if s.industry:
                    industry_name = [a for a in s.fields_get(allfields=['industry'])['industry']['selection'] if a[0] == s.industry][0][1]
                else:
                    industry_name = ''
                s.name = _(f"[{s.user_id.name}] {industry_name}")

    @api.depends('lead_ids')
    def _compute_lead_count(self):
        for s in self:
            s.lead_count = len(s.lead_ids)

    @api.depends('request_type','corporate_form', 'no_employees','lan','industry','revenue_from','revenue_to','industry_xv')
    def _compute_leads_url(self):
        """ When changing the request info also update url """
        for lead in self:
            # ~ lead.leads_url = 'https://allabolag.se'
            lead.leads_url = ''
            if lead.request_type != 'industry':
                lead.leads_url += lead.request_type if lead.request_type else ''
                if lead.industry_xv:
                    lead.leads_url += '/' + lead.industry_xv
            elif lead.industry:
                lead.leads_url += lead.industry
            if lead.corporate_form:
                lead.leads_url += '/' + lead.corporate_form
            if lead.no_employees:
                lead.leads_url += '/' + lead.no_employees
            if lead.lan:
                lead.leads_url += '/' + lead.lan
            if lead.revenue_from or lead.revenue_to:
                lead.leads_url += '/xr/'
                if  lead.revenue_from > 0:
                    lead.leads_url += str(lead.revenue_from)
                lead.leads_url += '-'
                if  lead.revenue_to > 0:
                    lead.leads_url += str(lead.revenue_to)


    @api.depends('user_id', 'type')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
                continue
            team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            lead.team_id = team.id


    def action_get_lead_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'lead')]
        action['help'] = _("""<p class="o_view_nocontent_empty_folder">
            No leads found
        </p><p>
            No leads could be generated according to your search criteria
        </p>""")
        return action

    def action_get_opportunity_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
        action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'opportunity')]
        action['help'] = _("""<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>""")
        return action

    def action_draft(self):
        self.ensure_one()
        self.lead_ids.unlink()
        self.state = 'draft'
        return None
        
    def action_enrich(self):
        self.ensure_one()
        for lead in self.lead_ids:
            if lead.summary_revenue == 0.0:
                try:
                    lead.enrich_allabolag()
                except Exception as e:
                    _logger.warning(f"Allabolag: An unexpected error occurred: {e}")
                    self.state = 'error'
                    self.message_post(body=_(f"An unexpected error occurred for {lead.name}: {e}"))
                    return None

        self.state = 'done'
        if self.type == 'lead':
            action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
            action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'lead')]
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
            action['domain'] = [('id', 'in', self.lead_ids.ids), ('type', '=', 'opportunity')]
        action['help'] = _("""<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>""")
        return action

    def scrape_traffar_number(self):
        self.ensure_one()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        _logger.warning(f"https://allabolag.se/{self.leads_url}?page=1")

        r = requests.get(f"https://allabolag.se/{self.leads_url}?page=1", headers=headers)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        return int(soup.select_one(".page.search-results search").attrs[":total-hits-default"])


    def action_check(self):
        self.ensure_one()
        
        self.selected_count = self.scrape_traffar_number()
        if self.max_no_leads > self.selected_count:
            self.max_no_leads = self.selected_count
        #TODO logg

        

    def action_submit(self):
        self.ensure_one()
    
        self.selected_count = self.scrape_traffar_number()
        if self.selected_count == 0:
            raise UserError(_("There are no companies to fetch"))
            
        if self.max_no_leads > self.selected_count:
            self.max_no_leads = self.selected_count
        #TODO logg

        i = 1
        try:
            for item in iter_list(
                    self.leads_url,
                    # ~ lambda x: _parse_liquidated_company_item(until=until),
                    # ~ lambda x: _parse_liquidated_company_item(x)["Konkurs inledd"] < until,
                ):
                    # ~ _logger.warning(f"{item=}  {self.env['crm.lead'].search_count([('company_registry', '=', item['orgnr'])])=}")
                    if self.env['crm.lead'].search_count([('company_registry', '=', item['orgnr'] )])==0:
                        # ~ {'orgnr': '556588-3534', 'jurnamn': 'Toyota Industries Europe AB', 'ftgtyp': 'ab', 'bolpres': '', 
                        # ~ 'abv_hgrupp': 'Bank, Finans & Försäkring', 'abv_ugrupp': 'Holdingverksamhet i icke-finansiella koncerner', 'ba_postort': 'Mjölby', 'companyPresentation': {}, 
                        # ~ 'linkTo': '5565883534/toyota-industries-europe-ab', 'score': {'0': '1.000'}, 'remarks': [], 
                        # ~ 'hasremarks': False, 'relatedmetadata': [], 'hasrelatedmetadata': False, 'status': ''}
                        
                        lead = self.env['crm.lead'].create({
                                'name': item['jurnamn'],
                                'partner_name': item['jurnamn'],
                                'company_registry': item['orgnr'], 
                                'mining_id': self.id,
                                'linkTo': f"https://allabolag.se/{item['linkTo']}",
                                'city': item['ba_postort'],
                                'tag_ids': self.tag_ids,
                                'type': self.type,
                                'user_id': self.user_id.id if self.user_id else None,
                                'description': self.description,
                                'team_id': self.team_id.id if self.team_id else None,
                                'campaign_id': self.campaign_id.id if self.campaign_id else None,
                                'source_id': self.source_id.id if self.source_id else None,
                                'medium_id': self.medium_id.id if self.medium_id else None,
                                'expected_revenue': self.expected_revenue,
                            }) 

                        # ~ if self.recurring_revenue:
                            # ~ lead.write({'recurring_revenue': self.recurring_revenue,
                                        # ~ 'recurring_plan': self.recurring_plan.id if self.recurring_plan else None,})


                        i += 1
                        if i > self.max_no_leads:
                            break 
        except Exception as e:
            _logger.warning(f"Allabolag: An unexpected error occurred: {e}")    
            self.message_post(body=_(f"An unexpected error occurred: {e}"),message_type='notification')
            self.state = 'error'

            return None

        self.state = 'list'
        if self.type == 'lead':
            return self.action_get_lead_action()
        elif self.type == 'opportunity':
            return self.action_get_opportunity_action()
    
    
    
    
    def action_allabolag_url(self):
        self.ensure_one()
        return {
                'type': 'ir.actions.act_url',
                'url': f"https://allabolag.se/{self.leads_url}",
                'target': 'new'
                }
        

    company_name = 'what/{name}'
    city = 'where/{city}'
    sni = "verksamhet/{sni}"
