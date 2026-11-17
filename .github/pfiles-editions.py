#!/usr/bin/env python3
"""pfiles-editions.py — läs .pfiles-ci och skriv utgåvorna som CI behöver.

Workflowen behöver veta två saker: vilka utgåvor som ska köras, och vilka som
faktiskt har en branch. Det här skriptet svarar på båda och skiljer på
"utgåvan är avstängd" och "utgåvan är efterfrågad men grenen saknas" — det
senare är ett konfigurationsfel, inte en trasig modul.

Användning:
    scripts/pfiles-editions.py --repo . --format json
    scripts/pfiles-editions.py --repo . --format github-matrix
    scripts/pfiles-editions.py --repo . --check        # bara validering

Utdata (--format json):
    {"editions": ["18.0", "19.0", "20.0"], "missing_branches": [], "source": ".pfiles-ci"}

--format github-matrix skriver det som actions-matrix förväntar:
    {"edition": ["18.0", "19.0", "20.0"]}

Exitkoder:
    0  konfigurationen är läsbar och alla efterfrågade grenar finns
    2  felaktig användning
    5  konfigurationsfel (okänd utgåva, gren saknas, trasig syntax)

Skriptet frågar git efter grenar. I CI är checkouten shallow, så workflowen
hämtar grenarna först (fetch-depth: 0); saknas de ändå rapporteras det som
miljöfel av workflowen, inte härifrån.
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Samma uppsättning som EDITION_PROFILES i pfiles-check.py. En utgåva som
# saknas där skulle köra täckningskontrollen utan formatkontroll, vilket är
# precis den tysta halvkontroll vi vill undvika.
KNOWN_EDITIONS = ["18.0", "19.0", "20.0"]

DEFAULT_SOURCE = ".pfiles-ci"

# Repon som modulerna beror på, från 'deps:' i .pfiles-ci. Fylls av
# parse_config() och skrivs ut i JSON-utdata så workflowen kan hämta dem.
DEPENDENCIES = []
EDITION_RE = re.compile(r"^\d{2}\.0$")


def fail(msg, code=5):
    print("pfiles-editions: %s" % msg, file=sys.stderr)
    sys.exit(code)


def parse_config(path):
    """Returnera listan av utgåvor ur .pfiles-ci, eller None om filen saknas."""
    if not os.path.exists(path):
        return None
    editions = []
    deps = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                fail("%s:%d: förväntade 'nyckel: värde', fick %r" % (path, lineno, line))
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if key == "deps":
                # Repon som modulerna beror på. Hämtas av workflowen innan
                # modulerna prövas — annars är de "oinstallerbara" av ett
                # skenskal, eftersom grannen helt enkelt inte finns i sokvagen.
                deps.extend(p for p in re.split(r"[\s,]+", value) if p)
                continue
            if key != "editions":
                # pfiles-ci: 1 är en versionsmarkör, inte en utgåva.
                continue
            parts = [p for p in re.split(r"[\s,]+", value) if p]
            if not parts:
                fail("%s:%d: 'editions:' är tomt" % (path, lineno))
            for part in parts:
                if not EDITION_RE.match(part):
                    fail(
                        "%s:%d: %r är inte en utgåva (väntade t.ex. 18.0)"
                        % (path, lineno, part)
                    )
                editions.append(part)
    if not editions:
        fail("%s: ingen 'editions:'-rad hittades" % path)
    DEPENDENCIES[:] = deps
    # Behåll ordning men ta bort dubbletter.
    seen, unique = set(), []
    for e in editions:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return unique


def branches(repo):
    """Lokala och remote-spårade grennamn, utan 'origin/'-prefix."""
    try:
        out = subprocess.run(
            ["git", "-C", repo, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        fail("kunde inte läsa grenar ur %s: %s" % (repo, exc))
    names = set()
    for line in out.splitlines():
        line = line.strip()
        if not line or line.endswith("/HEAD"):
            continue
        names.add(line.rsplit("/", 1)[-1])
    return names


def main():
    ap = argparse.ArgumentParser(description="Läs .pfiles-ci och skriv utgåvorna.")
    ap.add_argument("--repo", default=".", help="repo att läsa konfigurationen ur")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="konfigurationsfil (default .pfiles-ci)")
    ap.add_argument("--format", choices=["json", "github-matrix", "lines"], default="json")
    ap.add_argument("--check", action="store_true", help="validera och avsluta (inget matrisutdata)")
    ap.add_argument(
        "--allow-missing-branches",
        action="store_true",
        help="rapportera saknade grenar men avsluta 0 (för lokal körning)",
    )
    args = ap.parse_args()

    path = os.path.join(args.repo, args.source)
    configured = parse_config(path)
    source = args.source if configured is not None else "<default>"

    have = branches(args.repo)

    if configured is None:
        # Ingen konfigurationsfil: härled ur de utgåvegernar som faktiskt finns
        # i repot. Det gör att ett repo med bara 18.0 kör 18.0 utan att någon
        # behöver skriva en konfiguration (spec: "Repo med färre utgåvor").
        # Att i stället anta samtliga kända utgåvor skulle fälla varje sådant
        # repo på en gren som aldrig funnits.
        configured = [e for e in KNOWN_EDITIONS if e in have]
        if not configured:
            fail(
                "ingen .pfiles-ci och ingen utgåvegern (18.0/19.0/20.0) hittades "
                "i %s — kan inte avgöra vilka utgåvor som ska köras" % args.repo
            )

    unknown = [e for e in configured if e not in KNOWN_EDITIONS]
    if unknown:
        fail(
            "utgåva %s finns inte i pfiles-check.py (kända: %s)"
            % (", ".join(unknown), ", ".join(KNOWN_EDITIONS))
        )

    missing = [e for e in configured if e not in have]

    result = {"editions": configured, "missing_branches": missing,
              "deps": DEPENDENCIES, "source": source}

    if args.format == "github-matrix":
        print(json.dumps({"edition": configured}))
    elif args.format == "lines":
        for edition in configured:
            print(edition)
    else:
        print(json.dumps(result, ensure_ascii=False))

    if missing and not args.allow_missing_branches:
        fail(
            "utgåva %s är konfigurerad i %s men grenen finns inte — "
            "ta bort utgåvan ur %s eller skapa grenen. "
            "Detta är ett konfigurationsfel, inte en trasig modul."
            % (", ".join(missing), source, source)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
