#!/usr/bin/env python3
"""Bind every version row in TASKS.md to the commit that actually shipped it.

⚠⚠ WHY THIS EXISTS. MEASURED 2026-09-11: **249 of 280 rows** in the TASKS.md version table carried
the literal `(this commit)` and only 31 carried a real SHA. `bump_version.py` writes that literal
because at bump time the commit does not exist yet — and nothing ever came back to fill it in. So
89% of the ship history could not bind a version to a commit at all.

Grok Bot raised it three times running (GB-B-403/404/405) as a refutable claim: *"a next model
restoring status from the version table alone will not bind v2924 to `d2ec0fcd`"*. It is right, and
it is the exact failure CLAUDE.md §3 was written after — a list that survives only in a session is
not a list.

⚠ THE AUTHORITY IS THE STAMP, NOT THE SUBJECT LINE. A commit subject can MENTION a version it does
not ship ("v2924 was wrong, fixed in v2925"), so binding on subjects invents provenance. This binds
on the commit whose diff ADDED `VERSION = "vNNNN"` to tv/tv_diablo.py — the first of the four
stamps, and the thing a vNNNN label is defined to mean.

⚠⚠ AND THERE ARE THREE ANSWERS, NOT TWO. Versions are batched 3-4 per push on purpose, so an
intermediate version's VERSION line NEVER appears alone in any commit — it was carried into the
commit that stamps the top of its batch. MEASURED: 230 of the 249 bind directly, 19 are carried.
Calling a carried version "bound" would assert a precision that does not exist; calling it unknown
would throw away a fact that does. It gets its own word. [[unknown-stays-unknown]]
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TASKS = os.path.join(REPO, "TASKS.md")

sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

# ⚠⚠ THE CELL MAY CARRY AN ANNOTATION, AND THE FIRST CUT COULD NOT SEE ONE.
# This was `\| `([^`]*)` \|` — it required the cell to END at the closing backtick, so the moment
# this tool wrote a carried row (`sha` (in the vNNNN commit)) its OWN reader stopped matching it.
# MEASURED the same minute: the stamp run counted 278 rows and the audit that followed counted
# 259 — the 19 carried rows, invisible to the instrument that had just written them, with no
# word said about the missing denominator. A backfill whose audit cannot re-read its own output
# is a backfill nobody can check. [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
ROW = re.compile(r'^\| \*\*(v\d{4})\*\* \| (`[^`]*`[^|]*?) \|', re.M)
# ⚠⚠ v2929 — AND A SECOND TABLE SHAPE, WHICH THE FIRST CUT COULD NOT SEE AT ALL.
# MEASURED at origin the same hour v2927 shipped: the table holds **330** version rows and ROW
# matched **280**. The other 47 (v2435..v2510) are a LEGACY TWO-COLUMN shape —
# `| **v2435** | the page published ... |` — with no SHA slot whatsoever. They were silently
# excluded, so "no unbound row" was a claim about a subset presented as the whole table, and the
# law's `len(rows) > 250` floor passed comfortably at 280 while 47 versions stayed unbindable.
# That is [[regression-guard]]'s first rule — A SAMPLE IS NOT A VERDICT — inside the tool written
# to fix exactly this class of gap. Grok Bot was still right after the first fix.
# [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
VROW = re.compile(r'^\| \*\*(v\d{4})\*\* \|(.*)$', re.M)


def row_cells(rest):
    """The cells AFTER the version cell, for either table shape. -> [str]

    3-column row -> ['`sha`', 'note']   ·   legacy 2-column row -> ['note']
    """
    return [p.strip() for p in rest.rstrip().rstrip("|").split("|")]


_ADDED_STAMP = re.compile(r'^\+VERSION = "(v\d{4})"')
CARRIED = "in the %s commit"          # the words a carried row wears


def version_commits(cwd=None):
    """{version: sha} for every version whose VERSION stamp landed in a commit. -> dict

    ONE git call, not one per version: `git log -p -- tv/tv_diablo.py` already contains every
    change to the stamp, and 249 subprocesses to learn the same thing is how a tool becomes
    something nobody runs.
    """
    out = subprocess.run(["git", "log", "-p", "--format=@@@%H", "--", "tv/tv_diablo.py"],
                         capture_output=True, text=True, cwd=cwd or REPO).stdout
    sha, found = None, {}
    for line in out.splitlines():
        if line.startswith("@@@"):
            sha = line[3:].strip()
            continue
        m = _ADDED_STAMP.match(line)
        if m and sha and m.group(1) not in found:
            found[m.group(1)] = sha
    return found


def resolve(version, known, newest=None):
    """How this version binds to a commit. -> (state, sha, why)

    state is one of:
      bound   — its own VERSION stamp landed in this commit. Exact.
      carried — no commit stamps it alone; it shipped inside the commit that stamps the next
                version up, because versions are batched per push.
      pending — it IS the newest row and its commit does not exist yet. Honest as `(this commit)`.
      unknown — nothing above could be established. NOT a zero, NOT a guess.
    """
    if version in known:
        return ("bound", known[version], "its own VERSION stamp landed here")
    n = int(version[1:])
    for k in range(n + 1, n + 12):
        nxt = "v%d" % k
        if nxt in known:
            return ("carried", known[nxt], CARRIED % nxt)
    if newest and version == newest:
        return ("pending", None, "the commit that will carry it does not exist yet")
    return ("unknown", None, "no commit stamps this version and none above it does either")


def cell_for(state, sha, why):
    """The table cell text for a resolution. -> str"""
    if state == "bound":
        return "`%s`" % sha[:8]
    if state == "carried":
        return "`%s` (%s)" % (sha[:8], why)
    if state == "pending":
        return "`(this commit)`"
    return "`(UNKNOWN — %s)`" % why


def stamp(path=None, write=True, cwd=None, known=None):
    """Fill every unbound row, in EITHER table shape. -> dict of counts and the rows it changed

    ⚠ IT ONLY EVER REPLACES `(this commit)` OR INSERTS A MISSING CELL. A cell already carrying a
    SHA is left exactly as it is — a backfill that can overwrite is a backfill that can launder a
    wrong answer.
    """
    p = path or TASKS
    src = io.open(p, encoding="utf-8").read()
    # ⚠ `known` EXISTS SO A LAW CAN ASK THE REAL QUESTION — the same seam surface_verdict(path=)
    # carries. A law that needs this machine's git history can only pass on this machine.
    # [[feedback-fixtures-never-touch-live-data]]
    known = version_commits(cwd) if known is None else known
    counts = {"bound": 0, "carried": 0, "pending": 0, "unknown": 0, "left": 0, "legacyFilled": 0}
    changed = []
    all_rows = VROW.findall(src)
    newest = all_rows[0][0] if all_rows else None

    def _fix(m):
        ver, rest = m.group(1), m.group(2)
        cells = row_cells(rest)
        legacy = len(cells) < 2
        cell = "" if legacy else cells[0]
        if not legacy and cell != "`(this commit)`":
            counts["left"] += 1
            return m.group(0)
        state, sha, why = resolve(ver, known, newest)
        counts[state] += 1
        fresh = cell_for(state, sha, why)
        changed.append((ver, state, (sha or "")[:8]))
        if legacy:
            counts["legacyFilled"] += 1
            return "| **%s** | %s |%s" % (ver, fresh, rest)
        return m.group(0).replace(cell, fresh, 1)

    out = VROW.sub(_fix, src)
    if write and out != src:
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(out)
        os.replace(tmp, p)       # atomic: a reader never sees a half table
    counts["rows"] = len(all_rows)
    # ⚠ BEFORE AND AFTER ARE DIFFERENT FACTS, and a --dry run that prints only the projected
    # number reads as a description of the file on disk. [[stale-reading]]
    counts["shaCellsBefore"] = len(ROW.findall(src))
    counts["shaCellsAfter"] = len(ROW.findall(out))
    counts["knownVersions"] = len(known)
    return {"counts": counts, "changed": changed, "wrote": bool(write and out != src)}


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--dry", action="store_true", help="report without writing")
    a.add_argument("--audit", action="store_true", help="exit 1 if any row is unbound past the newest")
    ns = a.parse_args(argv)
    r = stamp(write=not (ns.dry or ns.audit))
    c = r["counts"]
    # ⚠ BOTH NUMBERS, ALWAYS. v2927 printed only what its reader could see, and the 50-row gap
    # between that and the real table was the whole of the defect it went on to have.
    print("   %d row(s) in the version table · %d carry a SHA cell now%s · %d version(s) have a "
          "VERSION-stamp commit"
          % (c["rows"], c["shaCellsBefore"],
             ("" if c["shaCellsAfter"] == c["shaCellsBefore"]
              else " -> %d after this run" % c["shaCellsAfter"]),
             c["knownVersions"]))
    print("   bound %d · carried %d · pending %d · UNKNOWN %d · already stamped %d · "
          "legacy rows given a cell %d"
          % (c["bound"], c["carried"], c["pending"], c["unknown"], c["left"], c["legacyFilled"]))
    if c["rows"] != c["shaCellsAfter"]:
        print("   \u26a0 %d row(s) still carry NO SHA cell — this tool cannot speak for them"
              % (c["rows"] - c["threeColumn"]))
    if ns.audit and c["unknown"]:
        print("   ✗ %d row(s) bind to nothing at all." % c["unknown"])
        return 1
    if r["wrote"]:
        print("   wrote TASKS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
