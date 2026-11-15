# odoo-crm — gren 19.0

> **Denna gren är avsiktligt tom.** Modulerna är INTE portade till Odoo 19.
> Grenen finns så att dev-miljöer (`hansolo19`) kan klona den utan att falla,
> men den påstår ingenting om att koden är portad.

## Baseline

| | |
|---|---|
| Källa | `20.0` |
| Moduler | **15** |
| Grenar i repot | `12.0`, `13.0`, `14.0`, `16.0`, `17-wip_bolagsfakta`, `17.0`, `18.0`, `20.0`, `iammiracle/crm_linkedin`, `master`, `master10` |

## Moduler

- `crm_ai`
- `crm_allabolag`
- `crm_bolagsfakta`
- `crm_builtwith`
- `crm_campaign_addons`
- `crm_campaign_phase`
- `crm_campaign_phase_default_variant`
- `crm_campaign_product`
- `crm_campaign_supplier`
- `crm_enrich_base`
- `crm_enrich_crawlai`
- `crm_enrich_phonemail`
- `crm_fetchmail`
- `crm_lead_created_on`
- `crm_monitor`

## Blockerare

✅ Inga externa beroenden saknas i Odoo 19-kärnan eller OCA 19.0.

Modulerna kan troligen portas utan att vänta på externa bidrag.

## Nästa steg

Portering sker på `*-pfile`-maskin med versionsagnostisk kod
(`.p.py` / `.p.xml`). Se `/skill:odoo-pfiles`.
