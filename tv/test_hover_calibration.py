#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The measurement mini auto already had and threw away.

⚠⚠ THE CHAIN THIS SITS AT THE BOTTOM OF, traced 2026-09-04 from his question *"no reel can reach
the pruning zone at all"*: `out` decides nothing for 40 reels <- the FRAME door has never said YES
<- no seal carries `extracted` (22 of 30 are `[]`, 8 predate it, ZERO satisfy the contract) <- the
contract needs `name` <- `name` only appears in a hover tooltip <- MINI AUTO is the only thing that
films tooltips <- and its tooltip->cell offset was never calibrated.

⚠ NOTHING HERE TOUCHES HIS FOOTAGE OR HIS POINTER. Every case builds its own journal in a temp dir
and stubs `tooltip_crop.changed_rect`, so these grade the arithmetic and never his 5.6 GB shelf.
[[feedback-fixtures-never-touch-live-data]] [[borrowed-surface]]
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

import hover_calibration as HC  # noqa: E402


class _Base(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="hovercal_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.journal = os.path.join(self.dir, "j.jsonl")
        self.reel = os.path.join(self.dir, "reel_s_1")
        os.makedirs(self.reel)

    def _frames(self, stamps):
        for ms in stamps:
            io.open(os.path.join(self.reel, "f_%d.jpg" % ms), "w").close()

    def _journal(self, rows):
        with io.open(self.journal, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")

    def _stub_rect(self, rects):
        """changed_rect returns rects.pop(0) each call — one per pairable step."""
        import tooltip_crop as TC
        real = TC.changed_rect
        seq = list(rects)

        def fake(a, b, thresh=18):
            return (seq.pop(0), "") if seq else (None, "no more stubbed rects")
        TC.changed_rect = fake
        self.addCleanup(setattr, TC, "changed_rect", real)

    #: ⚠ THIRTEEN DIGITS, BECAUSE THE FRAME NAME IS THE CLOCK. `_frames_by_ts` requires 13 digits
    #: — that is what `f_<epoch-ms>.jpg` carries on his real shelf, and it is deliberate: a short
    #: number in a filename is far more likely to be an index than a timestamp. My first fixture
    #: used t0=1000, every frame was skipped, and four cases failed for a reason that had nothing
    #: to do with the code they were grading. [[feedback-suspect-the-instrument]]
    def _steps(self, n, target=(500.0, 400.0), t0=1788500000000):
        """n hovers, each straddled by a frame before and after."""
        rows = [{"ts": t0 + i * 100, "i": i, "target": list(target), "container": "stash"}
                for i in range(n)]
        stamps = []
        for i in range(n):
            stamps += [t0 + i * 100 - 10, t0 + i * 100 + 10]
        return rows, stamps


class ItRefusesRatherThanGuessingAnOffset(_Base):
    """★ THE WHOLE POINT. `slot_identity.anchor_from_tooltip_rect` refuses a zero offset because a
    guessed one *"would place items in the wrong cell with total confidence"*. A calibrator that
    defaults hands it exactly the guess it is refusing to make for itself."""

    def test_an_EMPTY_journal_is_UNATTEMPTED_not_a_failed_calibration(self):
        off, rep = HC.calibrate(self.reel, path=os.path.join(self.dir, "nope.jsonl"))
        self.assertIsNone(off, "an offset was invented from no data at all")
        self.assertIn("has not run", rep["why"])
        self.assertIn("unattempted", rep["why"],
                      "it reports nothing-recorded as a FAILED calibration rather than an "
                      "unattempted one: %r" % rep["why"])

    def test_too_FEW_pairable_hovers_refuses_and_says_how_many(self):
        rows, stamps = self._steps(2)
        self._journal(rows); self._frames(stamps)
        self._stub_rect([(100.0, 100.0, 200.0, 160.0)] * 2)
        off, rep = HC.calibrate(self.reel, path=self.journal)
        self.assertIsNone(off)
        self.assertEqual(rep["used"], 2)
        self.assertIn(str(HC.MIN_STEPS), rep["why"])

    def test_a_reel_with_NO_frames_cannot_pair_anything(self):
        rows, _ = self._steps(HC.MIN_STEPS)
        self._journal(rows)
        off, rep = HC.calibrate(self.reel, path=self.journal)
        self.assertIsNone(off)
        self.assertIn("no timestamped frames", rep["why"])

    def test_hovers_that_DISAGREE_are_refused_not_averaged(self):
        """⚠ THE SPREAD IS THE CHECK. The offset is a property of the game's layout, so honest
        readings repeat almost exactly. A tip drawn on the other side of the cursor near a screen
        edge gives a wildly different pair, and averaging it produces a number no single frame
        supports — confidently wrong, which is the one outcome that matters here."""
        n = 8
        rows, stamps = self._steps(n)
        self._journal(rows); self._frames(stamps)
        rects = [(100.0, 100.0, 200.0, 160.0)] * 3 + [(900.0, 700.0, 1000.0, 760.0)] * 5
        self._stub_rect(rects)
        off, rep = HC.calibrate(self.reel, path=self.journal)
        self.assertIsNone(off, "readings that disagree by hundreds of pixels were averaged")
        self.assertIn("disagree", rep["why"])


class ItCanActuallySUCCEED(_Base):
    """⚠⚠ THE BASELINE, AND THE MOST IMPORTANT CASE IN THIS FILE. Every other case here proves a
    refusal. A calibrator that can ONLY refuse is indistinguishable from a broken one, and it would
    leave `anchor_from_tooltip_rect` blocked forever while looking rigorous.

    This is the same rule the locks live under: a door never seen to say YES cannot be trusted to
    decide anything. [[feedback-blind-fixture-green-gate]]"""

    def test_enough_agreeing_hovers_yield_the_measured_offset(self):
        n = HC.MIN_STEPS + 2
        rows, stamps = self._steps(n, target=(500.0, 400.0))
        self._journal(rows); self._frames(stamps)
        # tip top-left at (560, 430) every time -> offset is (-60, -30)
        self._stub_rect([(560.0, 430.0, 700.0, 500.0)] * n)
        off, rep = HC.calibrate(self.reel, path=self.journal)
        self.assertIsNotNone(off, "a clean, repeatable reading still produced no offset: %r" % rep)
        self.assertAlmostEqual(off[0], -60.0, places=1)
        self.assertAlmostEqual(off[1], -30.0, places=1)
        self.assertEqual(rep["used"], n)

    def test_the_offset_it_returns_is_ACCEPTED_by_the_door_that_refused(self):
        """★ THE JOIN. An offset nothing will take is a number in a report. This drives the actual
        function whose refusal started the whole chain."""
        import slot_identity as SI
        n = HC.MIN_STEPS + 1
        rows, stamps = self._steps(n, target=(500.0, 400.0))
        self._journal(rows); self._frames(stamps)
        self._stub_rect([(560.0, 430.0, 700.0, 500.0)] * n)
        off, _ = HC.calibrate(self.reel, path=self.journal)
        pt, why = SI.anchor_from_tooltip_rect((560.0, 430.0, 700.0, 500.0),
                                              cursor_corner="topleft", offset=off)
        self.assertIsNotNone(pt, "the door still refused a MEASURED offset: %s" % why)
        self.assertAlmostEqual(pt[0], 500.0, places=1)
        self.assertAlmostEqual(pt[1], 400.0, places=1)

    def test_a_ZERO_offset_is_still_refused_by_that_door(self):
        """⚠ BASELINE FOR THE BASELINE — proves the case above passed because the offset was
        measured, not because the door accepts anything."""
        import slot_identity as SI
        pt, why = SI.anchor_from_tooltip_rect((560.0, 430.0, 700.0, 500.0), offset=(0, 0))
        self.assertIsNone(pt)
        self.assertIn("calibrated", why)


class TheRecorderMayNeverStrandHisPointer(_Base):
    """A calibration note that raises inside the sweep would leave the cursor mid-walk on his
    machine. It is a passive witness of a thing he started; it gets no say in whether it finishes."""

    def test_an_unwritable_journal_does_not_raise(self):
        bad = os.path.join(self.dir, "no-such-dir", "j.jsonl")
        row = HC.record_step(0, (1.0, 2.0), (3.0, 4.0), path=bad)
        self.assertEqual(row["i"], 0)

    def test_a_None_target_is_recorded_as_None_not_as_a_point(self):
        """[[unknown-stays-unknown]] — a step with no target cannot calibrate anything, and must
        not be silently turned into (0, 0)."""
        row = HC.record_step(1, None, None, path=self.journal)
        self.assertIsNone(row["target"])
        rows, _ = HC.steps(path=self.journal)
        self.assertIsNone(rows[0]["target"])


class TheJoinExists(unittest.TestCase):
    """⚠ MINI AUTO MUST ACTUALLY CALL IT. The defect this whole file exists for was a value that
    was known and never written down; shipping a recorder nobody calls would reproduce it exactly
    one layer up. [[the-unjoined-end]]"""

    def test_hover_mode_records_every_step(self):
        import inspect
        import hover_mode
        src = inspect.getsource(hover_mode.start)
        self.assertIn("hover_calibration", src,
                      "hover_mode's step callback does not record the cell it hovered, so the "
                      "true cell is still discarded at the moment of hovering")

    def test_it_records_OUTSIDE_the_state_lock(self):
        """A disk write holding the sweep's mutex is how a slow disk becomes a stuck pointer."""
        import inspect
        import hover_mode
        src = inspect.getsource(hover_mode.start)
        i_lock = src.index('_STATE["lastStep"]')
        i_rec = src.index("hover_calibration")
        self.assertLess(i_lock, i_rec,
                        "the calibration write happens inside the `with _LOCK` block")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
