# -*- coding: utf-8 -*-
"""2026-09-28 — THE FLEET BEACON SAYS HOW EACH PC FILMS D2R, AND HOW ITS RIVER DRAINS.

His order: "yea add those beacon fields". Dean's laptop plays D2R NATIVELY ("usually" how he plays), his
ALT streams through Boosteroid, and every console now decides from its OWN machine whether the triage
lane may run (it stands aside while a local D2R.exe runs and catches up after). From his Mac, /api/fleet
has to be able to say which way each PC films and whether its river is draining — two fields inside the
`system` block every console already sends:

    system.capture = {route: native|boosteroid|geforce-now|unknown, ageS, why, source}
    system.river   = {lanes: {STATION: n} | None, ageS, why,
                      triage: {lastKey, lastWhy, lastTs, backlog, owedSince, skips, ...}}

WHAT THIS LAW DRIVES — every end of the joint, the shipped code with only the edges stubbed:
  · the CAPTURE ROUTE: Windows reads the capture half's own pin (cap_target.json, "<proc> [<route>] - ..."),
    the Mac reads the finder's last pick (_PICK_ROUTE, written by the SHIPPED finder at the pick); a pin's
    age is the pin's; waiting / off / missing / corrupt are UNKNOWN with a why; no window title crosses;
  · the RIVER: cached WHERE /api/river computes it (the handler driven for real), carried with ITS age;
    no cache -> lanes None with a why; a newer failed read keeps the last good lanes and says so;
  · THE BEACON NEVER COMPUTES THE RIVER: every river computation is patched to count its calls — zero, and
    _system_for_wire() returns in < 0.5 s;
  · NOTHING IDENTIFYING CROSSES: a Windows path, a home path, a URL, an IP, this host's name and a reel id
    in the lane's last refusal all arrive as placeholders;
  · THE WORKER keeps them (functions/api/console.js's shaper, run in node), and /api/fleet relays them
    for every peer, online and offline — the beacon's own output, through the shaper, through the route.

⚠ NOTHING REAL IS TOUCHED: TV_HIST and HIST_DIR point at a scratch world, the capture pin is a fixture
file, the river's modules are stubbed, and no console, network or KV is contacted. RED_PROOF below.
[[the-unjoined-end]] [[unknown-stays-unknown]] [[stale-reading]] [[heart-first]]
"""
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_WORLD = tempfile.mkdtemp(prefix="beacon_world_")
os.environ["TV_HIST"] = _WORLD

import control_app as ca  # noqa: E402
import river_lanes as RL  # noqa: E402
import river_stamp as RVS  # noqa: E402
import tv_diablo as TVD  # noqa: E402

NODE = shutil.which("node")
NOW = lambda: int(time.time() * 1000)  # noqa: E731


def _between(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _node(js):
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped code - UNKNOWN, not passing: %s" % r.stderr[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _shape(system):
    """The SHIPPED worker shaper for `system`, run in node."""
    with io.open(os.path.join(ROOT, "functions", "api", "console.js"), encoding="utf-8") as f:
        src = f.read()
    fn = _between(src, "    system: (function (s) {", "    })(body.system),")
    fn = "(" + fn[len("    system: "):-len("(body.system),")] + ")"
    return _node("var shape = %s; console.log(JSON.stringify(shape(%s)));" % (fn, json.dumps(system)))


class _World(unittest.TestCase):
    """A scratch world: the fixture shelf, the fixture store, a fresh lane, no cached river."""

    SAVED = ("HIST_DIR", "IS_WIN", "_CAP_TARGET_FILE", "_CAPTURE_ROUTE_SEEN", "_RIVER_LAST",
             "_TRIAGE_LANE", "_TRIAGE_STORE_SEED", "_EAGLE")

    def setUp(self):
        self.world = tempfile.mkdtemp(prefix="beacon_case_")
        self.addCleanup(shutil.rmtree, self.world, True)
        self._env = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = self.world
        self._saved = {k: getattr(ca, k) for k in self.SAVED}
        self._pick = {k: getattr(TVD, k) for k in ("_PICK_ROUTE", "_PICK_WHY", "_PICK_UNKNOWN")}
        self.addCleanup(self._restore)
        ca.HIST_DIR = self.world
        ca.IS_WIN = False
        ca._CAP_TARGET_FILE = os.path.join(self.world, "cap_target.json")
        ca._CAPTURE_ROUTE_SEEN = {"route": None, "ts": None}
        ca._RIVER_LAST = {"good": None, "fail": None}
        ca._TRIAGE_LANE = dict(self._saved["_TRIAGE_LANE"], skips={}, ticks=0, lastKey=None,
                               lastWhy=None, lastTs=None, backlog=None, owedSince=None,
                               caughtUpTs=None, upSince=NOW())
        ca._TRIAGE_STORE_SEED = {"read": False, "ts": None, "why": ""}
        ca._EAGLE = {"rows": []}
        TVD._PICK_ROUTE, TVD._PICK_WHY, TVD._PICK_UNKNOWN = None, "", False

    def _restore(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)
        for k, v in self._pick.items():
            setattr(TVD, k, v)
        if self._env is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._env

    def pin(self, doc):
        with io.open(ca._CAP_TARGET_FILE, "w", encoding="utf-8") as fh:
            if isinstance(doc, str):
                fh.write(doc)
            else:
                json.dump(doc, fh)


class TheCaptureRouteOnWindows(_World):
    """Windows: the capture half's OWN pin, as capture_win.ps1 writes it."""

    def setUp(self):
        super(TheCaptureRouteOnWindows, self).setUp()
        ca.IS_WIN = True

    def test_each_route_the_capture_half_names_crosses_as_its_route(self):
        for label, want in (("D2R.exe [local] - Diablo II: Resurrected via PrintWindow", "native"),
                            ("Boosteroid [boosteroid] - Boosteroid via PrintWindow", "boosteroid"),
                            ("chrome [geforce-now] - Diablo II on GeForce NOW via BitBlt", "geforce-now"),
                            ("D2R alive - full virtual fallback", "native")):
            self.pin({"mode": "window", "label": label, "ts": NOW() - 30000, "d2rProcess": False})
            got = ca._capture_route_for_wire()
            self.assertEqual(got["route"], want, "%r read as %r" % (label, got))
            self.assertEqual(got["source"], "capture-half")
            self.assertGreaterEqual(got["ageS"], 29.0, "the age is not the PIN's own age: %r" % got)
            self.assertLess(got["ageS"], 120.0)

    def test_a_window_title_never_crosses(self):
        self.pin({"mode": "window", "ts": NOW(),
                  "label": "chrome [boosteroid] - Boosteroid - my private tab title via BitBlt"})
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "boosteroid")
        self.assertNotIn("private", json.dumps(got), "a window title rode the wire")

    def test_a_pin_whose_route_is_not_named_is_unknown_not_guessed(self):
        self.pin({"mode": "window", "label": "D2R foreground - primary monitor", "ts": NOW()})
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown", "a foreground pin (maybe a cloud window) was guessed")
        self.assertIn("without naming its route", got["why"])

    def test_waiting_after_a_pin_keeps_the_last_pin_with_its_age(self):
        self.pin({"mode": "window", "label": "Boosteroid [boosteroid] - Boosteroid via PrintWindow",
                  "ts": NOW() - 600000})
        self.assertEqual(ca._capture_route_for_wire()["route"], "boosteroid")
        self.pin({"mode": "waiting", "label": "eye held - no game window", "ts": NOW()})
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "boosteroid", "the last pin was forgotten between sessions")
        self.assertGreaterEqual(got["ageS"], 599.0, "the remembered pin lost its own age: %r" % got)
        self.assertIn("last pin this console read", got["why"])

    def test_unknown_with_a_why_when_nothing_was_ever_pinned(self):
        got = ca._capture_route_for_wire()
        self.assertEqual((got["route"], got["ageS"]), ("unknown", None))
        self.assertIn("written no target", got["why"])
        self.pin({"mode": "waiting", "label": "D2R.exe not found", "ts": NOW()})
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertIn("not pinned", got["why"])
        self.pin("{not json")
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertIn("could not be read", got["why"])
        self.pin({"mode": "off", "label": "capture is OFF", "ts": NOW()})
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertIn("OFF", got["why"])


class TheCaptureRouteOnTheMac(_World):
    """The Mac: the finder's last pick in THIS process, recorded by the finder when it picked."""

    def _row(self, pid, title, hwnd, w=1920, h=1080):
        return {"kCGWindowOwnerName": title, "kCGWindowOwnerPID": pid, "hwnd": hwnd, "iconic": False,
                "kCGWindowBounds": {"X": 0, "Y": 0, "Width": w, "Height": h}}

    def _pick_window(self, rows, procs):
        class _W(object):
            def rows(self):
                return rows
        return TVD.find_d2r_window_win(win=_W(), procs=procs)

    def test_the_finder_records_the_route_at_the_pick_and_the_wire_reads_it(self):
        self.assertIsNotNone(self._pick_window([self._row(11, "Boosteroid", 501)], {11: "Boosteroid.exe"}),
                             "premise: the shipped judge pins a bare Boosteroid app window")
        self.assertEqual(TVD._PICK_ROUTE["route"], "boosteroid")
        got = ca._capture_route_for_wire()
        self.assertEqual((got["route"], got["source"]), ("boosteroid", "finder"))
        self.assertLess(got["ageS"], 60.0)
        self.assertIsNotNone(self._pick_window([self._row(12, "Diablo II: Resurrected", 502)], {12: "D2R.exe"}))
        self.assertEqual(ca._capture_route_for_wire()["route"], "native",
                         "D2R.exe on this machine is NATIVE play")

    def test_no_look_and_a_blind_look_are_unknown_and_quote_no_title(self):
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertIn("has not looked", got["why"])
        TVD._PICK_UNKNOWN = True
        self.assertIn("could not look", ca._capture_route_for_wire()["why"])
        TVD._PICK_UNKNOWN = False
        TVD._PICK_WHY = "no game window; a cloud window is open: boosteroid Boosteroid 'my private title'"
        got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertNotIn("private", json.dumps(got), "_PICK_WHY quotes titles and rode the wire")

    def test_a_console_that_never_imported_the_finder_says_so(self):
        with mock.patch.dict(sys.modules):
            sys.modules.pop("tv_diablo", None)
            got = ca._capture_route_for_wire()
        self.assertEqual(got["route"], "unknown")
        self.assertIn("has not looked", got["why"])


def _lanes_payload():
    return {"ok": True, "reconciles": True, "shelf": 10, "hidden": [], "closed": 0, "lifetime": 10,
            "closedWhy": "", "unknown": 0,
            "lanes": [{"name": "INTAKE", "why": "w", "stations": ["INTAKE", "TRIAGE"], "count": 7,
                       "byStation": {"INTAKE": 0, "TRIAGE": 7, "STATION": 0, "EMPTY": 0},
                       "reels": [], "closedReels": None},
                      {"name": "PRINTER", "why": "w", "stations": ["PRINTER", "JOIN"], "count": 3,
                       "byStation": {"PRINTER": 3, "JOIN": 0}, "reels": [], "closedReels": None}]}


class TheRiver(_World):
    """The river rides from WHERE it is computed; the beacon never pays for it."""

    def _drive_river(self, census=None):
        h = ca.Handler.__new__(ca.Handler)
        h.path = "/api/river"
        out = []
        h._json = lambda code, obj: out.append((code, obj))
        cen = census or (lambda *a, **k: {"ok": True, "counts": {}, "visits": {}, "reels": 10})
        with mock.patch.object(RVS, "census", cen), \
                mock.patch.object(RVS, "stations", lambda: (("INTAKE", "TRIAGE"), "")), \
                mock.patch.object(RVS, "rows", lambda *a, **k: {"rows": [], "n": 0}), \
                mock.patch.object(RL, "lanes", lambda *a, **k: _lanes_payload()), \
                mock.patch.object(ca, "shelf_hidden_reels", lambda *a, **k: ([], "")), \
                mock.patch.object(ca, "river_mouth", lambda *a, **k: {}), \
                mock.patch.object(ca, "reel_census", lambda *a, **k: {}), \
                mock.patch.object(ca, "_river_labels", lambda: {}), \
                mock.patch.object(ca, "_river_vocab_facts", lambda: {}):
            h.do_GET()
        self.assertEqual(len(out), 1, "premise: the river route answered once")
        return out[0][1]

    def test_no_cached_river_is_lanes_none_with_a_why(self):
        got = ca._river_for_wire()
        self.assertIsNone(got["lanes"], "an uncomputed river reached the wire as a river")
        self.assertIsNone(got["ageS"])
        self.assertIn("has not computed its river", got["why"])
        self.assertTrue(got["triage"]["ok"], "the lane's own record does not depend on the river cache")

    def test_the_river_route_leaves_its_lanes_for_the_beacon(self):
        payload = self._drive_river()
        self.assertTrue(payload.get("ok"), "premise: the stubbed river computed: %r" % payload.get("why"))
        got = ca._river_for_wire()
        self.assertEqual(got["lanes"], {"INTAKE": 0, "TRIAGE": 7, "STATION": 0, "EMPTY": 0,
                                        "PRINTER": 3, "JOIN": 0},
                         "the lanes /api/river computed did not reach the beacon")
        self.assertLess(got["ageS"], 5.0)
        self.assertEqual(got["why"], "")

    def test_the_lanes_carry_their_own_age(self):
        self._drive_river()
        g = dict(ca._RIVER_LAST["good"])
        g["ts"] -= 600000
        ca._RIVER_LAST = {"good": g, "fail": None}
        self.assertGreaterEqual(ca._river_for_wire()["ageS"], 599.0,
                                "a ten-minute-old river went out as current")

    def test_a_newer_failed_read_keeps_the_last_good_lanes_and_says_so(self):
        self._drive_river()

        def _boom(*a, **k):
            raise RuntimeError("census exploded")
        payload = self._drive_river(census=_boom)
        self.assertFalse(payload.get("ok"))
        got = ca._river_for_wire()
        self.assertEqual(got["lanes"]["TRIAGE"], 7)
        self.assertIn("a newer river read failed", got["why"])

    def test_the_beacon_never_computes_the_river(self):
        self._drive_river()
        calls = []

        def _counted(name):
            def _f(*a, **k):
                calls.append(name)
                time.sleep(3.0)          # the cost the beacon must never pay
                raise AssertionError("the beacon computed the river (%s)" % name)
            return _f
        with mock.patch.object(RVS, "census", _counted("river_stamp.census")), \
                mock.patch.object(RVS, "run", _counted("river_stamp.run")), \
                mock.patch.object(RL, "lanes", _counted("river_lanes.lanes")), \
                mock.patch.object(ca, "reel_census", _counted("reel_census")), \
                mock.patch.object(ca, "shelf_hidden_reels", _counted("shelf_hidden_reels")), \
                mock.patch.object(ca, "river_mouth", _counted("river_mouth")):
            t0 = time.time()
            sysb = ca._system_for_wire()
            took = time.time() - t0
        self.assertEqual(calls, [], "the beacon called the river computation: %r" % calls)
        self.assertLess(took, 0.5, "the beacon took %.2f s" % took)
        self.assertEqual(sysb["river"]["lanes"]["TRIAGE"], 7)


class NothingIdentifyingCrosses(_World):

    def test_the_lanes_last_refusal_is_scrubbed(self):
        ca._TRIAGE_LANE.update({
            "ticks": 3, "lastKey": "raised", "skips": {"raised": 3, "C:\\evil": 1},
            "lastWhy": ("the tick raised OSError: [Errno 13] C:\\Users\\Dean\\tv\\retro_triage.json and "
                        "/Users/konyo/d2r_bible_tests/tv/x.json via https://bull-4-u.com/api/console "
                        "from 10.0.0.4 on MYHOST-7 for reel_s_1789000000000_1")})
        with mock.patch.object(ca.socket, "gethostname", return_value="MYHOST-7"):
            wire = json.dumps(ca._system_for_wire())
            tri = ca._triage_for_wire()
        for leak in ("Dean", "konyo", "bull-4-u", "10.0.0.4", "MYHOST", "reel_s_", "C:\\\\evil", "https"):
            self.assertNotIn(leak, wire, "%r crossed the wire: %s" % (leak, wire[:400]))
        self.assertIn("<path>", tri["lastWhy"])
        self.assertEqual(tri["lastKey"], "raised")
        self.assertEqual(tri["skips"], {"raised": 3}, "a key outside the lane's vocabulary crossed")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheWorkerKeepsThem(_World):
    """functions/api/console.js stores what the beacon posts through a fixed shaper - the joint that
    dropped `tally`'s fields four times. Run for real in node."""

    def test_the_beacons_own_block_survives_the_shaper(self):
        ca.IS_WIN = True
        self.pin({"mode": "window", "label": "D2R.exe [local] - Diablo II via PrintWindow", "ts": NOW()})
        ca._RIVER_LAST = {"good": {"ts": NOW(), "stations": {"TRIAGE": 2, "PRINTER": 1}}, "fail": None}
        ca._TRIAGE_LANE.update({"ticks": 4, "lastKey": "playing", "backlog": 2, "owedSince": NOW() - 60000,
                                "skips": {"playing": 4}, "lastWhy": "he is playing"})
        sent = json.loads(json.dumps(ca._system_for_wire()))
        kept = _shape(sent)
        self.assertEqual(kept["capture"]["route"], "native")
        self.assertEqual(kept["capture"]["source"], "capture-half")
        self.assertEqual(kept["river"]["lanes"], {"TRIAGE": 2, "PRINTER": 1})
        for k in ("lastKey", "backlog", "owedSince", "skips", "lastWhy", "waitS"):
            self.assertEqual(kept["river"]["triage"][k], sent["river"]["triage"][k],
                             "the worker dropped or changed triage.%s" % k)

    def test_anything_else_is_null_and_absent_stays_absent(self):
        kept = _shape({"tree": "ok", "reels": 1,
                       "capture": {"route": "local", "ageS": -5, "why": "C:\\Users\\Dean\\x", "source": "x"},
                       "river": {"lanes": {"TRIAGE": "7", "bad key": 1, "PRINTER": 3}, "ageS": "9",
                                 "triage": {"lastKey": "C:\\x", "skips": {"ok-key": 2, "Bad": 1},
                                            "backlog": -1, "lastWhy": "see /Users/konyo/tv/a.json"}}})
        self.assertEqual(kept["capture"], {"route": None, "ageS": None, "why": "<path>", "source": None})
        self.assertEqual(kept["river"]["lanes"], {"PRINTER": 3})
        self.assertIsNone(kept["river"]["ageS"])
        self.assertIsNone(kept["river"]["triage"]["lastKey"])
        self.assertEqual(kept["river"]["triage"]["skips"], {"ok-key": 2})
        self.assertIsNone(kept["river"]["triage"]["backlog"])
        self.assertNotIn("konyo", kept["river"]["triage"]["lastWhy"])
        self.assertEqual(_shape({"tree": "ok", "reels": 1}), {"tree": "ok", "reels": 1},
                         "an older console's record changed shape")


class TheFleetRelaysThemForEveryPeer(_World):
    """/api/fleet hands every row's `system` through, online and offline - driven through the route."""

    def _fleet(self, rows_online, rows_offline):
        h = ca.Handler.__new__(ca.Handler)
        h.path = "/api/fleet"
        out = []
        h._json = lambda code, obj: out.append(obj)
        fl = {"ok": True, "online": rows_online, "offline": rows_offline}
        with mock.patch.object(ca, "fleet_presence", lambda force=False: json.loads(json.dumps(fl))), \
                mock.patch.object(ca, "fleet_origin_status", lambda *a, **k: {"ahead": None,
                                                                               "publishedVer": None}), \
                mock.patch.object(ca, "board_tally_load", lambda: None), \
                mock.patch.object(ca, "fleet_presence_last_good", lambda: (None, None)):
            h.do_GET()
        self.assertEqual(len(out), 1)
        return out[0]

    def test_every_peer_keeps_its_capture_and_river(self):
        dean = {"capture": {"route": "native", "ageS": 12.0, "why": "", "source": "capture-half"},
                "river": {"lanes": {"TRIAGE": 3}, "ageS": 40.0, "why": "",
                          "triage": {"ok": True, "lastKey": "playing", "backlog": 3, "skips": {"playing": 9}}}}
        alt = {"capture": {"route": "boosteroid", "ageS": 5.0, "why": "", "source": "capture-half"},
               "river": {"lanes": None, "ageS": None, "why": "not computed", "triage": None}}
        got = self._fleet([{"machine": "PEER-A", "install": "aaaa", "ver": "v1", "system": dean}],
                          [{"machine": "PEER-B", "install": "bbbb", "ver": "v1", "offline": True,
                            "system": alt}])
        rows = {r["machine"]: r for r in (got.get("online") or []) + (got.get("offline") or [])}
        self.assertEqual(set(rows), {"PEER-A", "PEER-B"}, "premise: both peers reached the payload")
        self.assertEqual(rows["PEER-A"]["system"], dean, "an online peer's system block was changed")
        self.assertEqual(rows["PEER-B"]["system"], alt, "an offline peer's system block was changed")


RED_PROOF = [
    {
        "why": "2026-09-28 - /api/river stops leaving its lanes for the beacon: the fleet can never see a river",
        "file": "control_app.py",
        "find": "                _river_remember(_lanes)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the beacon computes the river itself (2-4 s on every heartbeat)",
        "file": "control_app.py",
        "find": "    g, f = _RIVER_LAST.get(\"good\"), _RIVER_LAST.get(\"fail\")\n",
        "replace": "    import river_lanes as _RL0\n    _RL0.lanes(hide=None)\n"
                   "    g, f = _RIVER_LAST.get(\"good\"), _RIVER_LAST.get(\"fail\")\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a cached river goes out wearing the heartbeat's age, not its own",
        "file": "control_app.py",
        "find": "        out[\"ageS\"] = round(max(0.0, (now - int(g[\"ts\"])) / 1000.0), 1)\n",
        "replace": "        out[\"ageS\"] = 0.0\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the capture half's 'local' crosses raw instead of as native play",
        "file": "control_app.py",
        "find": "                route = \"native\" if m.group(1) == \"local\" else m.group(1)\n",
        "replace": "                route = m.group(1)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a capture pin's age is the read, not the pin",
        "file": "control_app.py",
        "find": "                out.update(route=route, ageS=_age(d.get(\"ts\")))\n",
        "replace": "                out.update(route=route, ageS=0.0)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - an unread capture route is guessed as native instead of UNKNOWN",
        "file": "control_app.py",
        "find": "    out = {\"route\": \"unknown\", \"ageS\": None, \"why\": \"\", \"source\": None}\n",
        "replace": "    out = {\"route\": \"native\", \"ageS\": None, \"why\": \"\", \"source\": None}\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the finder picks a window and records no route, so the Mac's wire is always UNKNOWN",
        "file": "tv_diablo.py",
        "find": "    if best:\n        _note_pick_route(_rows, best)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a path in the lane's last refusal crosses to the fleet (a PUBLIC repo's worker)",
        "file": "control_app.py",
        "find": "    txt = _WIRE_PATH_RX.sub(\"<path>\", txt)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the worker's shaper drops the river on arrival (tally's seventh-joint shape)",
        "file": "functions/api/console.js",
        "find": "        out.river = { lanes: lanes, ageS: num(rv.ageS, DAY400), why: txt(rv.why, 200), triage: tri };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the worker's shaper drops the capture route on arrival",
        "file": "functions/api/console.js",
        "find": "      if (s.capture && typeof s.capture === 'object') {\n",
        "replace": "      if (false) {\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
