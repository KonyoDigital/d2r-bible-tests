# -*- coding: utf-8 -*-
"""REG-1302 — A LAST-SEEN IS AGED AT THE MOMENT ITS ROSTER WAS LISTED, NOT AT THE MOMENT WE LOOK.

The doctor row "a present machine has a fresh last-seen" (v3390, #135) asks whether a machine the
roster lists ONLINE carries a last-seen older than the presence window it must have beaconed in.
Both sides come from ONE cached roster - and it aged them against time.time(). So it measured the
CACHE: MEASURED 2026-09-25 on his console, "GrokBot (57m); Konyo ALT TEST (58m); Konyo (59m)" while
a fresh /api/fleet showed the same three rows 133-226 s old. His roster had not been re-fetched for
~55 minutes, and the row told him three present machines were away. No law drove this row at all.

  · DRIVEN (the shipped check, a cached roster fetched 57 min ago): rows that were 2 min old when
    listed read OK, and the sentence says how old the roster is.
  · DRIVEN: a row that was genuinely stale INSIDE its snapshot still reads MISSING and is named.
  · DRIVEN: no server `now` -> the local fetch time is the clock; no clock at all -> UNKNOWN.
  · DRIVEN: nothing online -> UNMEASURED (an offline row may be old).
RED_PROOF below.
"""
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import control_app as CA  # noqa: E402
import console_doctor as CD  # noqa: E402


def _iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + ".000Z"


class ALastSeenIsAgedAtItsOwnSnapshot(unittest.TestCase):

    def _run(self, d, fetched_at):
        keep = dict(CA._FLEET_PRESENCE_CACHE)
        CA._FLEET_PRESENCE_CACHE["d"] = d
        CA._FLEET_PRESENCE_CACHE["t"] = fetched_at
        try:
            return CD._check_a_present_machine_has_a_fresh_last_seen()
        finally:
            CA._FLEET_PRESENCE_CACHE.clear()
            CA._FLEET_PRESENCE_CACHE.update(keep)

    def test_an_old_roster_of_fresh_rows_is_not_a_stale_fleet(self):
        """His console on 2026-09-25: the roster fetched ~57 min ago, every row minutes old in it."""
        t0 = time.time() - 57 * 60
        d = {"now": _iso(t0), "online": [
            {"nickname": "Konyo", "t": _iso(t0 - 133)},
            {"nickname": "Konyo ALT TEST", "t": _iso(t0 - 190)},
            {"nickname": "GrokBot", "t": _iso(t0 - 226)}], "offline": []}
        st, why = self._run(d, t0)
        self.assertEqual(st, CD.OK, "present machines were reported away because the CACHE is old: %s" % why)
        self.assertIn("this roster is 57m old", why)

    def test_a_row_stale_inside_its_own_snapshot_is_still_missing(self):
        t0 = time.time() - 5 * 60
        d = {"now": _iso(t0), "online": [
            {"nickname": "Konyo", "t": _iso(t0 - 60)},
            {"nickname": "Dean", "t": _iso(t0 - 50 * 60)}], "offline": []}
        st, why = self._run(d, t0)
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("Dean (50m)", why)
        self.assertNotIn("Konyo (", why, "a fresh row was named stale")

    def test_no_server_clock_falls_back_to_the_fetch_time(self):
        t0 = time.time() - 57 * 60
        d = {"online": [{"nickname": "Konyo", "t": _iso(t0 - 120)}], "offline": []}
        st, why = self._run(d, t0)
        self.assertEqual(st, CD.OK, why)
        self.assertIn("the time this console fetched the roster", why)

    def test_no_clock_at_all_is_unknown_not_stale(self):
        d = {"online": [{"nickname": "Konyo", "t": _iso(time.time() - 120)}], "offline": []}
        st, why = self._run(d, 0.0)
        self.assertEqual(st, CD.UNKNOWN, "a roster with no clock was aged anyway: %s" % why)

    def test_nothing_online_is_unmeasured(self):
        st, _ = self._run({"now": _iso(time.time()), "online": [],
                           "offline": [{"nickname": "Dean", "t": _iso(time.time() - 86400)}]},
                          time.time())
        self.assertEqual(st, CD.UNMEASURED)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1302 - the row ages a cached roster against the check's own clock again: an old "
               "cache tells him present machines are away",
        "file": "tv/console_doctor.py",
        "find": "            age = snap_now - _cal.timegm(time.strptime(str(t)[:19], \"%Y-%m-%dT%H:%M:%S\"))\n",
        "replace": "            age = time.time() - _cal.timegm(time.strptime(str(t)[:19], \"%Y-%m-%dT%H:%M:%S\"))\n",
        "matches": 1,
    },
    {
        "why": "REG-1302 - a roster with no clock is guessed instead of reported UNKNOWN",
        "file": "tv/console_doctor.py",
        "find": "    if snap_now is None:\n        return UNKNOWN, (\"the cached roster carries no clock",
        "replace": "    if snap_now is None:\n        snap_now = time.time()\n    if False:\n        return UNKNOWN, (\"the cached roster carries no clock",
        "matches": 1,
    },
]
