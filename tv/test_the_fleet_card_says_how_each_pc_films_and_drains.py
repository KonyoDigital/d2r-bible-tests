# -*- coding: utf-8 -*-
"""2026-09-28 — THE FLEET CARD SAYS HOW EACH PC FILMS AND DRAINS, AND THE RIVER SAYS WHAT ITS TRIAGE LANE IS DOING.

His order: "make sure its all properly rendering everywhere". The beacon fields shipped on the wire the same day
(tv/test_the_beacon_says_how_each_pc_films_and_drains.py drives them to /api/fleet):

    system.capture = {route: native|boosteroid|geforce-now|unknown, ageS, why, source}
    system.river   = {lanes: {STATION: n} | None, ageS, why, triage: {lastKey, lastWhy, backlog, sinceLastS, ...}}
    formerMachines = [{machine, lastSeen, ver}]       (one install that reported under two host names)

and /api/river carries `triage` (triage_lane_state()). The fleet card in tv/control_ui.html drew NONE of the first
three and the river panel drew nothing of the fourth: the wire carried it and no reader spent it — the seventh-joint
shape the worker's shaper already names. [[the-unjoined-end]]

WHAT THIS LAW DRIVES — the SHIPPED helpers cut from control_ui.html between real anchors and RUN in node over fixture
rows (never re-typed here), and the SHIPPED card rendered in a real headless Chrome from a stubbed /api/fleet:
  · A ROUTE IS NAMED WITH THE AGE OF ITS PIN: native / Boosteroid / GeForce NOW, aged ageS + (now - the row's record
    time `t`) — the pin's age when the beacon left, plus how long the site has held that beacon. An offline machine's
    route keeps ageing; a row with no `t` reads "age UNKNOWN", never "just now". [[stale-reading]]
  · UNKNOWN IS NEVER 0: an unnamed route, no lane map, an unreadable triage lane and a console older than the fields
    each read UNKNOWN in words; a null backlog is "owed UNKNOWN", never "0 owed"; a null lane map never "TRIAGE 0".
  · THE RIVER'S STATIONS in the order that console counted them, zero stations left out, with the river's age.
  · THE TRIAGE LANE IN WORDS: walking / caught up / "standing aside for his game" / "last refusal: <words>", with
    the backlog and the last walk's age.
  · A RENAMED HOST is a quiet "formerly <name>" line under the row that absorbed it.
  · THE RIVER PANEL'S ONE LINE: the backlog, the last walk's age, the last refusal in words, "standing aside for his
    game" when that is the state, UNKNOWN when absent — and _shLanesRender draws it on every path, lanes or none.
  · THE JOIN, in Chrome: _fleetRefresh over a stubbed /api/fleet draws every row's films / river / triage line and
    the "formerly" line, and nothing in the card scrolls sideways at 901 and 1280 wide.

⚠ NOTHING REAL IS TOUCHED: fixture rows only, a file:// page with fetch stubbed at document start, its own headless
Chrome on its own port (render_check's handle, killed by it). No console, no store, no network. RED_PROOF below.
[[unknown-stays-unknown]] [[heart-first]] [[visual-regression-detector]]
"""
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


# ⚠ BEFORE the import: render_check reads its port once. Never 9222/9223 (his).
_LAW_PORT = os.environ.get("TV_LAW_PORT", "").strip()
os.environ["TV_RENDER_PORT"] = _LAW_PORT if _LAW_PORT.isdigit() and _LAW_PORT not in ("9222", "9223") else str(_free_port())
import render_check as RC  # noqa: E402

UI_PATH = os.path.join(HERE, "control_ui.html")
UI = io.open(UI_PATH, encoding="utf-8").read()

#: the fleet helpers (second script block): _fleetSince .. _fleetSysHtml, bounded by the next section's own heading
FLEET_START = "  var _fleetSince = function (iso) {"
FLEET_END = "  /* ── v2851 — A TRANSIENT FAILURE MUST NOT BECOME A PERMANENT CARD"
#: the river panel (first script block): the triage vocabulary, its line and the whole lane renderer
RIVER_START = "  var _TRIAGE_WORDS = {"
RIVER_END = "  window._shLanesRender = _shLanesRender;"

NOW = 1790000000000          # a fixed "now" (ms) so every age below is exact
NBSP = u" "


def _iso(ms):
    import datetime
    return datetime.datetime.utcfromtimestamp(ms / 1000.0).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _node():
    for c in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=10)
            return c
        except Exception:
            continue
    return None


NODE = _node()


def _cut(start, end, inclusive_end=False):
    """The SHIPPED text between two anchors that each occur ONCE. -> str

    ⚠ both ends anchored, counted first: a fixed window reads its own reach, and an anchor that matches twice grades the
    wrong block. [[source-reading-guard]]"""
    assert UI.count(start) == 1, "anchor %r occurs %d times in control_ui.html" % (start, UI.count(start))
    assert UI.count(end) == 1, "anchor %r occurs %d times in control_ui.html" % (end, UI.count(end))
    i = UI.find(start)
    j = UI.find(end, i)
    assert j > i, "the anchors are out of order"
    return UI[i:(j + len(end)) if inclusive_end else j]


HARNESS = r"""
var window = {}; var ELS = {};
var document = { getElementById: function(id){ return ELS[id] || null; } };
var localStorage = { getItem: function(){ return null; }, setItem: function(){} };
function esc(s){ return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }
var escC = esc;
"""


def _run(body):
    """Run `body` against the shipped helpers in node. -> the OUT object it filled"""
    prog = (HARNESS + _cut(RIVER_START, RIVER_END, inclusive_end=True) + "\n" + _cut(FLEET_START, FLEET_END) + "\n"
            + "var NOW = %d; function iso(ms){ return new Date(ms).toISOString(); }\n" % NOW
            + "function plain(s){ return String(s).replace(/\\u00a0/g, ' '); }\n"
            + "function strip(h){ return plain(String(h).replace(/<[^>]+>/g, '')); }\n"
            + ";(function(){ var OUT = {};\n" + body + "\nprocess.stdout.write(JSON.stringify(OUT)); })();\n")
    fh = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    fh.write(prog)
    fh.close()
    try:
        r = subprocess.run([NODE, fh.name], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped helpers would not run: %s" % (r.stderr or r.stdout)[-1500:])
        return json.loads(r.stdout)
    finally:
        try:
            os.unlink(fh.name)
        except Exception:
            pass


def _parts(row):
    """_fleetSysParts over one fixture row at NOW -> {films|river|triage: {t, unk, stand, why}}"""
    out = _run("var p = _fleetSysParts(%s, NOW); OUT.p = {}; p.forEach(function(x){ OUT.p[x.k] = { t: plain(x.t), unk: !!x.unk, stand: !!x.stand, why: x.why }; });"
               % json.dumps(row))
    return out["p"]


def _row(t_ago_s=None, **system):
    r = {"nickname": "Box", "machine": "box-1", "ver": "v3522"}
    if t_ago_s is not None:
        r["t"] = _iso(NOW - t_ago_s * 1000)
    r["system"] = dict({"tree": "ok", "reels": 4}, **system)
    return r


TRI_OK = {"ok": True, "lastKey": "surveyed", "lastWhy": "walked one reel", "lastTs": NOW - 90000, "sinceLastS": 60.0,
          "backlog": 2, "owedSince": None, "owedForS": None, "waitS": 60.0, "ticks": 9, "skips": {}}


def _tri(**kw):
    d = dict(TRI_OK)
    d.update(kw)
    return d


@unittest.skipIf(NODE is None, "node is not on this machine - this law RUNS the shipped helpers and will not re-implement them")
class TheFleetRowSaysHowItFilmsAndDrains(unittest.TestCase):

    def test_a_route_is_named_with_the_age_of_its_pin_not_of_the_fetch(self):
        """ageS 30 when the beacon left + 1770 s the site has held it = 30 min — never "30s ago" (the pin's age at send)"""
        p = _parts(_row(1770, capture={"route": "native", "ageS": 30.0, "why": "", "source": "finder"}))
        self.assertEqual(p["films"]["t"], "native · 30m ago", p["films"])
        self.assertFalse(p["films"]["unk"])
        for route, word in (("boosteroid", "Boosteroid"), ("geforce-now", "GeForce NOW")):
            q = _parts(_row(0, capture={"route": route, "ageS": 12.0, "why": "", "source": "capture-half"}))
            self.assertEqual(q["films"]["t"], word + " · 12s ago", q["films"])

    def test_an_unnamed_route_is_unknown_with_the_machines_own_reason(self):
        why = "the window finder could not look (no desktop was visible to it)"
        p = _parts(_row(5, capture={"route": "unknown", "ageS": None, "why": why, "source": "finder"}))
        self.assertEqual((p["films"]["t"], p["films"]["unk"]), ("UNKNOWN", True), p["films"])
        self.assertEqual(p["films"]["why"], why)

    def test_a_row_with_no_record_time_has_an_unknown_age_never_just_now(self):
        p = _parts(_row(None, capture={"route": "native", "ageS": 20.0, "why": "", "source": "finder"},
                        river={"lanes": {"TRIAGE": 1}, "ageS": 5.0, "why": "", "triage": _tri()}))
        self.assertEqual(p["films"]["t"], "native · age UNKNOWN", p["films"])
        self.assertTrue(p["river"]["t"].endswith("age UNKNOWN"), p["river"])
        self.assertIn("(age UNKNOWN)", p["triage"]["t"])
        self.assertIn("last walk age UNKNOWN", p["triage"]["t"])

    def test_the_river_names_its_stations_in_that_consoles_order_with_the_rivers_age(self):
        p = _parts(_row(60, river={"lanes": {"INTAKE": 0, "TRIAGE": 7, "PRINTER": 1, "JOIN": 0, "TOMBSTONE": 2},
                                   "ageS": 300.0, "why": "", "triage": _tri()}))
        self.assertEqual(p["river"]["t"], "TRIAGE 7 · PRINTER 1 · TOMBSTONE 2 · 6m ago", p["river"])
        z = _parts(_row(0, river={"lanes": {"TRIAGE": 0, "PRINTER": 0}, "ageS": 1.0, "why": "", "triage": _tri()}))
        self.assertTrue(z["river"]["t"].startswith("empty — 0 reels at every station"), z["river"])

    def test_no_lane_map_is_unknown_never_a_river_of_zeroes(self):
        why = "this console has not computed its river since it started"
        p = _parts(_row(5, river={"lanes": None, "ageS": None, "why": why, "triage": _tri()}))
        self.assertEqual((p["river"]["t"], p["river"]["unk"], p["river"]["why"]), ("UNKNOWN", True, why), p["river"])
        self.assertNotIn("0", p["river"]["t"])

    def test_the_triage_lane_is_said_in_words(self):
        cases = (("surveyed", "walking ("), ("done", "caught up ("), ("playing", "standing aside for his game ("),
                 ("cpu-shadow", "last refusal: a shadow reel is rolling and the CPU is busy ("),
                 ("capture-mini", "last refusal: standing aside for a live capture ("),
                 ("a-key-with-no-words", "last refusal: a-key-with-no-words ("), (None, "no tick yet ("))
        for key, want in cases:
            p = _parts(_row(120, river={"lanes": {"TRIAGE": 3}, "ageS": 1.0, "why": "", "triage": _tri(lastKey=key)}))
            self.assertTrue(p["triage"]["t"].startswith(want), "%s: %r" % (key, p["triage"]))
            self.assertEqual(p["triage"]["stand"], key == "playing", "%s: only 'playing' is drawn standing aside" % key)
            self.assertIn("2m ago)", p["triage"]["t"], "%s: the state's age is the beacon's record age" % key)

    def test_the_backlog_and_the_last_walk_carry_their_ages_and_unknown_is_never_zero(self):
        p = _parts(_row(3600, river={"lanes": {"TRIAGE": 7}, "ageS": 1.0, "why": "",
                                     "triage": _tri(backlog=7, sinceLastS=3600.0)}))
        self.assertIn("7 owed", p["triage"]["t"])
        self.assertIn("last walk 2h ago", p["triage"]["t"], "3600 s at the beacon + 3600 s held = 2 h: %r" % p["triage"])
        q = _parts(_row(10, river={"lanes": {"TRIAGE": 7}, "ageS": 1.0, "why": "",
                                   "triage": _tri(backlog=None, sinceLastS=None)}))
        self.assertIn("owed UNKNOWN", q["triage"]["t"])
        self.assertNotIn("0 owed", q["triage"]["t"])
        self.assertIn("no walk on record", q["triage"]["t"])
        r = _parts(_row(10, river={"lanes": None, "ageS": None, "why": "x",
                                   "triage": {"ok": False, "why": "the triage lane could not be read (KeyError)"}}))
        self.assertEqual((r["triage"]["t"], r["triage"]["unk"]), ("UNKNOWN", True), r["triage"])
        self.assertIn("KeyError", r["triage"]["why"])

    def test_a_console_older_than_the_fields_says_so_rather_than_an_empty_machine(self):
        p = _parts(_row(86400))
        for k in ("films", "river", "triage"):
            self.assertEqual((p[k]["t"], p[k]["unk"]), ("UNKNOWN · an older build", True), "%s: %r" % (k, p[k]))

    def test_a_renamed_host_is_a_quiet_formerly_line(self):
        m = _row(30, capture={"route": "native", "ageS": 1.0, "why": "", "source": "finder"})
        m["formerMachines"] = [{"machine": "cursor", "lastSeen": _iso(NOW - 8 * 86400 * 1000), "ver": "v3377"},
                               {"machine": "old-box", "lastSeen": None, "ver": None}]
        out = _run("OUT.h = _fleetSysHtml(%s, NOW); OUT.none = _fleetSysHtml(%s, NOW);"
                   % (json.dumps(m), json.dumps(_row(30))))
        self.assertIn('class="fleet-meta fleet-sys fleet-former"', out["h"])
        # lastSeen is aged by the page's own clock (a wall time, not a reading): the fixture is 8 d before NOW, so only
        # its shape is pinned here
        self.assertRegex(out["h"].replace(NBSP, " "), r"formerly cursor · v3377 · last seen \d+d ago")
        self.assertIn("formerly old-box · version UNKNOWN · last seen UNKNOWN", out["h"])
        self.assertNotIn("fleet-former", out["none"], "a machine with no former name grew a 'formerly' line")

    def test_a_machines_own_words_are_escaped(self):
        m = _row(1, capture={"route": "unknown", "ageS": None, "why": '<img src=x onerror="boom">', "source": "finder"})
        h = _run("OUT.h = _fleetSysHtml(%s, NOW);" % json.dumps(m))["h"]
        self.assertNotIn("<img", h)
        self.assertIn("&lt;img", h)


RIVER_LANES = {"ok": True, "reconciles": True, "shelf": 4, "closed": 3, "lifetime": 7, "lanes": [
    {"name": "INTAKE", "count": 2, "stations": ["INTAKE", "TRIAGE"], "byStation": {"INTAKE": 0, "TRIAGE": 2}, "why": ""},
    {"name": "TOMBSTONE", "count": 2, "stations": ["ROUTED", "TOMBSTONE"], "byStation": {"ROUTED": 2, "TOMBSTONE": 0},
     "closedCount": 3, "closedShown": 0, "closedWhy": "the ledger", "why": ""}]}


def _lane(**kw):
    t = {"ok": True, "on": True, "stoodDown": False, "lastKey": "playing", "lastWhy": "he is playing",
         "lastAt": NOW - 20000, "lastSkipKey": "playing", "lastSkipWhy": "he is playing", "lastSkipTs": NOW - 20000,
         "backlog": 7, "sinceSurveyS": 3600.0, "lastSurveyTs": NOW - 3600000, "storeWhy": "", "ticks": 5, "skips": {}}
    t.update(kw)
    return t


@unittest.skipIf(NODE is None, "node is not on this machine - this law RUNS the shipped helpers and will not re-implement them")
class TheRiverSaysWhatItsTriageLaneIsDoing(unittest.TestCase):

    def _line(self, d):
        return _run("OUT.h = _shTriageLine(%s, NOW); OUT.s = strip(OUT.h);" % json.dumps(d))

    def test_standing_aside_for_his_game_with_the_backlog_and_the_last_walks_age(self):
        d = {"triage": _lane(), "__askedAt": NOW - 1800000}
        out = self._line(d)
        self.assertIn('<b class="shr-tri-stand"', out["h"])
        self.assertIn("standing aside for his game (20s ago)", out["s"])
        self.assertIn("7 owed", out["s"])
        self.assertIn("last walk 2h ago", out["s"], "3600 s when asked + 1800 s on the page = 90 min = 2 h: %r" % out["s"])
        self.assertNotIn("last refusal", out["s"], "the state already says it - the refusal is not said twice")

    def test_the_last_refusal_is_said_in_words_with_its_age(self):
        d = {"triage": _lane(lastKey="cpu-loaded", lastSkipKey="cpu-loaded", lastSkipTs=NOW - 180000,
                             lastSkipWhy="the machine is 97% busy")}
        out = self._line(d)
        self.assertIn("last refusal: the machine is too busy · 3m ago", out["s"])
        self.assertNotIn("standing aside for his game", out["s"])
        w = self._line({"triage": _lane(lastKey="surveyed", lastSkipKey=None, lastSkipTs=None)})
        self.assertIn("walking", w["s"])
        self.assertIn("no refusal since this console started", w["s"])

    def test_absent_or_unreadable_is_unknown_never_a_backlog_of_zero(self):
        self.assertIn("UNKNOWN", self._line(None)["s"])
        a = self._line({"lanes": RIVER_LANES})
        self.assertIn("UNKNOWN — this console does not publish its triage lane", a["s"])
        b = self._line({"triage": {"ok": False, "why": "the triage lane state could not be read: boom"}})
        self.assertIn("UNKNOWN — the triage lane state could not be read: boom", b["s"])
        c = self._line({"triage": _lane(backlog=None, sinceSurveyS=None, storeWhy="the survey store could not be read")})
        self.assertIn("owed UNKNOWN", c["s"])
        self.assertNotIn("0 owed", c["s"])
        self.assertIn("last walk UNKNOWN", c["s"])

    def test_the_lane_renderer_draws_it_on_every_path(self):
        """THE JOIN: _shLanesRender writes the line with the lanes, with a refused river and with no answer at all"""
        out = _run(r"""
          ELS['sh-lanes'] = { innerHTML: '', querySelector: function(){ return null; } };
          var lanes = %s, tri = %s;
          _shLanesRender({ lanes: lanes, triage: tri, __askedAt: NOW }); OUT.full = ELS['sh-lanes'].innerHTML;
          _shLanesRender({ ok: false, triage: tri }); OUT.noLanes = ELS['sh-lanes'].innerHTML;
          _shLanesRender({ lanes: { ok: false, why: 'the map stopped partitioning' }, triage: tri }); OUT.refused = ELS['sh-lanes'].innerHTML;
          _shLanesRender(null); OUT.none = ELS['sh-lanes'].innerHTML;
        """ % (json.dumps(RIVER_LANES), json.dumps(_lane())))
        for k in ("full", "noLanes", "refused", "none"):
            self.assertIn('class="shr-tri', out[k], "%s: the river drew no triage line" % k)
        self.assertIn("standing aside for his game", out["full"])
        self.assertGreater(out["full"].find('class="shr-tri'), out["full"].find("</details>"),
                           "the line sits inside the fold - it must read with the river shut")
        self.assertIn("UNKNOWN", out["none"])


# ── THE JOIN, IN A REAL BROWSER: the shipped card from a stubbed /api/fleet ─────────────────────────────────────────
STUB = r"""(function(){
  var FLEET = %s;
  var _f = window.fetch;
  window.fetch = function(u, o){
    var s = String(u && u.url || u), body = null;
    if (s.indexOf('/api/fleet') >= 0) body = FLEET;
    else if (s.indexOf('/api/') >= 0) body = { ok: false, why: 'law page - no console behind it' };
    if (body !== null) return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    return _f ? _f.apply(this, arguments) : Promise.reject(new Error('no fetch'));
  };
})();"""

READ = r"""(function(){ var l = document.getElementById('fleet-list'); if (!l) return JSON.stringify({ err: 'no #fleet-list' });
  var lr = l.getBoundingClientRect();
  var rows = [].map.call(l.querySelectorAll('.fleet-row'), function(r){
    var sys = r.querySelector('.fleet-sys:not(.fleet-former)'), fm = r.querySelector('.fleet-former');
    var spill = [].filter.call(r.querySelectorAll('.fleet-sys .fs-l'), function(e){ var b = e.getBoundingClientRect(); return b.width > 0 && b.right > lr.right + 0.5; }).length;
    return { name: (r.querySelector('b') || {}).textContent || '', sys: sys ? sys.innerText.replace(/ /g, ' ') : null,
             former: fm ? fm.innerText : null, spill: spill, h: sys ? sys.getBoundingClientRect().height : 0 }; });
  return JSON.stringify({ rows: rows, sw: [l.scrollWidth, l.clientWidth], w: lr.width }); })()"""

WIDTHS = ((901, 900), (1280, 800))
_CACHE = {}


def _fixture():
    now = int(time.time() * 1000)
    iso = lambda ago_s: _iso(now - ago_s * 1000)   # noqa: E731
    return {"ok": True, "me": "box-a", "publishedVer": "v3522", "fromCache": False, "staleAgeS": 0.0, "webOnly": [],
            "online": [
                {"nickname": "Konyo", "machine": "box-a", "ver": "v3522", "mode": "idle", "t": iso(40),
                 "formerMachines": [{"machine": "cursor", "lastSeen": iso(8 * 86400), "ver": "v3377"}],
                 "system": {"tree": "ok", "reels": 9,
                            "capture": {"route": "native", "ageS": 95.0, "why": "", "source": "finder"},
                            "river": {"lanes": {"TRIAGE": 2, "PRINTER": 3, "CAPTURE": 4, "TOMBSTONE": 1}, "ageS": 120.0,
                                      "why": "", "triage": dict(TRI_OK, lastTs=now - 90000)}}},
                {"nickname": "ALT", "machine": "box-b", "ver": "v3521", "mode": "live", "t": iso(20),
                 "system": {"tree": "ok", "reels": 10,
                            "capture": {"route": "boosteroid", "ageS": 12.0, "why": "", "source": "capture-half"},
                            "river": {"lanes": {"TRIAGE": 7, "PRINTER": 1, "TOMBSTONE": 2}, "ageS": 300.0, "why": "",
                                      "triage": dict(TRI_OK, lastKey="cpu-shadow", backlog=7, sinceLastS=10800.0)}}}],
            "offline": [
                {"nickname": "Wife PC", "machine": "box-c", "ver": "v3401", "mode": "idle", "t": iso(5 * 86400),
                 "system": {"tree": "ok", "reels": 3}}]}


def _render():
    if "r" in _CACHE:
        return _CACHE["r"]
    if not RC._chrome_up():
        raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d" % (RC.CHROME, RC.PORT))
    res = {}
    try:
        t = RC._Tab("about:blank")
        t.send("Page.enable")
        t.send("Runtime.enable")
        t.send("Page.addScriptToEvaluateOnNewDocument", source=STUB % json.dumps(_fixture()))
        for (w, h) in WIDTHS:
            t.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
            t.send("Page.navigate", url="file://" + UI_PATH)
            for _ in range(160):
                time.sleep(0.25)
                try:
                    if t.ev("document.readyState==='complete' && typeof window._fleetRefresh === 'function'") is True:
                        break
                except Exception:
                    pass
            else:
                raise AssertionError("control_ui.html never exposed _fleetRefresh in 40s - UNKNOWN, not passing")
            time.sleep(0.8)
            t.ev("(function(){ try { window._fleetRefresh(); } catch (e) {} return 1; })()")
            for _ in range(60):
                time.sleep(0.25)
                if t.ev("document.querySelectorAll('#fleet-list .fleet-row').length") == 3:
                    break
            time.sleep(0.3)
            res["%dx%d" % (w, h)] = json.loads(t.ev(READ))
        res["errors"] = list(getattr(t, "page_errors", []) or [])
        try:
            t.close()
        except Exception:
            pass
    finally:
        RC._chrome_down()
    _CACHE["r"] = res
    return res


@unittest.skipUnless(os.path.exists(RC.CHROME), "no Chrome on this machine - the card was not rendered (declared skip 77)")
class TheShippedCardDrawsIt(unittest.TestCase):

    def test_every_row_draws_its_films_river_and_triage_line_and_nothing_goes_sideways(self):
        r, bad = _render(), []
        for (w, h) in WIDTHS:
            m = r["%dx%d" % (w, h)]
            self.assertNotIn("err", m, m)
            self.assertEqual(len(m["rows"]), 3, "%dx%d: PRINT THE DENOMINATOR - %d rows drawn of 3" % (w, h, len(m["rows"])))
            for row in m["rows"]:
                s = row["sys"] or ""
                for word in ("films", "river", "triage"):
                    if word not in s:
                        bad.append("%dx%d %s: no %s fact on the row (%r)" % (w, h, row["name"], word, s))
                if row["spill"]:
                    bad.append("%dx%d %s: %d fact line(s) run past the card's right edge" % (w, h, row["name"], row["spill"]))
            byname = dict((x["name"], x) for x in m["rows"])
            k, a, wp = byname.get("Konyo") or {}, byname.get("ALT") or {}, byname.get("Wife PC") or {}
            if "native" not in (k.get("sys") or "") or "walking" not in (k.get("sys") or ""):
                bad.append("%dx%d Konyo: %r" % (w, h, k.get("sys")))
            if "formerly cursor" not in (k.get("former") or ""):
                bad.append("%dx%d Konyo: no 'formerly cursor' line (%r)" % (w, h, k.get("former")))
            if "Boosteroid" not in (a.get("sys") or "") or "TRIAGE 7" not in (a.get("sys") or ""):
                bad.append("%dx%d ALT: %r" % (w, h, a.get("sys")))
            if (wp.get("sys") or "").count("UNKNOWN") != 3:
                bad.append("%dx%d Wife PC (an older build): not three UNKNOWNs (%r)" % (w, h, wp.get("sys")))
            if m["sw"][0] > m["sw"][1] + 1:
                bad.append("%dx%d the fleet list scrolls sideways %s" % (w, h, m["sw"]))
        self.assertEqual(r.get("errors"), [], "the page threw: %s" % r.get("errors"))
        self.assertEqual(bad, [], "\n  ".join(bad))


RED_PROOF = [
    {
        "why": "2026-09-28 - a route's age is the pin's age at send again, not ageS + how long the site has held the beacon",
        "file": "control_ui.html",
        "find": "    return ageS + Math.max(0, (now - rec) / 1000);\n",
        "replace": "    return ageS;\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a row with no record time reads its send-time age as if it were current",
        "file": "control_ui.html",
        "find": "    if (!isFinite(rec)) return null;\n",
        "replace": "    if (!isFinite(rec)) return ageS;\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a river with no lane map is drawn as an empty river (a confident zero)",
        "file": "control_ui.html",
        "find": "      out.push({ k: 'river', t: 'UNKNOWN', unk: true, why: String(rv.why || 'no lane answered') });\n",
        "replace": "      out.push({ k: 'river', t: 'empty \\u2014 0 reels at every station', why: '' });\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - 'standing aside for his game' reads as one more refusal on the fleet row",
        "file": "control_ui.html",
        "find": "      else if (lk === 'playing') st = 'standing aside for his game';\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the fleet row stops drawing how its PC films and drains (the wire carries it, nothing reads it)",
        "file": "control_ui.html",
        "find": "          + _fleetSysHtml(m, Date.now())\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a renamed host's 'formerly' line is dropped",
        "file": "control_ui.html",
        "find": "    if (fm.length) {\n",
        "replace": "    if (false) {\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the river line prints a null backlog as a number",
        "file": "control_ui.html",
        "find": "    bits.push((typeof t.backlog === 'number')\n",
        "replace": "    bits.push((true)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the river panel draws its lanes and not its triage lane (the fold's line is gone)",
        "file": "control_ui.html",
        "find": "                 /* outside the fold: the lane's one line reads with the river shut */\n                 + _shTriageLine(d);\n",
        "replace": "                 ;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
