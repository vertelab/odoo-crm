# -*- coding: utf-8 -*-
# Part of Vertel. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM AI — Bridge',
    'version': '18.0.1.0.3',
    'summary': 'OKF-kontraktet på crm.lead — leadets anteckningar blir sökbara',
    'category': 'AI Orchestration',
    'description': """
        Domänbridge mellan odoo-crm och ai_agent_core.

        Lägger ai.okf.mixin på crm.lead, så att leadets name/description/
        partner_name indexeras som OKF-koncept och blir sökbara i Odoo Mind.

        Bryggan äger sitt eget artifact_type (crm_lead) och registrerar
        crm.lead för dirty-indexering — kärnan namnger aldrig en domänmodell.
    """,
    'author': 'Vertel Sverige AB',
    'license': 'AGPL-3',
    'depends': [
        'ai_agent_core',
        'crm',
    ],
    'data': [
        'data/crm_ai_artifact_types.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
