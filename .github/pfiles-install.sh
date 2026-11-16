#!/usr/bin/env bash
#
# pfiles-install.sh — installera en expanderad modul i rätt Odoo-utgåva.
#
# Steg 3 i CI. Skiljer medvetet på tre utfall, eftersom de kräver olika åtgärd:
#
#   OK        modulen installerades (rc=0)
#   MODULE    Odoo startade men modulen gick inte att ladda  -> trasig modul
#   ENV       Odoo gick inte att starta alls                 -> miljöfel
#
# Skillnaden är spec:ens krav "Saknad testmiljö skiljs från trasig modul". En
# trasig modul ska peka ut modulen; ett miljöfel ska peka ut miljön och inte
# anklaga koden.
#
# Användning:
#   .github/pfiles-install.sh <utgåva> <modulkatalog> [modulnamn]
#
# Miljö:
#   PFILES_OCB_SRC   befintligt OCB-repo (lokal körning). Saknas den klonas
#                    OCB shallow till PFILES_OCB_CACHE.
#   PFILES_OCB_CACHE katalog att klona till (default /tmp/pfiles-ocb)
#   PFILES_EXTRA_ADDONS  kolon-separerad lista av extra addons-kataloger
#                    (t.ex. ett odoo-base-arbetsträd med beroenden som inte
#                    finns i OCB). Saknade beroenden är ett miljöfel, inte en
#                    trasig modul.
#   PFILES_DB_NAME   databas (default pfiles_ci_<utgåva>)
#   PFILES_DB_USER / PFILES_DB_PASSWORD  roll (default odoo / pfiles-scratch)
#
# Exitkoder:
#   0  OK
#   2  felaktig användning
#   4  ENV  — Odoo/OCB/databas gick inte att få igång
#   6  MODULE — modulen laddades inte
#
set -euo pipefail

VERSION="${1:-}"
MODDIR="${2:-}"
MODNAME="${3:-}"
[ -n "$VERSION" ] && [ -n "$MODDIR" ] || {
  echo "pfiles-install: användning: pfiles-install.sh <utgåva> <modulkatalog> [modulnamn]" >&2
  exit 2
}
[[ "$VERSION" =~ ^[0-9]{2}\.0$ ]] || { echo "pfiles-install: utgåvan måste se ut som 20.0" >&2; exit 2; }

MODDIR="$(cd "$MODDIR" && pwd)"
MODNAME="${MODNAME:-$(basename "$MODDIR")}"

log()  { echo "pfiles-install: $*" >&2; }
env_fail() { echo "pfiles-install: ENV: $*" >&2; exit 4; }
mod_fail() { echo "pfiles-install: MODULE: $*" >&2; exit 6; }

# --- Odoo-källa -----------------------------------------------------------

OCB_SRC="${PFILES_OCB_SRC:-}"
OCB_CACHE="${PFILES_OCB_CACHE:-/tmp/pfiles-ocb}"

fresh_clone=0
if [ -z "$OCB_SRC" ]; then
  repo="$OCB_CACHE/OCB"
  if [ ! -d "$repo/.git" ]; then
    fresh_clone=1
    log "klonar OCB $VERSION shallow till $repo"
    rm -rf "$repo"
    mkdir -p "$OCB_CACHE"
    if ! timeout 900 git clone --quiet --depth 1 --branch "$VERSION" \
          https://github.com/OCA/OCB.git "$repo" 2>&1 | sed 's/^/pfiles-install: git: /' >&2; then
      env_fail "kunde inte klona OCB $VERSION — är nätverket/branchen tillgänglig?"
    fi
  else
    log "återanvänder OCB-klon $repo"
  fi
  OCB_SRC="$repo"
fi

[ -x "$OCB_SRC/odoo-bin" ] || env_fail "odoo-bin saknas i $OCB_SRC"

# PEP420: OCB 19/20 skeppar odoo/init.py men ingen odoo/__init__.py. Utan
# symlänken importeras den systeminstallerade Odoo i stället — tyst, och
# felen man ser pekar på fel sak.
#
# Länken läggs ENDAST på ett träd vi själva hämtade i den här körningen. Ett
# befintligt träd (lokal utveckling, återanvänd cache) lämnas orört: har
# någon tagit bort länken där ska assertionen nedan FALLA, inte reparera tyst.
# Samma princip som --fix i scripts/pfiles-ocb.sh.
if [ "$fresh_clone" -eq 1 ] && [ -f "$OCB_SRC/odoo/init.py" ] && [ ! -e "$OCB_SRC/odoo/__init__.py" ]; then
  log "lägger symlänk odoo/__init__.py -> init.py (PEP420-fix, ny klon)"
  ln -sfn init.py "$OCB_SRC/odoo/__init__.py" || env_fail "kunde inte lägga PEP420-symlänken"
fi

# --- hård versionsassertion ----------------------------------------------
# Utan denna kan hela steget köra 18.0 och rapportera 20.0-fel som aldrig fanns.
actual="$(PYTHONPATH="$OCB_SRC" python3 "$OCB_SRC/odoo-bin" --version 2>&1 | tail -1 || true)"
series="$(printf '%s' "$actual" | grep -oE '[0-9]{2}\.0' | head -1 || true)"
if [ "$series" != "$VERSION" ]; then
  env_fail "fel utgåva skulle köras: begärde $VERSION, fick '${series:-okänt}' ($actual)"
fi
log "Odoo $series i $OCB_SRC"

# --- databas --------------------------------------------------------------
# Peer-auth fungerar inte för shell-användaren; vi använder alltid TCP med
# explicit roll. Skapas databasen redan av workflowen återanvänds den.
DB="${PFILES_DB_NAME:-pfiles_ci_${VERSION//./_}}"

DB_USER="${PFILES_DB_USER:-odoo}"
DB_PASS="${PFILES_DB_PASSWORD:-pfiles-scratch}"

# En modul ska prövas i en REN databas. Annars ärver den grannmodulers
# halva installationer och fälls för fel som inte är dess eget — ett
# modulfel som i själva verket är ett testmetodfel. Workflowen sätter
# PFILES_DB_FRESH=1 och får då en ny databas per modul.
if [ "${PFILES_DB_FRESH:-0}" = "1" ] && command -v psql >/dev/null; then
  # Anslut som superuser över TCP. I CI är postgres en service-container där
  # rollen i POSTGRES_USER redan är superuser; lokalt krävs sudo -u postgres
  # eftersom shell-användaren saknar roll. Vi provar sudo först och faller
  # tillbaka på TCP, så samma skript fungerar på båda ställena.
  psql_admin() {
    if sudo -n -u postgres psql -v ON_ERROR_STOP=1 -tAc "SELECT 1" >/dev/null 2>&1; then
      sudo -n -u postgres psql -v ON_ERROR_STOP=1 -tAc "$1"
    else
      PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -U "$DB_USER" -d postgres \
        -v ON_ERROR_STOP=1 -tAc "$1"
    fi
  }
  psql_admin "DROP DATABASE IF EXISTS \"$DB\" WITH (FORCE)" >/dev/null 2>&1 || true
  psql_admin "CREATE DATABASE \"$DB\" OWNER \"$DB_USER\"" >/dev/null 2>&1 \
    || env_fail "kunde inte skapa en ren databas $DB (miljöfel)"
  psql_admin "ALTER ROLE \"$DB_USER\" WITH PASSWORD '$DB_PASS'" >/dev/null 2>&1 || true
fi

if command -v pg_isready >/dev/null; then
  pg_isready -q -h 127.0.0.1 || env_fail "PostgreSQL svarar inte på 127.0.0.1 (miljöfel)"
fi

# --- kör ------------------------------------------------------------------
# Vi kör i en kopia av modulkatalogen: Odoo skriver __pycache__ och kan i
# värsta fall skapa filer bredvid modulen, och CI-trädet ska förbli orört så
# att nästa utgåvas jämförelse inte påverkas.
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
addons="$work/addons"
mkdir -p "$addons"
cp -a "$MODDIR" "$addons/$MODNAME"

# Extra addons-kataloger (beroenden som bor utanför OCB). De läggs efter
# modulens egen katalog men före OCB:s, så en lokal kopia vinner över en
# eventuell OCB-version med samma namn.
addons_path="$addons"
if [ -n "${PFILES_EXTRA_ADDONS:-}" ]; then
  IFS=':' read -r -a extra <<< "$PFILES_EXTRA_ADDONS"
  for d in "${extra[@]}"; do
    [ -d "$d" ] || env_fail "extra addons-katalog saknas: $d"
    addons_path="$addons_path,$d"
    log "extra addons: $d"
  done
fi
addons_path="$addons_path,$OCB_SRC/addons,$OCB_SRC/odoo/addons"

logfile="$work/odoo.log"
set +e
PYTHONPATH="$OCB_SRC" python3 "$OCB_SRC/odoo-bin" \
  --addons-path="$addons_path" \
  --db_host=127.0.0.1 --db_port=5432 \
  --db_user="$DB_USER" --db_password="$DB_PASS" \
  -d "$DB" -i "$MODNAME" --stop-after-init --without-demo=all \
  --log-level=info >"$logfile" 2>&1
rc=$?
set -e

if [ "$rc" -eq 0 ]; then
  # rc=0 är inte nog: Odoo kan logga felet och ändå avsluta noll. Kontrollera
  # att modulen verkligen står som installerad, annars godkänner vi tyst en
  # modul som inte laddades.
  state="$(PYTHONPATH="$OCB_SRC" python3 "$OCB_SRC/odoo-bin" shell \
      --db_host=127.0.0.1 --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASS" \
      -d "$DB" --no-http 2>/dev/null <<PY || true
print(env['ir.module.module'].search([('name','=','$MODNAME')]).state or 'missing')
PY
)"
  state="$(printf '%s' "$state" | tail -1)"
  if [ "$state" != "installed" ]; then
    log "modulen är inte installerad (state='$state'), rc=$rc"
    tail -40 "$logfile" >&2
    mod_fail "$MODNAME installerades inte i $VERSION (state='$state')"
  fi
  log "OK: $MODNAME installerades i $VERSION"
  grep -E "ERROR|CRITICAL|Traceback" "$logfile" >&2 || true
  exit 0
fi

# Ett saknat BEROENDE är ett miljöfel: modulen är inte trasig, det är
# testsviten som inte fick med sig beroendet. Att klassa det som MODULE
# skickar utvecklaren att leta fel i sin egen kod.
# Odoo delar upp meddelandet på TVÅ rader:
#   You try to install module "x" that depends on module "y".
#   But the latter module is not available in your system.
# Ett grep efter hela frasen på en rad matchar därför aldrig — det var
# felet som först klassade saknade beroenden som trasiga moduler.
if grep -qF 'But the latter module is not available' "$logfile"; then
  missing="$(grep -oE 'depends on module "[^"]+"' "$logfile" | head -1 | sed 's/.*"\(.*\)"/\1/')"
  tail -20 "$logfile" >&2
  env_fail "beroendet '${missing:-okänt}' finns inte i addons-path — lägg till det med PFILES_EXTRA_ADDONS (miljöfel, inte modulfel)"
fi

# Skilj miljöfel från modulfel. En modul som inte kan laddas ger typiskt
# KeyError/ParseError/ValueError med modulnamnet i spåret, och Odoo hinner
# starta registret. Ett miljöfel (DB nekar, port stängd, fel lösenord) syns
# som anslutningsfel INNAN registret laddas.
if grep -qE "could not connect|Connection refused|password authentication failed|FATAL:|database .* does not exist|psycopg2.OperationalError" "$logfile"; then
  tail -30 "$logfile" >&2
  env_fail "kunde inte ansluta till databasen $DB (miljöfel, inte modulfel)"
fi

if grep -qE "CRITICAL.*Failed to (load|initialize) (registry|database)|Failed to initialize database" "$logfile"; then
  tail -40 "$logfile" >&2
  mod_fail "$MODNAME kunde inte laddas i $VERSION (rc=$rc) — se spåret ovan"
fi

tail -40 "$logfile" >&2
mod_fail "$MODNAME gav rc=$rc i $VERSION och kunde inte klassas som miljöfel"
