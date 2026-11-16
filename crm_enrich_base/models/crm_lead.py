# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Lead-level enrichment: the same provider contract as ``res.partner``.

The old ``crm_enrich()`` did nothing but log and call ``super()``. Each
provider module then implemented its own ``crm_enrich()``, and because
``crm_allabolag`` called ``super()`` *after* writing, the order of the chain
decided the result — the same collision the partner side had.

This module owns the dispatcher. Providers implement
``_crm_enrich_from_provider(provider_key, ctx)`` and return canonical dicts;
everything else — policy, one write per record, bookkeeping — happens here.

Deliberate differences from the partner side:

* ``name`` maps to ``partner_name``, never to ``name``. A lead's ``name`` is
  the opportunity title; overwriting it with a company name destroys the
  salesperson's own words.
* ``email`` maps to ``email_from``.
* There is no logo: a lead has no image field.
"""

import json
import logging

from odoo import api, fields, models

from odoo.addons.partner_enrich_base.models.enrich_format import (
    FIELD_GROUP,
    LEAD_FIELD_MAP,
    clean,
    empty,
)

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # -- bookkeeping --------------------------------------------------------

    enrich_fetched_at = fields.Datetime(
        string='Enriched At', readonly=True, copy=False,
    )
    enrich_provider = fields.Char(
        string='Enrichment Provider', readonly=True, copy=False,
    )
    enrich_raw = fields.Text(
        string='Raw Enrichment Response', readonly=True, copy=False,
    )

    # -- provider contract --------------------------------------------------

    @api.model
    def _crm_enrich_from_provider(self, provider_key, ctx):
        """Answer one provider's lookup for a lead. Providers override this.

        Defined here so that ``super()`` works once a second provider module
        inherits the first — the same gap that broke the partner side.
        """
        return [] if (ctx or {}).get('mode') == 'search' else {}

    def _crm_enrich_collect(self, ctx):
        """Ask every configured provider. Returns ``[(key, data)]``."""
        policy = self.env['res.partner.enrich.policy']
        collected = []
        for provider_key in policy._enrich_provider_keys():
            try:
                data = self._crm_enrich_from_provider(provider_key, ctx)
            except Exception:  # noqa: BLE001 - one provider must not sink the run
                _logger.warning(
                    "Lead enrichment provider %r failed — continuing.",
                    provider_key, exc_info=True,
                )
                continue
            if not data:
                continue
            collected.append((provider_key, data))
        return collected

    def _crm_enrich_context(self):
        """The lookup context for a lead, normalised once.

        ``company_registry`` and ``vat`` are not stock ``crm.lead`` fields —
        ``crm_allabolag`` adds them. Reading them with ``getattr`` keeps this
        module installable without any provider, which is the whole point of a
        base module.
        """
        self.ensure_one()
        registry_source = (
            getattr(self, 'company_registry', False)
            or getattr(self, 'vat', False)
        )
        registry, vat = self.env['res.partner']._enrich_normalize_registry(
            registry_source,
        )
        return {
            'name': self.partner_name or self.name,
            'registry': registry,
            'vat': vat,
            'country_code': self.country_id.code or 'SE',
            'website': self.website,
            'duns': False,
            'mode': 'enrich',
            'record': self,
        }

    def _crm_enrich_current_values(self, keys):
        """Current field values, keyed canonically, for the policy.

        A mapped field that this installation does not have (``company_registry``
        and ``vat`` are added by ``crm_allabolag``) is skipped rather than
        raising: the base module must work with no provider installed.
        """
        self.ensure_one()
        current = {}
        for key in keys:
            fname = LEAD_FIELD_MAP.get(key)
            if not fname or fname not in self._fields:
                continue
            value = self[fname]
            if fname == 'country_id':
                value = value.code if value else False
            current[key] = value
        return current

    def _crm_enrich_prepare_vals(self, resolved):
        """Turn ``{key: (value, provider)}`` into ``write()`` values."""
        vals = {}
        for key, (value, _provider) in resolved.items():
            fname = LEAD_FIELD_MAP.get(key)
            if not fname or fname not in self._fields:
                continue
            if fname == 'country_id':
                country = self.env['res.country'].search(
                    [('code', '=', str(value).upper())], limit=1,
                )
                if not country:
                    _logger.info(
                        "Lead enrichment: unknown country %r — skipped.", value,
                    )
                    continue
                vals[fname] = country.id
                continue
            vals[fname] = value
        return vals

    def _crm_enrich_apply_extra(self, resolved, collected):
        """Hook for provider modules to map their own lead fields."""
        return {}

    def _crm_enrich_raw_payload(self, collected):
        payload = {}
        for provider_key, data in collected:
            serialisable = {}
            for key, value in data.items():
                try:
                    json.dumps(value)
                except (TypeError, ValueError):
                    serialisable[key] = str(value)
                else:
                    serialisable[key] = value
            payload[provider_key] = serialisable
        return json.dumps(payload, ensure_ascii=False, indent=1, default=str)

    def _crm_enrich_message_post(self, resolved):
        self.ensure_one()
        lines = []
        for group in sorted({FIELD_GROUP.get(k) for k in resolved}):
            if not group:
                continue
            providers = sorted({
                provider for key, (_v, provider) in resolved.items()
                if FIELD_GROUP.get(key) == group
            })
            lines.append('%s: %s' % (group, ', '.join(providers)))
        if not lines:
            return
        self.message_post(
            body='Enriched from %s' % '; '.join(lines),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    # -- entry point --------------------------------------------------------

    def crm_enrich(self):
        """Enrich these leads from the configured providers.

        Public, argument-free entry point kept from the original API — the
        server action in ``data/ir_action.xml`` calls it.
        """
        policy = self.env['res.partner.enrich.policy']
        for lead in self:
            ctx = lead._crm_enrich_context()
            collected = [
                (provider_key, clean(data))
                for provider_key, data in lead._crm_enrich_collect(ctx)
                if isinstance(data, dict)
            ]
            collected = [(k, d) for k, d in collected if d]
            if not collected:
                _logger.info(
                    "Lead enrichment: no provider returned data for %r.",
                    lead.display_name,
                )
                continue

            data_keys = {key for _pkey, data in collected for key in data}
            current = lead._crm_enrich_current_values(data_keys)
            resolved = policy._enrich_resolve(collected, current)
            vals = lead._crm_enrich_prepare_vals(resolved)
            extra = lead._crm_enrich_apply_extra(resolved, collected)

            if not vals and not extra:
                _logger.info(
                    "Lead enrichment: nothing to write for %r.",
                    lead.display_name,
                )
                continue

            provider_keys = sorted({pkey for pkey, _d in collected})
            vals.update(extra or {})
            vals.update({
                'enrich_fetched_at': fields.Datetime.now(),
                'enrich_provider': ','.join(provider_keys),
                'enrich_raw': lead._crm_enrich_raw_payload(collected),
            })
            lead.write(vals)
            lead._crm_enrich_message_post(resolved)
        return True

    # -- kept for compatibility ---------------------------------------------

    @api.model
    def orgnr2vat(self, company_registry):
        """Build a Swedish VAT number from an organisation number.

        Kept because other code calls it, but it now delegates to the base
        normaliser: this module used to produce ``SE<digits>01`` from whatever
        it was handed, including strings that were not organisation numbers.
        """
        _registry, vat = self.env['res.partner']._enrich_normalize_registry(
            company_registry,
        )
        return vat or None
