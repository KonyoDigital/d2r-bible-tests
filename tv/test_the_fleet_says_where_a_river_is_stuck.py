# -*- coding: utf-8 -*-
"""#74 — THE FLEET SAYS WHERE A PC'S RIVER IS STUCK, AND WHY (REG-1461).

His ask 2026-09-29, after the ALT was found with 76 reels at EMPTY and 25 at PRINTER for two days and nothing
on any screen said so: *"we need to be able to see that deans console is also architectured correctly ...
see whats getting updated/fetched and logged and registered live while hes on playing"* - step 1, the alarm.

Three joints, each driven, never grepped:
  · the console: `_river_stuck_for_wire` over stamp rows - a station whose oldest reel waited > 6 h is named
    with the owning lane's reason; CAPTURE never alarms (it waits on a capture change by design); an
    unreadable log is None, never "flowing".
  · the worker (functions/api/console.js, the REAL shaper in node): stuck/heart cross shaped - bad keys
    dropped, text scrubbed of paths; null stays null; absent stays absent.
  · the card (control_ui.html, the REAL _fleetSysParts / _fleetStuckChip in node): a red "river stuck" on the
    row, the stations with their age in the detail, "none" when it drains, UNKNOWN when it cannot say.
RED_PROOF below.
"""
import io
import json
import os
import sys
import unittest

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
import test_the_fleet_card_says_how_each_pc_films_and_drains as F  # noqa: E402  (its node harness)
import test_each_console_says_its_own_system as S  # noqa: E402  (its worker slicer)

H = 3600
NOW = F.NOW


def _stamp(reel, station, ago_s, seq):
    return {"at": NOW - int(ago_s * 1000), "seq": seq, "reel": reel, "station": station,
            "by": "law", "byKind": "observer"}


class TheConsoleNamesItsStuckStations(unittest.TestCase):

    def _stuck(self, rows):
        import control_app as ca
        return ca._river_stuck_for_wire(now_ms=NOW, _rows=rows)

    def test_the_alts_shape_is_named_with_ages(self):
        rows = [_stamp("reel_s_1_a", "TRIAGE", 50 * H, 1), _stamp("reel_s_1_a", "EMPTY", 40 * H, 2),
                _stamp("reel_s_2_b", "EMPTY", 20 * H, 3), _stamp("reel_s_3_c", "PRINTER", 38 * H, 4),
                _stamp("reel_s_4_d", "PRINTER", 1 * H, 5),          # fresh - not stuck
                _stamp("reel_s_5_e", "CAPTURE", 90 * H, 6),         # by design - never an alarm
                _stamp("reel_s_6_f", "ROUTED", 90 * H, 7)]          # the far end
        got = {e["station"]: e for e in self._stuck(rows)}
        self.assertEqual(sorted(got), ["EMPTY", "PRINTER"], got)
        self.assertEqual(got["EMPTY"]["n"], 2)
        self.assertEqual(got["EMPTY"]["oldestS"], 40 * H)
        self.assertEqual(got["PRINTER"]["n"], 1, "a reel at PRINTER for an hour was called stuck")
        for e in got.values():
            self.assertTrue(e["why"], "a stuck station was named without its lane's reason")

    def test_a_flowing_river_is_an_empty_list_and_an_unreadable_log_is_none(self):
        self.assertEqual(self._stuck([_stamp("reel_s_1_a", "EMPTY", 60, 1)]), [])
        import control_app as ca
        from unittest import mock
        import river_stamp as rvs
        with mock.patch.object(rvs, "rows", lambda path=None: {"ok": False, "rows": [], "why": "law"}):
            self.assertIsNone(ca._river_stuck_for_wire(now_ms=NOW), "an unreadable log read as FLOWING")


class TheWorkerCarriesIt(unittest.TestCase):

    def _shape(self, river):
        return S.TheRelayShapesIt._shape(self, {"tree": "ok", "reels": 3, "river": river})

    def test_stuck_and_heart_cross_shaped(self):
        got = self._shape({"lanes": {"PRINTER": 25}, "stuck": [
            {"station": "PRINTER", "n": 25, "oldestS": 38 * H, "why": r"vault lane: owes 0 C:\Users\Dean Smith\tv\x.json"},
            {"station": "bad station", "n": 1, "oldestS": 1, "why": "x"}],
            "heart": {"census": "missing", "key": "busy", "blind": 0}})
        rv = got["river"]
        self.assertEqual([e["station"] for e in rv["stuck"]], ["PRINTER"], "a bad station key crossed")
        self.assertNotIn("Dean", rv["stuck"][0]["why"], "a user path crossed the PUBLIC wire")
        self.assertEqual(rv["heart"], {"census": "missing", "key": "busy", "blind": 0})

    def test_null_stays_null_and_absent_stays_absent(self):
        self.assertIsNone(self._shape({"lanes": {}, "stuck": None})["river"]["stuck"])
        self.assertNotIn("stuck", self._shape({"lanes": {}})["river"], "an older console gained a field")


class TheCardSaysIt(unittest.TestCase):

    def _run(self, river):
        row = F._row(t_ago_s=60, river=dict({"lanes": {"PRINTER": 25}, "ageS": 30.0, "why": "", "triage": F.TRI_OK},
                                             **river))
        return F._run("var p = _fleetSysParts(%s, NOW); OUT.p = {}; p.forEach(function(x){ OUT.p[x.k] = "
                      "{ t: plain(x.t), unk: !!x.unk, warn: !!x.warn, why: x.why }; });"
                      "OUT.chip = strip(_fleetStuckChip(%s)); OUT.chipHtml = _fleetStuckChip(%s);"
                      % (json.dumps(row), json.dumps(row), json.dumps(row)))

    def test_a_stuck_pc_says_so_on_the_row_and_in_the_detail(self):
        out = self._run({"stuck": [{"station": "PRINTER", "n": 25, "oldestS": 38 * H,
                                    "why": "vault lane: owes 0"}], "heart": {"census": "missing", "blind": None}})
        st = out["p"]["stuck"]
        self.assertTrue(st["warn"], "a stuck river was not drawn as a warning")
        self.assertIn("PRINTER 25 for", st["t"])
        self.assertIn("vault lane: owes 0", st["why"])
        self.assertIn("river stuck", out["chip"], "the row does not say the river is stuck")
        self.assertIn("vault lane: owes 0", out["chipHtml"], "the row's hover does not carry the reason")
        self.assertIn("never proved on this PC", out["p"]["proved"]["t"])
        self.assertTrue(out["p"]["proved"]["warn"])

    def test_a_draining_pc_is_calm_and_an_unknown_one_says_unknown(self):
        out = self._run({"stuck": [], "heart": {"census": "current", "blind": 0}})
        self.assertIn("none", out["p"]["stuck"]["t"])
        self.assertFalse(out["p"]["stuck"]["warn"])
        self.assertEqual(out["chip"], "", "a draining PC grew an alarm")
        self.assertFalse(out["p"]["proved"]["warn"])
        out = self._run({"stuck": None})
        self.assertTrue(out["p"]["stuck"]["unk"], "an unreadable log read as draining")
        self.assertEqual(out["chip"], "")


RED_PROOF = [
    {
        "why": "2026-09-29 - the fleet row stops saying a PC's river is stuck (REG-1461)",
        "file": "tv/control_ui.html",
        "find": "    if (!sk || !sk.length) return '';\n",
        "replace": "    return '';\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - CAPTURE (stuck by design) and fresh reels read as an alarm",
        "file": "tv/control_app.py",
        "find": "        if age < RIVER_STUCK_AFTER_S:\n            continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the worker drops the stuck list, so no other PC ever sees it",
        "file": "functions/api/console.js",
        "find": "        if (Array.isArray(rv.stuck)) {\n",
        "replace": "        if (false) {\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
