#!/usr/bin/env python3
"""A TASK LIST THAT NAMES FINISHED WORK AS READY IS WORSE THAN NO LIST. gh #179 (GB-B-3/GB-B-4).

Grok Bot filed this on 2026-09-01 and repeated it on every watch tick for nineteen ticks:

    "`TASKS.md` READY table still lists 159 / GB-B-1" — GB-B-3 / GB-B-4: still OPEN
    (`TASKS.md` honesty / index drift)

Measured 2026-09-02, and it was right. Four of the five rows under **READY TO APPLY** shipped in
**v2400**, thirty-four versions earlier, and the table never moved:

    143  delete `fv.onclick`            -> `fv.onclick` occurs 0 times in bible.html
    159  doc says KEEP=2 / THROW=3      -> the doc says "THREE LOOKS TO KEEP, FOUR TO THROW"
    153  register hover_wilson as a gate-> 5 references in tv/run_gates.py
    164  paint witness `>=` not `==`    -> `elsHigh >= _UI_PAINT_FLOOR_ELS` at control_app.py:11592

⚠ AND THE MEASUREMENT ITSELF NEARLY GOT 159 WRONG. Grepping the doc for the old wording returned a
hit, so the first pass reported 159 still OPEN. The hit was inside the correction note recording the
fix — *"This page said 'KEEP = 2 distinct sessions...' until this"*. My own prose about a fix
satisfying my own search for the bug. That is why a fingerprint here is anchored and counted rather
than merely grepped. [[feedback-comments-vs-code]] [[source-reading-guard]]

WHY THIS IS A GATE AND NOT AN EDIT. Editing the four rows fixes today and drifts again next ship —
the file has drifted for thirty-four versions precisely because keeping it current depends on
remembering. So each READY row carries a FINGERPRINT: the string whose PRESENCE means the work is
still undone. When the fingerprint disappears, the work landed, and this says so by name.

    <!--fp: bible.html :: fv.onclick-->

⚠ A ROW WITH NO FINGERPRINT IS UNKNOWN, NOT CLEAN. Most prose cannot be fingerprinted, and a gate
that silently passed those would read as coverage over a file it barely inspected. Unfingerprinted
rows are counted and named on every run. [[unknown-stays-unknown]]

    python3 tv/tasks_freshness.py           # the gate
    python3 tv/tasks_freshness.py --prove   # make it go RED for its own reason
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS = os.path.join(ROOT, "TASKS.md")

#: the tables whose rows are CLAIMS ABOUT UNDONE WORK. A row here that is actually finished is the
#: defect; rows in the shipped/blocked tables are history and are not graded.
GRADED_HEADINGS = ("READY TO APPLY",)

FP = re.compile(r"<!--\s*fp:\s*([^:]+?)\s*::\s*(.+?)\s*-->")


def _rows(md):
    """-> [(heading, row_id, line_no, line)] for every table row under a graded heading."""
    out, heading = [], None
    for i, line in enumerate(md.splitlines(), 1):
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            continue
        if not line.startswith("|"):
            continue
        if heading is None or not any(g in heading for g in GRADED_HEADINGS):
            continue
        m = re.match(r"\|\s*\*\*([^*]+)\*\*\s*\|", line)
        if not m:
            continue                       # header row, separator row
        out.append((heading, m.group(1).strip(), i, line))
    return out


def check(path=None):
    """-> (code, lines). 0 green · 1 a row claims undone work that is done · 2 UNKNOWN."""
    path = path or TASKS
    try:
        md = io.open(path, encoding="utf-8").read()
    except Exception as e:
        return 2, ["⚪ UNKNOWN — TASKS.md could not be read (%s). That is not a clean list." % e]
    rows = _rows(md)
    if not rows:
        return 2, ["⚪ UNKNOWN — no graded rows found under %s. Either the headings were renamed "
                   "or the row shape changed; a parser that matches nothing looks exactly like a "
                   "list with nothing wrong in it." % (", ".join(GRADED_HEADINGS))]
    out, stale, unknown = [], [], []
    for heading, rid, ln, line in rows:
        m = FP.search(line)
        if not m:
            unknown.append((rid, ln))
            continue
        rel, needle = m.group(1), m.group(2)
        f = os.path.join(ROOT, rel)
        try:
            src = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            out.append("🔴 row %s fingerprints %s, which cannot be read" % (rid, rel))
            stale.append(rid)
            continue
        n = src.count(needle)
        if n == 0:
            stale.append(rid)
            out.append("🔴 %-6s READY, but its fingerprint %r is GONE from %s — the work landed "
                       "and the row was never closed." % (rid, needle, rel))
        else:
            out.append("🟢 %-6s still open (%r occurs %d× in %s)" % (rid, needle, n, rel))
    if unknown:
        out.append("⚪ %d row(s) carry NO fingerprint, so this gate did not inspect them: %s"
                   % (len(unknown), ", ".join("%s (line %d)" % (r, l) for r, l in unknown)))
        out.append("   That is UNKNOWN, not clean. Add `<!--fp: <file> :: <string>-->` to a row "
                   "whose undone-ness has a string, or leave it and read this line each run.")
    out.append("   %d graded row(s) · %d fingerprinted · %d stale · %d unknown"
               % (len(rows), len(rows) - len(unknown), len(stale), len(unknown)))
    return (1 if stale else 0), out


def prove():
    """Founding rule 2 — RED for its own reason, on a fixture, never on his file."""
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="tf_")
    bad = 0
    try:
        global ROOT
        keep = ROOT
        ROOT = d
        io.open(os.path.join(d, "subject.py"), "w", encoding="utf-8").write(
            "def still_here():\n    return 1\n")
        cases = [
            ("a fingerprint that is STILL THERE is open", 0,
             "## READY TO APPLY\n\n| # | What |\n|---|---|\n"
             "| **900** | do the thing. <!--fp: subject.py :: still_here--> |\n"),
            ("a fingerprint that is GONE is a stale row", 1,
             "## READY TO APPLY\n\n| # | What |\n|---|---|\n"
             "| **901** | do the thing. <!--fp: subject.py :: already_deleted--> |\n"),
            ("a row with NO fingerprint is not graded green", 0,
             "## READY TO APPLY\n\n| # | What |\n|---|---|\n"
             "| **902** | prose nobody can fingerprint. |\n"),
            ("no graded rows at all is UNKNOWN, not clean", 2,
             "## SOMETHING ELSE\n\n| # | What |\n|---|---|\n| **903** | not graded. |\n"),
            ("a fingerprint pointing at a missing file is a finding", 1,
             "## READY TO APPLY\n\n| # | What |\n|---|---|\n"
             "| **904** | x <!--fp: no_such_file.py :: anything--> |\n"),
        ]
        for name, want, body in cases:
            p = os.path.join(d, "T.md")
            io.open(p, "w", encoding="utf-8").write(body)
            code, lines = check(p)
            ok = code == want
            bad += 0 if ok else 1
            print("   %s %-48s want %d  got %d" % ("🟢" if ok else "🔴", name, want, code))
            if not ok:
                for l in lines:
                    print("        %s" % l)
        # and the 159 trap: a needle that appears ONLY inside a note about the fix must still
        # count as present — this gate reports occurrences, it does not judge prose. The guard
        # against that error lives in the FINGERPRINT CHOICE, so prove the counter is honest.
        io.open(os.path.join(d, "doc.md"), "w", encoding="utf-8").write(
            'This page said "KEEP = 2" until v2400 corrected it.\n')
        p = os.path.join(d, "T.md")
        io.open(p, "w", encoding="utf-8").write(
            "## READY TO APPLY\n\n| # | What |\n|---|---|\n"
            '| **905** | x <!--fp: doc.md :: KEEP = 2--> |\n')
        code, lines = check(p)
        ok = code == 0 and any("occurs 1" in l for l in lines)
        bad += 0 if ok else 1
        print("   %s %-48s want 1 occurrence counted" % ("🟢" if ok else "🔴",
                                                         "an occurrence is COUNTED, not judged"))
        ROOT = keep
    finally:
        shutil.rmtree(d, True)
    print()
    if bad:
        print("🔴 %d case(s) wrong — this gate may not be trusted." % bad)
        return 1
    print("🟢 red for a landed row, green for an open one, UNKNOWN when it parsed nothing.")
    return 0


def main(argv):
    if "--prove" in argv:
        print("PROVING THE TASK-FRESHNESS GATE — on fixtures, never on his list.\n")
        return prove()
    code, lines = check()
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
