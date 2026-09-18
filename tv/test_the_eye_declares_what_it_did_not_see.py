# -*- coding: utf-8 -*-
"""v3299 — THE SECOND EYE MUST DECLARE WHAT IT DID NOT LOOK AT.

`payload_for(sha)` runs `git show <sha>` on the ONE commit that carries the version stamp. A push
carries as many commits as it carries. So every `fix:` commit landing after the bump and before the
push is **never seen by any eye** — while the ledger row that lands reads as though the push was
reviewed.

MEASURED 2026-09-18 on v3298. Four commits shipped in one push and the eye saw ONE:

    bc6b74b4  v3298                                  <- the only commit reviewed
    d284f7e7  fix: retract REG-1108's cause          NEVER LOOKED AT
    b70e1af8  fix: invert the law, re-anchor proofs  NEVER LOOKED AT
    1a110dae  fix: re-owe is MEMBERSHIP not timing   NEVER LOOKED AT

The last of those took THREE cuts, two of them wrong, and was the most consequential change in the
push. And the consequence showed up in the verdict immediately: the eye's fourth finding attacked
`_fnew > _dm + 0.5` — code SUPERSEDED two commits later. **That is not the eye being wrong; it is the
gate handing it bytes that no longer ship.**

⚠ THIS LAW DOES NOT CLOSE THE GAP. Closing it means a wider payload, and the payload already
truncates at roughly 35% of the diff — the two are one problem and the cost is HIS call. What this
law pins is that the runner STATES ITS OWN REACH, so a row stops implying a coverage it never had.
A guard that cannot say what it did not measure is the defect this repo keeps re-learning.

THREE STATES, AND COLLAPSING ANY TWO IS THE DEFECT:
    a LIST  -> measured, and these are the commits that ship unreviewed
    []      -> MEASURED AND NONE — the look genuinely covers the push
    None    -> the range could not be listed: UNKNOWN, and NEVER "nothing was missed"
[[zero-needs-a-denominator]] [[unknown-stays-unknown]] [[source-reading-guard]]

⚠ PINS THE RULE, NOT TODAY'S SHAS. It uses HEAD~1 and HEAD rather than hardcoded commits, so it
keeps meaning the same thing after the next ship. A law that pins a roster goes stale the day
reality moves. [[regression-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


class TestTheEyeDeclaresWhatItDidNotSee(unittest.TestCase):

    def setUp(self):
        import second_eye_run as r
        self.r = r
        if not os.path.isdir(os.path.join(ROOT, ".git")):
            self.skipTest("no git checkout here — the range cannot be asked for")

    def test_a_commit_with_later_work_names_every_unreviewed_commit(self):
        """BEHAVIOURAL: HEAD~1 always has exactly one commit after it — HEAD."""
        got = self.r.uncovered_commits("HEAD~1")
        self.assertIsNotNone(
            got,
            "uncovered_commits('HEAD~1') returned None in a real checkout. The range IS listable "
            "here, so None means the caller will be told UNKNOWN when the answer was available.")
        self.assertGreaterEqual(
            len(got), 1,
            "HEAD~1 has %d commit(s) after it; there is always at least HEAD. A look at HEAD~1 "
            "that reports nothing unreviewed is exactly the false coverage this law exists for."
            % len(got))

    def test_a_tip_commit_reports_MEASURED_AND_NONE_not_unknown(self):
        """[] and None are different facts. HEAD has nothing after it — that is a MEASUREMENT."""
        got = self.r.uncovered_commits("HEAD")
        self.assertIsNotNone(
            got,
            "uncovered_commits('HEAD') returned None. Nothing ships after HEAD and the range is "
            "perfectly listable, so this must be a measured empty list — not UNKNOWN.")
        self.assertEqual(
            got, [],
            "HEAD reported %r commit(s) after it, which cannot be true of the tip." % (got,))

    def test_an_unresolvable_sha_is_UNKNOWN_and_never_an_empty_list(self):
        """⚠ THE ONE THAT MATTERS. An empty list means 'the push is fully covered'."""
        got = self.r.uncovered_commits("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
        self.assertIsNone(
            got,
            "an unresolvable sha returned %r instead of None. An empty list is read by the caller "
            "as MEASURED-AND-NONE — it would print nothing and the operator would conclude the "
            "look covered the whole push, on the strength of a git command that failed. That is a "
            "confident zero manufactured from an error." % (got,))

    def test_the_caller_tells_the_two_apart(self):
        """A correct helper feeding a caller that collapses None into [] fixes nothing."""
        import re
        with io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.find("_rows = uncovered_commits(sha)")
        self.assertGreater(
            i, -1,
            "the reporting path no longer calls uncovered_commits() — the helper is correct and "
            "nothing reads it, so the row goes back to implying full coverage.")
        # Anchor BOTH ends: the region is the reporting block, not its neighbourhood.
        j = src.find("if prompt_out:", i)
        self.assertGreater(j, i, "could not bound the reporting block; refusing to judge a slice "
                                 "whose far end is a guess. [[source-reading-guard]]")
        blk = src[i:j]
        code = "\n".join(l.split("#", 1)[0] for l in blk.split("\n"))
        self.assertIn(
            "_rows is None", code,
            "the reporting block does not branch on `_rows is None`, so an UNLISTABLE range and a "
            "genuinely-covered push print the same thing. Comments stripped before this check, "
            "because the prose above it explains exactly this distinction. [[REG-1070]]")
        self.assertTrue(
            re.search(r"len\(\s*_rows\s*\)", code),
            "the block never reports HOW MANY commits ship unreviewed. A warning without its count "
            "is not a denominator.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "returning [] for an unlistable range turns a failed git call into 'fully covered'",
        "file": "tv/second_eye_run.py",
        "find": "    if out is None:\n        return None\n    return [l.strip() for l in out.splitlines() if l.strip()]",
        "replace": "    if out is None:\n        return []\n    return [l.strip() for l in out.splitlines() if l.strip()]",
        "matches": 1,
    },
    {
        "why": "dropping the None branch makes UNKNOWN and fully-covered print identically",
        "file": "tv/second_eye_run.py",
        "find": "    if _rows is None:",
        "replace": "    if False:",
        "matches": 1,
    },
]
