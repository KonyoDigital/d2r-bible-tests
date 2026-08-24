#!/usr/bin/env python3
"""THE SPACE WARDEN — reclaim REGENERABLE output automatically, propose everything else.

Konyo, 2026-08-24, after a stuck Playwright run wrote 60,232 files / 9.5 GB into test-results/ in
95 minutes and took his disk from 14 GB free to 2.8 GB:
    "is there a way we can do this automatically with a pruning AI system ... so we dont hit cap
     limit again?"

WHY NOTHING CAUGHT IT. Three pruners already existed and every one of them owned a different thing:
`reel_retention` owns whole reels, v2037's rolling prune owns loose live frames, and v2041's
snapshot owns ledger backups. Playwright's output had NO OWNER, so it grew without a bound and
without a complaint. The gap was not a missing policy, it was a missing OWNER.

THE ONE RULE THAT MAKES THIS SAFE TO RUN UNATTENDED:

    AUTO-DELETE ONLY WHAT A COMMAND CAN REGENERATE.  PROPOSE EVERYTHING ELSE.

Test output is regenerable by re-running the suite. A reel of his farming is not regenerable by
anything, and no amount of free-space pressure changes that. So reels and live frames are REPORTED
here and deleted by nobody: `reel_retention` already owns that decision and requires an explicit
yes. [[feedback-fixtures-never-touch-live-data]]

Every AUTO path is re-verified at run time, not trusted from this list:
  * it resolves INSIDE the repo (no symlink or `..` escape),
  * git ignores it, and
  * git tracks ZERO files inside it.
A path failing any of those is skipped and SAID, never deleted on the strength of being on a list.
"""
import json
import os
import shutil
import subprocess
import sys

# REG-044/054/077/078 — a tool that dies while REPORTING turns a clean tree red. This one prints
# 🧹 🟢 🔒, so stdout is made encoding-safe before anything reaches it. His own gate caught this
# file on its first push, which is the gate working.
from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# free space below which the warden acts at all. Above it, a full test-results/ is not a problem —
# it is a debugging aid someone may still want.
FLOOR_GB = float(os.environ.get("TV_SPACE_FLOOR_GB", "20") or 20)

# REGENERABLE, and by what. The second field is what a person would run to get it back; if you
# cannot name that command, the path does not belong in this list.
AUTO = [
    ("test-results",        "npx playwright test"),
    ("playwright-report",   "npx playwright test"),
    ("blob-report",         "npx playwright test --reporter=blob"),
    # node_modules/.cache was here and was DEAD: NEVER contains node_modules, so the safety check
    # blocked it on every run. A list entry that can never fire reads like coverage and is not.
]

# NEVER, at any pressure. Named so the list is a statement rather than an omission.
NEVER = ("tv/frames", "art", ".git", "node_modules")


def _du(path):
    try:
        r = subprocess.run(["du", "-sk", path], capture_output=True, text=True, timeout=120)
        return int(r.stdout.split()[0]) * 1024
    except Exception:
        return 0


def _free_gb():
    try:
        s = os.statvfs(REPO)
        return s.f_bavail * s.f_frsize / float(1 << 30)
    except Exception:
        return None


def _safe(rel):
    """(ok, why). Every condition is re-checked here; the AUTO list is a proposal, not a warrant."""
    full = os.path.realpath(os.path.join(REPO, rel))
    if not (full + os.sep).startswith(os.path.realpath(REPO) + os.sep):
        return False, "resolves OUTSIDE the repo (%s) — refusing" % full
    for n in NEVER:
        nf = os.path.realpath(os.path.join(REPO, n))
        if full == nf or (full + os.sep).startswith(nf + os.sep):
            return False, "lives under %s, which is never auto-deleted" % n
    if not os.path.exists(full):
        return False, "absent"
    try:
        if subprocess.run(["git", "check-ignore", "-q", rel], cwd=REPO).returncode != 0:
            return False, "git does NOT ignore it — that makes it source, not output"
        r = subprocess.run(["git", "ls-files", rel], capture_output=True, text=True, cwd=REPO)
        n = len([l for l in r.stdout.split("\n") if l.strip()])
        if n:
            return False, "git tracks %d file(s) inside it" % n
    except Exception as e:
        return False, "could not ask git (%s) — refusing rather than guessing" % str(e)[:50]
    return True, "regenerable, ignored, nothing tracked"


def survey():
    """What exists, what is safe, what is his. Reads only."""
    rows = []
    for rel, regen in AUTO:
        ok, why = _safe(rel)
        rows.append({"path": rel, "tier": "auto", "bytes": _du(os.path.join(REPO, rel)) if ok else 0,
                     "safe": ok, "why": why, "regeneratedBy": regen})
    for rel, why in (("tv/frames/hist", "his footage — reel_retention owns this and needs a yes"),
                     ("tv/frames/corpus", "the hand-labelled corpus — never")):
        full = os.path.join(REPO, rel)
        if os.path.exists(full):
            rows.append({"path": rel, "tier": "propose", "bytes": _du(full),
                         "safe": False, "why": why, "regeneratedBy": None})
    return {"freeGB": _free_gb(), "floorGB": FLOOR_GB, "rows": rows,
            "reclaimableBytes": sum(r["bytes"] for r in rows if r["tier"] == "auto" and r["safe"])}


def reclaim(dry_run=True, force=False):
    """Delete the AUTO tier when free space is under the floor. Returns what it did and why."""
    s = survey()
    free = s["freeGB"]
    if free is None:
        return dict(s, acted=False, why="could not read free space — doing nothing")
    if free >= FLOOR_GB and not force:
        return dict(s, acted=False,
                    why="%.1f GB free is above the %.0f GB floor — a full test-results/ is a "
                        "debugging aid until space is actually short" % (free, FLOOR_GB))
    freed, did = 0, []
    for r in s["rows"]:
        if r["tier"] != "auto" or not r["safe"] or not r["bytes"]:
            continue
        if not dry_run:
            try:
                shutil.rmtree(os.path.join(REPO, r["path"]))
            except Exception as e:
                did.append({"path": r["path"], "ok": False, "why": str(e)[:80]})
                continue
        freed += r["bytes"]
        did.append({"path": r["path"], "ok": True, "bytes": r["bytes"],
                    "regeneratedBy": r["regeneratedBy"]})
    return dict(s, acted=bool(did) and not dry_run, dryRun=dry_run, freedBytes=freed, did=did,
                why="reclaimed %.2f GB of regenerable output" % (freed / float(1 << 30)))


def main(argv):
    apply = "--apply" in argv
    out = reclaim(dry_run=not apply, force="--force" in argv)
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False)); return 0
    print("\n🧹 SPACE WARDEN — %.1f GB free (floor %.0f GB)\n" % (out["freeGB"] or -1, FLOOR_GB))
    for r in out["rows"]:
        mark = "🟢" if (r["tier"] == "auto" and r["safe"]) else ("🔒" if r["tier"] == "propose" else "⚪")
        print("  %s %-22s %7.2f GB  %s" % (mark, r["path"], r["bytes"] / float(1 << 30), r["why"]))
    print("\n  %s" % out["why"])
    if not apply and out.get("reclaimableBytes"):
        print("  run with --apply to reclaim (or --force to ignore the floor)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
