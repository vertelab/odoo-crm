# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class CrmEnrichCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lead_model = cls.env['crm.lead']
        cls.params = cls.env['ir.config_parameter'].sudo()
        cls.params.set_param('partner_enrich.provider_order', 'foretagssok,allabolag')

    def setUp(self):
        super().setUp()
        vals = {
            'name': 'Offert till Testbolaget',
            'partner_name': 'Testbolaget AB',
        }
        # ``company_registry`` is added by crm_allabolag, not by this module.
        if 'company_registry' in self.env['crm.lead']._fields:
            vals['company_registry'] = '556000-1234'
        self.lead = self.env['crm.lead'].create(vals)

    def _install_provider(self, handler):
        lead_model = type(self.lead_model)

        def _call(self, provider_key, ctx):
            return handler(provider_key, ctx)

        lead_model._crm_enrich_from_provider = _call
        self.addCleanup(
            lambda: delattr(lead_model, '_crm_enrich_from_provider'),
        )


class TestLeadEnrichment(CrmEnrichCase):

    def test_name_is_never_overwritten(self):
        """The regression: ``_set_company_details`` wrote ``name``.

        ``crm.lead.name`` is the opportunity title — the salesperson's own
        words. Enrichment must never touch it.
        """
        self._install_provider(
            lambda key, ctx: {'name': 'Testbolaget AB', 'city': 'Stockholm'},
        )
        self.lead.crm_enrich()
        self.assertEqual(self.lead.name, 'Offert till Testbolaget')
        self.assertEqual(self.lead.partner_name, 'Testbolaget AB')

    def test_missing_name_does_not_blank_the_title(self):
        """The old code wrote ``name: None`` when Allabolag had no name."""
        self._install_provider(lambda key, ctx: {'city': 'Stockholm'})
        self.lead.crm_enrich()
        self.assertEqual(self.lead.name, 'Offert till Testbolaget')

    def test_email_maps_to_email_from(self):
        self._install_provider(
            lambda key, ctx: {'email': 'info@testbolaget.se'},
        )
        self.lead.crm_enrich()
        self.assertEqual(self.lead.email_from, 'info@testbolaget.se')

    def test_country_code_maps_to_country_id(self):
        self._install_provider(lambda key, ctx: {'country_code': 'SE'})
        self.lead.crm_enrich()
        self.assertEqual(self.lead.country_id.code, 'SE')

    def test_bookkeeping_fields_are_set(self):
        # ``city`` is empty, so ``fill_empty`` has something to write and the
        # bookkeeping fields are set alongside it.
        self._install_provider(lambda key, ctx: {'city': 'Stockholm'})
        self.lead.crm_enrich()
        self.assertTrue(self.lead.enrich_fetched_at)
        # Sorted alphabetically, not in policy order — the field records which
        # providers answered, not the order they were asked.
        self.assertEqual(
            set(self.lead.enrich_provider.split(',')),
            {'foretagssok', 'allabolag'},
        )
        self.assertTrue(self.lead.enrich_raw)

    def test_nothing_to_write_means_no_bookkeeping(self):
        """A run that changes nothing must not claim it enriched anything."""
        self._install_provider(
            lambda key, ctx: {'name': 'Testbolaget AB'},
        )
        self.lead.crm_enrich()
        self.assertFalse(self.lead.enrich_fetched_at)

    def test_provider_failure_does_not_abort(self):
        def handler(provider_key, ctx):
            if provider_key == 'foretagssok':
                raise RuntimeError('down')
            return {'city': 'Stockholm'}

        self._install_provider(handler)
        self.lead.crm_enrich()
        self.assertEqual(self.lead.city, 'Stockholm')

    def test_fill_empty_preserves_manual_values(self):
        self.lead.city = 'Göteborg'
        self._install_provider(lambda key, ctx: {'city': 'Stockholm'})
        self.lead.crm_enrich()
        self.assertEqual(self.lead.city, 'Göteborg')

    def test_manual_policy_blocks_write(self):
        self.params.set_param('partner_enrich.policy.identity', 'manual')
        self._install_provider(
            lambda key, ctx: {'name': 'Annat namn AB'},
        )
        self.lead.crm_enrich()
        self.assertEqual(self.lead.partner_name, 'Testbolaget AB')

    def test_no_data_writes_nothing(self):
        self._install_provider(lambda key, ctx: {})
        self.lead.crm_enrich()
        self.assertFalse(self.lead.enrich_fetched_at)

    def test_second_run_is_idempotent(self):
        self._install_provider(
            lambda key, ctx: {'city': 'Stockholm', 'zip': '111 22'},
        )
        self.lead.crm_enrich()
        first = (self.lead.city, self.lead.zip)
        self.lead.crm_enrich()
        self.assertEqual((self.lead.city, self.lead.zip), first)


class TestOrgnr2Vat(CrmEnrichCase):

    def test_builds_vat_from_org_number(self):
        self.assertEqual(
            self.lead_model.orgnr2vat('556000-1234'), 'SE556000123401',
        )

    def test_handles_bare_digits(self):
        self.assertEqual(
            self.lead_model.orgnr2vat('5560001234'), 'SE556000123401',
        )

    def test_handles_a_vat_number(self):
        self.assertEqual(
            self.lead_model.orgnr2vat('SE556000123401'), 'SE556000123401',
        )

    def test_invalid_gives_none(self):
        self.assertIsNone(self.lead_model.orgnr2vat('123'))
        self.assertIsNone(self.lead_model.orgnr2vat(False))
