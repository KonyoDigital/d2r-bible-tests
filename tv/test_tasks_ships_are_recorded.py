"""v2670 — a shipped version that appears nowhere in TASKS.md is drift, and drift here has a history.

THE DEFECT, and it is this file's own recurring one. TASKS.md opens with a drift audit that says
    "newest LANDED row in this file: v2648 · HEAD: v2657 — so 9 ships are absent from the file"
and that audit was written BY HAND. Re-measured 2026-09-05 against `git log -200`: **81** shipped
versions appeared nowhere in the file. So noticing the drift did not stop it, and the number was
9× worse than the notice claimed.

⚠ WHY A GATE AND NOT A HABIT. The list has already been lost once, on 2026-09-01, because it lived
in a session instead of a file — 993 of his turns had to be pulled back out of a 688 MB transcript.
A tracked file that silently stops matching what shipped is the same failure wearing a filename.
`tasks_freshness.py` exists and did NOT catch this: it grades named HEADINGS, and a ship missing
from every heading is invisible to it. [[the-unjoined-end]] [[regression-guard]]

SCOPE IS DELIBERATE. Only the most recent ships are required to appear. Demanding every version
back to v2000 would force this file to grow without bound, which is the OTHER way it became
unreadable — the audit's own words: "a file long enough to contradict itself is a file nobody can
read to the end". Older ships are a DECLARED omission in the file, not a silent one.
"""
import ast
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TASKS = os.path.join(REPO, "TASKS.md")

#: how many of the newest ships must be findable in TASKS.md. Small enough that the file does not
#: grow without bound, large enough that a normal day's batch cannot slip through unrecorded.
RECENT = 12


def _shipped(limit=200):
    """(version, sha) for every commit that MOVED THE STAMP, newest first.

    ⚠ READS THE STAMP, NOT THE COMMIT SUBJECT, and the difference is not academic — it is what the
    first version of this gate got wrong. The repo's rule is *"a vNNNN label means the four stamps
    MOVED"*, so reading subjects looks equivalent. It is not, in two ways, both measured here:

      · A RANGE subject ships more than one version. `v2650-v2651 — a retraction that vanished`
        ships v2651, and a regex anchored at the start of the subject cannot see it.
      · **A STAMP CAN MOVE UNDER A `fix:` SUBJECT, and four of them did.** `96a4eafb` carries
        `"ver": "v2666"` while its subject reads *"fix: the shelf door reported success…"*. CI
        called that run v2666; `git log --grep` cannot find it at all. Those ships are invisible to
        every subject-based audit, which is exactly the blindness this file exists to end.

    `WINDOWS_SHIP.json` is one of the four stamps `bump_version.py` writes, so a change to its
    `ver` field IS the ship, by the repo's own definition. [[feedback-verify-not-proxy]]
    """
    out = subprocess.run(
        ["git", "log", "-%d" % limit, "--format=COMMIT %h", "-p", "--", "tv/WINDOWS_SHIP.json"],
        cwd=REPO, capture_output=True, text=True, timeout=90).stdout
    rows, sha = [], None
    for ln in out.splitlines():
        if ln.startswith("COMMIT "):
            sha = ln.split()[1]
        elif ln.startswith("+") and not ln.startswith("+++"):
            # ⚠⚠ #123 — `v2[0-9]{3}` matched v2000-v2999 ONLY. From v3000 on it found ZERO ships
            # and the gate sat red in every FULL clone ("git named 0 shipped versions") while CI's
            # shallow clone skipped it — found by the v3483 census, not by the gate's own output.
            m = re.search(r'"ver"\s*:\s*"(v[0-9]{3,5})"', ln)
            if m and sha:
                rows.append((m.group(1), sha))
                sha = None
    return rows


def _missing_rows(text, ships):
    """-> the (ver, sha) of each ship that has NO ROW in the ship table.

    ⚠ 2026-09-26 — A VERSION NAMED IN PROSE IS NOT ITS ROW. This law asked `v not in self.text`, and so did the bump's
    writer: the #174 row said "R1 (v3507)" and "v-B3 (v3509)", each written just before its bump, so both bumps skipped
    the row and this law stayed green while two of the last three ships had none. [[a-presence-law-is-not-a-reachability-law]]"""
    rows = set(re.findall(r"^\| \*\*(v[0-9]{3,5})\*\* \|", text or "", re.M))
    return [(v, sha) for v, sha in ships if v not in rows]


class RecentShipsAreRecordedInTheList(unittest.TestCase):

    @staticmethod
    def _is_shallow():
        """⚠ CI CHECKS OUT SHALLOW, AND THIS TEST READS HISTORY.

        Measured on run 33975750007: `git log -200` returned **1** shipped version, because
        `actions/checkout@v4` clones with depth=1 by default. The denominator guard below caught it
        and refused to call that a pass — which is the guard doing its job — but a test that cannot
        see history must SAY SO rather than fail a correct tree for ever. A gate that is always red
        carries as much information as one always green. [[regression-guard]]
        """
        try:
            out = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                                 cwd=REPO, capture_output=True, text=True, timeout=30).stdout
            return out.strip() == "true"
        except Exception:
            return False

    def setUp(self):
        self.assertTrue(os.path.isfile(TASKS), "TASKS.md is the list; without it there is no list")
        with open(TASKS, encoding="utf-8") as fh:
            self.text = fh.read()
        self.ships = _shipped()
        # ⚠ DENOMINATOR FIRST, AND IT SPLITS TWO CASES THAT LOOK IDENTICAL.
        #
        # v2677 skipped whenever the clone was shallow. That was right for depth=1 and WRONG the
        # moment the workflow set `fetch-depth: 200`: a depth-limited clone is STILL shallow by
        # `git rev-parse --is-shallow-repository`, so the gate would have gone on declaring itself
        # dark on the very venue the fetch-depth was added to light up. **Shallowness is not the
        # question — SUFFICIENCY is.**
        #
        #   · enough ships visible          -> run, whatever the clone depth
        #   · too few AND the clone is cut  -> UNKNOWN, declared, never a pass
        #   · too few on a FULL clone       -> a real failure; something is wrong with the reader
        if len(self.ships) < RECENT:
            if self._is_shallow():
                self.skipTest("UNKNOWN, not a pass: this checkout carries only %d shipped "
                              "version(s) and %d are needed. The clone is shallow — deepen it "
                              "(actions/checkout `fetch-depth`) to light this gate up."
                              % (len(self.ships), RECENT))
            self.fail("git named %d shipped versions on a FULL clone; %d are needed. This is not a "
                      "venue problem — the stamp reader is not finding ships that exist."
                      % (len(self.ships), RECENT))

    def test_the_newest_ships_appear_in_TASKS_md(self):
        recent = self.ships[:RECENT]
        missing = _missing_rows(self.text, recent)
        self.assertEqual(
            [], missing,
            "these versions MOVED THE STAMP but have NO ROW in TASKS.md's ship table (a mention in prose is not a row), so the list no longer "
            "describes what the repo did:\n" + "\n".join("    %s  %s" % (v, sha) for v, sha in missing))

    def test_a_version_named_in_prose_is_not_its_row(self):
        """2026-09-26 - the check this law makes, driven on a fixture: a version that has a table row passes, a version
        named only in a sentence does not"""
        text = ("| version | commit | commit subject |\n|---|---|---|\n| **v9998** | `abc12345` | v9998 - a ship |\n\n"
                "| **#174** | R1 (v9999): a task row that NAMES the next version before its bump |\n")
        self.assertEqual(_missing_rows(text, [("v9999", "s1"), ("v9998", "s2")]), [("v9999", "s1")],
                         "a version named only in prose was counted as recorded in the ship table")

    def test_a_bump_writes_the_row_for_a_version_it_has_only_mentioned(self):
        """2026-09-26 - DRIVEN: the bump's own writer, aimed at a fixture tree whose TASKS.md names the version in a task
        row and has no ship row for it, must add the row - and must not touch the REAL TASKS.md (it used to stamp the
        real one whatever tree it was aimed at)"""
        import shutil
        import sys
        import tempfile
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import bump_version as BV
        real = io.open(TASKS, "rb").read()
        d = tempfile.mkdtemp(prefix="shiprow-")
        self.addCleanup(shutil.rmtree, d, True)
        with io.open(os.path.join(d, "TASKS.md"), "w", encoding="utf-8") as fh:
            fh.write("| **#174** | R1 (v9999): a task row naming the version before its bump |\n\n"
                     "| version | commit | commit subject |\n|---|---|---|\n| **v9998** | `abc12345` | v9998 - a ship |\n")
        BV._record_ship_in_tasks("v9999", "a name", "a note", repo=d)
        got = io.open(os.path.join(d, "TASKS.md"), encoding="utf-8").read()
        self.assertEqual(_missing_rows(got, [("v9999", "x")]), [],
                         "the bump saw v9999 named in a task row and wrote no ship row for it:\n%s" % got)
        self.assertEqual(io.open(TASKS, "rb").read(), real, "a bump aimed at a fixture tree changed the REAL TASKS.md")

    def test_the_bump_RECORDS_the_row_itself(self):
        """v2715 — the middle step failed THREE times, so it is no longer a thing to remember.

        ⚠⚠ v2888 — THE 'IS IT CALLED' HALF OF THIS LAW WAS INERT, AND I MEASURED IT.
        It read the source as TEXT and asserted two substrings: `def _record_ship_in_tasks` and
        `_record_ship_in_tasks(`. But the DEFINITION LINE CONTAINS THE CALL SUBSTRING — `def
        _record_ship_in_tasks(` ends in `_record_ship_in_tasks(` — so the second assertion was
        satisfied by the definition itself. MEASURED: delete every call site, leave the def alone,
        and the counts go 1/2 -> 1/1 and the law still PASSES. A guard written to catch plumbing
        with no tap was itself plumbing with no tap.
        So it PARSES now, and demands a real Call node OUTSIDE the function's own body — which is
        the only form of the question that can tell "defined and used" from "defined and orphaned".
        [[plumbing-with-no-tap]] [[source-reading-guard]] [[feedback-blind-fixture-green-gate]]"""
        path = os.path.join(HERE, "bump_version.py")
        tree = ast.parse(io.open(path, encoding="utf-8").read())
        defs = [n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "_record_ship_in_tasks"]
        self.assertEqual(len(defs), 1,
                         "bump_version.py declares %d function(s) named _record_ship_in_tasks — the "
                         "step that writes the TASKS.md row must exist exactly once" % len(defs))
        body = defs[0]
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_record_ship_in_tasks"
                 and not (body.lineno <= getattr(n, "lineno", 0) <= body.end_lineno)]
        self.assertTrue(calls,
                        "_record_ship_in_tasks is DEFINED and never CALLED from outside itself, so "
                        "a bump would stamp four files and silently skip the TASKS.md row — the "
                        "exact failure this function was written to end, back as an orphan")

    # ⚠ A SECOND TEST WAS WRITTEN HERE AND THEN REMOVED, BECAUSE ITS LAW WAS FALSE.
    # It asserted the mirror defect: that any version TASKS.md names must have moved the stamp.
    # It fired on 7 versions - and the premise, not the file, was wrong. A RANGE ship
    # (`v2642-v2643 — freed megabytes nobody freed`, `v2496-v2498 — A3 closed`) bumps the stamp
    # ONCE, to the range's LAST version, so v2642 and v2496 are real ships that correctly own no
    # stamp of their own. Keeping the test would have meant a gate that is permanently red for
    # legitimate history, and a gate that is always red carries exactly as much information as one
    # that is always green - the repo has already paid for that lesson once, with 149-red TV DIABLO
    # gating nothing. [[regression-guard]] [[feedback-threshold-above-the-ceiling]]
    #
    # It is recorded rather than silently dropped: v2470 and v2532 are named in TASKS.md and appear
    # in NO commit subject and NO stamp within the window. That is UNKNOWN, not proven-fictional,
    # and it is not worth a gate until someone can say which. [[unknown-stays-unknown]]




#: v2888 — this suite reads GIT HISTORY (it asks git which versions shipped), and a heart2 sandbox
#: is a plain copy with no .git, so every law failed there with "git named 0 shipped versions on a
#: FULL clone" — a message that denies being a venue problem while being one. The .git comes across
#: as an APFS clone: measured 0.09s for 297 MB, and blocks are SHARED, so it costs no disk and a
#: write in the sandbox cannot reach his real history.
PROOF_NEEDS = ["../.git"]
RED_PROOF = [
    {
        "why": "2026-09-26 - the bump's writer takes any mention of the version for its row again: v3507 and v3509 got none",
        "file": "bump_version.py",
        "find": "        if _has_ship_row(s, ver):\n",
        "replace": "        if ver in s:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-26 - this law counts a version named in prose as recorded again, and stays green with the rows missing",
        "file": "test_tasks_ships_are_recorded.py",
        "find": "    return [(v, sha) for v, sha in ships if v not in rows]\n",
        "replace": "    return [(v, sha) for v, sha in ships if v not in (text or \"\")]\n",
        "matches": 1,
    },
    {
        "why": "v2888 — the tamper ORPHANS the step: it deletes the only call to "
               "_record_ship_in_tasks and leaves the definition intact, so a bump would stamp four "
               "files and silently skip the TASKS.md row. That is the exact failure the function "
               "was written to end, and it is the failure the OLD law could not see — it matched "
               "the substring `_record_ship_in_tasks(`, which the DEFINITION LINE also contains. "
               "MEASURED before the law was rewritten: delete every call, counts go 1/2 -> 1/1, law "
               "still PASSES. It parses for a real Call node outside the def now, so this tamper "
               "reddens it. [[plumbing-with-no-tap]] [[source-reading-guard]]",
        "file": 'bump_version.py',
        "find": "    _record_ship_in_tasks(ver, name, note, repo)",
        "replace": '    pass  # _HEART2_TAMPERED_ the row is never recorded',
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS HEBREW (cp1255) AND CANNOT ENCODE THE CHARACTERS THIS FILE PRINTS. Without
    # this, a CORRECT tree reports FAILURE because the script dies while REPORTING — which teaches
    # people to ignore the tool, and then the next real failure is ignored too. The gate caught
    # this file on its first push, which is the gate doing precisely its job.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
