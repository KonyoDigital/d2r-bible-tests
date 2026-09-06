# -*- coding: utf-8 -*-
"""v2740 — THE FRAME DELETER OFFERED 7 FRAMES OUT OF A REEL HELD SO IT COULD BE RE-READ.

Konyo: *"fix the 7 evidence frames"*.

MEASURED at origin: `frame_authority.plan_frames()` offered 805 frames, and ALL 805 sat inside
reels `reel_retention` HOLDS. Split by WHY they were held — and the split is the whole point,
because one number covering two situations overstated his exposure by roughly 100x:

    reel_s_1786999742937_35523   483   test-fixture   POLICY     releasable
    reel_s_1786385768689_67392   217   test-fixture   POLICY     releasable
    reel_s_1785708285647_38665    98   test-fixture   POLICY     releasable
    reel_s_1787243026006_12211     7   zero-pages     EVIDENCE   swept        <- these

A `zero-pages` reel is held because, in the shelf's own words, "the engine reopens these when the
prompt improves". Freeing its frames destroys the only thing the hold protects: a re-read with no
frames is not a re-read.

⚠ THE DEFECT WAS A MISSING JOIN, NOT A RECKLESS DELETER. `frame_authority` holds WITNESS FRAMES
(23, witnessOk True, keeping 4217 of 5022); `reel_retention` holds WHOLE REELS. Neither consulted
the other, so the deleter had no way to know a reel can be held for a reason that needs its frames.
It was found by the HEART (`frame-deleter-not-looser` reading DISAGREE), not by a gate — a gate
fails when code changes; a heart says a thing is wrong when nobody touched it. [[join-gate-heart]]

MEASURED AFTER: 805 -> 798 prunable, kept 4217 -> 4224 (+7 exactly), and the 7 are held under
"its reel is held as EVIDENCE by the shelf".

=== THE THREE DESIGN CALLS THIS FILE PINS ===
1. THE REFUSAL LIVES IN `plan_frames`, NOT `frame_verdict`. That function is a per-frame PREDICATE
   used by river.py's joint and by tests; giving it a new input would break them or hand them a
   default, and the only available default — "assume nothing is held" — is the unsafe direction.
2. AN UNREADABLE HOLD LIST MEANS NOTHING IS PRUNABLE, mirroring the seal refusal already in that
   function rather than inventing a second shape for the same ignorance. v2229 records the cost of
   the other direction: the prune deleted two fixture reels (80.5 MB / 71 pages and 42.4 MB / 35
   pages) that nothing had told it were fixtures.
3. ⛔ POLICY HOLDS ARE DELIBERATELY NOT COVERED. He asked for the evidence frames. Widening the
   refusal from 7 to 805 would answer a question he did not ask, and a test-fixture hold is a
   different argument with a different owner.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import frame_authority as FA  # noqa: E402
import reel_story as RS  # noqa: E402

SRC = io.open(os.path.join(HERE, "frame_authority.py"), encoding="utf-8").read()


class _Shelf(object):
    """Stands in for reel_story.story so every case is forced without touching his tree."""

    def __init__(self, payload):
        self.payload = payload

    def __call__(self, hist_dir=None):
        return self.payload


def _with_shelf(payload, fn):
    real = RS.story
    RS.story = _Shelf(payload)
    try:
        return fn()
    finally:
        RS.story = real


class FramesRespectEvidenceHolds(unittest.TestCase):

    # ── the reader ────────────────────────────────────────────────────────────────────────────
    def test_it_reports_ONLY_evidence_holds(self):
        got = _with_shelf({"ok": True, "reels": [
            {"reel": "reel_ev", "held": True, "holdKind": "evidence"},
            {"reel": "reel_pol", "held": True, "holdKind": "policy"},
            {"reel": "reel_free", "held": False, "holdKind": None},
        ]}, lambda: FA.evidence_held_reels("/nowhere"))
        self.assertEqual(({"reel_ev"}, ""), got,
                         "a POLICY hold was folded in with the evidence holds. He asked for the 7 "
                         "evidence frames; widening the refusal to the 798 test-fixture frames "
                         "answers a question nobody asked.")

    def test_an_unreadable_shelf_is_None_not_an_empty_set(self):
        """⚠ THE LOAD-BEARING DISTINCTION. An empty set means "measured, nothing is held" and would
        let every frame through. None means nobody could look. [[unknown-stays-unknown]]"""
        for bad in ({"ok": False, "why": "the shelf blew up"}, {"ok": True}, None, "not a dict"):
            got, why = _with_shelf(bad, lambda: FA.evidence_held_reels("/nowhere"))
            self.assertIsNone(got, "an unreadable shelf (%r) returned a SET, which reads as "
                                   "'nothing is held'" % (bad,))
            self.assertTrue(why, "the refusal carries no reason")

    # ── ⚠⚠ THE OFFER ITSELF ───────────────────────────────────────────────────────────────────
    def test_an_UNKNOWN_hold_list_makes_NOTHING_prunable(self):
        """The same answer the seal refusal already gives to the same shape of ignorance. Assuming
        'nothing is held' is how v2229 lost two fixture reels."""
        out = _with_shelf({"ok": False, "why": "simulated"},
                          lambda: FA.plan_frames(os.path.join(HERE, "frames", "hist")))
        self.assertEqual([], out.get("prunable"),
                         "frames were offered while the hold list was UNKNOWN")
        self.assertIn("NOTHING is prunable", out.get("say") or "")
        self.assertIsNone(out.get("evidenceHeldReels"),
                          "the plan reported a hold list it could not read")

    def test_the_plan_PUBLISHES_which_reels_it_treated_as_held(self):
        """A refusal nobody can audit is a promise. The list travels in the payload so the count
        can be checked against the shelf rather than taken on trust."""
        out = _with_shelf({"ok": True, "reels": [
            {"reel": "reel_ev", "held": True, "holdKind": "evidence"}]},
            lambda: FA.plan_frames(os.path.join(HERE, "frames", "hist")))
        self.assertEqual(["reel_ev"], out.get("evidenceHeldReels"))

    # ── the source-level properties, each with its reason ─────────────────────────────────────
    def test_the_refusal_is_applied_where_the_OFFER_is_made(self):
        """⚠ NOT inside frame_verdict — it is a predicate shared with river.py's joint and with
        tests, and the only default it could take is the unsafe one."""
        self.assertIn("held_reels, held_why = evidence_held_reels(hist_dir)", SRC,
                      "plan_frames no longer reads the hold list")
        # ⚠ ANCHOR BOTH ENDS ON frame_verdict ITSELF. The first cut sliced frame_verdict ->
        # plan_frames, and `evidence_held_reels` is DEFINED between them — so the law failed
        # against correct code. A window that spans a third function measures the wrong region.
        # [[source-reading-guard]]
        i = SRC.find("def frame_verdict(")
        j = SRC.find("\ndef ", i + 1)
        self.assertGreater(j, i, "frame_verdict moved; re-anchor this law before trusting it")
        self.assertNotIn("evidence_held_reels", SRC[i:j],
                         "the hold lookup was moved INTO frame_verdict, whose callers cannot "
                         "supply it and would silently get the unsafe default")

    def test_the_import_of_reel_story_stays_LAZY(self):
        """`reel_retention` imports THIS module, so a module-level import here is a cycle.
        reel_retention already uses the same lazy shape for the same reason."""
        head = SRC.split("def ", 1)[0]
        self.assertNotIn("import reel_story", head,
                         "reel_story is imported at module level — reel_retention imports "
                         "frame_authority, so this is an import cycle waiting to fire")
        self.assertIn("import reel_story as _rs", SRC, "the lazy import is gone entirely")

    def test_the_module_still_DELETES_NOTHING(self):
        """This module reports; removal stays behind prune.arm, which is LOCKED and disarmed by his
        standing ruling. A fix that added a delete would be a far worse defect than the one it fixed."""
        import ast
        tree = ast.parse(SRC)
        WRITERS = {"remove", "unlink", "rmtree", "rmdir", "system", "run", "Popen"}
        called = {n.func.attr for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertEqual(set(), called & WRITERS,
                         "frame_authority calls %s — it reports, it does not delete"
                         % sorted(called & WRITERS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
