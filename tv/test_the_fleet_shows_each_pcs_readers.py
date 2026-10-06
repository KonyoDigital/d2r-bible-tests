# -*- coding: utf-8 -*-
"""#108 — EVERY PC ON THE FLEET SAYS WHETHER ITS READERS CAN READ, SO A SIGNED-OUT PC SHOWS ON HIS CONSOLE.

His question, 2026-09-30, after his ALT filmed a day and read nothing because Claude was signed out there: "maybe this
happened to dean too?". The CLAUDE / GROK lamps under each console's corner chip (REG-1604) answer it only on THAT PC's
own screen, and nobody stands at Dean's. The fleet card is where he sees every PC at once.

FOUR JOINTS, each DRIVEN here through the shipped code (never re-implemented):
  1. THE CONSOLE - _readers_for_wire(): _reader_health's two lamps - one measure, never a second derivation - cut to
     {state, needsLogin, why}: a lamp that is neither on nor off is 'unknown', the reason is capped, and a console that
     cannot measure its readers posts None. _reader_health itself answers UNKNOWN (it used to raise NameError) when the
     Grok lane answers with no status.
  2. THE BEACON - `readers` rides every beacon beside `shadow`.
  3. THE WORKER - the shaper keeps state / needsLogin / why (absent stays null, an odd state is 'unknown'), and a flip
     of a state or of needsLogin is news - the words are not (their counts move every read).
  4. THE CARD - the calm row says "Claude signed out" / "Claude not reading" ONLY when that PC's primary reader
     cannot read, and "Grok signed out" only when the + GROK layer is on and signed out there; nothing when they
     read, when the layer is simply switched off, when the PC is offline or when an older build sends nothing. The box
     a click opens says both lamps in words, each reader's reason in its hover.
[[heart-first]] [[unknown-stays-unknown]] [[the-unjoined-end]] [[stale-reading]]
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402
import test_console_fleet as CF  # noqa: E402  the real worker handler over an in-memory KV
import test_the_picker_census_reaches_the_fleet as PK  # noqa: E402  its node runner and cutter, one copy
from test_the_fleet_card_says_how_each_pc_films_and_drains import _run as _ui_run, NOW as UI_NOW  # noqa: E402
import worker_source as _ws  # noqa: E402  REG-1839 - the worker's top-level helpers, lifted with the shaper

NODE = PK.NODE
API = os.path.join(ROOT, "functions", "api", "console.js")
UI = os.path.join(HERE, "control_ui.html")

PROOF_NEEDS = ["../functions/api/console.js", "../functions/_middleware.js"]

RED_PROOF = [
    {
        "why": "#108 - a lamp that is neither on nor off rides to the fleet as whatever it said",
        "file": "control_app.py",
        "find": "        out[k] = {\"state\": st if st in (\"on\", \"off\") else \"unknown\",\n",
        "replace": "        out[k] = {\"state\": st or \"unknown\",\n",
        "matches": 1,
    },
    {
        "why": "#108 - a Grok lane that answers with no status raises NameError instead of reading UNKNOWN",
        "file": "control_app.py",
        "find": "    gwhy = \"the Grok lane answered with no status - whether Grok can read is UNKNOWN\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#108 - the beacon stops carrying the readers",
        "file": "control_app.py",
        "find": "            \"readers\": _readers_for_wire(),\n",
        "replace": "            \"readers\": None,\n",
        "matches": 1,
    },
    {
        "why": "#108 - the worker's shaper keeps any state it is sent",
        "file": "functions/api/console.js",
        "find": "          state: (x.state === 'on' || x.state === 'off') ? x.state : 'unknown',\n",
        "replace": "          state: x.state,\n",
        "matches": 1,
    },
    {
        "why": "#108 - a reader that stops reading is not news: the row keeps saying nothing for up to 15 min",
        "file": "functions/api/console.js",
        "find": "    || readersNews(prev) !== readersNews(rec)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#108 - an OFFLINE PC's last report is drawn as the present",
        "file": "control_ui.html",
        "find": "    if (!online || !rd) return '';\n    var c = (rd.claude && typeof rd.claude === 'object') ? rd.claude : {};\n    var g = (rd.grok && typeof rd.grok === 'object') ? rd.grok : {};\n    var out = '';\n",
        "replace": "    if (!rd) return '';\n    var c = (rd.claude && typeof rd.claude === 'object') ? rd.claude : {};\n    var g = (rd.grok && typeof rd.grok === 'object') ? rd.grok : {};\n    var out = '';\n",
        "matches": 1,
    },
    {
        "why": "#108 - a signed-out PC reads as a reader that merely failed: the fix (/login) is not named",
        "file": "control_ui.html",
        "find": "(c.needsLogin ? 'Claude signed out' : 'Claude not reading')",
        "replace": "'Claude not reading'",
        "matches": 1,
    },
    {
        "why": "#108 - a + GROK layer switched off by choice is drawn as a fault",
        "file": "control_ui.html",
        "find": "    if (g.state === 'off' && g.needsLogin === true) {\n",
        "replace": "    if (g.state === 'off') {\n",
        "matches": 1,
    },
    {
        "why": "#108 - the row stops asking for its readers (the helper stays, the join is gone)",
        "file": "control_ui.html",
        "find": "    var s = _fleetStuckChip(m) + _fleetPickerChip(m) + _fleetReaderChip(m, online);\n",
        "replace": "    var s = _fleetStuckChip(m) + _fleetPickerChip(m);\n",
        "matches": 1,
    },
    {
        "why": "#108 - the click box stops saying the readers",
        "file": "control_ui.html",
        "find": "    out.push(_fleetReadersPart(m));\n",
        "replace": "",
        "matches": 1,
    },
]

SIGNED_OUT = {
    "claude": {"state": "off", "needsLogin": True, "ok": 0, "failed": 3,
               "why": "Claude cannot sign in on this PC: Failed to authenticate: OAuth session expired - open "
                      "PowerShell or a terminal, run `claude`, type /login"},
    "grok": {"state": "off", "needsLogin": False, "why": "the + GROK layer is switched off on this PC"},
}
READING = {
    "claude": {"state": "on", "needsLogin": False, "why": "Claude read on this PC 1 min ago (41 ok, 0 failed in 2 h)"},
    "grok": {"state": "on", "needsLogin": False, "why": "Grok is on (shadow) - 1344 ok, 229 errors"},
}


def _wire(rd):
    fn = rd if callable(rd) else (lambda *a, **k: rd)
    with mock.patch.object(ca, "_reader_health", fn):
        return ca._readers_for_wire()


# ══ JOINT 1 — THE CONSOLE ═════════════════════════════════════════════════════════════════════════════════════════
class OneMeasureOnThisPc(unittest.TestCase):

    def test_the_lamps_are_cut_to_what_a_row_needs(self):
        w = _wire(SIGNED_OUT)
        self.assertEqual(set(w), {"claude", "grok"})
        self.assertEqual((w["claude"]["state"], w["claude"]["needsLogin"]), ("off", True), w)
        self.assertIn("/login", w["claude"]["why"])
        self.assertEqual(set(w["claude"]), {"state", "needsLogin", "why"}, "the wire carries more than a row needs")
        self.assertEqual((w["grok"]["state"], w["grok"]["needsLogin"]), ("off", False), w)
        long = {"claude": {"state": "on", "why": "x " * 200}, "grok": {"state": "on", "why": "y"}}
        self.assertLessEqual(len(_wire(long)["claude"]["why"]), 160, "the reason is not capped")

    def test_a_lamp_that_is_neither_on_nor_off_is_unknown(self):
        w = _wire({"claude": {"state": "maybe", "needsLogin": "yes"}, "grok": None})
        self.assertEqual((w["claude"]["state"], w["claude"]["needsLogin"]), ("unknown", False), w)
        self.assertEqual(w["grok"], {"state": "unknown", "needsLogin": False, "why": None})
        self.assertEqual(_wire({"claude": {"state": "unknown", "why": "no Claude read in the last 2 h"},
                                "grok": READING["grok"]})["claude"]["state"], "unknown")

    def test_a_console_that_cannot_measure_its_readers_posts_nothing(self):
        def boom(*a, **k):
            raise RuntimeError("the journal went away mid-read")
        self.assertIsNone(_wire(boom), "a console that could not measure posted a guessed lamp")
        self.assertIsNone(_wire(None))
        self.assertIsNone(_wire(["not", "a", "dict"]))

    def test_a_grok_lane_that_answers_with_no_status_is_unknown_not_an_error(self):
        # the same measure the corner lamps and the doctor row read: a lane that answers with something other than a
        # dict must read UNKNOWN - it raised NameError (its reason was only set by the except branch)
        out = ca._reader_health(now_ms=UI_NOW, rows=[], g5=[], use_cache=False)
        self.assertEqual(out["grok"]["state"], "unknown", out["grok"])
        self.assertIn("UNKNOWN", out["grok"]["why"])
        self.assertEqual(out["claude"]["state"], "unknown", "no read in the window must be UNKNOWN, not on or off")


# ══ JOINT 2 — THE BEACON ══════════════════════════════════════════════════════════════════════════════════════════
class TheBeaconCarriesIt(unittest.TestCase):

    def test_every_beacon_carries_the_readers(self):
        import urllib.request as _ur
        sent = {}

        def fake_urlopen(req, timeout=None):
            sent["body"] = json.loads(req.data.decode("utf-8"))

            class R(object):
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

                def read(self):
                    return b"{}"
            return R()
        saved_env = {k: os.environ.pop(k, None) for k in ("CI", "GITHUB_ACTIONS", "TVD_NO_BEACON")}
        bdir = tempfile.mkdtemp(prefix="readers_beacon_")
        self.addCleanup(shutil.rmtree, bdir, True)
        self.addCleanup(setattr, ca, "_BEACON_STATE_PATH", ca._BEACON_STATE_PATH)
        ca._BEACON_STATE_PATH = os.path.join(bdir, ".tvd_beacon.json")
        try:
            with mock.patch.object(_ur, "urlopen", fake_urlopen), \
                    mock.patch.object(ca, "_reader_health", lambda *a, **k: SIGNED_OUT):
                ca._console_beacon("hb")
        finally:
            for k, v in saved_env.items():
                if v is not None:
                    os.environ[k] = v
        rd = sent.get("body", {}).get("readers")
        self.assertIsInstance(rd, dict, "the beacon carries no readers: %r" % sorted(sent.get("body", {})))
        self.assertEqual((rd["claude"]["state"], rd["claude"]["needsLogin"]), ("off", True), rd)


# ══ JOINT 3 — THE WORKER ══════════════════════════════════════════════════════════════════════════════════════════
def _shape(readers):
    """The SHIPPED worker shaper for `readers`, run in node."""
    with io.open(API, encoding="utf-8") as f:
        src = f.read()
    fn = PK._between_once(src, "    readers: (function (r) {", "    })(body.readers),") + "    })"
    fn = "(" + fn[len("    readers: "):] + ")"
    return PK._node_json(_ws.prelude(src) + "var shape = %s; console.log(JSON.stringify({ v: shape(%s) }));"
                         % (fn, json.dumps(readers)))["v"]


@unittest.skipIf(NODE is None, "node is absent - this law RUNS the real worker and will not re-implement it")
class TheWorkerKeepsIt(unittest.TestCase):

    def test_the_shaper_keeps_the_lamps_and_names_what_it_cannot_read(self):
        v = _shape(SIGNED_OUT)
        self.assertEqual((v["claude"]["state"], v["claude"]["needsLogin"]), ("off", True), v)
        self.assertIn("/login", v["claude"]["why"])
        odd = _shape({"claude": {"state": "yes", "needsLogin": "true", "why": "   "}})
        self.assertEqual(odd["claude"], {"state": "unknown", "needsLogin": False, "why": None}, odd)
        self.assertEqual(odd["grok"], {"state": "unknown", "needsLogin": False, "why": None},
                         "a lamp the PC did not send was guessed")
        self.assertIsNone(_shape(None), "an older console grew readers it never sent")

    def test_a_reader_that_stops_reading_is_news_and_its_words_are_not(self):
        body = {"machine": "dean-pc", "nickname": "Dean", "install": "i-dean", "ver": "v3531", "mode": "idle",
                "event": "hb", "readers": READING}
        first = CF.run_handler(API, method="POST", body=body)
        prior = [p for p in first["puts"] if p["name"] == "console:dean-pc"]
        self.assertEqual(len(prior), 1, "premise: the first beacon stored its record")
        seed = {"console:dean-pc": json.loads(prior[0]["value"])}
        words = dict(READING, claude=dict(READING["claude"], why="Claude read on this PC 3 min ago (44 ok, 0 failed)"))
        same = CF.run_handler(API, method="POST", body=dict(body, readers=words), seed=seed)
        self.assertEqual([p for p in same["puts"] if p["name"] == "console:dean-pc"], [],
                         "premise: only the reason's words moved, which is not news")
        out = CF.run_handler(API, method="POST", body=dict(body, readers=SIGNED_OUT), seed=seed)
        recs = [json.loads(p["value"]) for p in out["puts"] if p["name"] == "console:dean-pc"]
        self.assertEqual(len(recs), 1, "a PC whose reader signed out was not written - its row says nothing for 15 min")
        self.assertEqual(recs[0]["readers"]["claude"]["state"], "off")


# ══ JOINT 4 — THE CARD ════════════════════════════════════════════════════════════════════════════════════════════
def _chip(readers, online=True):
    row = {"nickname": "Dean", "machine": "dean-pc", "ver": "v3531"}
    if readers != "absent":
        row["readers"] = readers
    return _ui_run("var h = _fleetReaderChip(%s, %s); OUT.h = h; OUT.text = strip(h).trim();"
                   % (json.dumps(row), "true" if online else "false"))


def _part(readers):
    row = {"nickname": "Dean", "machine": "dean-pc", "ver": "v3531"}
    if readers != "absent":
        row["readers"] = readers
    return _ui_run("var p = _fleetSysParts(%s, NOW); OUT.p = null; p.forEach(function(x){ if (x.k === 'readers') "
                   "OUT.p = { t: plain(x.t), unk: !!x.unk, warn: !!x.warn, why: x.why }; });" % json.dumps(row))["p"]


@unittest.skipIf(NODE is None, "node is absent - this law RUNS the shipped card helpers and will not re-implement them")
class TheWordOnTheRowAndTheBox(unittest.TestCase):

    def test_a_signed_out_pc_says_so_on_its_row_and_names_the_fix(self):
        c = _chip(SIGNED_OUT)
        self.assertEqual(c["text"], "Claude signed out", c)
        self.assertIn("/login", c["h"], "the hover does not carry the reader's own reason")
        failed = _chip(dict(SIGNED_OUT, claude=dict(SIGNED_OUT["claude"], needsLogin=False,
                                                    why="Claude's last read on this PC failed: timeout")))
        self.assertEqual(failed["text"], "Claude not reading", failed)

    def test_a_calm_row_stays_calm(self):
        for label, readers, online in (("reading", READING, True), ("offline", SIGNED_OUT, False),
                                       ("older build", "absent", True),
                                       ("Grok switched off by choice", dict(READING, grok=SIGNED_OUT["grok"]), True),
                                       ("Claude UNKNOWN", dict(READING, claude={"state": "unknown"}), True)):
            self.assertEqual(_chip(readers, online)["h"], "", "%s put a word on the calm row" % label)

    def test_grok_signed_out_while_its_layer_is_on_is_said(self):
        g = _chip(dict(READING, grok={"state": "off", "needsLogin": True, "why": "Grok is not signed in on this PC"}))
        self.assertEqual(g["text"], "Grok signed out", g)

    def test_the_box_says_both_lamps_in_words(self):
        p = _part(SIGNED_OUT)
        self.assertEqual((p["t"], p["warn"], p["unk"]), ("CLAUDE signed out · GROK off", True, False), p)
        self.assertIn("/login", p["why"])
        ok = _part(READING)
        self.assertEqual((ok["t"], ok["warn"], ok["unk"]), ("CLAUDE reads · GROK reads", False, False), ok)
        old = _part("absent")
        self.assertTrue(old["unk"], "an older build's readers were not said UNKNOWN: %r" % old)
        self.assertIn("UNKNOWN", old["t"])

    def test_the_row_asks_for_its_readers(self):
        """The join, DRIVEN (REG-1613): the row's exception line - _fleetRowChips, the one item the row places under its
        name - carries the readers' word beside the river's, and is nothing at all on a calm row. That the ROW draws
        that line is rendered in a browser by test_the_fleet_row_keeps_its_name_whole and render_check fleet-xref."""
        stuck = {"river": {"stuck": [{"station": "EMPTY", "n": 3, "oldestS": 90000, "why": "route lane: law"}]}}
        loud = {"nickname": "Dean", "machine": "dean-pc", "ver": "v3531", "readers": SIGNED_OUT, "system": stuck}
        calm = {"nickname": "Dean", "machine": "dean-pc", "ver": "v3531", "readers": READING}
        out = _ui_run("OUT.h = _fleetRowChips(%s, true); OUT.calm = _fleetRowChips(%s, true); OUT.off = _fleetRowChips(%s, false);"
                      % (json.dumps(loud), json.dumps(calm), json.dumps(dict(loud, system=None))))
        self.assertIn('class="fleet-chips"', out["h"], "the row's words are not one line item")
        self.assertIn("Claude signed out", out["h"], "the row's line does not say its PC's readers")
        self.assertIn("river stuck", out["h"], "premise: the river's word shares the line")
        self.assertEqual(out["calm"], "", "a calm PC grew an exception line")
        self.assertEqual(out["off"], "", "an offline PC's last report was said as the present")


if __name__ == "__main__":
    unittest.main(verbosity=2)
