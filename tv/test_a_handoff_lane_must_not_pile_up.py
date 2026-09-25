# -*- coding: utf-8 -*-
"""#199 — a lane nobody drains is a queue of answers nobody reads.

HIS ORDER, 2026-09-23, after #230 reached FORTY-ONE unread: *"make sure they both get done
inbetween and DONT stack up like it just did 41 times"*. The drainers existed; nothing WATCHED
them, so nothing noticed. This is the law for the watcher.

⚠ MEASURED when written: #230's watermark sat 16.1h stale and its 41 unread ticks carried
`freeze=AFTER_REOPEN_PAINT·58756` (#172, still live at v3456), `Fleet PARTIAL` (#157's instance 4)
and ASK digests for #37/#45/#113. Not noise — answers.
"""
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as D          # noqa: E402


def _row():
    return dict(D.CHECKS)["handoff lanes drained"]


def _stamp(hours_ago):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - hours_ago * 3600))


class AHandoffLaneMustNotPileUp(unittest.TestCase):

    def setUp(self):
        self.fn = _row()
        self.assertIsNotNone(self.fn, "the row is not registered, so nothing watches the lanes")
        import handoff as H
        self._real_marks = H._marks
        self._H = H

    def tearDown(self):
        self._H._marks = self._real_marks

    def _drain_stub(self, pending):
        """Make #231 answer `pending` without touching GitHub."""
        import second_eye_drain as SD
        self._real_gh, self._real_seen = SD._handoff._gh, SD.already_recorded
        SD.already_recorded = lambda: set()
        SD._handoff._gh = lambda *_a, **_k: ([{"id": 1, "body":
            "SECOND-EYE\n\nversion: v9999\nsha: abc\nverdict: clean\nmodel: grok-4.7\nchars: 10\n"
            "reach: x\nfindings: none\n"}] if pending else [])
        self.addCleanup(lambda: (setattr(SD._handoff, "_gh", self._real_gh),
                                 setattr(SD, "already_recorded", self._real_seen)))

    def test_a_FRESH_pair_of_lanes_reads_OK(self):
        self._H._marks = lambda: {"230": {"ts": _stamp(0.5)}}
        self._drain_stub(pending=False)
        state, why = self.fn()
        self.assertEqual(state, D.OK,
                         "both lanes were read minutes ago and the row still complained: %s" % why)

    def test_a_STALE_lane_is_named_and_the_row_goes_MISSING(self):
        self._H._marks = lambda: {"230": {"ts": _stamp(40)}}
        self._drain_stub(pending=False)
        state, why = self.fn()
        self.assertEqual(state, D.MISSING,
                         "#230 unread for 40 HOURS and the row said %r: %s" % (state, why))
        self.assertIn("#230", why, "the stale lane was not NAMED, so nobody knows which: %s" % why)

    def test_an_UNDRAINED_second_eye_lane_also_counts(self):
        self._H._marks = lambda: {"230": {"ts": _stamp(0.5)}}
        self._drain_stub(pending=True)
        state, why = self.fn()
        self.assertEqual(state, D.MISSING,
                         "#231 had a look that never reached the ledger and the row was quiet: %s"
                         % why)
        self.assertIn("#231", why)

    def test_a_machine_that_NEVER_drained_is_UNMEASURED_not_billed(self):
        """#141 — the ALT read MISSING for lanes nobody works there. No watermark ever written and
        not one look ever filed: there is no drain on this machine to fall behind."""
        self._H._marks = lambda: {}
        self._drain_stub(pending=True)
        st, why = self.fn()
        self.assertEqual(st, D.UNMEASURED, "a machine that never drained was billed: %s" % why)
        self.assertIn("never drained", why)

    def test_a_machine_that_drained_ONCE_keeps_the_full_bar(self):
        """The discrimination: one filed look means a drainer lives here, so a missing #230
        watermark is a backlog again."""
        import second_eye_drain as SD
        self._H._marks = lambda: {}
        self._drain_stub(pending=False)
        SD.already_recorded = lambda: {"41"}
        st, why = self.fn()
        self.assertEqual(st, D.MISSING, why)
        self.assertIn("NO watermark", why)

    def test_an_UNREADABLE_watermark_is_UNKNOWN_and_never_an_empty_queue(self):
        """[[unknown-stays-unknown]] — a store nobody could read must not look like nothing pending."""
        self._H._marks = lambda: None
        state, why = self.fn()
        self.assertEqual(state, D.UNKNOWN,
                         "an unreadable watermark store was graded as a fact: %r %s" % (state, why))

    def test_the_age_is_right_UNDER_DST_and_not_an_hour_high(self):
        """⚠⚠ v3462 — `mktime(...) + time.timezone` IS AN HOUR WRONG WHILE DST IS IN EFFECT.

        time.timezone is the STANDARD offset; under DST the real one is altzone. MEASURED on a
        real watermark: the old formula said 1.385h where the true age was 0.385h — exactly 1.000h
        high. A lane read 5.1h ago then reports 6.1h and trips the 6h bar, so the row that exists
        to stop cry-wolf cried wolf.
        ⚠ THE ORIGINAL CASES USED 0.5h AND 40h, WHICH CANNOT SEE A ONE-HOUR ERROR. This one sits
        just inside the bar on purpose: at the true age it must be OK, and one hour of drift flips
        it. Found by the cross-family eye on the SHIPPED v3458 bytes.
        """
        # 5.1h ago: comfortably inside the 6h bar, but 6.1h under the old off-by-one-hour formula
        self._H._marks = lambda: {"230": {"ts": _stamp(5.1)}}
        self._drain_stub(pending=False)
        state, why = self.fn()
        self.assertEqual(state, D.OK,
                         "a lane read 5.1h ago was reported over the 6h bar — the age is drifting "
                         "(DST offset): %s" % why)

    def test_an_UNREACHABLE_second_eye_lane_is_UNKNOWN_and_never_OK(self):
        """⚠ v3462 — it used to fall through to OK and print "both handoff lanes read recently"
        about a lane it never reached, while the comment beside it said the opposite.
        [[feedback-comments-vs-code]] [[feedback-silence-is-not-evidence]]"""
        import second_eye_drain as SD
        self._H._marks = lambda: {"230": {"ts": _stamp(0.5)}}
        real_gh, real_seen = SD._handoff._gh, SD.already_recorded
        try:
            SD.already_recorded = lambda: set()
            def _boom(*_a, **_k):
                raise RuntimeError("github unreachable")
            SD._handoff._gh = _boom
            state, why = self.fn()
        finally:
            SD._handoff._gh, SD.already_recorded = real_gh, real_seen
        self.assertEqual(state, D.UNKNOWN,
                         "#231 could not be reached and the row still graded it: %r %s"
                         % (state, why))
        self.assertNotIn("read recently", why,
                         "it claimed both lanes were read while one was never reached: %s" % why)

    def test_the_row_is_NOT_on_the_every_tick_roster(self):
        """It shells out to `gh`. A stall would hold up the doctor tick — which runs at every
        console BOOT and on the ten-minute watchdog — and bills a network round trip to the cheap
        subset #194 is about. The staleness bar is SIX HOURS; hourly loses nothing."""
        self.assertIn("handoff lanes drained", D.PERIODIC,
                      "the lane watcher is back on the every-tick roster, so a GitHub stall can "
                      "hold up his console boot")

    def test_the_row_NEVER_drains_and_never_marks_anything_read(self):
        """A watcher that silenced the backlog would be the truncation regression-guard names."""
        import inspect
        src = inspect.getsource(D._check_the_handoff_lanes_are_being_drained)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        for banned in (".mark(", "drain("):
            self.assertNotIn(banned, code,
                             "the watcher calls %s — it would consume or silence the very backlog "
                             "it exists to report" % banned)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#141 - a machine that never drained either lane is billed MISSING again (the ALT's false bill)",
        "file": "tv/console_doctor.py",
        "find": '    if not (marks.get("230") or {}).get("ts") and _filed == 0:\n',
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#141 - the exemption widens to any machine missing a #230 watermark, hiding a drainer that stopped",
        "file": "tv/console_doctor.py",
        "find": '    if not (marks.get("230") or {}).get("ts") and _filed == 0:\n',
        "replace": '    if not (marks.get("230") or {}).get("ts"):\n',
        "matches": 1,
    },
]
