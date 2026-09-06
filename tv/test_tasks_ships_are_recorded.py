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
            m = re.search(r'"ver"\s*:\s*"(v2[0-9]{3})"', ln)
            if m and sha:
                rows.append((m.group(1), sha))
                sha = None
    return rows


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
        missing = [(v, sha) for v, sha in recent if v not in self.text]
        self.assertEqual(
            [], missing,
            "these versions MOVED THE STAMP but appear NOWHERE in TASKS.md, so the list no longer "
            "describes what the repo did:\n" + "\n".join("    %s  %s" % (v, sha) for v, sha in missing))

    def test_the_bump_RECORDS_the_row_itself(self):
        """v2715 — THE MIDDLE STEP FAILED THREE TIMES, SO IT IS NO LONGER A STEP.

        This file already told anyone reading it: *"THE WORKFLOW IT ENFORCES: bump -> record the
        row here -> commit. The gate fails on its own ship if that middle step is skipped - it did,
        on v2670, which is how this line came to exist."*

        It then happened on v2712, v2713 AND v2714, in a single session, by the same hand that had
        just read that sentence. This gate caught it in CI, correctly, three ships late.

        A step a human must remember, in the middle of a mechanical sequence a tool is already
        performing, will be skipped again. `bump_version` already edits four files; TASKS.md is the
        fifth surface describing the same event, and the tool that moves the stamp is the only
        thing that reliably knows a ship happened. So it writes the row now — and this pins that it
        still DOES, because a recorder that exists and is never called is the purest form of the
        defect this repo keeps paying for. [[the-unjoined-end]]
        """
        import io as _io
        src = _io.open(os.path.join(HERE, "bump_version.py"), encoding="utf-8").read()
        src = re.sub(r'"""(?:.|\n)*?"""', " ", src)          # judge CODE, not the prose about it
        src = re.sub(r"(?m)#.*$", " ", src)
        self.assertIn(
            "def _record_ship_in_tasks", src,
            "bump_version has no ship recorder, so recording a ship is a step somebody has to "
            "remember — and that has now failed on v2670, v2712, v2713 and v2714."
        )
        self.assertIn(
            "_record_ship_in_tasks(", src.split("def _record_ship_in_tasks", 1)[0]
            + src.split("def _record_ship_in_tasks", 1)[1].split("\ndef ", 1)[-1],
            "the recorder is DEFINED but never CALLED from the bump. A tested helper nobody "
            "invokes is exactly the shape this gate exists to prevent."
        )

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
