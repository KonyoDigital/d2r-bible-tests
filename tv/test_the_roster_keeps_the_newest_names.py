# -*- coding: utf-8 -*-
"""#200 (the v3802 look) - THE ROSTER KEEPS THE NEWEST NAMES, SAYS HOW MANY THERE WERE, AND READS ONLY WHEN IT CAN POST.

Measured in code at v3812:
  - _list_names stopped at 400 in store order. A found log is {name: date} in the order he found them, newest last, so a
    list of 461 published his OLDEST 400 and silently dropped the 61 newest finds.
  - _roster_publish_once ran every read (a whole board read over 5,000 rows) on every 60 s tick, before due() said
    "within the hour".

Driven on roster_publish and the real _roster_publish_once (reads and network stubbed):
  - 461 names -> the newest 400, and counts["uniquesNamed"] == 461 rides beside the tally;
  - reads_due: a boot reads; inside the hour or a fresh refusal does not; past the hour it does;
  - a tick inside the hour calls the reads 0 times.
RED_PROOF below.
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import roster_publish as RP  # noqa: E402

NOW = 1792800000000
FOUND = {"Unique %03d" % i: "2026-10-%02d" % (1 + i % 27) for i in range(461)}


class TheRosterKeepsTheNewestNames(unittest.TestCase):

    def test_the_newest_400_are_kept_and_the_whole_count_rides(self):
        names = RP._list_names(FOUND)
        self.assertEqual(len(names), 400)
        self.assertEqual(names[0], "Unique 061", "the oldest names were kept and the newest dropped (#200)")
        self.assertEqual(names[-1], "Unique 460")
        tally = {"uniques": {"have": 461, "total": 403}, "at": NOW}
        sec = RP.chronicle_read(tally, NOW, {"uniques": FOUND})
        self.assertEqual(sec["counts"].get("uniquesNamed"), 461, "how many names there were did not ride: %r" % sec["counts"])
        self.assertEqual(len([r for r in sec["rows"] if r["lane"] == "uniques"]), 400)
        none = RP.chronicle_read(tally, NOW, None)
        self.assertNotIn("uniquesNamed", none["counts"], "an unread list was given a count")

    def test_reads_wait_for_a_post_that_could_go(self):
        hour = RP.HOUR_MS
        self.assertTrue(RP.reads_due({"at": NOW - 60000}, NOW, True)[0], "a boot did not read")
        self.assertFalse(RP.reads_due({"at": NOW - 60000}, NOW, False)[0], "a tick inside the hour read the board")
        self.assertFalse(RP.reads_due({"refuseAt": NOW - 60000}, NOW, False)[0])
        self.assertTrue(RP.reads_due({"at": NOW - hour - 1}, NOW, False)[0])
        self.assertTrue(RP.reads_due({}, NOW, False)[0])

    def test_a_tick_inside_the_hour_reads_nothing(self):
        import control_app as ca
        reads = []
        state = {"at": int(__import__("time").time() * 1000) - 600000, "hash": "x"}
        saved = []
        with mock.patch.object(ca, "_beacon_suppressed_by", lambda: None), \
                mock.patch.object(ca, "_roster_claimed_name", lambda: "Dean"), \
                mock.patch.object(ca, "_roster_platform", lambda: "windows"), \
                mock.patch.object(ca, "_roster_state_load", lambda: dict(state)), \
                mock.patch.object(ca, "_roster_state_save", lambda s: saved.append(dict(s))), \
                mock.patch.object(ca, "_roster_reads", lambda now: reads.append(now) or {}), \
                mock.patch.object(ca, "_roster_post", lambda *a: self.fail("posted inside the hour")):
            self.assertIsNotNone(RP.owner_of("Dean", "windows"), "PREMISE: Dean on windows is not a roster label")
            ca._roster_publish_once(False)
        self.assertEqual(reads, [], "the board was read on a tick that could not post (#200)")
        self.assertEqual(saved[-1].get("why"), "within the hour")


RED_PROOF = [
    {"why": "#200 - the cap keeps the oldest 400 names again and drops his newest finds",
     "file": "tv/roster_publish.py",
     "find": "    return names[-limit:] if limit and len(names) > limit else names\n",
     "replace": "    return names[:limit] if limit else names\n",
     "matches": 1},
    {"why": "#200 - how many names there were stops riding beside the tally",
     "file": "tv/roster_publish.py",
     "find": "                counts[lane + \"Named\"] = n\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "#200 - the lane reads the whole board on every tick again",
     "file": "tv/control_app.py",
     "find": "    _open, _shut_why = _rp.reads_due(state, now_ms, True if boot else False)\n",
     "replace": "    _open, _shut_why = True, \"\"\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
