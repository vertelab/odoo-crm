#!/usr/bin/env python3
"""pfiles-expand.py — expandera p-filerna för EN utgåva i en egen katalog.

Steg 2 i CI ("Expansion — committad utdata ska stämma") gjorde detta med en
shell-loop som expanderade på plats och sedan jämförde `git diff`. Det fungerar
bara för en utgåva i taget: expanderar man 20.0 på plats skrivs 18.0-filerna
över, och nästa utgåva jämförs mot fel innehåll.

Därför expanderar det här skriptet till en SEPARAT katalog (--out) och jämför
den mot arbetskatalogen. Två utgåvor kan då köras efter varandra utan att röra
varandra.

Användning:
    .github/pfiles-expand.py --repo . --version 20.0 --out /tmp/x20
    .github/pfiles-expand.py --repo . --version 20.0 --out /tmp/x20 --quiet
    .github/pfiles-expand.py --repo . --version 20.0 --out /tmp/x20 --json

Utdata: en rad per avvikelse på stdout (eller JSON med --json).
Diagnostik på stderr.

Exitkoder:
    0  all committad utdata stämmer med p-filerna för den utgåvan
    1  avvikelse (utdata är inaktuell) — listan anger vilka filer
    2  felaktig användning
    5  miljöfel (preprocess saknas, katalogen går inte att skriva)
"""

import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys

# Samma ändelser som hooken expanderar. .kpf/.xul finns i hookens lista men
# används inte i Vertels repon; de hoppas över här eftersom preprocess inte
# har stöd för dem och en fil vi inte kan expandera är ett fel vi inte kan
# åtgärda.
EXTENSIONS = [".py", ".xml", ".js", ".csv", ".sh", ".html", ".htm"]

EXCLUDED_DIRS = {".git", "__pycache__", ".tox", ".venv", "venv", "node_modules",
                 ".idea", ".mypy_cache", ".pytest_cache"}


def die(msg, code):
    print("pfiles-expand: %s" % msg, file=sys.stderr)
    sys.exit(code)


def pfiles(repo):
    """Alla p-filer i repot, som relativa sökvägar."""
    found = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in files:
            if any(name.endswith(".p" + ext) for ext in EXTENSIONS):
                found.append(os.path.relpath(os.path.join(root, name), repo))
    return sorted(found)


def output_name(pfile):
    """a/b.p.py -> a/b.py. '.p' sitter före ändelsen."""
    for ext in EXTENSIONS:
        if pfile.endswith(".p" + ext):
            return pfile[: -len(".p" + ext)] + ext
    return pfile  # kan inte inträffa, pfiles() filtrerar


def main():
    ap = argparse.ArgumentParser(description="Expandera p-filer för en utgåva.")
    ap.add_argument("--repo", default=".", help="repo att expandera ur")
    ap.add_argument("--version", required=True, help="utgåva, t.ex. 20.0")
    ap.add_argument("--out", required=True, help="katalog att expandera till")
    ap.add_argument("--quiet", action="store_true", help="bara avvikelser")
    ap.add_argument("--json", action="store_true", help="JSON-utdata")
    ap.add_argument("--allow-missing-preprocess", action="store_true",
                    help="hoppa över med exit 0 i stället för miljöfel")
    args = ap.parse_args()

    preprocess = shutil.which(os.environ.get("PFILES_PREPROCESS", "preprocess"))
    if not preprocess:
        if args.allow_missing_preprocess:
            print("pfiles-expand: preprocess saknas i PATH — hoppar över", file=sys.stderr)
            return 0
        die("preprocess saknas i PATH (miljöfel, inte ett fel i modulen)", 5)

    repo = os.path.abspath(args.repo)
    sources = pfiles(repo)
    if not args.quiet:
        print("pfiles-expand: %d p-filer, utgåva %s" % (len(sources), args.version), file=sys.stderr)

    stale, errors = [], []

    # Kopiera hela modulkatalogerna först. Expansionen nedan skriver bara de
    # filer som har en p-fil — moduler som enbart består av genererad utdata
    # (eller av handskrivna filer utan p-källa) skulle annars aldrig hamna i
    # utdatakatalogen, och CI skulle tyst hoppa över dem. Det var precis vad
    # som hände: 4 av 21 moduler testades.
    copied = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        # En modulkatalog är varje katalog som har ett manifest, i vilket
        # format det än finns. Vi kopierar den och hoppar över allt under
        # den — en modul kan innehålla undermappar som ser ut som moduler
        # men inte är det.
        if "__manifest__.py" in files or "__manifest__.p.py" in files:
            dest = os.path.join(args.out, os.path.relpath(root, repo))
            shutil.copytree(root, dest, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            copied += 1
            dirs[:] = []

    for src in sources:
        rel_out = output_name(src)
        outpath = os.path.join(args.out, rel_out)
        os.makedirs(os.path.dirname(outpath) or args.out, exist_ok=True)
        proc = subprocess.run(
            [preprocess, "-f", "-D", "VERSION=%s" % args.version, "-o", outpath,
             os.path.join(repo, src)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            errors.append({"file": src, "stderr": proc.stderr.strip()[:800]})
            continue
        committed = os.path.join(repo, rel_out)
        if not os.path.exists(committed):
            # p-fil utan committad utdata är täckningskontrollens sak, inte
            # expansionens. Här jämför vi bara det som finns.
            continue
        if not filecmp.cmp(committed, outpath, shallow=False):
            stale.append(rel_out)

    if args.json:
        print(json.dumps({"version": args.version, "checked": len(sources),
                          "stale": stale, "errors": errors}, ensure_ascii=False))
    else:
        for rel_out in stale:
            print("STALE %s" % rel_out)
        for err in errors:
            print("EXPANSION_ERROR %s" % err["file"])

    if errors:
        if not args.json:
            for err in errors:
                print("--- %s ---\n%s" % (err["file"], err["stderr"]), file=sys.stderr)
        return 1
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
