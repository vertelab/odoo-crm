# -*- coding: utf-8 -*-
##############################################################################
#
#    CRM: Skapad datum och tid
#    Copyright (C) 2025- Vertel AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'CRM: Skapad datum och tid',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Visar skapad datum och tid (utan sekunder) i CRM-listor och kanban',
    'description': """
CRM: Skapad datum och tid
==========================
Visar kolumnen "Skapad den" i CRM:s listvyer (Leads och Opportunities)
samt på kanban-korten.

* Kolumnen är alltid synlig och kan inte döljas (ingen valbar kolumn).
* Klockslaget visas med timmar och minuter, utan sekunder.
* Visas i användarens tidszon och språkformat.
""",
    'author': 'Vertel AB',
    'website': 'https://vertel.se',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
