# odoo-crm
Extra crm-modules

## Porteringsstatus

18.0 är baseline. 19.0/20.0 visar om p-filen har ett villkor för utgåvan
— inte om grenen finns. Blockerare är `depends` som saknas i 20.0
(kärna + alla 20.0-grenar).

| Modul | Beskrivning | Manifest | p-fil | 19.0 | 20.0 | Blockerare |
|---|---|---|---|---|---|---|
| crm_ai | OKF-kontraktet på crm.lead — leadets anteckningar blir sö... | 1.0.3 | 2 | ✓ | — | — |
| crm_allabolag | Adding valuable internet-data to CRM contacts. | 1.0 | 9 | — | — | — |
| crm_bolagsfakta | Adding data to CRM contacts. | 1.0.0 | 0 | — | — | — |
| crm_builtwith | Adding valuable internet-data to CRM contacts. | 1.0.0 | 0 | — | — | — |
| crm_campaign_addons | Campaign management for CRM with objects, calendar, and G... | 1.0.0 | 0 | — | — | — |
| crm_campaign_phase | Campaign phases with pricelists and country filtering. | 1.0.0 | 0 | — | — | `website_crm_campaign` |
| crm_campaign_phase_default_variant | Prefer campaign product variants as default. | 1.0.0 | 0 | — | — | — |
| crm_campaign_product | Link products to CRM campaigns. | 1.0.0 | 0 | — | — | — |
| crm_campaign_supplier | Link suppliers to CRM campaigns. | 1.0.0 | 0 | — | — | — |
| crm_enrich_base | Adding data. | 1.1.0 | 0 | — | — | — |
| crm_enrich_crawlai | AI-driven lead enrichment via a pi-python agent (website,... | 1.1.0 | 0 | — | — | — |
| crm_enrich_phonemail | Enrich CRM-leads records with companys website. | 1.1.0 | 0 | — | — | — |
| crm_fetchmail | Adds a server-action for fetching mail. | 1.0.0 | 0 | — | — | — |
| crm_lead_created_on | Shows the creation date and time (without seconds) in CRM... | 1.0.0 | 0 | — | — | — |
| crm_monitor | Add montitor capabilities to leads and opportunity | 1.0 | 8 | — | — | — |
