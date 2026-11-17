# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Sakerhetsraden ska finnas, oavsett vilken utgaVas filformat som anvands.

Odoo 20 bytte form pa ir.model.access: filen heter ir.access.csv, modellen
tas ur filnamnet, och perm_*-kolumnerna ersatts av operation + domain. Vilken
fil som laddas avgor manifestet med '# #if VERSION >= "20.0"'.

Det har testet ar medvetet formatblindt: det fragar ORM:en vilka rattigheter
som galler for modellen, inte vilken CSV som lag bakom. Da passerar det pa
bada utgaVorna och faller om raden tas bort -- vilket ar det som ska
bevisas. Ett test som last csv-headern hade statt sig pa formatet i stallet
for pa beteendet.
"""

from odoo.tests.common import TransactionCase


class CrmAllabolagAccessCase(TransactionCase):
    """Sakerhetsraden for crm.allabolag.mining ska ge base.group_user CRUD."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env['ir.model']._get('crm.allabolag.mining')
        cls.group_user = cls.env.ref('base.group_user')

    def _access_rows(self):
        """Rattighetsrader for modellen, oavsett utgaVans modellnamn.

        I 18/19 heter modellen ir.model.access, i 20 ir.access. Vi slar upp
        modellen via ir.model i stallet for att ga direkt pa ett tabellnamn,
        sa testet inte behover veta vilken utgaVa det kor i.
        """
        # Vi letar efter VAR rad (det xml-id manifestets fil skapar), inte
        # efter "nagon rad for modellen". Skalet: crm.allabolag.mining arvs
        # aven av partner_allabolag, som skapar sin egen rad for samma
        # modell. Ett test som bara fragar efter modellen passerar darfor
        # aven nar VAR rad ar borta -- ett falskt gront som bevisar ingenting.
        access_model = self.env['ir.model.access']
        return access_model.search([('name', '=', 'access_crm_allabolag_mining')])

    def test_access_row_exists(self):
        """Raden ska finnas -- annars kan en vanlig anvandare inte anvanda modellen."""
        rows = self._access_rows()
        self.assertTrue(
            rows,
            "Raden access_crm_allabolag_mining saknas. Kontrollera att ratt "
            "security-fil laddas for utgaVan (manifestets "
            "'# #if VERSION >= \"20.0\"').",
        )

    def test_access_row_grants_crud(self):
        """Raden ska ge full CRUD, inte bara lasning.

        Falten heter perm_read/perm_write/... i 18/19. Vi laser dem via
        getattr sa att testet inte kraschar om en utgaVa byter namn; saknas
        ett falt ar det ett fel i sig och testet faller da pa AssertionError
        i stallet for AttributeError.
        """
        rows = self._access_rows()
        self.assertTrue(rows, "Ingen behorighetsrad att granska")
        for row in rows:
            for perm in ('perm_read', 'perm_write', 'perm_create', 'perm_unlink'):
                if not hasattr(row, perm):
                    self.fail(
                        "Falt %r saknas pa behorighetsraden i den har utgaVan. "
                        "Sakerhetsformatet har andrats utan att testet foljt med."
                        % perm
                    )
                self.assertTrue(
                    getattr(row, perm),
                    "Behorighetsraden saknar %s for crm.allabolag.mining" % perm,
                )
