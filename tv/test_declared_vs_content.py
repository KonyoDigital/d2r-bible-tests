# -*- coding: utf-8 -*-
"""A15 — zero disagreements over a sample that cannot disagree is the sample speaking.

The clause: **the route is derived from the CONTENT, never declared up front, never guessed from a
filename or a focus stamp** (v1783 — *a default is not a declaration*).

⚠⚠ MEASURED ON HIS TREE: 40 reel dirs, 40 with an index.json, and exactly **1 declaring a chronicle
focus — carrying 0 surveyed panels**. So there is nothing for a declaration to contradict, and a
report of AGREES would say the routing law holds when nobody has shown it.

⚠ And one suspicion was REFUTED BY THE SOURCE before it was published: `_vault_lane_owes` returns
True when there is NO declared focus, which looks exactly like v1783 — and its docstring says
*"Errs toward KEEPING... 'I could not tell' must never resolve to 'delete it'"*. An absent stamp
HOLDS the reel. That is the safe direction, deliberately. [[measured-true-read-wrong]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import declared_vs_content as DVC   # noqa: E402


class AZeroMustEarnTheWordAgrees(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="dvc_")
        self.hist, self.triage = DVC.HIST, DVC.TRIAGE
        DVC.HIST = os.path.join(self.dir, "hist")
        DVC.TRIAGE = os.path.join(self.dir, "triage.json")
        os.makedirs(DVC.HIST)
        self.tri = {}

    def tearDown(self):
        DVC.HIST, DVC.TRIAGE = self.hist, self.triage
        shutil.rmtree(self.dir, ignore_errors=True)

    def _reel(self, name, focus, panels=0, kinds=None):
        p = os.path.join(DVC.HIST, "reel_" + name)
        os.makedirs(p)
        io.open(os.path.join(p, "index.json"), "w", encoding="utf-8").write(
            json.dumps({"focus": focus}))
        self.tri["reel_" + name] = {"panels": panels, "kinds": kinds or {}}
        io.open(DVC.TRIAGE, "w", encoding="utf-8").write(json.dumps(self.tri))

    def test_one_declaring_reel_with_no_content_is_UNTESTABLE(self):
        """His tree exactly: a declaration with nothing surveyed to check it against."""
        self._reel("a", "chronicle-uniques", panels=0)
        r = DVC.report()
        self.assertEqual(
            r["state"], DVC.UNTESTABLE,
            "a single declaring reel carrying NO panels reported %r. There is nothing for the "
            "declaration to contradict, and agreement would claim the routing law holds."
            % r["state"])
        self.assertIn("measures the SAMPLE", r["why"])

    def test_THREE_reels_with_no_content_are_still_UNTESTABLE(self):
        """⚠ THE SAMPLE FLOOR MASKED THIS GUARD, so the sabotage for it passed at first.

        With ONE no-content reel, both the guarded and unguarded paths end UNTESTABLE — the floor
        catches it either way. It takes THREE to tell them apart: without the "no panels means
        nothing to compare" branch, three empty reels count as EXERCISED and the report says
        AGREES, claiming the routing law holds on reels that surveyed nothing at all.
        """
        for n in ("a", "b", "c"):
            self._reel(n, "chronicle-uniques", panels=0)
        r = DVC.report()
        self.assertEqual(
            r["state"], DVC.UNTESTABLE,
            "three declaring reels with NO surveyed panels reported %r. Nothing was found to "
            "check any declaration against, and agreement would be a clean bill drawn from "
            "empty reels." % r["state"])
        self.assertEqual(r["exercised"], 0,
                         "a reel with no panels was counted as exercising the check")

    def test_a_declaration_its_content_contradicts_is_reported(self):
        """⚠ BASELINE: DISAGREES must be reachable, or UNTESTABLE is all this can ever say."""
        self._reel("a", "chronicle-uniques", panels=4, kinds={"stash": 4})
        r = DVC.report()
        self.assertEqual(r["state"], DVC.DISAGREES, r["why"])
        self.assertIn("stash", r["rows"][0]["why"])

    def test_AGREES_needs_enough_exercised_reels(self):
        """Two agreeing reels is still an anecdote — the floor is deliberately above 1."""
        self._reel("a", "chronicle-uniques", panels=3, kinds={"panel": 3})
        self._reel("b", "chronicle-sets", panels=2, kinds={"panel": 2})
        self.assertEqual(DVC.report()["state"], DVC.UNTESTABLE)
        self._reel("c", "chronicle-uniques", panels=5, kinds={"panel": 5})
        r = DVC.report()
        self.assertEqual(
            r["state"], DVC.AGREES,
            "with %d exercised reels and no contradiction it still refused to say AGREES — a "
            "check that can never agree is as useless as one that always does" % r["exercised"])

    def test_a_disagreement_outranks_a_thin_sample(self):
        """A real contradiction is a finding even when the sample is too small to clear."""
        self._reel("a", "chronicle-uniques", panels=4, kinds={"stash": 4})
        r = DVC.report()
        self.assertEqual(r["state"], DVC.DISAGREES,
                         "a real disagreement was hidden behind the sample-size floor")

    def test_an_unreadable_TRIAGE_is_also_UNTESTABLE_not_agreement(self):
        os.unlink(DVC.TRIAGE) if os.path.exists(DVC.TRIAGE) else None
        r = DVC.report()
        self.assertEqual(r["state"], DVC.UNTESTABLE)
        self.assertIn("UNKNOWN, not agreement", r["why"],
                      "the message gives only an errno, so a reader cannot tell 'clean' from "
                      "'I could not look'")

    def test_a_reel_declaring_no_chronicle_focus_is_not_counted(self):
        self._reel("a", "stash", panels=9, kinds={"stash": 9})
        r = DVC.report()
        self.assertEqual(r.get("declaring"), 0,
                         "a reel that declares no chronicle focus was counted as declaring one")

    def test_a_missing_corpus_is_UNTESTABLE_not_agreement(self):
        # ⚠ reach the CORPUS branch, not the triage one — the first cut of this test asserted a
        # message it never got to, because no triage file had been written yet.
        io.open(DVC.TRIAGE, "w", encoding="utf-8").write("{}")
        DVC.HIST = os.path.join(self.dir, "gone")
        r = DVC.report()
        self.assertEqual(r["state"], DVC.UNTESTABLE)
        self.assertIn("UNKNOWN", r["why"])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
