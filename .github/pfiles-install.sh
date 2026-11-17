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
user_supplied=1
if [ -z "$OCB_SRC" ]; then
  user_supplied=0
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

# Behåll en ärvd PYTHONPATH. Att sätta PYTHONPATH="$OCB_SRC" ensamt ERSÄTTER
# den, och då tappar Odoo de paket som ligger i site-packages (babel, jinja2).
# Felet ser ut som "fel utgåva skulle köras" eftersom --version kraschar.
ODOO_PYPATH="$OCB_SRC${PYTHONPATH:+:$PYTHONPATH}"

# PEP420: OCB 19/20 skeppar odoo/init.py men ingen odoo/__init__.py. Utan
# symlänken importeras den systeminstallerade Odoo i stället — tyst, och
# felen man ser pekar på fel sak.
#
# Länken läggs ENDAST på ett träd vi själva hämtade i den här körningen. Ett
# befintligt träd (lokal utveckling, återanvänd cache) lämnas orört: har
# någon tagit bort länken där ska assertionen nedan FALLA, inte reparera tyst.
# Samma princip som --fix i scripts/pfiles-ocb.sh.
# Länken läggs när trädet är VÅRT (klonat eller cachet av det här skriptet).
# Ett träd användaren pekat ut med PFILES_OCB_SRC lämnas orört: där ska en
# borttagen länk fällas av assertionen nedan, inte lagas tyst — annars kan
# utvecklaren aldrig upptäcka att den egna miljön kör fel utgåva.
if [ "$user_supplied" -eq 0 ] && [ -f "$OCB_SRC/odoo/init.py" ] && [ ! -e "$OCB_SRC/odoo/__init__.py" ]; then
  log "lägger symlänk odoo/__init__.py -> init.py (PEP420-fix)"
  ln -sfn init.py "$OCB_SRC/odoo/__init__.py" || env_fail "kunde inte lägga PEP420-symlänken"
fi

# --- hård versionsassertion ----------------------------------------------
# Utan denna kan hela steget köra 18.0 och rapportera 20.0-fel som aldrig fanns.
actual="$(PYTHONPATH="$ODOO_PYPATH" python3 "$OCB_SRC/odoo-bin" --version 2>&1 | tail -1 || true)"
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
if [ "${PFILES_DB_FRESH:-0}" = "1" ]; then
  # Utan psql-klient kan vi inte garantera en ren databas. Att då köra vidare
  # mot en databas som redan har grannmodulerna installerade ger falskt grönt:
  # en trasig modul "installeras" utan att något laddas, eftersom Odoo hoppar
  # över en modul som redan står som installerad. Det hände på en runner utan
  # psql — linkedin_contacts med en trasig xpath rapporterades som OK.
  command -v psql >/dev/null \
    || env_fail "PFILES_DB_FRESH=1 men psql saknas — kan inte skapa en ren databas (miljöfel)"
  # Anslut som superuser över TCP. I CI är postgres en service-container där
  # rollen i POSTGRES_USER redan är superuser; lokalt krävs sudo -u postgres
  # eftersom shell-användaren saknar roll. Vi provar sudo först och faller
  # tillbaka på TCP, så samma skript fungerar på båda ställena.
  psql_admin() {
    if sudo -n -u postgres psql -v ON_ERROR_STOP=1 -tAc "SELECT 1" >/dev/null 2>&1; then
      sudo -n -u postgres psql -v ON_ERROR_STOP=1 -tAc "$1"
    else
      # I CI ar POSTGRES_USER redan superuser men har ett annat losenord an
      # DB_PASS. Vi provar DB_PASS forst och faller tillbaka pa losenordet
      # postgres-tjansten satt, annars misslyckas CREATE DATABASE tyst och
      # varje modul blir ENV av fel anledning.
      if PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -U "$DB_USER" -d postgres \
           -v ON_ERROR_STOP=1 -tAc "SELECT 1" >/dev/null 2>&1; then
        PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -U "$DB_USER" -d postgres \
          -v ON_ERROR_STOP=1 -tAc "$1"
      else
        PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -h 127.0.0.1 -U "$DB_USER" -d postgres \
          -v ON_ERROR_STOP=1 -tAc "$1"
      fi
    fi
  }
  # DROP kan misslyckas tyst om en anslutning ligger kvar. Da finns databasen
  # kvar med grannmodulerna installerade och nasta modul "installeras" utan
  # att nagot laddas. Vi kollar efterat att databasen verkligen ar borta och
  # skapar den sedan — ordningen maste vara DROP -> verifiera -> CREATE.
  psql_admin "DROP DATABASE IF EXISTS \"$DB\" WITH (FORCE)" >/dev/null 2>&1 || true
  still_there="$(psql_admin "SELECT 1 FROM pg_database WHERE datname='$DB'" 2>/dev/null | tr -d ' ' || true)"
  if [ -n "$still_there" ]; then
    psql_admin "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB'" >/dev/null 2>&1 || true
    psql_admin "DROP DATABASE IF EXISTS \"$DB\" WITH (FORCE)" >/dev/null 2>&1 || true
    still_there="$(psql_admin "SELECT 1 FROM pg_database WHERE datname='$DB'" 2>/dev/null | tr -d ' ' || true)"
    [ -z "$still_there" ] || env_fail "kunde inte ta bort databasen $DB (miljöfel)"
  fi
  if ! psql_admin "CREATE DATABASE \"$DB\" OWNER \"$DB_USER\"" >/dev/null 2>&1; then
    # Visa VARFOR det gick fel, inte bara att det gick fel. Utan orsaken gar
    # det inte att skilja en trasig miljo fran en trasig grind.
    why="$(psql_admin "CREATE DATABASE \"$DB\" OWNER \"$DB_USER\"" 2>&1 | head -2 | tr '\n' ' ')"
    env_fail "kunde inte skapa en ren databas $DB (miljöfel): $why"
  fi
  psql_admin "ALTER ROLE \"$DB_USER\" WITH PASSWORD '$DB_PASS'" >/dev/null 2>&1 || true

  # Verifiera att databasen verkligen ar NY. Om DROP/CREATE tyst misslyckades
  # (fel roll, ingen rattighet) skulle modulen koras mot en databas dar
  # grannarna redan ar installerade — och da ar "installerad" ett falskt
  # gront, eftersom Odoo hoppar over en modul som redan star som installerad.
  # Rak TCP-anslutning som primar vag. psql_admin valjer sudo forst, och i
  # en runner dar sudo finns men postgres-rollen inte gor det kan det ge tom
  # utdata — vilket gjorde att ALLA moduler rapporterades som "inte ren
  # databas". Samma anslutningssatt som workflowens miljosteg anvander.
  n_tables="$(PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -U "$DB_USER" -d "$DB" \
      -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" \
      2>/dev/null | tr -d ' \n' || true)"
  if [ -z "$n_tables" ]; then
    n_tables="$(psql_admin "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null | tr -d ' \n' || true)"
  fi
  if [ "${n_tables:-x}" != "0" ]; then
    env_fail "databasen $DB ar inte ren (${n_tables:-okant} tabeller) — kan inte bevisa nagot om modulen (miljofel)"
  fi
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
    # Hoppa over kataloger som inte finns i stallet for att falla. Listan
    # kommer fran en sokning i .deps och kan innehalla t.ex. docs/ som inte
    # ar en addons-katalog; att falla pa en sadan gor att HELA sokvagen
    # forkastas och modulen rapporteras sakna ett beroende den hade.
    [ -d "$d" ] || continue
    addons_path="$addons_path,$d"
  done
fi
addons_path="$addons_path,$OCB_SRC/addons,$OCB_SRC/odoo/addons"

logfile="$work/odoo.log"
set +e
PYTHONPATH="$ODOO_PYPATH" python3 "$OCB_SRC/odoo-bin" \
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
  # Las modulens state ur databasen. Vi fragar efter en MARKOR i utdata i
  # stallet for att lita pa sista raden: odoo-bin shell skriver en banner och
  # kan skriva varningar efter svaret, sa `tail -1` kan ge en varning som
  # state. Det gjorde att ett falskt gront slank igenom pa en runner.
  state="$(PYTHONPATH="$ODOO_PYPATH" python3 "$OCB_SRC/odoo-bin" shell \
      --db_host=127.0.0.1 --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASS" \
      -d "$DB" --no-http 2>/dev/null <<PYSTATE || true
print("PFILES_STATE=" + (env['ir.module.module'].search([('name','=','$MODNAME')]).state or 'missing'))
PYSTATE
)"
  state="$(printf '%s\n' "$state" | grep -o 'PFILES_STATE=.*' | head -1 | cut -d= -f2)"

  # Tom state betyder att fragan aldrig nadde databasen — det ar ett miljofel,
  # inte ett godkannande. Utan den kontrollen blir ett trasigt svar "OK".
  if [ -z "$state" ]; then
    tail -20 "$logfile" >&2
    env_fail "kunde inte lasa modulstatus for $MODNAME i $DB (miljofel)"
  fi
  if [ "$state" != "installed" ]; then
    log "modulen ar inte installerad (state='$state'), rc=$rc"
    # 'uninstallable' betyder att Odoo sjalv fann modulen oinstallerbar —
    # nastan alltid ett beroende som inte finns. Det ar ett miljofel, inte
    # en trasig modul, och ska inte skicka utvecklaren att leta i sin kod.
    # Vilka beroenden som saknas star i loggen (Module <x> not found).
    # Fraga databasen vilka beroenden modulen har och om de finns. Forst om
    # ett beroende SAKNAS ar det ett miljofel. 'uninstallable' med alla
    # beroenden pa plats betyder att modulen sjalv ar trasig (t.ex. en vy som
    # inte kan laddas) och da ar MODULE ratt svar.
    if [ "$state" = "uninstallable" ]; then
      deps_ok="$(PYTHONPATH="$ODOO_PYPATH" python3 "$OCB_SRC/odoo-bin" shell \
          --db_host=127.0.0.1 --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASS" \
          -d "$DB" --no-http 2>/dev/null <<PYDEPS || true
m = env['ir.module.module'].search([('name','=','$MODNAME')])
deps = m.dependencies_id.mapped('name')
have = set(env['ir.module.module'].search([('name','in',deps)]).mapped('name'))
missing = sorted(set(deps) - have)
print("PFILES_MISSING=" + (",".join(missing) if missing else "NONE"))
PYDEPS
)"
      deps_ok="$(printf '%s\n' "$deps_ok" | grep -o 'PFILES_MISSING=.*' | head -1 | cut -d= -f2)"
      if [ -n "$deps_ok" ] && [ "$deps_ok" != "NONE" ]; then
        tail -20 "$logfile" >&2
        env_fail "$MODNAME ar oinstallerbar i $VERSION — saknade beroenden: $deps_ok (miljofel)"
      fi
      # Alla beroenden finns: modulen ar trasig, inte miljon.
      tail -40 "$logfile" >&2
      mod_fail "$MODNAME ar oinstallerbar i $VERSION trots att beroendena finns — modulen kan inte laddas"
    fi
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
