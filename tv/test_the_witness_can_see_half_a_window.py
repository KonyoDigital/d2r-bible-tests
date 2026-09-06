# -*- coding: utf-8 -*-
"""v2747 — THE ONLY INSTRUMENT WATCHING FOR A BLANK CONSOLE COULD NOT SEE HALF A BLANK CONSOLE.

Konyo, 2026-09-06, with a screenshot: *"theres a big empty space here im pretty sure there was
something here"*. The Sessions tab's right rail rendered correctly — relaunch, eagle, repair, THE
FLEET, THE SHELF — while ~1080x560 of the MAIN COLUMN was blank.

⚠⚠ THE GAP IS MEASURED, NOT ARGUED. `paint_witness.blank_strikes(pid)` asks about the WHOLE WINDOW;
its own message reads *"look N of M found content ON THE WINDOW, so it is not blank"*. His rail was
painting, so the window HAD content, so the witness answered PAINTED — correctly, for the question
it asks. And `tv/ui_faults.jsonl` proves the blindness rather than hinting at it: on the day of the
sighting it recorded 21 faults, SIXTEEN of them `console-pixels-blank-nothing-else-saw-it`, and
**ZERO within 45 minutes of 20:14**. The instrument was working and blind at the same time.
[[gate-blind-to-unexercised-input]] [[unknown-stays-unknown]]

=== THREE THINGS TESTING ON HIS REAL MACHINE CHANGED, each of which would have shipped a defect ===

1. A GRID, NOT TWO NAMED PANELS. Hardcoding "main column" and "rail" puts today's layout inside a
   health check, and the layout is the thing most likely to move. The grid asks no layout question;
   the named regions are DERIVED from its columns so the two cannot drift apart. [[copy-drift]]

2. SAMPLES 40, NOT 24 — MEASURED. At 24 samples one cell of his live console read BLANK; at 40 the
   same cell read PAINTED. BLANK-by-ink needs BOTH p99 and brightShare under their bars, and a
   sparsely-sampled cell near that boundary flips. A verdict that changes with the sample count is
   not a verdict, which is why nothing here is believed from ONE frame.

3. ⚠⚠ OCCLUSION, AND THIS IS THE ONE THAT WOULD HAVE MADE THE ROW USELESS. Caught live: Safari and
   Terminal covered 100% of his console, so every cell read blank. A window covered on ONE SIDE —
   Safari over the left half — reads blank-left/painted-right and would fire "the window is PARTLY
   drawn" as a FAULT about a perfectly healthy console sitting behind another window.
   ⚠ AND MY FIRST GUARD WAS PRESENT AND DID NOTHING: `occluded_by` returns a TUPLE
   `(coverers, why)`, not a dict with a "state" key, so `occ.get("state")` matched nothing and the
   occluded window sailed through. Verified against the real return value before trusting it.
   [[feedback-suspect-the-instrument]] [[the-unjoined-end]]
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

import paint_witness as PW  # noqa: E402
import region_witness as RW  # noqa: E402


def _code_only(src):
    """Strip comments and the module docstring. ⚠ THIRD TIME THIS SESSION a text law has failed on
    its OWN PROSE about the bug it guards: the module explains that a first guard read
    `occ.get("state")`, and a law searching for that string finds it IN THE COMMENT and fails a
    correct file. Read comments before judging a MEASUREMENT; ignore them when judging CODE.
    [[measured-true-read-wrong]] [[source-reading-guard]]
    """
    out, in_doc = [], False
    for ln in src.split("\n"):
        st = ln.strip()
        if st.startswith('"""') or st.endswith('"""'):
            # a one-line docstring opens and closes on the same line
            if st.count('"""') == 1:
                in_doc = not in_doc
            continue
        if in_doc or st.startswith("#"):
            continue
        out.append(ln)
    return "\n".join(out)


def _shot(w, h, fill=(8, 8, 8), boxes=()):
    """A synthetic BGRA bitmap in the shape _grab returns. `boxes` are painted regions.

    ⚠⚠ A PAINTED BOX IS TEXTURED, NOT A SOLID SLAB, AND MY FIRST FIXTURE GOT THIS WRONG.
    Filling a box with one flat colour makes a cell that is 100% a single colour — and
    `verdict()`'s FIRST test is exactly that: `modalShare >= 0.98` means nothing is drawn. So a
    "fully painted" fixture reported BLANK, and the failure was mine, not the module's.
    That is not a quirk to work around; it is the module being right. A real painted UI is never one
    flat colour — his console's background is a GRADIENT that never collapses to a single value,
    which is precisely why the ink test had to exist at all.
    So a painted region here is INK ON A GROUND: bright pixels scattered over the dark fill, which
    is what text actually is. [[sabotage-is-usually-the-wrong-one]] [[feedback-blind-fixture-green-gate]]
    """
    bpp, bpr = 4, w * 4
    buf = bytearray()
    for y in range(h):
        for x in range(w):
            c = fill
            for (x0, y0, x1, y1, cc) in boxes:
                if x0 <= x < x1 and y0 <= y < y1:
                    # ~28% bright ink over the ground, plus a slight gradient in the ground itself,
                    # so no cell is ever one uniform colour
                    c = cc if ((x * 7 + y * 3) % 7 < 2) else (fill[0] + (x % 5), fill[1] + (y % 5),
                                                              fill[2] + ((x + y) % 5))
            buf += bytes((min(255, c[0]), min(255, c[1]), min(255, c[2]), 255))
    return {"w": w, "h": h, "buf": bytes(buf), "bpr": bpr, "bpp": bpp}


class _Fake(object):
    """Stands in for the compositor so every verdict is forced without touching his screen."""

    def __init__(self, shot, covered=None):
        self.shot = shot
        self.covered = covered or []

    def install(self):
        self._w, self._g, self._o = PW.window_for, PW._grab, PW.occluded_by
        PW.window_for = lambda pid, quartz=None: ({"id": 1}, "")
        PW._grab = lambda wid, quartz=None: (self.shot, "")
        PW.occluded_by = lambda pid, quartz=None: (list(self.covered), "covered" if self.covered else "")
        return self

    def remove(self):
        PW.window_for, PW._grab, PW.occluded_by = self._w, self._g, self._o


class TheWitnessCanSeeHalfAWindow(unittest.TestCase):

    def setUp(self):
        self._f = None

    def tearDown(self):
        if self._f:
            self._f.remove()

    def _use(self, shot, covered=None):
        self._f = _Fake(shot, covered).install()

    # ── ⚠ SUBJECTS EXIST, or every law below grades nothing ───────────────────────────────────
    def test_the_module_exposes_what_the_heart_reads(self):
        for fn in ("cells", "regions", "half_blank", "half_blank_strikes"):
            self.assertTrue(callable(getattr(RW, fn, None)), "%s is gone" % fn)

    def test_it_reuses_paint_witness_rather_than_re_deriving_blank(self):
        """A second opinion about what 'blank' means is a second opinion nobody reconciles. The
        thresholds were expensive: his console is a DARK THEME, 72.7% below luminance 24 while
        healthy, so the verdict rests on uniformity and an ink tail, never on darkness."""
        src = io.open(os.path.join(HERE, "region_witness.py"), encoding="utf-8").read()
        self.assertIn("PW.measure(", src, "it no longer uses paint_witness.measure")
        self.assertIn("PW.verdict(", src, "it no longer uses paint_witness.verdict")
        code = _code_only(src)
        for bad in ("BLANK_MODAL_SHARE =", "INK_SHARE_MAX =", "INK_LUM ="):
            self.assertNotIn(bad, code,
                             "it re-declares %r — a second set of bars that can drift from "
                             "paint_witness's" % bad)

    # ── ⚠⚠ THE LAW: half a window must be expressible ─────────────────────────────────────────
    def test_a_HALF_BLANK_window_is_seen_as_partly_drawn(self):
        """His sighting: one side painted, the other empty. 900x600 with ink only on the right."""
        self._use(_shot(900, 600, fill=(8, 8, 8),
                        boxes=[(600, 40, 900, 560, (240, 240, 240))]))
        r = RW.half_blank(1234)
        self.assertTrue(r["ok"], r.get("why"))
        self.assertTrue(r["half"],
                        "a window painted on one side and blank on the other was NOT reported as "
                        "partly drawn — which is the entire defect this module exists for. %s"
                        % str(r.get("why"))[:160])

    def test_the_WHOLE_WINDOW_witness_calls_that_same_window_fine(self):
        """⚠ THE POINT OF THE WHOLE FILE. If the old witness also caught it, this module is
        redundant. It does not: content anywhere means 'not blank'."""
        shot = _shot(900, 600, fill=(8, 8, 8), boxes=[(600, 40, 900, 560, (240, 240, 240))])
        st, why = PW.verdict(PW.measure(shot))
        self.assertEqual(PW.PAINTED, st,
                         "the whole-window verdict changed; if it now catches a half-blank window "
                         "this module's premise needs re-reading rather than trusting. why=%r"
                         % str(why)[:140])

    def test_a_FULLY_PAINTED_window_is_not_a_fault(self):
        self._use(_shot(900, 600, fill=(8, 8, 8), boxes=[(20, 40, 880, 560, (240, 240, 240))]))
        r = RW.half_blank(1234)
        self.assertTrue(r["ok"], r.get("why"))
        self.assertFalse(r["half"], "a fully painted window was reported as partly drawn")

    def test_a_FULLY_BLANK_window_is_not_reported_as_HALF(self):
        """A dead window is the OTHER witness's job. Reporting it here too would double-count one
        fault as two."""
        self._use(_shot(900, 600, fill=(8, 8, 8)))
        r = RW.half_blank(1234)
        self.assertFalse(r["half"],
                         "a fully blank window was called partly drawn — that is the whole-window "
                         "witness's finding, not this one's")

    # ── ⚠⚠ OCCLUSION — the false positive that would have made the row noise ───────────────────
    def test_a_COVERED_window_is_UNKNOWN_and_never_a_fault(self):
        self._use(_shot(900, 600, fill=(8, 8, 8),
                        boxes=[(600, 40, 900, 560, (240, 240, 240))]),
                  covered=["Safari (100.0%)"])
        g = RW.cells(1234)
        self.assertFalse(g["ok"], "a COVERED window produced a verdict; its bitmap is not evidence "
                                  "about what it painted")
        self.assertTrue(g.get("occluded"), "the occlusion was not recorded")
        self.assertIn("COVERED", str(g.get("why")))

    def test_the_occlusion_guard_reads_the_REAL_return_shape(self):
        """⚠ IT WAS PRESENT AND DOING NOTHING. occluded_by returns a TUPLE (coverers, why), and a
        first version read occ.get("state") — matched nothing, guard inert, occluded window through."""
        src = io.open(os.path.join(HERE, "region_witness.py"), encoding="utf-8").read()
        self.assertIn("_cov, _cwhy = PW.occluded_by(", src,
                      "the guard no longer unpacks occluded_by's tuple, so it may be inert again")
        self.assertNotIn('occ.get("state")', _code_only(src),
                         "the dict-shaped read is back in CODE; it matches nothing")

    # ── ⚠ ONE FRAME IS A SAMPLE, NOT A VERDICT ────────────────────────────────────────────────
    def test_a_MOVING_blank_cell_is_refused_as_a_fault(self):
        """A window mid-repaint shows different blank cells each look. That is repainting, not
        stuck, and averaging it into a fault is how a health row starts crying wolf."""
        # ⚠ THE BLANK SETS MUST ACTUALLY BE DISJOINT, and my first fixture's were not: painting
        # only the left in one shot and only the right in the other leaves the MIDDLE column blank
        # in BOTH, so the intersection was non-empty and the module correctly called it persistent.
        # The fixture was wrong, not the law. Paint left+middle, then middle+right, so the blank
        # cells genuinely move. [[sabotage-is-usually-the-wrong-one]]
        shots = [_shot(900, 600, fill=(8, 8, 8), boxes=[(0, 40, 600, 560, (240, 240, 240))]),
                 _shot(900, 600, fill=(8, 8, 8), boxes=[(300, 40, 900, 560, (240, 240, 240))])]
        state = {"i": 0}
        f = _Fake(shots[0]).install()
        try:
            def _g(wid, quartz=None):
                s = shots[state["i"] % len(shots)]
                state["i"] += 1
                return (s, "")
            PW._grab = _g
            r = RW.half_blank_strikes(1234, sleep=lambda *_: None)
            self.assertFalse(r["half"],
                             "blank cells that MOVED between looks were still called a fault: %s"
                             % str(r.get("why"))[:150])
            self.assertIn("MOVED", str(r.get("why")))
        finally:
            f.remove()

    def test_a_STUCK_half_blank_window_survives_the_strikes(self):
        """The other direction — this must not become a blanket refusal."""
        self._use(_shot(900, 600, fill=(8, 8, 8),
                        boxes=[(600, 40, 900, 560, (240, 240, 240))]))
        r = RW.half_blank_strikes(1234, sleep=lambda *_: None)
        self.assertTrue(r["ok"], r.get("why"))
        self.assertTrue(r["half"],
                        "a window blank in the SAME cells on every look was not reported: %s"
                        % str(r.get("why"))[:150])

    def test_an_UNREADABLE_window_is_UNKNOWN_not_healthy(self):
        f = _Fake(None).install()
        try:
            PW._grab = lambda wid, quartz=None: (None, "no image")
            r = RW.half_blank_strikes(1234, sleep=lambda *_: None)
            self.assertFalse(r["ok"])
            self.assertIsNone(r["half"], "a window nobody could photograph was given a verdict")
            self.assertIn("NOTHING is known", str(r.get("why")))
        finally:
            f.remove()

    # ── it never touches his surface ──────────────────────────────────────────────────────────
    def test_it_never_acts_on_the_window(self):
        src = io.open(os.path.join(HERE, "region_witness.py"), encoding="utf-8").read()
        code = _code_only(src)
        for bad in ("AXUIElement", "CGEventPost", "activateWithOptions", "reload", "restart",
                    "subprocess", "os.system"):
            self.assertNotIn(bad, code,
                             "the witness appears to ACT on the window (%r). It answers a question; "
                             "the rescue decides. [[borrowed-surface]]" % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
