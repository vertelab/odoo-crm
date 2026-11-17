#!/usr/bin/env python3
"""pfiles-check — hitta filer som borde vara p-filer men inte är det.

Kontrollerar en modulkatalog (eller ett helt repo) och rapporterar:

  MISSING_SOURCE  genererad fil utan .p-källa  (FEL)
  STALE           utdata skiljer sig från expansionen (FEL)
  MANUAL_PFILE    p-fil, men ingen genererad fil  (FEL)
  ORPHAN_PFILE    .p-fil utan giltig utdata  (FEL)
  UNEXPLAINED     källfil utan p-motsvarighet och inte vitlistad (FEL)
  PAIRED          .p.x + x finns — OK
  ALLOWED         vitlistad — OK
  NOT_APPLICABLE  saknar stöd för preprocess — OK

Utgåvespecifika säkerhetskontroller (Odoo 20 bytte form på ir.model.access):

  WRONG_SECURITY_FORMAT  säkerhetsfilen har fel form för utgåvan (FEL)
  UNLISTED_SECURITY_FILE manifestet laddar en säkerhetsfil utgåvan inte kan läsa (FEL)
  BAD_DOMAIN_NAME        domän använder namn utanför utgåvans eval-kontext (FEL)

Användning:
  ./pfiles-check.py --version 18.0 /path/till/modul [...]
  ./pfiles-check.py --version 18.0 --json /path/till/repo
  ./pfiles-check.py --version 18.0 --print-allow /path | sudo tee .../.pfiles-allow

Vitlista: <repo- eller modulrot>/.pfiles-allow — en sökväg per rad,
relativ till roten. '#' inleder kommentar. Glöm inte '!' vid generering.

Exit: 0 = inga fel, 1 = fel hittade, 2 = användningsfel.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Filändelser som preprocess hanterar (jfr /skill:odoo-pfiles)
PREPROCESS_EXTS = (".py", ".xml", ".js", ".csv", ".sh", ".html", ".htm", ".pl",
                   ".rb", ".tcl", ".c", ".h", ".cpp", ".java", ".php")
# Filer som alltid är källor, aldrig genereras
EXCLUDED_NAMES = {"__init__.py", "__manifest__.py", "__manifest__.p.py"}
EXCLUDED_DIRS = {".git", "__pycache__", ".tox", ".venv", "venv", "node_modules",
                 ".idea", ".mypy_cache", ".pytest_cache"}
# p-fil-ändelser: (p-ändelse, utdata-ändelse). Ordningen har betydelse — längsta först.
PFILE_SUFFIXES = [(".p.py", ".py"), (".p.xml", ".xml"), (".p.js", ".js"),
                  (".p.csv", ".csv"), (".p.sh", ".sh"), (".p.html", ".html"),
                  (".p.htm", ".htm"), (".p.pl", ".pl"), (".p.rb", ".rb"),
                  (".p.tcl", ".tcl"), (".p.c", ".c"), (".p.h", ".h"),
                  (".p.cpp", ".cpp"), (".p.java", ".java"), (".p.php", ".php")]

OK, ERR = "OK", "ERROR"


# ---------------------------------------------------------------------------
# Utgåveprofiler
#
# Säkerhetsdatan för ir.model.access bytte form i Odoo 20.0:
#
#   18.0/19.0                20.0
#   fil  ir.model.access.csv  ir.access.csv      <- FILNAMNET avgör modellen
#   model_id:id               model_id           <- naket modellnamn
#   group_id:id               group_id/id
#   perm_read/write/create/unlink   operation     <- 'crud' etc.
#   (ir.rule separat)         domain-kolumn
#
# Filnamnet är inte kosmetik: Odoo 20 läser modellnamnet ur filnamnets prefix
# FÖRE innehållet (convert_csv_import). En ny-format fil som ligger i
# ir.model.access.csv fäller alltså fortfarande med KeyError: 'ir.model.access'.
#
# Verifierat 2026-11-16: 18/19 har tabellen ir_model_access, 20.0 har ir_access.
# OCB 19.0 är gammalt format (ingen ir_access.py) — bara 20.0 är nytt.
# ---------------------------------------------------------------------------
EDITION_PROFILES = {
    "18.0": {
        "security_filename": "ir.model.access.csv",
        "security_model": "ir.model.access",
        "security_format": "legacy",
        "security_columns": ("id", "name", "model_id:id", "group_id:id",
                             "perm_read", "perm_write", "perm_create", "perm_unlink"),
    },
    "19.0": {
        "security_filename": "ir.model.access.csv",
        "security_model": "ir.model.access",
        "security_format": "legacy",
        "security_columns": ("id", "name", "model_id:id", "group_id:id",
                             "perm_read", "perm_write", "perm_create", "perm_unlink"),
    },
    "20.0": {
        "security_filename": "ir.access.csv",
        "security_model": "ir.access",
        "security_format": "modern",
        "security_columns": ("id", "name", "model_id", "group_id/id",
                             "operation", "domain"),
    },
}

# Filer som hör till den gamla respektive nya säkerhetsformen. Används för att
# upptäcka en fil som ligger kvar i fel form för utgåvan.
SECURITY_FILENAMES = {"ir.model.access.csv", "ir.access.csv"}

# Domännamn som INTE finns i 20.0:s eval-kontext (_eval_context ger bara
# user, time, company_ids, company_id). 'uid' ger NameError vid installation.
BAD_DOMAIN_NAMES_MODERN = {"uid": "user.id"}

def edition_profile(version):
    """Profil för en utgåva. Okänd utgåva ger None (hoppa över formatkontroll)."""
    return EDITION_PROFILES.get(version)


def pfile_split(name):
    """a.p.py -> ('a.py', '.p.py');  a.py -> (None, None)."""
    for psuffix, suffix in PFILE_SUFFIXES:
        if name.endswith(psuffix):
            return name[: -len(psuffix)] + suffix, psuffix
    return None, None


def pepfile_hint(name):
    """a.xml -> a.p.xml, a.py -> a.p.py.

    Konventionen är att '.p' sätts IN före ändelsen, inte efter hela namnet.
    Det måste stämma med pfile_split: 'a.p.py' -> 'a.py'. Att föreslå
    'a.py.p.py' (som en tidigare version gjorde) ger pfile_split 'a.py.py'
    och skapar ett nytt fel i stället för att lösa det.
    """
    for psuffix, suffix in PFILE_SUFFIXES:
        if name.lower().endswith(suffix):
            return name[: -len(suffix)] + ".p" + suffix
    return name + ".p"


def is_preprocessable(name):
    return not name.startswith(".") and name.lower().endswith(PREPROCESS_EXTS)


def find_roots(paths, explicit):
    """Hitta modulrötter (katalog med __manifest__.py eller *.p.py) under paths."""
    if explicit:
        return [os.path.abspath(p) for p in paths]

    # Är en angiven sökväg redan en modulrot?
    roots = []
    for p in paths:
        p = os.path.abspath(p)
        direct = (os.path.isfile(os.path.join(p, "__manifest__.py")) or
                  any(f.endswith(".p.py") for f in os.listdir(p) if f.endswith(".py")))
        if direct:
            roots.append(p)
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
            if "__manifest__.py" in filenames:
                roots.append(dirpath)
                dirnames[:] = []   # moduler ligger inte inuti moduler
    return roots


def load_allow(root):
    """Läs .pfiles-allow från root eller repo-överliggande katalog."""
    allow, source = set(), None
    candidate = root
    for _ in range(4):                        # root, root/.., root/../.., ...
        f = os.path.join(candidate, ".pfiles-allow")
        if os.path.isfile(f):
            source = f
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.split("#", 1)[0].strip()
                    if line:
                        allow.add(os.path.normpath(line))
            break
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    return allow, source


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


# ---------------------------------------------------------------------------
# Säkerhetskontroller per utgåva (2.2, 2.3, 2.4)
# ---------------------------------------------------------------------------

def load_manifest(root):
    """Läs modulens manifest som en dict. None om det inte går.

    Föredrar __manifest__.py; faller tillbaka på __manifest__.p.py eftersom
    p-filen är källan när den finns. literal_eval fungerar på p-manifestet:
    villkoren ligger i kommentarer (# #if), inte i Pythonsyntax.
    """
    for name in ("__manifest__.py", "__manifest__.p.py"):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                value = ast.literal_eval(fh.read())
        except (OSError, SyntaxError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def csv_header(path):
    """Första raden i en CSV som en lista fält, eller None."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            first = fh.readline()
    except OSError:
        return None
    if not first.strip():
        return None
    return [c.strip() for c in next(csv.reader([first]))]


def csv_rows(path):
    """Alla datarader (inte header) i en CSV."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return []
    return [r for r in rows[1:] if r and any(c.strip() for c in r)]


def security_findings(root, version):
    """Kontrollera säkerhetsfilerna mot utgåvans profil.

    Tre fel (alla ERROR, alla skulle fälla en installation):

      WRONG_SECURITY_FORMAT  filen har fel form för utgåvan
                             (t.ex. perm_read-kolumner i 20.0, eller
                              operation/domain i 18.0)
      UNLISTED_SECURITY_FILE en säkerhetsfil ligger i modulen men laddas inte
                             av manifestets data — död vikt, och i värsta fall
                             en tyst överraskning när någon lägger till den
      BAD_DOMAIN_NAME        domän använder ett namn som inte finns i
                             utgåvans eval-kontext (uid i 20.0)

    Returnerar (findings, info) där info är en dict för --json.
    """
    profile = edition_profile(version)
    findings = []
    info = {"profile": None, "present": [], "listed": []}
    if profile is None:
        return findings, info
    info["profile"] = profile["security_format"]

    secdir = os.path.join(root, "security")
    present = []
    if os.path.isdir(secdir):
        for name in sorted(os.listdir(secdir)):
            if name in SECURITY_FILENAMES or name.endswith(".p.csv"):
                present.append(name)
    info["present"] = present

    # Vilka säkerhetsfiler manifestet faktiskt laddar. Bara de kan falla en
    # installation — en fil som ligger i security/ men inte listas laddas
    # aldrig, och ska därför inte bedömas (spec: "Fil för annan utgåva finns
    # men laddas inte"). Det är själva poängen med D1: bada filerna ligger
    # sida vid sida och manifestet valjer.
    manifest = load_manifest(root) or {}
    listed_secs = set()
    for entry in manifest.get("data", []) or []:
        if os.path.basename(entry).endswith(".csv") and \
           os.path.basename(entry) in SECURITY_FILENAMES:
            listed_secs.add(entry)

    # 2.2 — rätt format för utgåvan, för både utdata och p-källa
    expected = profile["security_columns"]
    # En .p.csv vars utdata redan rapporterats ger samma fel två gånger. Vi
    # hoppar över p-källan när dess utdatafil ligger i samma katalog — felet
    # är detsamma och användaren ska åtgärda paret, inte två filer.
    reported = set()
    for name in present:
        if name.endswith(".p.csv"):
            out = name[: -len(".p.csv")] + ".csv"
            if out in present:
                reported.add(name)
    for name in present:
        if name in reported:
            continue
        path = os.path.join(secdir, name)
        # Bara den fil manifestet laddar bedöms. Den andra utgåvans fil är
        # harmlös och ska inte ge ett fel — annars kan D1 aldrig användas.
        if ("security/" + name) not in listed_secs:
            continue
        header = csv_header(path)
        if header is None:
            continue                     # tom/headerlös — annan kontroll fångar det
        # En .p.csv är en källa; dess header är samma oavsett utgåva bara om
        # villkoren styr raderna. Vi kontrollerar bara utdatafilerna, plus
        # p-källan för att ge ett tidigt besked.
        looks_legacy = "perm_read" in header
        looks_modern = "operation" in header
        if profile["security_format"] == "modern" and looks_legacy:
            findings.append((ERR, "WRONG_SECURITY_FORMAT", rel(root, path),
                             f"{name} har gammalt format (perm_*-kolumner) men "
                             f"utgåvan {version} kräver {profile['security_filename']} "
                             f"med kolumnerna {','.join(expected)}"))
        elif profile["security_format"] == "legacy" and looks_modern:
            findings.append((ERR, "WRONG_SECURITY_FORMAT", rel(root, path),
                             f"{name} har nytt format (operation/domain) men "
                             f"utgåvan {version} kräver {profile['security_filename']}"))
        elif not looks_legacy and not looks_modern and header != list(expected):
            findings.append((ERR, "WRONG_SECURITY_FORMAT", rel(root, path),
                             f"{name} har oväntad header: {','.join(header)} — "
                             f"väntade {','.join(expected)}"))

        # Fel filnamn för formen: nytt format i ir.model.access.csv fäller
        # fortfarande eftersom Odoo 20 tar modellen ur filnamnet.
        if looks_modern and name == "ir.model.access.csv":
            findings.append((ERR, "WRONG_SECURITY_FORMAT", rel(root, path),
                             f"nytt format ligger i {name} — Odoo 20 tar modellen ur "
                             f"FILNAMNET före innehållet, så filen måste heta "
                             f"ir.access.csv"))

    # 2.3 — bara den valda säkerhetsfilen får ligga i manifestets data
    manifest = load_manifest(root)
    if manifest is not None:
        data = manifest.get("data") or []
        listed = [d for d in data
                  if isinstance(d, str) and os.path.basename(d) in SECURITY_FILENAMES]
        info["listed"] = listed
        want = f"security/{profile['security_filename']}"
        manifest_name = "__manifest__.py"
        if not os.path.isfile(os.path.join(root, manifest_name)):
            manifest_name = "__manifest__.p.py"
        if len(listed) > 1:
            findings.append((ERR, "UNLISTED_SECURITY_FILE", manifest_name,
                             f"manifestet listar flera säkerhetsfiler: "
                             f"{', '.join(listed)} — bara {want} kan laddas"))
        for entry in listed:
            if os.path.basename(entry) != profile["security_filename"]:
                findings.append((ERR, "UNLISTED_SECURITY_FILE", manifest_name,
                                 f"manifestet laddar {entry}, men utgåvan {version} "
                                 f"kräver {want}"))
        # En säkerhetsfil som finns men inte listas är död vikt. I sig inte
        # ett fel (den laddas aldrig), men den är en tyst fälla: läggs den
        # till i data utan att byta form fäller den. Rapporteras som varning.

    # 2.4 — domännamn som inte finns i utgåvans eval-kontext
    if profile["security_format"] == "modern":
        for name in present:
            path = os.path.join(secdir, name)
            header = csv_header(path)
            if not header or "domain" not in header:
                continue
            idx = header.index("domain")
            for lineno, row in enumerate(csv_rows(path), start=2):
                if len(row) <= idx:
                    continue
                # Odoo skriver domänen med kommatecken UTAN citattecken
                # ([('user_id','=',user.id)]), så csv-modulen delar upp den i
                # flera kolumner. En naiv läsning av row[idx] ser bara första
                # fragmentet ("[('user_id'") och missar 'uid' i svansen.
                # Slå ihop allt från idx och framåt — det är domänen.
                dom = ",".join(row[idx:])
                if not dom.strip():
                    continue
                for bad, good in BAD_DOMAIN_NAMES_MODERN.items():
                    if re.search(rf"\b{re.escape(bad)}\b", dom):
                        findings.append((ERR, "BAD_DOMAIN_NAME",
                                         f"{rel(root, path)}:{lineno}",
                                         f"domänen använder '{bad}' som inte finns i "
                                         f"20.0:s eval-kontext (user, time, "
                                         f"company_ids, company_id) — använd '{good}'"))
    return findings, info


def expand_ok(preprocess, pfile, outfile, version, repo, tmpdir, cache):
    """Returnerar (status, detalj) där status är OK/STALE/ERROR."""
    if preprocess is None:
        return "ERROR", "preprocess saknas — kan inte verifiera expansion"
    if pfile not in cache:
        candidate = os.path.join(tmpdir, os.path.basename(outfile) or "out")
        if os.path.exists(candidate):
            os.remove(candidate)
        cmd = [preprocess, "-f", "-D", f"VERSION={version}", "-D", f"REPO={repo}",
               "-o", candidate, pfile]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            cache[pfile] = ("ERROR", "preprocess timeout")
            return cache[pfile]
        if proc.returncode != 0:
            cache[pfile] = ("ERROR", f"preprocess misslyckades: {proc.stderr.strip()[:300]}")
            return cache[pfile]
        try:
            with open(candidate, "rb") as fh:
                cache[pfile] = (OK, fh.read())
        except OSError as exc:
            cache[pfile] = ("ERROR", f"kunde inte läsa expansionen: {exc}")
        if os.path.exists(candidate):
            os.remove(candidate)
    status, value = cache[pfile]
    if status != OK:
        return status, value
    try:
        with open(outfile, "rb") as fh:
            actual = fh.read()
    except OSError as exc:
        return "ERROR", f"kunde inte läsa utdata: {exc}"
    if actual != value:
        return "STALE", "utdata skiljer sig från expansionen — kör om preprocess"
    return OK, "matchar expansionen"


def check_root(root, version, exclude_allow, preprocess, tmpdir):
    allow, allow_src = load_allow(root)
    findings, cache = [], {}

    # Samla alla filer
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for name in sorted(filenames):
            files.append(os.path.join(dirpath, name))

    pfile_targets = {}
    for f in files:
        target, _ = pfile_split(os.path.basename(f))
        if target is not None:
            pfile_targets[os.path.join(os.path.dirname(f), target)] = f

    for f in files:
        name = os.path.basename(f)
        target, psuffix = pfile_split(name)
        relpath = rel(root, f)
        # Vitlistan är modul-kvalificerad: "modul/models/x.py". En platt rad
        # ("models/x.py") matchar BARA om modulnamnet inte är känt — annars
        # skulle en rad för en modul tysta samma filnamn i en annan modul.
        allowed = f"{os.path.basename(root)}/{relpath}" in allow

        if target is not None:                                  # en p-fil
            outfile = os.path.join(os.path.dirname(f), target)
            if not os.path.isfile(outfile):
                findings.append((ERR, "MANUAL_PFILE", rel(root, f),
                                 f"{name} saknar genererad {target}"))
                continue
            if exclude_allow:
                st, detail = expand_ok(preprocess, f, outfile, version,
                                       os.path.basename(root), tmpdir, cache)
                findings.append((OK if st == OK else ERR,
                                 "PAIRED" if st == OK else st, rel(root, f), detail))
            else:
                findings.append((OK, "PAIRED", rel(root, f), "har genererad utdata"))
            continue

        if name in EXCLUDED_NAMES or not is_preprocessable(name):
            continue

        source = pfile_targets.get(f)                           # genererad fil?
        if source:
            if exclude_allow:
                continue        # p-filen rapporterar redan PARED/STALE
            try:
                with open(f, "rb") as fh:
                    generated = fh.read()
                with open(source, "rb") as fh:
                    origin = fh.read()
            except OSError as exc:
                findings.append((ERR, "STALE", rel(root, f), str(exc)))
                continue
            # Jämförelsen måste faktiskt användas. Tidigare beräknades `same`
            # men resultatet slängdes: filen rapporterades alltid som identisk
            # med p-filen, även när den inte var det. I --no-expand-läget var
            # STALE därför omöjligt att få — en tyst falsk grön.
            if generated == origin:
                findings.append((OK, "PAIRED", rel(root, f), "identisk med p-filen"))
            else:
                findings.append((ERR, "STALE", rel(root, f),
                                 f"skiljer sig från {rel(root, source)} — "
                                 f"kör om preprocess (eller redigera p-filen, "
                                 f"inte utdatafilen)"))
            continue

        if allowed:
            findings.append((OK, "ALLOWED", rel(root, f), "vitlistad i .pfiles-allow"))
        else:
            findings.append((ERR, "UNEXPLAINED", rel(root, f),
                             f"{name} är varken p-fil eller genererad — döp till "
                             f"{pepfile_hint(name)} "
                             f"eller vitlista i .pfiles-allow"))

    # Utgåvespecifika säkerhetskontroller (2.2, 2.3, 2.4). De läggs till efter
    # täckningskontrollen så att de alltid körs, även med --no-expand.
    sec_findings, sec_info = security_findings(root, version)
    findings.extend(sec_findings)
    return findings, allow_src, allow, sec_info


def main(argv=None):
    ap = argparse.ArgumentParser(description="Hitta filer som saknar p-fil.")
    ap.add_argument("paths", nargs="+", help="moduler/repon att kontrollera")
    ap.add_argument("--version", default=os.environ.get("VERSION", ""),
                    help="Odoo-utgåva, t.ex. 18.0 (default: $VERSION)")
    ap.add_argument("--repo", default=None, help="REPO-definition (default: modulnamn)")
    ap.add_argument("--json", action="store_true", help="maskinläsbar utdata")
    ap.add_argument("--no-expand", action="store_true",
                    help="hoppa over expansionskontroll (bara täckning)")
    ap.add_argument("--print-allow", action="store_true",
                    help="skriv förslag till .pfiles-allow (UNEXPLAINED → rader)")
    ap.add_argument("-q", "--quiet", action="store_true", help="bara fel")
    args = ap.parse_args(argv)

    if not args.version and not args.no_expand:
        ap.error("--version krävs (eller $VERSION) — utdata beror på utgåvan")

    roots = find_roots(args.paths, explicit=False)
    if not roots:
        print("Hittade inga modulrötter (katalog med __manifest__.py eller *.p.py).",
              file=sys.stderr)
        return 2

    preprocess = None if args.no_expand else shutil.which("preprocess")
    tmpdir = tempfile.mkdtemp(prefix="pfiles-check-")
    all_findings, total_err = [], 0

    try:
        for root in roots:
            findings, allow_src, allow, sec_info = check_root(
                root, args.version, not args.no_expand, preprocess, tmpdir)
            errs = [f for f in findings if f[0] == ERR]
            total_err += len(errs)
            all_findings.append({"root": root, "allow": allow_src, "findings": findings,
                                 "errors": len(errs), "security": sec_info})
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if args.print_allow:
        seen = set()
        for entry in all_findings:
            root = entry["root"]
            for sev, kind, path, _ in entry["findings"]:
                if kind == "UNEXPLAINED":
                    line = f"{os.path.basename(root)}/{path}"
                    if line not in seen:
                        seen.add(line)
                        print(line)
        return 0

    if args.json:
        print(json.dumps({"version": args.version, "preprocess": preprocess,
                          "roots": all_findings}, indent=2, ensure_ascii=False))
        return 1 if total_err else 0

    for entry in all_findings:
        rows = entry["findings"]
        shown = [r for r in rows if args.quiet is False or r[0] == ERR]
        print(f"=== {entry['root']}  ({entry['errors']} fel av {len(rows)} poster)")
        if entry["allow"]:
            print(f"    vitlista: {entry['allow']}")
        for sev, kind, path, detail in shown:
            mark = "✗" if sev == ERR else "✓"
            print(f"  {mark} {kind:<14} {path}")
            if sev == ERR or not args.quiet:
                print(f"      {detail}")
        missing = [r for r in rows if r[1] == "UNEXPLAINED"]
        if missing:
            print(f"    → {len(missing)} vitliknande rad(er). "
                  f"Generera: pfiles-check --version {args.version} --print-allow <rot>")
        if not rows:
            print("  (inga p-filer och inga kandidater — modulen använder inte p-filer)")

    if preprocess is None and not args.no_expand:
        print("\n⚠ preprocess saknas i PATH — endast täckningskontroll gjord. "
              "Installera: python3 -m pip install --break-system-packages preprocess", file=sys.stderr)
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
