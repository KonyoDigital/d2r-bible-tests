"""v2457 — the beat must distinguish RUNNING from PAINTING.

⚠ THE DEFECT THIS EXISTS FOR, measured on his machine 2026-09-03 while he was looking at a black
window: the beat was perfectly healthy the entire time. n advanced, ageS stayed under 6 seconds,
els was 11,707, blankStrikes 0, rescues 0. His words: "i do see the tooltip images when the cursor
is floating so something is just bugged agian" — and v2336's comment records the SAME report about
a single panel a month earlier.

The beat's own premise, stated in its comment, is "a renderer that has wedged runs no timers, so it
stops beating". That is FALSE for this failure: setInterval and requestAnimationFrame are throttled
by different machinery, so a page that has stopped painting keeps every timer-driven signal
healthy. Nothing in the beat could see it, which is why he was the detector twice.

These pin the LAW, not the numbers: a frozen frame counter means NOT PAINTING, an advancing one
means painting, and an ABSENT one means UNKNOWN — never false. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import control_app as ca


def _beat(raf=None, els=11707):
    st = {"els": els, "hidden": True, "view": "sessions"}
    if raf is not None:
        st["raf"] = raf
    ca.ui_beat_record(st)
    return ca._UI_BEAT


class BeatingIsNotPainting(unittest.TestCase):

    def setUp(self):
        for k, v in (("rafNow", None), ("rafPrev", None), ("painting", None),
                     ("frozenBeats", 0), ("paintWhy", "")):
            ca._UI_BEAT[k] = v

    def test_an_advancing_frame_counter_reads_as_painting(self):
        _beat(raf=100)
        b = _beat(raf=140)
        self.assertIs(b["painting"], True, b.get("paintWhy"))
        self.assertEqual(b["frozenBeats"], 0)

    def test_a_FROZEN_frame_counter_with_a_healthy_dom_is_caught(self):
        """His black window exactly: els high, beat advancing, nothing drawn. Every other signal
        in this beat reads healthy, which is the whole reason this field had to exist."""
        _beat(raf=7331)
        b = _beat(raf=7331)
        self.assertIs(b["painting"], False,
                      "a page that drew no frame between two beats was reported as painting")
        self.assertEqual(b["elsNow"], 11707, "the DOM is intact — that is the point, not a bug")
        self.assertEqual(b["blankStrikes"], 0,
                         "the element-count detector cannot see this failure and must not "
                         "pretend to; if it ever strikes here the two signals have been confused")
        self.assertIn("no frame has been drawn", b["paintWhy"])
        # ⚠ AND IT MUST NOT CLAIM WHICH OF TWO CAUSES IT IS. A backgrounded WebKit window stops
        # running rAF exactly like a wedged one, and this console reports hidden:true even when
        # healthy, so the flag cannot separate them. The first cut asserted "this is the black
        # window" on its very first live reading; a diagnostic that cries wolf teaches him to
        # ignore it. [[unknown-stays-unknown]]
        self.assertIn("TWO THINGS LOOK LIKE THIS", b["paintWhy"],
                      "the diagnostic asserted one cause when it can distinguish neither")

    def test_consecutive_frozen_beats_accumulate_so_a_blip_is_not_a_verdict(self):
        _beat(raf=5)
        for expected in (1, 2, 3):
            b = _beat(raf=5)
            self.assertEqual(b["frozenBeats"], expected)
        b = _beat(raf=6)
        self.assertEqual(b["frozenBeats"], 0, "one painted frame must clear the count")

    def test_a_page_that_does_not_report_raf_is_UNKNOWN_and_never_accused(self):
        """A console left open across the upgrade sends no `raf`. Reporting that as 'not painting'
        would accuse a perfectly healthy window of the very wedge this is meant to find."""
        _beat(raf=None)
        b = _beat(raf=None)
        self.assertIsNone(b["painting"], "an absent counter was turned into a verdict")
        self.assertIn("unknown", b["paintWhy"].lower())

    def test_the_first_beat_alone_cannot_decide(self):
        """One sample has nothing to compare against. A verdict from a single beat would fire on
        every console the moment it opens."""
        b = _beat(raf=1)
        self.assertIsNone(b["painting"], "a verdict was reached from one sample")


class ItReportsAndNeverActs(unittest.TestCase):

    def test_a_frozen_counter_triggers_no_rescue_and_no_strike(self):
        """His standing rule: nothing auto-heals until it has proven itself. A watchdog that
        reloads his console on a signal this new is exactly the wrong first move."""
        before_rescues = int(ca._UI_BEAT.get("rescues") or 0)
        _beat(raf=42)
        for _ in range(10):
            _beat(raf=42)
        self.assertEqual(int(ca._UI_BEAT.get("rescues") or 0), before_rescues,
                         "the paint witness performed a rescue")
        self.assertEqual(ca._UI_BEAT.get("blankStrikes"), 0,
                         "the paint witness incremented the element-count detector's strikes")


if __name__ == "__main__":
    try:                       # cp1255 cannot encode the arrows these tests print
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
