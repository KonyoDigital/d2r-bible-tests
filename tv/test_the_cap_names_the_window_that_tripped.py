# -*- coding: utf-8 -*-
"""A CAPPED READ LANE MUST SAY WHICH WINDOW IS FULL, AND `atCap` MUST MIRROR THE LANE'S OWN REFUSAL.

⚠⚠ FOUND BY THE SECOND EYE, ON THE SHIPPED v3092 DIFF, AND BOTH HALVES REPRODUCED BEFORE A LINE
WAS CHANGED. The meter grew a second lane so that "off" and "at its ceiling" could never be drawn
alike — that was the whole point of it, after the Grok lane sat at 201 of a 200 daily cap refusing
every read while the console showed nothing. The lane it added then carried the same class of
defect twice:

    tv_diablo._sub_budget_check   refuses on  ANY max <= 0  ·  hour >= hourly  ·  day >= daily
    g5_grok_eyes._budget_ok       refuses on  ANY max <= 0  ·  hour >= hourly  ·  day >= daily
    the meter said, for claude    armed and dailyMax and day >= dailyMax
    the meter said, for grok      (hm > 0 and h >= hm) or (dm > 0 and d >= dm)

1. **An HOURLY exhaustion read as healthy on the Claude lane** — `_SUB_HOURLY_MAX` is 4000 and
   `_sub_budget_check` refuses the moment the hour reaches it, and the meter only ever looked at
   the day.
2. **A ceiling of 0 read as healthy on BOTH lanes** — which is the state where every read is
   refused outright, and is therefore the single most important one to show.
3. **And when it DID fire, the sentence named the wrong window** — the WARN always formatted the
   daily fraction, so an hour at its ceiling printed `grok (4000 of 20000 today) is AT ITS
   CEILING`. A correct number under a word that had stopped being true, on the one line whose
   entire job is to say there is no headroom. [[label-outlived-referent]]

⚠ WHY THE JOIN IS TESTED AND NOT THE COPY. Test 1 does not re-implement the rule — it drives
`g5_grok_eyes._budget_ok` itself across a grid and demands `_cap_state` agree on every cell. If
either side's rule moves, this fails, which is the only arrangement that survives someone editing
one of them. [[the-unjoined-end]] [[plumbing-with-no-tap]]

⚠ `enforced=False` IS NOT "NO CAP REACHED". The Claude lane disarms under TV_STUB and against a
fake binary, and an unarmed lane genuinely refuses nothing — reporting it as capped would be the
mirror-image lie.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable   # noqa: E402

_console_safe_enable()

import control_app as CA            # noqa: E402
import g5_grok_eyes as G5           # noqa: E402
import health_engine as HE          # noqa: E402


class TestTheCapNamesTheWindowThatTripped(unittest.TestCase):

    # ── 1. the JOIN: the meter must agree with the lane's own refusal, cell by cell ────────────
    def test_atcap_mirrors_the_grok_lanes_own_refusal(self):
        grid = [
            # hour, day, hourlyMax, dailyMax
            (0, 0, 30, 200), (29, 199, 30, 200), (30, 199, 30, 200), (29, 200, 30, 200),
            (30, 200, 30, 200), (0, 201, 30, 200), (5, 5, 0, 200), (5, 5, 30, 0),
            (0, 0, 0, 0), (1, 1, 1, 1),
        ]
        h0, d0 = G5._HOURLY_MAX, G5._DAILY_MAX
        counts0 = G5._budget_counts
        disagreed = []
        try:
            for hour, day, hm, dm in grid:
                G5._HOURLY_MAX, G5._DAILY_MAX = hm, dm
                G5._budget_counts = (lambda h=hour, d=day: (h, d))
                lane_refuses = not G5._budget_ok()
                meter_says, window, text = CA._cap_state(hour, day, hm, dm)
                if bool(meter_says) != bool(lane_refuses):
                    disagreed.append((hour, day, hm, dm, lane_refuses, meter_says))
        finally:
            G5._HOURLY_MAX, G5._DAILY_MAX = h0, d0
            G5._budget_counts = counts0
        # ⚠ PRINT THE MATCH COUNT — a green sabotage is meaningless without it.
        print("   join: %d of %d cell(s) agree between _budget_ok and _cap_state"
              % (len(grid) - len(disagreed), len(grid)))
        self.assertEqual(
            disagreed, [],
            "%d cell(s) where the meter and the lane disagree about whether a read is refused "
            "(hour, day, hourlyMax, dailyMax, laneRefuses, meterSaysAtCap): %s. A meter that "
            "disagrees with the thing it measures is worse than no meter." % (len(disagreed), disagreed))

    # ── 2. the hourly window is honoured at all ───────────────────────────────────────────────
    def test_an_exhausted_hour_is_a_capped_lane(self):
        at, win, txt = CA._cap_state(4000, 10, 4000, 20000)
        self.assertTrue(at, "an hour at 4000 of 4000 is a lane refusing every read; the meter "
                            "said %r" % (at,))
        self.assertEqual(win, "hour", "window was %r" % (win,))

    # ── 3. and it is DESCRIBED as the hour, never as a daily fraction ─────────────────────────
    def test_an_hourly_cap_is_not_reported_as_a_daily_one(self):
        _at, _win, txt = CA._cap_state(4000, 10, 4000, 20000)
        print("   hourly capText: %r" % txt)
        self.assertIn("this hour", txt,
                      "the sentence does not name the hour: %r" % txt)
        self.assertNotIn("today", txt,
                         "an HOURLY cap described with the word 'today': %r — this is the exact "
                         "'4000 of 20000 today' line that reads as headroom" % txt)
        self.assertIn("4000", txt, "the hour's own numbers are missing: %r" % txt)
        self.assertNotIn("20000", txt,
                         "the DAILY ceiling appears in an HOURLY refusal: %r" % txt)
        # the daily direction must still work, and must not borrow the hour's words
        _at2, win2, txt2 = CA._cap_state(3, 20000, 4000, 20000)
        self.assertEqual(win2, "day", "window was %r" % (win2,))
        self.assertIn("today", txt2)
        self.assertNotIn("this hour", txt2)

    # ── 4. a ceiling of zero is a REFUSING lane, not a resting one ────────────────────────────
    def test_a_zero_ceiling_is_a_refusing_lane(self):
        for hm, dm in ((0, 200), (30, 0), (0, 0)):
            at, win, txt = CA._cap_state(0, 0, hm, dm)
            self.assertTrue(at, "hourlyMax=%r dailyMax=%r refuses every read (_budget_ok returns "
                                "False outright) and the meter said atCap=%r" % (hm, dm, at))
            self.assertEqual(win, "circuit", "window was %r" % (win,))
            self.assertIn("refuses every read", txt)

    # ── 5. unarmed is the mirror image, and must not read as capped ───────────────────────────
    def test_an_unenforced_lane_is_never_capped(self):
        at, win, txt = CA._cap_state(99999, 99999, 1, 1, enforced=False)
        self.assertFalse(at, "an unarmed Claude lane refuses nothing; reporting it capped is the "
                             "mirror-image lie")
        self.assertIsNone(win)
        self.assertEqual(txt, "")

    # ── 6. the watchdog line actually PUBLISHES the window ────────────────────────────────────
    def test_the_watchdog_warn_names_the_window(self):
        real = CA._meter_state
        CA._meter_state = lambda: {"lanes": {"grok": {
            "label": "Grok", "on": True, "atCap": True, "hour": 4000, "day": 10,
            "hourlyMax": 4000, "dailyMax": 20000, "capWindow": "hour",
            "capText": "4000 of 4000 this hour"}}}
        try:
            row = HE.check_read_lanes_at_cap()
        finally:
            CA._meter_state = real
        line = str((row or {}).get("line") or "")
        print("   watchdog line: %r" % line[:150])
        self.assertIn("4000 of 4000 this hour", line,
                      "the WARN does not carry the window that tripped: %r" % line)
        self.assertNotIn("20000", line,
                         "the WARN prints the DAILY ceiling for an HOURLY refusal: %r" % line)

    # ── 7. and both lanes really carry it, on the live meter ──────────────────────────────────
    def test_both_lanes_publish_a_cap_window(self):
        lanes = (CA._meter_state() or {}).get("lanes") or {}
        self.assertTrue(lanes, "the meter published no lanes at all")
        missing = sorted(n for n, v in lanes.items()
                         if isinstance(v, dict) and "capText" not in v)
        print("   lanes: %s · without capText: %s" % (sorted(lanes), missing or "none"))
        self.assertEqual(missing, [],
                         "%d lane(s) do not publish capText, so the watchdog has nothing to name "
                         "the window with: %s" % (len(missing), missing))


RED_PROOF = [
    {
        "why": "the hourly window stops being checked, so a Claude lane at 4000 of 4000 — "
               "refusing every read — reports healthy, which is the defect the second eye found",
        "file": "control_app.py",
        "find": "    if h_full:\n        return True, \"hour\", \"%d of %d this hour\" % (hour, hm)",
        "replace": "    if False:\n        return True, \"hour\", \"%d of %d this hour\" % (hour, hm)",
        "matches": 1,
    },
    {
        "why": "a ceiling of 0 stops being a refusal, so both lanes report headroom in the one "
               "state where every single read is rejected outright",
        "file": "control_app.py",
        "find": "    if hm <= 0 or dm <= 0:\n        return True, \"circuit\",",
        "replace": "    if False:\n        return True, \"circuit\",",
        "matches": 1,
    },
    {
        "why": "the watchdog goes back to formatting the daily fraction, so an exhausted hour "
               "prints '4000 of 20000 today' and reads as headroom",
        "file": "health_engine.py",
        "find": '            capped.append("%s (%s)" % (name, v.get("capText")\n'
                '                                       or "at its ceiling, window UNKNOWN"))',
        "replace": '            capped.append("%s (%s of %s today)" % (name, v.get("day"), v.get("dailyMax")))',
        "matches": 1,
    },
    {
        "why": "an unarmed lane starts reporting as capped — the mirror-image lie, which would "
               "make every TV_STUB run scream that the vision lane is exhausted",
        "file": "control_app.py",
        "find": "    if not enforced:\n        return False, None, \"\"",
        "replace": "    if False:\n        return False, None, \"\"",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
