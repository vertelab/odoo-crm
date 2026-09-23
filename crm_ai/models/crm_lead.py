# -*- coding: utf-8 -*-
"""crm.lead bär OKF-kontraktet (crm_ai).

VARFÖR: leadets anteckningar (`description`, Html) är den enda platsen i CRM
där en säljare skriver fritext om affären — behov, invändningar, vad som
sagts. Den texten är kunskap, men den är osökbar: den ligger i en Html-kolumn
som varken BM25 eller embeddings ser. Mixinen ger den ett koncept.

Källor:
    name          — leadets titel (kort, alltid satt)
    description   — anteckningarna (Html; det egentliga innehållet)
    partner_name  — företagsnamnet när partnern inte är kopplad

`_okf_summary_source()` returnerar `name` — leadets titel ÄR dess
sammanfattning. Ingen LLM behövs för att veta det, och en deterministisk
sammanfattning är bättre än en som varierar mellan körningar.
"""

from odoo import models


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'ai.okf.mixin']

    # ==================================================================
    # Källor — vad mixinen läser
    # ==================================================================

    def _okf_text_source(self):
        """Leadets hela material: titel, anteckningar, företagsnamn."""
        self.ensure_one()
        parts = []
        if self.name:
            parts.append(self.name)
        if self.description:
            parts.append(self.description)
        if self.partner_name:
            parts.append(self.partner_name)
        return '\n\n'.join(parts)

    def _okf_summary_source(self):
        """Leadets titel är dess sammanfattning — ingen LLM behövs."""
        self.ensure_one()
        return self.name or None

    def _okf_tags_source(self):
        """Leadets taggar blir OKF-taggar."""
        self.ensure_one()
        return [t.name for t in self.tag_ids if t.name]

    def _okf_links_source(self):
        """Länk till partnern, när den finns."""
        self.ensure_one()
        if self.partner_id:
            return [{
                'type': 'BELONGS_TO',
                'target': 'res.partner,%s' % self.partner_id.id,
                'label': self.partner_id.display_name,
            }]
        return []

    # ==================================================================
    # Kontraktet — vad mixinen frågar om
    # ==================================================================

    def _okf_dirty_fields(self):
        """Fält vars ändring gör OKF-fälten inaktuella.

        Bara innehållsfält. `stage_id`/`user_id` ändras ofta och säger
        inget om texten — att flagga på dem skulle indexera om i onödan.
        """
        return {'name', 'description', 'partner_name', 'tag_ids'}

    def _okf_artifact_type(self):
        """Bryggans egen typ — spårbar till crm_ai i taxonomin."""
        return 'crm_lead'

    def _okf_owner_vals(self):
        """Exakt EN ägare. Leadet ägs av företaget, inte av säljaren.

        Varför inte `user_id`: en säljare kan byta jobb, men leadets
        kunskap tillhör fortfarande företaget. Att äga per användare skulle
        göra konceptet osynligt för kollegorna.
        """
        self.ensure_one()
        return {'owner_company_id': self.company_id.id or self.env.company.id}

    # ==================================================================
    # Registrering — kärnan ska inte känna crm.lead
    # ==================================================================

    def _register_hook(self):
        """Registrera crm.lead för dirty-indexering.

        Registrering, inte överridning: `_okf_indexable_models()` är
        `@api.model` på den ABSTRAKTA modellen — en överridning här hade
        ingen verkan på cronen (mätt i kärnan 2026-09-22).
        """
        res = super()._register_hook()
        self.env['ai.okf.mixin']._okf_register_indexable('crm.lead')
        return res
