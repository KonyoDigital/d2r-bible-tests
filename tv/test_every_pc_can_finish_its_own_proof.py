# -*- coding: utf-8 -*-
"""REG-1626 — EVERY PC CAN FINISH ITS OWN PROOF: NO LOCK STAYS SHUT OVER WHAT A PC CAN NEVER HAVE.

His directive, 2026-09-30: "individual consoles and each with a unified logic database wise but individual readings
... when this is finally working properly on GROKBOTs pc and also on ALT windows PC like it is suppose to obivously on
the MACBOOK ... then it should obviously work for dean's PC without needing to SSH".

MEASURED in the fleet the same night, after the ALT began proving itself:
  · GrokBot's box: its pull lane said "level with origin" (fleet_origin_status compares HEAD with origin/main) while
    self_prove.tree_state said tree-unknown - it asked only @{upstream}, and that checkout has no tracking branch - so
    it never proved at all. One tree, two refs, two answers.
  · the ALT: test_chronicle_template came back BLIND. Its PROOF_NEEDS is his hand-read footage, which never leaves his
    Mac; absent there, all 12 laws skipped, the run exited 0 and the gate was filed BLIND - and one blind gate keeps
    may() shut on that PC for good, over a law about data it will never hold. heart2's own comment always said an
    absent need reads UNPROVABLE; _prove_one never did it.

Driven here: tree_state with a fake git (the fleet's ref when there is no upstream; its words say so; an upstream
still wins), and _prove_one over a fixture repo copy (an absent subject is UNPROVABLE without running anything, and
says whether it is off this PC or only missing from the copy; a present one still goes to the clean run).
RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H2  # noqa: E402
import self_prove as SP  # noqa: E402

RED_PROOF = [
    {"why": "REG-1626 - a checkout with no tracking branch is tree-unknown again: GrokBot never proves",
     "file": "self_prove.py",
     "find": "            rc, counts = g(\"rev-list\", \"--left-right\", \"--count\", \"origin/main...HEAD\")\n",
     "replace": "            rc, counts = 1, \"\"\n", "matches": 1},
    {"why": "REG-1626 - a gate whose subject is not on this PC runs anyway and is filed BLIND",
     "file": "heart2.py",
     "find": "        if _gone:\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "REG-1644 - an unreadable PROOF_NEEDS goes to the clean run again and can be filed BLIND",
     "file": "heart2.py",
     "find": "    if _needs is None:\n",
     "replace": "    if False:\n", "matches": 1},
]


def _git(answers):
    """a fake git: answers[(args...)] -> (rc, out); anything not listed fails like git would"""
    calls = []

    def g(*args):
        calls.append(args)
        return answers.get(args, (128, ""))
    g.calls = calls
    return g


STATUS = ("status", "--porcelain", "--untracked-files=no")
UPSTREAM = ("rev-list", "--left-right", "--count", "@{upstream}...HEAD")
ORIGIN = ("rev-list", "--left-right", "--count", "origin/main...HEAD")


class ACheckoutWithNoUpstreamIsJudgedLikeTheFleetJudgesIt(unittest.TestCase):
    def test_level_with_origin_main_is_installed(self):
        kind, why = SP.tree_state(git=_git({STATUS: (0, ""), ORIGIN: (0, "0\t0")}))
        self.assertEqual(kind, "installed", "GrokBot's box - level with origin/main, no tracking branch: %r" % why)
        self.assertIn("origin/main", why, "the words do not say which ref judged it")

    def test_behind_and_ahead_keep_their_meaning(self):
        self.assertEqual(SP.tree_state(git=_git({STATUS: (0, ""), ORIGIN: (0, "2\t0")}))[0], "installed")
        self.assertEqual(SP.tree_state(git=_git({STATUS: (0, ""), ORIGIN: (0, "0\t3")}))[0], "dev",
                         "local commits not on origin must still be a development tree")

    def test_an_upstream_still_wins_and_nothing_else_is_asked(self):
        g = _git({STATUS: (0, ""), UPSTREAM: (0, "0\t0"), ORIGIN: (0, "5\t5")})
        kind, why = SP.tree_state(git=g)
        self.assertEqual(kind, "installed")
        self.assertNotIn(ORIGIN, g.calls, "origin/main was asked although the checkout has an upstream")

    def test_neither_is_unknown_and_edits_are_dev(self):
        self.assertEqual(SP.tree_state(git=_git({STATUS: (0, "")}))[0], "unknown")
        self.assertEqual(SP.tree_state(git=_git({STATUS: (0, " M tv/x.py"), ORIGIN: (0, "0\t0")}))[0], "dev")


class AGateWhoseSubjectIsNotHereIsUnprovableHere(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="absent_subject_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.sandbox = os.path.join(self.d, "copy", "tv")          # the copied tv/, inside a repo copy
        os.makedirs(self.sandbox)
        with io.open(os.path.join(self.sandbox, "target.py"), "w", encoding="utf-8") as fh:
            fh.write("ANCHOR = 1\n")
        self.law = os.path.join(self.d, "test_needs_footage.py")
        with io.open(self.law, "w", encoding="utf-8") as fh:
            fh.write('PROOF_NEEDS = ["frames/hist/reel_nowhere"]\n')
        self.pr = {"file": "target.py", "find": "ANCHOR = 1", "replace": "ANCHOR = 2", "matches": 1}
        self.said, self.ran = [], []

    def _prove(self):
        def run_gate(*a, **k):
            self.ran.append(a)
            return None, "fixture: the clean run was reached"
        why = {}
        with mock.patch.object(H2, "_run_gate", run_gate), mock.patch.object(H2, "gate_spec", lambda n: ([], 30, None)):
            v = H2._prove_one(self.sandbox, "test_needs_footage", self.law, self.pr, 0, self.said.append, why=why)
        return v, why

    def test_off_this_pc_it_is_unprovable_and_nothing_runs(self):
        v, why = self._prove()
        self.assertEqual(v, H2.UNPROVABLE, "an absent subject was graded - the ALT filed this BLIND")
        self.assertEqual(self.ran, [], "a gate with nothing to grade here was run anyway")
        self.assertEqual(why.get("absentSubject"), "frames/hist/reel_nowhere")
        self.assertIn("not on this PC", " ".join(self.said))

    def test_present_it_still_goes_to_the_clean_run(self):
        os.makedirs(os.path.join(self.sandbox, "frames", "hist", "reel_nowhere"))
        v, _why = self._prove()
        self.assertEqual(len(self.ran), 1, "a subject that IS here no longer reaches its clean run")

    def test_an_unreadable_declaration_is_unprovable_never_a_clean_run(self):
        """REG-1644 (the v3535 eye) - a PROOF_NEEDS that is not a literal cannot be read: UNKNOWN, never "needs nothing"."""
        with io.open(self.law, "w", encoding="utf-8") as fh:
            fh.write('import os\nPROOF_NEEDS = [os.path.join("frames", "hist", "reel_nowhere")]\n')
        self.assertIsNone(H2.proof_needs_in(self.law), "PREMISE: the fixture's declaration was readable after all")
        v, why = self._prove()
        self.assertEqual(v, H2.UNPROVABLE, "an unreadable PROOF_NEEDS was graded as if it needed nothing")
        self.assertEqual(self.ran, [], "a gate whose needs could not be read went to its clean run")
        self.assertTrue(why.get("needsUnreadable"))
        self.assertIn("cannot be read", " ".join(self.said))


if __name__ == "__main__":
    unittest.main(verbosity=2)
