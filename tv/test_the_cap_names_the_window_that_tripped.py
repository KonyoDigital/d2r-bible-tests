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

    # ── 7. the CLAUDE join, driven against its own refusal, not assumed from its shape ────────
    def test_atcap_mirrors_the_claude_lanes_own_refusal(self):
        """⚠ THE SECOND EYE CAUGHT THIS GATE OVERCLAIMING. Its `why` said the law "drives
        `_budget_ok` itself across a ten-cell grid" and that BOTH predicates are mirrored — and
        only the Grok half was driven. Claude was assumed to match because the operators looked
        the same. They did not receive the same OPERANDS: the meter counted `now - c <= 3600` over
        a hand-filtered list, while `_sub_budget_check` counts `now - t < 3600` over
        `_sub_budget_calls(st, now)`, which normalises milliseconds to seconds and drops the
        future. A claim in a gate's own prose is still a claim. [[unknown-stays-unknown]]

        This drives the REAL pipeline end to end on a temp ledger: file -> _meter_state -> the
        lane's atCap, against file -> _sub_budget_check.
        """
        import json as _json
        import shutil
        import tempfile
        import time as _time
        import tv_diablo as TV

        now = _time.time()
        cases = [
            # (name, call ages in seconds, hourlyMax, dailyMax, freeze_the_clock)
            ("quiet",                 [5, 10, 20, 30],                        5, 10, False),
            ("hour full",             [5, 10, 20, 30, 40],                    5, 10, False),
            # ⚠⚠ THE BOUNDARY CELL, AND IT ONLY EXISTS WITH THE CLOCK HELD STILL. A call at
            # EXACTLY 3600.0s old is outside `< 3600` and inside `<= 3600` — the one input where
            # the two spellings disagree. The first cut wrote `now - 3600.0` against a moving
            # clock, so by the time either predicate ran the age was already 3600.000004 and BOTH
            # excluded it: the red-proof that deletes the fix came back **BLIND — stayed GREEN
            # through its own defeat**, which is the only reason this is written properly.
            # A fixture that cannot reach the boundary cannot test the boundary.
            # [[feedback-blind-fixture-green-gate]] [[sabotage-is-usually-the-wrong-one]]
            ("hour boundary at 3600", [3600.0, 5, 10, 20, 30],                5, 10, True),
            ("day full",              [4000, 4100, 4200, 4300, 4400,
                                       4500, 4600, 4700, 4800, 4900],         5, 10, False),
            ("circuit hourly 0",      [5],                                    0, 10, False),
            ("circuit daily 0",       [5],                                    5, 0, False),
        ]
        sand = tempfile.mkdtemp(prefix="capjoin-")
        self.addCleanup(shutil.rmtree, sand, True)
        p0, h0, d0 = TV._SUB_BUDGET_PATH, TV._SUB_HOURLY_MAX, TV._SUB_DAILY_MAX
        armed0 = TV._vision_budget_armed
        disagreed = []
        try:
            TV._vision_budget_armed = lambda: True
            real_time = _time.time
            for name, ages, hm, dm, freeze in cases:
                path = os.path.join(sand, "ledger_%s.json" % abs(hash(name)))
                with io.open(path, "w", encoding="utf-8") as fh:
                    fh.write(_json.dumps({"calls": [now - a for a in ages]}))
                TV._SUB_BUDGET_PATH, TV._SUB_HOURLY_MAX, TV._SUB_DAILY_MAX = path, hm, dm
                try:
                    # ⚠ both sides call the SAME stdlib `time.time`, so holding it still is what
                    # makes "exactly 3600.0 old" a state either predicate can actually be in.
                    if freeze:
                        _time.time = (lambda _t=now: _t)
                    lane_refuses = TV._sub_budget_check() is not None
                    lane = ((CA._meter_state() or {}).get("lanes") or {}).get("claude") or {}
                finally:
                    _time.time = real_time
                meter_says = lane.get("atCap")
                if bool(meter_says) != bool(lane_refuses):
                    disagreed.append((name, lane_refuses, meter_says,
                                      lane.get("hour"), lane.get("day")))
                if freeze:
                    # the cell is only evidence if it really sat ON the boundary
                    print("   boundary cell: refuses=%r meterAtCap=%r hour=%r (hourlyMax %d)"
                          % (lane_refuses, meter_says, lane.get("hour"), hm))
                    self.assertEqual(lane.get("hour"), hm - 1,
                                     "the boundary fixture did not land where it claims: hour=%r "
                                     "with hourlyMax=%d — the 3600.0s call must be EXCLUDED, "
                                     "leaving exactly one slot free" % (lane.get("hour"), hm))
        finally:
            TV._SUB_BUDGET_PATH, TV._SUB_HOURLY_MAX, TV._SUB_DAILY_MAX = p0, h0, d0
            TV._vision_budget_armed = armed0
        print("   claude join: %d of %d case(s) agree between _sub_budget_check and the meter"
              % (len(cases) - len(disagreed), len(cases)))
        self.assertEqual(
            disagreed, [],
            "%d case(s) where the Claude meter and the Claude refusal disagree "
            "(case, laneRefuses, meterAtCap, hour, day): %s" % (len(disagreed), disagreed))

    # ── 8. lanes are published on EVERY path, including a machine that has never read ──────────
    def test_the_lanes_are_published_even_with_no_claude_ledger(self):
        """⚠⚠ THE SECOND EYE'S HIGH FINDING ON v3098, REPRODUCED BEFORE IT WAS FIXED:

            known : False
            why   : no vision read has been recorded on this machine yet
            lanes : NONE PUBLISHED
            watchdog: unknown — "the meter returned no lanes at all"

        The early return is CLAUDE's ledger path. Grok records into a different file entirely, so
        on a machine where Claude has never read — Grok as primary, Grok as shadow, a fresh
        checkout, CI — the Grok lane could be refusing every read and the meter said nothing. The
        dual meter sat one door behind the other lane's ledger. [[the-unjoined-end]]

        ⚠ AND THIS IS ALSO WHY THE OLD TEST 7 WAS WRONG: it asked the LIVE meter for lanes, so it
        only passed on a machine that had already run Claude vision. `.subscription_budget.json`
        is gitignored — on CI that assertion was a machine check wearing a law's clothes.
        """
        import tv_diablo as TV
        p0 = TV._SUB_BUDGET_PATH
        try:
            TV._SUB_BUDGET_PATH = os.path.join(HERE, "no-such-ledger-%d.json" % os.getpid())
            st = CA._meter_state() or {}
            lanes = st.get("lanes") or {}
            print("   with NO claude ledger -> known=%r lanes=%s"
                  % (st.get("known"), sorted(lanes)))
            self.assertFalse(st.get("known"), "the fixture did not actually remove the ledger")
            self.assertIn("grok", lanes,
                          "the GROK lane is invisible when CLAUDE has never read — it records "
                          "into a different file and can be refusing every read")
            self.assertIn("claude", lanes)
        finally:
            TV._SUB_BUDGET_PATH = p0

    # ── 9. every lane shape carries the cap keys, including the honest-absent one ──────────────
    def test_every_lane_shape_carries_the_cap_keys(self):
        """UNKNOWN IS A VALUE, NOT A MISSING FIELD. The grok except-path published a lane with no
        `capWindow`/`capText`, so a reader had to know which of two shapes it held — and the law
        that pins the contract went red on a perfectly honest state."""
        import g5_grok_eyes as G5b
        need = ("atCap", "capWindow", "capText", "on", "label")
        # the live shape
        live = (CA._meter_state() or {}).get("lanes") or {}
        # and the honest-absent shape, forced
        counts0 = G5b._budget_counts
        try:
            def _boom():
                raise RuntimeError("forced")
            G5b._budget_counts = _boom
            absent = (CA._meter_state() or {}).get("lanes") or {}
        finally:
            G5b._budget_counts = counts0
        bad = []
        for label, lanes in (("live", live), ("grok-unreadable", absent)):
            for n, v in sorted(lanes.items()):
                if not isinstance(v, dict):
                    continue
                for k in need:
                    if k not in v:
                        bad.append("%s/%s missing %s" % (label, n, k))
        print("   lane shapes checked: live=%s · forced-absent=%s · missing keys=%d"
              % (sorted(live), sorted(absent), len(bad)))
        self.assertEqual(bad, [], "lane shapes are not uniform: %s" % bad)
        self.assertIsNone((absent.get("grok") or {}).get("atCap"),
                          "a lane that could not be read must be UNKNOWN, never a comfortable "
                          "False")


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
        "why": "the lanes stop being published when CLAUDE has no ledger, so the GROK lane — which "
               "records into a different file entirely — goes invisible on exactly the machines "
               "where it is the lane doing the reading",
        "file": "control_app.py",
        "find": '            out["why"] = "no vision read has been recorded on this machine yet"\n'
                '            out["lanes"] = _meter_lanes(out)\n'
                '            return out',
        "replace": '            out["why"] = "no vision read has been recorded on this machine yet"\n'
                   '            return out',
        "matches": 1,
    },
    {
        "why": "the Claude meter goes back to counting with its own operands instead of the "
               "refusal's, so a call at exactly 3600.0s old makes the meter say AT ITS CEILING "
               "while every read is still allowed",
        "file": "control_app.py",
        "find": "        out[\"hour\"] = sum(1 for t in calls if now - t < 3600)",
        "replace": "        out[\"hour\"] = sum(1 for t in calls if now - t <= 3600)",
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
