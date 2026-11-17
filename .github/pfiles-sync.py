#!/usr/bin/env python3
"""pfiles-sync.py — håll SAMMA p-filer på alla utgåvegrenar.

Principen: en p-fil är källan för alla utgåvor. Därför ska varje p-fil finnas
på varje utgåvegren, och innehållet ska vara identiskt — utgåveskillnaderna
uttrycks med '# #if VERSION'-direktiv inne i filen, aldrig genom att filen
finns bara på en gren.

Det här skriptet gör två saker:

  --check   rapportera drift: p-filer som saknas på någon gren, eller som
            finns på flera grenar med olika innehåll. Exit 1 vid drift.
  --apply   åtgärda driften: kopiera varje p-fil till de grenar som saknar
            den, och uppdatera den som har ett äldre innehåll.

Vilken gren som är källa när innehållet skiljer sig går inte att avgöra
automatiskt — det är en mänsklig bedömning. --apply kräver därför --from,
och kopierar då från den grenen till de andra.

Användning:
    .github/pfiles-sync.py --repo . --check
    .github/pfiles-sync.py --repo . --check --json
    .github/pfiles-sync.py --repo . --apply --from 18.0 --push

Exitkoder:
    0  ingen drift (--check) / allt synkat (--apply)
    1  drift hittad (--check)
    2  felaktig användning
    5  miljöfel (git saknas, gren finns inte)
"""

import argparse
import json
import os
import subprocess
import sys

# Ändelser som behandlas som p-filer. Samma lista som hooken och checkern.
EXTENSIONS = (".py", ".xml", ".js", ".csv", ".sh", ".html", ".htm")


def die(msg, code=5):
    print("pfiles-sync: %s" % msg, file=sys.stderr)
    sys.exit(code)


def git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        die("git %s misslyckades: %s" % (" ".join(args), proc.stderr.strip()[:300]))
    return proc


def edition_branches(repo, wanted):
    """De av 'wanted' som finns som gren (lokal eller origin/)."""
    out = git(repo, "for-each-ref", "--format=%(refname:short)",
              "refs/heads", "refs/remotes").stdout
    have = {line.strip().rsplit("/", 1)[-1] for line in out.splitlines() if line.strip()}
    return [e for e in wanted if e in have]


def pfiles_on(repo, branch):
    """p-filer som finns på grenen, som relativa sokvagar."""
    out = git(repo, "ls-tree", "-r", "--name-only", "origin/%s" % branch).stdout
    return {line.strip() for line in out.splitlines()
            if line.strip().endswith(tuple(".p" + e for e in EXTENSIONS))}


def blob(repo, branch, path):
    """Filens innehall pa grenen, eller None om den inte finns."""
    proc = git(repo, "show", "origin/%s:%s" % (branch, path), check=False)
    return proc.stdout if proc.returncode == 0 else None


def check(repo, branches):
    """Returnera {'missing': {gren: [filer]}, 'diverged': [{'path', 'branches'}]}."""
    per_branch = {b: pfiles_on(repo, b) for b in branches}
    union = set()
    for files in per_branch.values():
        union |= files

    missing = {}
    for b in branches:
        saknas = sorted(union - per_branch[b])
        if saknas:
            missing[b] = saknas

    diverged = []
    for path in sorted(union):
        contents = {}
        for b in branches:
            if path in per_branch[b]:
                contents[b] = blob(repo, b, path)
        if len(set(contents.values())) > 1:
            diverged.append({"path": path, "branches": sorted(contents)})

    return {"missing": missing, "diverged": diverged,
            "editions": branches,
            "counts": {b: len(per_branch[b]) for b in branches}}


def apply(repo, branches, source, push):
    """Kopiera alla p-filer fran 'source' till ovriga grenar och expandera dar."""
    if source not in branches:
        die("kallgrenen %s finns inte (har: %s)" % (source, ", ".join(branches)), 2)

    # Unionen av alla p-filer, inte bara kallans: en fil som bara finns pa
    # EN gren ar ocksa drift och ska till de andra. Kallan avgor innehaller
    # nar filen finns pa flera grenar.
    src_files = set()
    for b in branches:
        src_files |= pfiles_on(repo, b)
    changed = {}

    for branch in branches:
        # Kallgrenen hoppas inte over: den kan sakna en fil som bara finns pa
        # en annan gren, och da ska den ocksa fa den.
        theirs = pfiles_on(repo, branch)
        todo = []
        wanted = {}
        for path in sorted(src_files):
            want = blob(repo, source, path)
            if want is None:
                # Filen finns bara pa andra grenar an kallan. Da ar den gren
                # som HAR filen kallan for just den filen — en unik fil ska
                # spridas, inte ignoreras.
                for other in branches:
                    if other == branch:
                        continue
                    cand = blob(repo, other, path)
                    if cand is not None:
                        want = cand
                        break
            if want is None:
                continue
            have = blob(repo, branch, path) if path in theirs else None
            if have != want:
                todo.append(path)
                wanted[path] = want
        if not todo:
            continue

        # Arbeta i ett tillfalligt arbetstrad sa att vi inte ror den
        # utcheckade grenen.
        work = os.path.join(repo, ".git", "pfiles-sync-%s" % branch)
        subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", work],
                       capture_output=True)
        git(repo, "worktree", "add", "-f", "--detach", work, "origin/%s" % branch)

        for path in todo:
            content = wanted[path]
            dest = os.path.join(work, path)
            os.makedirs(os.path.dirname(dest) or work, exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)

        # Expandera for DEN har utgaVan och lagg den genererade kallkoden i
        # tradet. Expansionen skrivs till en katalog utanfor tradet, sa att
        # inget halvfardigt hamnar i commiten.
        expand = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "pfiles-expand.py")
        outroot = os.path.join(repo, ".git", "pfiles-sync-expand-%s" % branch)
        subprocess.run(["rm", "-rf", outroot], capture_output=True)
        copied = 0
        if os.path.exists(expand):
            subprocess.run([sys.executable, expand, "--repo", work,
                            "--version", branch, "--out", outroot],
                           capture_output=True, text=True)
            for root, _dirs, files in os.walk(outroot):
                for name in files:
                    srcf = os.path.join(root, name)
                    rel = os.path.relpath(srcf, outroot)
                    if rel.endswith(tuple(".p" + e for e in EXTENSIONS)):
                        continue        # p-filerna ar redan kopierade
                    dst = os.path.join(work, rel)
                    os.makedirs(os.path.dirname(dst) or work, exist_ok=True)
                    with open(srcf, "rb") as a, open(dst, "wb") as b:
                        b.write(a.read())
                    copied += 1
            subprocess.run(["rm", "-rf", outroot], capture_output=True)
        print("pfiles-sync: %s — %d p-filer, %d genererade"
              % (branch, len(todo), copied), file=sys.stderr)

        git(work, "add", "-A")
        msg = ("pfiles: sync from %s\n\n"
               "Samma p-filer ska finnas pa alla utgavegrenar; utgaverSkillnaderna\n"
               "uttrycks med '# #if VERSION' inne i filen. De genererade filerna\n"
               "ar expanderade for %s." % (source, branch))
        proc = git(work, "-c", "user.email=ci@vertel.se",
                   "-c", "user.name=pfiles-sync", "commit", "-q", "-m", msg,
                   check=False)
        if proc.returncode != 0:
            changed[branch] = "inget att committa"
        else:
            sha = git(work, "rev-parse", "--short", "HEAD").stdout.strip()
            changed[branch] = "%s (%d filer)" % (sha, len(todo))
            if push:
                p = git(work, "push", "origin", "HEAD:%s" % branch, check=False)
                changed[branch] += " pushad" if p.returncode == 0 else " PUSH MISSLYCKADES"
        subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", work],
                       capture_output=True)

    return changed


def main():
    ap = argparse.ArgumentParser(description="Synka p-filer mellan utgavegrenar.")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--editions", default="18.0,19.0,20.0")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--from", dest="source", help="kallgren for --apply")
    ap.add_argument("--push", action="store_true", help="pusha efter --apply")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.check and not args.apply:
        die("ange --check eller --apply", 2)

    wanted = [e.strip() for e in args.editions.split(",") if e.strip()]
    branches = edition_branches(args.repo, wanted)
    if not branches:
        die("inga utgavegrenar hittades (ville ha: %s)" % ", ".join(wanted))
    git(args.repo, "fetch", "-q", "origin", check=False)

    if args.check:
        result = check(args.repo, branches)
        drift = bool(result["missing"] or result["diverged"])
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("p-filer per gren: %s" % ", ".join(
                "%s=%d" % (b, n) for b, n in result["counts"].items()))
            for b, files in result["missing"].items():
                print("\nSaknas pa %s (%d):" % (b, len(files)))
                for f in files:
                    print("  - %s" % f)
            if result["diverged"]:
                print("\nSamma fil, olika innehall (%d):" % len(result["diverged"]))
                for d in result["diverged"]:
                    print("  - %s  [%s]" % (d["path"], ", ".join(d["branches"])))
            if not drift:
                print("\nIngen drift: samma p-filer, samma innehall.")
        return 1 if drift else 0

    if not args.source:
        die("--apply kraver --from <gren> — vilken gren som ar kallan ar en "
            "bedomning, inte nagot skriptet kan avgora", 2)
    changed = apply(args.repo, branches, args.source, args.push)
    if args.json:
        print(json.dumps({"source": args.source, "changed": changed}, ensure_ascii=False))
    else:
        for b, what in changed.items():
            print("%s: %s" % (b, what))
        if not changed:
            print("Inget att gora — grenarna ar redan synkade.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
