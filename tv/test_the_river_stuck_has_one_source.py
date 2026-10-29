# -*- coding: utf-8 -*-
"""#86 / Fleet (REG-3051, GrokBot 04:30, #230 6486545342) - "RIVER STUCK" HAS ONE SOURCE, AND ITS AGE NAMES WHAT WAITED.

GrokBot: the Mac's Fleet row said "river stuck" for the Mac and the ALT while /api/river "is OK on both (ALT 727 reels,
0 moved; Mac shelf 40, 239 reels)". Two answers to two questions, neither named. The row reads the beacon's stuck list
(_river_stuck_for_wire: reels held past six hours at a station they should have left, or past the newest 16 and owed a
tombstone); /api/river's `ok` says only that its census could be read, and the route carried no stuck reading at all.
MEASURED on his Mac on 2026-10-29, read only: 25 reels past the newest 16, owed tombstones (ROUTED 11, the oldest about
18 days) - the row was right. Now /api/river serves the SAME reading the beacon last sent, with the time it was computed,
never a second reckoning (a cold one took 10 s on his Mac), and UNKNOWN until the beacon has read it; and the Fleet chip
names how long each station's oldest reel has waited.

Driven: control_app._river_for_wire and _river_stuck_view on a fixture reading (never his river); the route's line read
from control_app.py; _fleetStuckChip and _fleetStuckWhy cut out of control_ui.html and run in node. RED_PROOF below.
"""
import html
import io
import json
import os
import re
import subprocess
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
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import control_app as CA  # noqa: E402
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
APP = os.path.join(HERE, "control_app.py")
CHIP = ("  var _fleetStuckChip = function (m, nowMs) {\n", "    return bits.join('');\n  };\n")
WHY = ("  function _fleetStuckWhy(list, label){\n", "join('  |  ');\n  }\n")
NOW = 1793240000000
ROWS = [{"station": "ROUTED", "n": 11, "oldestS": 1581835, "window": False,
         "why": "older than the newest 16 - the drain owes them a tombstone"},
        {"station": "STATION", "n": 1, "oldestS": 33835, "why": "the reel sweep owes 1 read(s)"}]


def _read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start.strip()[:40], s.count(start)))
    i = s.index(start)
    return s[i:s.index(end, i) + len(end)]


def _tip(rows):
    if NODE is None:
        raise AssertionError("node is not on this machine - this law does not skip")
    s = _read(UI)
    js = """
var window = {};
function escC(x){ return String(x).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
%s
%s
var m = { system: { river: { stuck: %s, heart: { census: 'current' } } } };
console.log(JSON.stringify(_fleetStuckChip(m)));
""" % (_cut(s, WHY), _cut(s, CHIP), json.dumps(rows))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    out = json.loads(r.stdout.strip().splitlines()[-1])
    m = re.search(r'class="fleet-riverstuck" title="river stuck on this PC - ([^"]*)"', out)
    if not m:
        raise AssertionError("premise: the chip painted no river-stuck tip: %r" % out[:300])
    return html.unescape(m.group(1))


class TheRouteServesTheBeaconsReading(unittest.TestCase):

    def setUp(self):
        self.keep = dict(CA._RIVER_STUCK_LAST)
        CA._RIVER_STUCK_LAST.update(ts=None, stuck=None, keep=None)

    def tearDown(self):
        CA._RIVER_STUCK_LAST.clear()
        CA._RIVER_STUCK_LAST.update(self.keep)

    def _beacon(self, rows):
        good = {"stations": {"ROUTED": 11, "STATION": 1}, "ts": NOW - 60000, "n": 3}
        with mock.patch.dict(CA._RIVER_LAST, {"good": good, "fail": None}), \
                mock.patch.object(CA, "_river_stuck_for_wire", lambda now=None: rows), \
                mock.patch.object(CA, "_triage_for_wire", lambda: {"ok": True}):
            return CA._river_for_wire(NOW)

    def test_before_the_beacon_has_read_it_the_route_says_unknown(self):
        v = CA._river_stuck_view(NOW)
        self.assertIsNone(v["rows"], "an unread stuck list was served as a flowing river")
        self.assertIsNone(v["asOf"])
        self.assertIn("UNKNOWN", v["why"])

    def test_the_route_serves_exactly_what_the_beacon_sent_with_its_time(self):
        sent = self._beacon(ROWS)
        v = CA._river_stuck_view(NOW + 5000)
        self.assertEqual(v["rows"], sent["stuck"], "the route and the Fleet row read two different stuck lists")
        self.assertEqual((v["asOf"], v["ageS"]), (NOW, 5.0), "the route's stuck reading does not carry its own time")
        self.assertIsNone(v["why"])
        if "stuckKeep" in sent:
            self.assertEqual(v["keep"], sent["stuckKeep"])

    def test_a_write_between_reads_never_pairs_one_readings_time_with_anothers_rows(self):
        # REG-3120 (the second eye on v3840): the beacon thread writes while a request thread reads. The store below
        # lands a NEW reading the moment anyone asks it a field with .get() - what a write between two reads does.
        class Racing(dict):
            def get(self, k, d=None):
                v = dict.get(self, k, d)
                dict.update(self, ts=NOW, stuck=[{"station": "NEW", "n": 9}], keep=16)
                return v
        old = [{"station": "OLD", "n": 1}]
        with mock.patch.object(CA, "_RIVER_STUCK_LAST", Racing(ts=NOW - 600000, stuck=old, keep=16)):
            got = CA._river_stuck_view(NOW)
        self.assertEqual((got["asOf"], got["rows"]), (NOW - 600000, old),
                         "one reading's time was served with another reading's rows: %r" % (got,))

    def test_an_unreadable_reading_stays_unknown(self):
        self._beacon(None)
        v = CA._river_stuck_view(NOW + 1000)
        self.assertIsNone(v["rows"])
        self.assertEqual(v["asOf"], NOW)
        self.assertIn("could not be read", v["why"])

    def test_the_river_route_carries_the_reading(self):
        src = _read(APP)
        i = src.index('        if path == "/api/river":\n')
        route = src[i:src.index("        if path == ", i + 40)]
        self.assertIn('"stuck": _river_stuck_view(),', route, "/api/river does not serve the Fleet row's stuck reading")


class TheChipNamesWhatWaited(unittest.TestCase):

    def test_each_station_says_how_long_its_oldest_reel_has_waited(self):
        tip = _tip(ROWS)
        self.assertTrue(tip.endswith(" · oldest reel waiting: ROUTED older 18 d, STATION 9 h"), tip)

    def test_a_row_without_its_age_adds_no_clause(self):
        tip = _tip([{"station": "PRINTER", "n": 2, "why": "vault lane: owes 7"}])
        self.assertNotIn("waiting", tip)


RED_PROOF = [
    {"why": "REG-3120 - the route reads the stuck reading field by field, so a write between reads mixes two readings",
     "file": "tv/control_app.py",
     "find": "    snap = dict(_RIVER_STUCK_LAST)\n",
     "replace": "    snap = _RIVER_STUCK_LAST\n",
     "matches": 1},
    {"why": "REG-3051 - the beacon's stuck reading is not kept for the route",
     "file": "tv/control_app.py",
     "find": "        _RIVER_STUCK_LAST.update(ts=now, stuck=out[\"stuck\"], keep=out.get(\"stuckKeep\"))\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3051 - /api/river carries no stuck reading again",
     "file": "tv/control_app.py",
     "find": "                    \"stuck\": _river_stuck_view(),\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3051 - a stuck list never read is served as an empty, flowing one",
     "file": "tv/control_app.py",
     "find": "        return {\"rows\": None, \"asOf\": None, \"ageS\": None, \"keep\": None,\n",
     "replace": "        return {\"rows\": [], \"asOf\": None, \"ageS\": None, \"keep\": None,\n",
     "matches": 1},
    {"why": "REG-3051 - the route's stuck reading drops its own age",
     "file": "tv/control_app.py",
     "find": "            \"ageS\": round(max(0, now - ts) / 1000.0, 1), \"keep\": snap.get(\"keep\"),\n",
     "replace": "            \"ageS\": None, \"keep\": snap.get(\"keep\"),\n",
     "matches": 1},
    {"why": "REG-3051 - the chip names no wait",
     "file": "tv/control_ui.html",
     "find": "      if (_waits.length) tip += ' \u00b7 oldest reel waiting: ' + _waits.join(', ');\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3051 - a wait past the window is not told from one inside it",
     "file": "tv/control_ui.html",
     "find": "          return e.station + (older ? ' older' : '') + ' ' + say;\n",
     "replace": "          return e.station + ' ' + say;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
