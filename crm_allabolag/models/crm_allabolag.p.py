# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Allabolag as a provider for ``crm.lead``.

The old ``_set_company_details()`` had a bug that is worth naming: it wrote

    "name": company_data.get("name"),

on a ``crm.lead``. ``name`` is the *opportunity title* — the salesperson's own
words. Enriching a lead therefore renamed the opportunity to the company name,
and if Allabolag returned no name, it set the title to ``None``. On top of
that it wrote ``None`` for a dozen optional fields, which is exactly what the
canonical contract's ``empty()`` exists to prevent.

It is now a provider: it returns canonical dicts, and the base module decides
what to write. ``name`` maps to ``partner_name`` through ``LEAD_FIELD_MAP``.
"""

import logging

from odoo import api, models

from odoo.addons.partner_enrich_base.models.enrich_format import empty, pick

_logger = logging.getLogger(__name__)

#: The key this provider registers under in ``partner_enrich.provider_order``.
PROVIDER_KEY = 'allabolag'


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ---------------------------------------------------------------------
    # Provider contract
    # ---------------------------------------------------------------------

    @api.model
    def _crm_enrich_from_provider(self, provider_key, ctx):
        """Answer the base module's provider call for ``allabolag``."""
        if provider_key != PROVIDER_KEY:
            return super()._crm_enrich_from_provider(provider_key, ctx)
        mode = ctx.get('mode') or 'enrich'
        try:
            if mode == 'search':
                return self._allabolag_lead_search(ctx)
            return self._allabolag_lead_fetch(ctx)
        except ImportError:
            _logger.info(
                "The 'allabolag' Python package is not installed — the "
                "allabolag provider is disabled for leads.",
            )
            return [] if mode == 'search' else {}
        except Exception:  # noqa: BLE001 - a scrape failure is not fatal
            _logger.warning(
                "Allabolag lead lookup failed (mode=%s).", mode, exc_info=True,
            )
            return [] if mode == 'search' else {}

    @api.model
    def _allabolag_lead_search(self, ctx):
        """One scrape by organisation number or name."""
        registry = ctx.get('registry')
        if empty(registry):
            name = ctx.get('name')
            if empty(name):
                return []
            registry, _item = self.env['res.partner'].name2orgno(name)
        if empty(registry):
            return []
        canonical = self._allabolag_lead_fetch({'registry': registry})
        return [canonical] if canonical else []

    @api.model
    def _allabolag_lead_fetch(self, ctx):
        """Fetch one company and map it to the canonical format.

        Delegates the mapping to ``partner_allabolag``: the company object is
        the same regardless of whether it is being attached to a partner or a
        lead, and two mappings of the same data is how the two sides drift.
        """
        from allabolag import Company
        from allabolag.company import NoSuchCompany

        registry = ctx.get('registry')
        if empty(registry):
            return {}
        digits = ''.join(ch for ch in str(registry) if ch.isdigit())
        if len(digits) != 10:
            _logger.info("Allabolag: %r is not an organisation number.", registry)
            return {}
        try:
            company = Company('%s-%s' % (digits[:6], digits[6:]))
            data = company.data
        except NoSuchCompany:
            _logger.info("Allabolag has no company %s.", digits)
            return {}
        if not data:
            return {}
        return self.env['res.partner']._allabolag_map_company(data)

    # ---------------------------------------------------------------------
    # Provider-specific lead fields
    # ---------------------------------------------------------------------

    def _crm_enrich_apply_extra(self, resolved, collected):
        """Store the raw Allabolag payload and the link.

        ``mining_id`` is deliberately **not** set: ``crm.allabolag.mining`` is
        a *search request* (SNI, county, revenue range, how many leads you
        want), not a company record. Attaching a company to it would be
        attaching a result to a query. The ``mining_*`` related fields stay
        empty on an enriched lead, which is correct — they describe a search,
        not this company.
        """
        vals = super()._crm_enrich_apply_extra(resolved, collected)
        if not any(pkey == PROVIDER_KEY for _v, pkey in resolved.values()):
            return vals
        canonical = dict(collected).get(PROVIDER_KEY) or {}
        company = canonical.get('payload') or {}
        if not company:
            return vals

        # The raw company object, kept for troubleshooting and re-apply.
        vals['allabolag_json_data'] = str(company)
        link = pick(company, 'linkTo', 'url')
        if link:
            vals['linkTo'] = link
        return vals
