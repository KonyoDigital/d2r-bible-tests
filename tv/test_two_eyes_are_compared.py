# -*- coding: utf-8 -*-
"""#188 — the G5 eye runs PRIMARY on a two-family comparison, and the row that reads it must say
what it read, on what, and how old it is.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED. v3450 built tv/g5_shadow_reducer.py and its
`divergence_row()` — "one row a console doctor can render" — and nothing outside its own tests ever
called it. The 6,082-row shadow log was written and read by no surface while
tv/g5_grok_eyes.state said {"on": true, "mode": "primary"}. MEASURED 2026-09-24 when this gate was
written: the newest row where both eyes answered is 2026-09-14 18:05:20 — ten days old — and the
two denominators disagree: 1,078/1,596 READS (67.5%) against 66/165 distinct FRAMES (40.0%).
[[the-unjoined-end]] [[plumbing-with-no-tap]]

These cases DRIVE the doctor row with a stubbed reducer; they never read the live store (it is
gitignored and per-machine). RED_PROOF below.
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

import console_doctor as cd            # noqa: E402
import g5_shadow_reducer as R          # noqa: E402

NAME = "two eyes compared"


def _ts(days_ago):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days_ago * 86400))


def _measured(mode, reads, frames, days_ago):
    return {"id": "g5-shadow-divergence", "state": "measured", "mode": mode,
            "label": "G5 two-eye divergence", "detail": "stub",
            "report": {"fields": {"names": {
                "disagree": {"n": reads[0], "d": reads[1], "last_ts": _ts(days_ago)},
                "frames_disagree": {"n": frames[0], "d": frames[1], "last_ts": _ts(days_ago)}}}},
            "store": {"exists": True}}


class TheRowReadsTheComparison(unittest.TestCase):

    def _drive(self, row):
        calls = []
        real = R.divergence_row
        try:
            R.divergence_row = lambda *a, **k: calls.append(1) or row
            st, say = dict(cd.CHECKS)[NAME]()
        finally:
            R.divergence_row = real
        self.assertEqual(len(calls), 1, "the row never asked the reducer — the tap is not joined")
        return st, say

    def test_no_store_is_UNKNOWN_never_agreement(self):
        st, say = self._drive({"state": "unread", "mode": "primary", "detail": "no shadow store"})
        self.assertEqual(st, cd.UNKNOWN, "a machine with no comparison read %r: %s" % (st, say))

    def test_no_row_both_eyes_answered_is_UNKNOWN(self):
        st, say = self._drive({"state": "no-evidence", "mode": "primary", "detail": "0 both"})
        self.assertEqual(st, cd.UNKNOWN, "silence read as %r: %s" % (st, say))

    def test_PRIMARY_on_a_stale_comparison_is_MISSING(self):
        st, say = self._drive(_measured("primary", (10, 100), (4, 40), days_ago=10))
        self.assertEqual(st, cd.MISSING, "PRIMARY on a ten-day-old comparison read %r: %s" % (st, say))
        self.assertIn("PRIMARY", say)

    def test_one_denominator_alone_does_not_decide(self):
        """His live shape: a majority by READS, a minority by FRAMES. The contradiction is published,
        never averaged, and neither side alone turns the row red."""
        st, say = self._drive(_measured("primary", (1078, 1596), (66, 165), days_ago=0.5))
        self.assertEqual(st, cd.OK, "one denominator alone decided the row (%r): %s" % (st, say))
        self.assertIn("1078/1596", say, "the READ figure did not travel in the sentence: %s" % say)
        self.assertIn("66/165", say, "the FRAME figure did not travel in the sentence: %s" % say)

    def test_a_majority_by_BOTH_denominators_is_MISSING(self):
        st, say = self._drive(_measured("primary", (80, 100), (30, 40), days_ago=0.5))
        self.assertEqual(st, cd.MISSING, "the eyes disagree on most of everything and it read %r: %s"
                         % (st, say))

    def test_a_lane_that_is_not_primary_is_not_billed_for_staleness(self):
        st, say = self._drive(_measured("shadow", (10, 100), (4, 40), days_ago=10))
        self.assertEqual(st, cd.OK, "a SHADOW lane read %r for being stale: %s" % (st, say))

    def test_an_unreadable_time_is_UNKNOWN(self):
        row = _measured("primary", (10, 100), (4, 40), days_ago=1)
        row["report"]["fields"]["names"]["disagree"]["last_ts"] = "yesterday-ish"
        st, say = self._drive(row)
        self.assertEqual(st, cd.UNKNOWN, "an age nobody could read became %r: %s" % (st, say))

    def test_it_is_registered_where_the_console_reads_it(self):
        self.assertIn(NAME, dict(cd.CHECKS), "not on the roster")
        self.assertIn(NAME, cd.WATCHES, "not declared in WATCHES (the v3458 omission)")
        self.assertIn(NAME, cd.MINE, "not in MINE — a red here would bill him for work that is mine")
        self.assertIn(NAME, cd.PERIODIC, "on the every-tick subset; its age is measured in days")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the staleness arm removed: PRIMARY on a comparison nobody has taken for days reads OK",
        "file": "console_doctor.py",
        "find": "        if age > _EYES_STALE_DAYS:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "one denominator deciding alone: 67.5% of READS turns the row red while 40% of FRAMES "
               "says otherwise — the contradiction averaged away",
        "file": "console_doctor.py",
        "find": "        if _maj(reads) and _maj(frames):\n",
        "replace": "        if _maj(reads):\n",
        "matches": 1,
    },
    {
        "why": "no comparison read as a clean bill — silence as agreement",
        "file": "console_doctor.py",
        "find": "    if st != \"measured\":\n        return UNKNOWN, (\"%s - nothing has compared the two eyes",
        "replace": "    if st != \"measured\":\n        return OK, (\"%s - nothing has compared the two eyes",
        "matches": 1,
    },
    {
        "why": "out of MINE: a red row about my own investigation bills him on WAITING ON YOU",
        "file": "console_doctor.py",
        "find": "    \"two eyes compared\":\n        \"#188",
        "replace": "    \"two eyes compared (retired)\":\n        \"#188",
        "matches": 1,
    },
]
