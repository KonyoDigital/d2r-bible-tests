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
#: The version table's own header. ⚠⚠ v2930 — SCOPE, AND IT COST A SELF-INFLICTED REGRESSION.
# v2929 read every `| **vNNNN** |` line in the FILE, concluded that 50 of them were "legacy
# two-column version rows", and inserted a SHA cell into all 50. They were not version rows at
# all: they belong to a SEPARATE table headed `| ship | what it closed |` at the top of TASKS.md,
# which has two columns BY DESIGN and no commit column to fill. The result was 50 three-cell rows
# under a two-column header — a malformed table, in the file this tool exists to keep honest.
# v2927's narrow reader had been RIGHT to skip them, and REG-934 mis-read its correctness as a
# blind spot. A row is a version row because of the TABLE IT IS IN, not because it starts with a
# bold vNNNN. [[regression-guard]] [[source-reading-guard]] [[ab-against-head-before-blaming-the-room]]
TABLE_HEAD = "| version | commit | commit subject |"
#: the markdown rule line under a table header — `|---|---|---|`, with optional alignment colons.
_RULE = re.compile(r"^\|[\s:|-]+\|\s*$")


def table_region(src):
    """(start, end) character offsets of the version table's ROWS. -> tuple|None

    Everything outside this is another table's business and must never be touched.

    ⚠⚠ v2935 — THE FIRST CUT SKIPPED TWO NEWLINES AND CHECKED NEITHER, and the row it dropped was
    the NEWEST one. `i = src.find("\n", src.find("\n", i) + 1) + 1` assumes the line after the
    header is the `|---|---|---|` rule. MEASURED on a table written without that rule: the second
    newline ended the FIRST DATA ROW, so the region began one row late, `rows` reported **1 where
    there were 2**, and the newest row stayed `(this commit)` forever. And `str.find` returns -1 on
    failure, which was never tested — a header with no two following newlines collapsed the start
    to 0 and walked the `|` lines from the TOP of the file, which is the ship table this function
    exists to exclude. That is the v2929 regression, back, on a truncated file.

    So the rule line is now REQUIRED and matched, not assumed. A shape this cannot recognise is
    UNKNOWN — it returns None rather than guessing an offset.
    [[unknown-stays-unknown]] [[source-reading-guard]]
    """
    i = src.find(TABLE_HEAD)
    if i < 0:
        return None
    lines = src[i:].splitlines(True)
    if len(lines) < 2 or not _RULE.match(lines[1]):
        return None
    start = i + len(lines[0]) + len(lines[1])
    j = start
    for line in src[start:].splitlines(True):
        if not line.startswith("|"):
            break
        j += len(line)
    return (start, j)


def row_cells(rest):
    """The cells AFTER the version cell, for either table shape. -> [str]

    3-column row -> ['`sha`', 'note']   ·   legacy 2-column row -> ['note']
    """
    return [p.strip() for p in rest.rstrip().rstrip("|").split("|")]


_ADDED_STAMP = re.compile(r'^\+VERSION = "(v\d{4})"')
CARRIED = "in the %s commit"          # the words a carried row wears


def version_commits(cwd=None):
    """{version: sha} for every version whose VERSION stamp landed in a commit. -> dict|None

    None means GIT COULD NOT BE ASKED. That is not an empty history.

    ONE git call, not one per version: `git log -p -- tv/tv_diablo.py` already contains every
    change to the stamp, and 249 subprocesses to learn the same thing is how a tool becomes
    something nobody runs.
    """
    # ⚠⚠ v2931 — None WHEN GIT COULD NOT BE ASKED, `{}` ONLY WHEN IT ANSWERED AND SAID NOTHING.
    # The cross-family eye caught this and it reproduces: in a directory with no history,
    # `version_commits()` returned `{}`, every row resolved UNKNOWN, and the tool WROTE
    # `(UNKNOWN — ...)` over the honest `(this commit)`. An instrument failure turned into a
    # measurement — by the tool whose own docstring says it must never launder a wrong answer.
    # [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    try:
        r = subprocess.run(["git", "log", "-p", "--format=@@@%H", "--", "tv/tv_diablo.py"],
                           capture_output=True, text=True, cwd=cwd or REPO)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    out = r.stdout
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
    # ⚠⚠ v2931 — AN UNKNOWN ROW KEEPS `(this commit)` RATHER THAN BEING STAMPED UNKNOWN.
    # Writing UNKNOWN looks more honest and is strictly worse: `stamp()` never overwrites a cell
    # that is not the literal, so a row that simply has not been committed YET — three bumps
    # batched before a commit, which is the documented workflow — would be frozen as UNKNOWN
    # forever, and the one rule that protects real provenance would be what keeps the lie.
    # The count is still reported, and --audit still exits 1. [[unknown-stays-unknown]]
    return "`(this commit)`"


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
    if known is None:
        # ⚠ REFUSE, LOUDLY. Writing anything here would record the state of a broken `git log`
        # as the provenance of his ship history.
        # ⚠⚠ v2939 — `rows=None`, NOT 0, AND THE SIBLING ARM ALREADY KNEW THAT. v2935 taught the
        # no-table refusal to report None because zero examined is not zero unbound; this arm kept
        # reporting 0 with a `why` beside it, so a caller reading `rows is None` as UNMEASURED read
        # a broken `git log` as a MEASURED EMPTY TABLE. Two refusals in one function disagreeing
        # about how to say "I did not look" is the defect v2935 closed, on the arm it did not
        # touch. Caught by the cross-family eye on v2935. [[zero-needs-a-denominator]]
        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,
                               knownVersions=None),
                "changed": [], "wrote": False,
                "why": "git could not be asked for the version history, so NOTHING was written — "
                       "this is UNMEASURED, not a table with no bindings"}
    changed = []
    span = table_region(src)
    if span is None:
        # ⚠⚠ v2935 — NOT FINDING THE TABLE IS NOT FINDING NOTHING WRONG. The first cut returned
        # all-zero counters here, so `--audit` saw `unknown == 0` and exited 0: the command whose
        # whole job is to refuse an unbound table was VACUOUSLY GREEN whenever it could not find
        # the table — a renamed header, a drifted TABLE_HEAD, a truncated file. MEASURED: a
        # TASKS.md holding only the ship table printed "0 row(s) in the version table" and exited
        # 0. That is [[zero-needs-a-denominator]] in the tool written to close exactly that shape.
        return {"counts": dict(counts, rows=None, shaCellsBefore=None, shaCellsAfter=None,
                               knownVersions=len(known)), "changed": [], "wrote": False,
                "why": "the version table header was not found (or its |---| rule line is "
                       "missing), so NOTHING here was examined — this is UNMEASURED, not a table "
                       "with nothing unbound"}
    head, body, tail = src[:span[0]], src[span[0]:span[1]], src[span[1]:]
    all_rows = VROW.findall(body)
    # ⚠ THE NEWEST IS THE HIGHEST NUMBER, not the first line. v2929 took all_rows[0] and got
    # v2435 — a row from a different table that happened to appear earlier in the file.
    newest = ("v%d" % max(int(v[1:]) for v, _ in all_rows)) if all_rows else None

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

    # ⚠ SUBSTITUTE ONCE. The first cut called VROW.sub(_fix, body) twice — once here and once to
    # measure the result — so every counter was tallied twice and `already stamped` printed 560
    # for a 281-row table. A counter incremented inside a substitution callback is state, and
    # running the substitution again is not a free read. [[feedback-suspect-the-instrument]]
    new_body = VROW.sub(_fix, body)
    out = head + new_body + tail
    if write and out != src:
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(out)
        os.replace(tmp, p)       # atomic: a reader never sees a half table
    counts["rows"] = len(all_rows)
    # ⚠ BEFORE AND AFTER ARE DIFFERENT FACTS, and a --dry run that prints only the projected
    # number reads as a description of the file on disk. [[stale-reading]]
    counts["shaCellsBefore"] = len(ROW.findall(body))
    counts["shaCellsAfter"] = len(ROW.findall(new_body))
    counts["knownVersions"] = len(known)
    return {"counts": counts, "changed": changed, "wrote": bool(write and out != src)}


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--dry", action="store_true", help="report without writing")
    a.add_argument("--audit", action="store_true", help="exit 1 if any row is unbound past the newest")
    ns = a.parse_args(argv)
    r = stamp(write=not (ns.dry or ns.audit))
    c = r["counts"]
    if r.get("why"):
        # ⚠ the refusal is the answer. Printed and non-zero, never a quiet success.
        print("   \u2717 %s" % r["why"])
        return 1
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
        # ⚠⚠ v2933 — `c["threeColumn"]` DIED IN THE v2929 RENAME AND THE BODY KEPT USING IT.
        # I renamed the key in the CONDITION and not in the line it guards, so the ONE path that
        # reports "this tool cannot speak for these rows" raised KeyError instead of warning.
        # It never fired because on the happy path `rows == shaCellsAfter` and the branch is dead
        # — a diagnostic that has never had a green run is a diagnostic nobody has proven can
        # speak. MEASURED: a version-table row whose SHA cell carries no backticks makes
        # rows=2 / shaCellsAfter=1, reaches this line, and raises.
        # Caught by the cross-family eye on v2929. [[plumbing-with-no-tap]] [[label-outlived-referent]]
        print("   \u26a0 %d row(s) still carry NO SHA cell — this tool cannot speak for them"
              % (c["rows"] - c["shaCellsAfter"]))
    if ns.audit and c["unknown"]:
        print("   ✗ %d row(s) bind to nothing at all." % c["unknown"])
        return 1
    if r["wrote"]:
        print("   wrote TASKS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
