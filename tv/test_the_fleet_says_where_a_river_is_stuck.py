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

    def _stuck(self, rows, shelf=None, fixtures=()):
        """every reel in `rows` is on the shelf unless `shelf` names which are (REG-1614)"""
        import control_app as ca
        on = set(r["reel"] for r in rows) if shelf is None else shelf
        return ca._river_stuck_for_wire(now_ms=NOW, _rows=rows, _shelf=on, _fixtures=fixtures)

    def test_a_reel_gone_from_the_shelf_or_pinned_by_the_suite_is_never_stuck(self):
        """REG-1614 - his Mac on 2026-09-30: 27 'stuck', of which 16 were closed out by retention, 1 reaped by the disk
        floor and 4 were suite fixtures. A reel that has left the shelf cannot be stuck on it, and a fixture never
        moves by design - neither is an alarm. PREMISE: the same rows with every reel on the shelf DO alarm."""
        rows = [_stamp("reel_s_1_on", "EMPTY", 40 * H, 1), _stamp("reel_s_2_gone", "JOIN", 30 * H, 2),
                _stamp("reel_s_3_pin", "TRIAGE", 20 * H, 3), _stamp("reel_s_4_on", "PRINTER", 10 * H, 4)]
        every = {e["station"] for e in self._stuck(rows)}
        self.assertEqual(every, {"EMPTY", "JOIN", "TRIAGE", "PRINTER"}, "PREMISE: the rows do not alarm at all")
        got = {e["station"]: e["n"] for e in self._stuck(rows, shelf={"reel_s_1_on", "reel_s_3_pin", "reel_s_4_on"},
                                                          fixtures=("reel_s_3_pin",))}
        self.assertEqual(got, {"EMPTY": 1, "PRINTER": 1}, "a reel off the shelf or a suite fixture was called stuck")

    def test_the_real_shelf_is_asked_and_an_unreadable_one_is_unknown(self):
        """the default path asks the console's own shelf folder, one reel at a time; no shelf folder at all is None
        (UNKNOWN), never an empty list that reads as a river draining"""
        import shutil
        import tempfile
        from unittest import mock
        import control_app as ca
        d = tempfile.mkdtemp(prefix="stuck_shelf_")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "reel_s_1_on"))
        rows = [_stamp("reel_s_1_on", "EMPTY", 40 * H, 1), _stamp("reel_s_2_gone", "EMPTY", 30 * H, 2)]
        with mock.patch.object(ca, "HIST_DIR", d):
            got = ca._river_stuck_for_wire(now_ms=NOW, _rows=rows, _fixtures=())
        self.assertEqual([(e["station"], e["n"]) for e in got], [("EMPTY", 1)], got)
        with mock.patch.object(ca, "HIST_DIR", os.path.join(d, "no_such_shelf")):
            self.assertIsNone(ca._river_stuck_for_wire(now_ms=NOW, _rows=rows, _fixtures=()),
                              "a shelf that is not there read as a river draining")

    def test_a_route_this_pc_never_proved_names_what_its_prover_waits_for(self):
        """REG-1614 - the ALT on 2026-09-30: its row said 'Run python3 tv/heart2.py --prove', the one thing a prove beside
        his game must never be (REG-1502). With the route locked and this PC's census not current, the reason is its own
        prover's word; with the census current, a locked route still says the lane's own reason."""
        from unittest import mock
        import control_app as ca
        locked = {"why": "reel.route is LOCKED — the heart has never run here, so nothing has shown that the gates "
                         "watching this surface can still go red. Run `python3 tv/heart2.py --prove`. UNKNOWN fails CLOSED."}
        playing = "he is playing on this PC (the game or its cloud client) - a proof never starts beside it"
        with mock.patch.object(ca, "_ROUTE_LANE", locked), \
                mock.patch.object(ca, "_SELF_PROVE", {"census": "absent", "key": "playing", "say": playing}):
            w = ca._river_stuck_why("EMPTY")
        self.assertIn("proves its own gates", w)
        self.assertIn(playing, w)
        self.assertNotIn("heart2.py --prove", w, "the ALT is told to run a prove beside his game")
        merit = {"why": "reel.route is LOCKED — 3 of 7 refusals seen; the bar is 0.510"}
        with mock.patch.object(ca, "_ROUTE_LANE", merit), \
                mock.patch.object(ca, "_SELF_PROVE", {"census": "current", "key": "current", "say": "current"}):
            self.assertEqual(ca._river_stuck_why("EMPTY"), "route lane: " + merit["why"])

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

    def test_a_river_nobody_ever_stamped_is_unknown_while_reels_wait(self):
        """REG-1738 (#86 gap item 8) - no stamp log at all answered [] ("draining") whatever sat on the shelf."""
        import control_app as ca
        from unittest import mock
        import river_stamp as rvs
        never = {"ok": True, "rows": [], "everStamped": False, "why": "no stamp has ever been recorded"}
        with mock.patch.object(rvs, "rows", lambda path=None: never):
            self.assertIsNone(ca._river_stuck_for_wire(now_ms=NOW, _shelf={"reel_s_1_a"}, _fixtures=()),
                              "a shelf of reels with no stamp ever written read as FLOWING")
            self.assertEqual(ca._river_stuck_for_wire(now_ms=NOW, _shelf=set(), _fixtures=()), [],
                             "an empty shelf with no stamps is measured-and-empty")
            self.assertEqual(ca._river_stuck_for_wire(now_ms=NOW, _shelf={"reel_s_9_pin"},
                                                      _fixtures=("reel_s_9_pin",)), [],
                             "a suite fixture alone made the river UNKNOWN")


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
    {"why": "REG-1738 - a river nobody ever stamped reads as draining again",
     "file": "control_app.py",
     "find": "            _never = rep.get(\"everStamped\") is False\n",
     "replace": "            _never = False\n",
     "matches": 1},
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
    {
        "why": "REG-1614 - reels that left the shelf are counted again: his Mac's 17 deleted reels read as stuck",
        "file": "tv/control_app.py",
        "find": "        if reel in _pinned or not _on(reel):\n            continue\n",
        "replace": "        if reel in _pinned:\n            continue\n",
        "matches": 1,
    },
    {
        "why": "REG-1614 - the suite's fixture reels are counted again: reels that never move by design read as stuck",
        "file": "tv/control_app.py",
        "find": "        if reel in _pinned or not _on(reel):\n            continue\n",
        "replace": "        if not _on(reel):\n            continue\n",
        "matches": 1,
    },
    {
        "why": "REG-1614 - a shelf that is not there reads as a river draining (an empty list, not UNKNOWN)",
        "file": "tv/control_app.py",
        "find": "        if not os.path.isdir(HIST_DIR):\n            return None\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "REG-1614 - the ALT's locked route tells him to run a prove beside his game again",
        "file": "tv/control_app.py",
        "find": "            if w.startswith(\"reel.route is LOCKED\") and _sp.get(\"census\") not in (None, \"current\"):\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
