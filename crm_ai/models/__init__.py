# -*- coding: utf-8 -*-
"""crm_ai — bridge mellan odoo-crm och ai_agent_core.

Domänbridge per Vertel-konvention: `<domän>_ai`.
Lägger OKF-kontraktet (ai.okf.mixin) på crm.lead så att leadets
description/note blir sökbart kunskapsinnehåll i Odoo Mind.

Manifestet beror ENDAST på ai_agent_core + crm — kärnan förblir domän-ren.
"""

from . import crm_lead
