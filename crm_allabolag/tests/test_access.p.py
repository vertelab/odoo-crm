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
        # Modellen heter ir.model.access i 18/19 och ir.access i 20. Slå upp
        # den via ir.model i stället för att hårdkoda namnet: annars är testet
        # inte formatblint alls, utan kraschar på 20.0 med KeyError -- vilket
        # det gjorde, och felet såg ut som ett modulfel.
        access_model = self.env['ir.model']._get('ir.access' if 'ir.access' in self.env else 'ir.model.access')
        return self.env[access_model.model].search(
            [('name', '=', 'access_crm_allabolag_mining')])

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

        Formatet skiljer sig: 18/19 har perm_read/perm_write/perm_create/
        perm_unlink, 20 har ett enda `operation`-falt med en delmangd av
        'crud' (t.ex. 'crud', 'cru', 'r'). Testet provar darfor det som
        galler for utgaVan i stallet for att kräva 18/19-falten -- annars
        faller det pa 20.0 av ett skal som inte ar ett fel.
        """
        rows = self._access_rows()
        self.assertTrue(rows, "Ingen behorighetsrad att granska")
        for row in rows:
            if 'operation' in row._fields:
                # 20.0: 'crud' ar fullstandig; varje tecken ar en rattighet.
                self.assertEqual(
                    set(row.operation or ''), set('crud'),
                    "operation=%r ger inte full CRUD for crm.allabolag.mining"
                    % (row.operation,),
                )
            else:
                for perm in ('perm_read', 'perm_write', 'perm_create', 'perm_unlink'):
                    self.assertTrue(
                        getattr(row, perm),
                        "Behorighetsraden saknar %s for crm.allabolag.mining" % perm,
                    )
