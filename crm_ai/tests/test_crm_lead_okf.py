# -*- coding: utf-8 -*-
"""Tester för crm_ai — OKF-kontraktet på crm.lead.

VARFÖR: bryggan är den första domänmodellen som bär ai.okf.mixin utanför
kärnans egna minnen. Testerna bevisar tre saker:

  1. kontraktet fungerar på en riktig domänmodell (inte bara i teorin)
  2. kärnan förblir domän-ren — crm.lead nämns bara här, aldrig i kärnan
  3. leadets text blir ett sökbart koncept med rätt typ och ägare
"""

from odoo.tests import common, tagged


@tagged('okf', 'post_install', '-at_install')
class TestCrmLeadOkf(common.TransactionCase):
    """crm.lead bär mixinen och indexeras som ett koncept."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lead = cls.env['crm.lead']
        cls.Concept = cls.env['ai.okf.concept']

    def _make_lead(self, **vals):
        base = {
            'name': 'Testaffär — ny hemsida',
            'description': 'Kunden vill ha en ny hemsida med bokningsflöde. '
                           'Budget cirka 150 000 kr. Beslut i oktober.',
            'partner_name': 'Testbolaget AB',
        }
        base.update(vals)
        return self.Lead.create(base)

    # ==================================================================
    # Kontraktet
    # ==================================================================

    def test_mixin_is_inherited(self):
        """crm.lead bär mixinens fält."""
        for f in ('okf_text', 'okf_summary', 'okf_dirty', 'okf_indexed_at'):
            self.assertIn(f, self.Lead._fields, f)

    def test_create_sets_dirty(self):
        """En ny post flaggas — arbetet väntar på cron, inte på create()."""
        lead = self._make_lead()
        self.assertTrue(lead.okf_dirty)

    def test_content_field_flags_dirty(self):
        """Ändring av ett innehållsfält flaggar posten."""
        lead = self._make_lead()
        lead._okf_index_record()  # rensa flaggan
        self.assertFalse(self.Lead.browse(lead.id).okf_dirty)

        lead.description = 'Uppdaterad: budget höjd till 200 000 kr.'
        self.assertTrue(self.Lead.browse(lead.id).okf_dirty)

    def test_non_content_field_does_not_flag(self):
        """stage_id/user_id säger inget om texten — ingen omindexering."""
        lead = self._make_lead()
        lead._okf_index_record()
        self.assertFalse(self.Lead.browse(lead.id).okf_dirty)

        lead.expected_revenue = 999.0
        self.assertFalse(self.Lead.browse(lead.id).okf_dirty)

    # ==================================================================
    # Källor
    # ==================================================================

    def test_text_source_joins_the_parts(self):
        """Texten är titel + anteckningar + företagsnamn."""
        lead = self._make_lead()
        text = lead._okf_text_source()
        self.assertIn('Testaffär', text)
        self.assertIn('bokningsflöde', text)
        self.assertIn('Testbolaget AB', text)

    def test_summary_source_is_the_title(self):
        """Leadets titel ÄR dess sammanfattning — ingen LLM behövs."""
        lead = self._make_lead()
        self.assertEqual(lead._okf_summary_source(), lead.name)

    def test_artifact_type_is_the_bridge_type(self):
        """Bryggan äger sin typ — inte kärnans generiska 'knowledge'."""
        lead = self._make_lead()
        self.assertEqual(lead._okf_artifact_type(), 'crm_lead')

    def test_concept_key_is_stable(self):
        """Nyckeln härleds ur modell+id — aldrig ur innehållet."""
        lead = self._make_lead()
        key = lead._okf_concept_key()
        self.assertEqual(key, 'crm.lead,%s' % lead.id)

        lead.description = 'Helt annan text.'
        self.assertEqual(lead._okf_concept_key(), key)

    def test_owner_is_the_company(self):
        """Leadet ägs av företaget, inte av säljaren."""
        lead = self._make_lead()
        vals = lead._okf_owner_vals()
        self.assertIn('owner_company_id', vals)
        self.assertEqual(len(vals), 1)

    def test_tags_become_okf_tags(self):
        """Leadets taggar följer med som OKF-taggar."""
        tag = self.env['crm.tag'].create({'name': 'Hemsida'})
        lead = self._make_lead(tag_ids=[(4, tag.id)])
        self.assertIn('Hemsida', lead._okf_tags_source())

    # ==================================================================
    # Indexering — hela vägen
    # ==================================================================

    def test_index_creates_a_concept(self):
        """Indexeringen skapar ett koncept med rätt källa och typ."""
        lead = self._make_lead()
        concept = lead._okf_index_record()

        self.assertTrue(concept)
        self.assertEqual(concept.source_ref, 'crm.lead,%s' % lead.id)
        self.assertEqual(concept.artifact_type_id.name, 'crm_lead')

    def test_index_clears_the_flag(self):
        """Efter lyckad indexering är flaggan rensad."""
        lead = self._make_lead()
        lead._okf_index_record()
        self.assertFalse(self.Lead.browse(lead.id).okf_dirty)

    def test_index_is_idempotent(self):
        """Oförändrat innehåll ger ingen ny rad (D5).

        Rader är ADD-only: en ny version är en NY rad med samma
        concept_key och version+1. Oförändrad källa ska därför ge
        exakt samma rad tillbaka — inte en kopia.
        """
        lead = self._make_lead()
        first = lead._okf_index_record()

        lead.okf_dirty = True
        second = lead._okf_index_record()

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.version, second.version)

    def test_edit_creates_a_new_version(self):
        """Ändrat innehåll ger version+1 i samma kedja.

        Ny version = ny rad (ADD-only). Den gamla blir `superseded` och
        den nya pekar tillbaka via `supersedes_id`.
        """
        lead = self._make_lead()
        first = lead._okf_index_record()

        lead.description = 'Kunden har höjt budgeten till 250 000 kr.'
        lead.okf_dirty = True
        second = lead._okf_index_record()

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(second.concept_key, first.concept_key)
        self.assertEqual(second.version, first.version + 1)
        self.assertEqual(second.supersedes_id.id, first.id)
        self.assertEqual(first.status, 'superseded')

    # ==================================================================
    # Registrering — kärnan känner inte crm.lead
    # ==================================================================

    def test_lead_is_registered_for_indexing(self):
        """Bryggan har registrerat crm.lead hos kärnan."""
        models = self.env['ai.okf.mixin']._okf_indexable_models()
        self.assertIn('crm.lead', models)

    def test_core_does_not_name_crm(self):
        """Kärnans indexeringskod nämner aldrig crm (F4.5).

        Bara KODEN prövas — docstrings och kommentarer får nämna domäner
        som exempel ("website_ai, hr_ai, crm_ai"). Det är koden som inte
        får känna en domän, inte dokumentationen.
        """
        import ast
        import inspect
        from odoo.addons.ai_agent_core.models import ai_okf_mixin

        tree = ast.parse(inspect.getsource(ai_okf_mixin))
        # Nollställ docstrings och kommentarer — behåll bara koden.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    node.body.pop(0)
        code_only = ast.unparse(tree).lower()

        for domain in ('crm', 'website', 'blog', 'event', 'hr.job'):
            self.assertNotIn(domain, code_only,
                             'domänen %r finns i mixinens KOD' % domain)
