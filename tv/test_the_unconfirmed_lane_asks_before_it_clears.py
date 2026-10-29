# -*- coding: utf-8 -*-
"""REG-3011 (#163, his ruling 2026-10-29 Q6) - THE CONSOLE'S UNCONFIRMED LANE: ONE BATCH PER MINUTE, CONFIRM OR CLEAR, ASKED FIRST.

Dean's 117 set pieces were stamped in one minute and nothing asked him about them. The Chronicle inbox now has a third lane,
"⚠ Unconfirmed": the board's list of ticks nothing on it vouches for (REG-3009), minus every name the console's ledgers have
seen (REG-3010), grouped by the minute each was stamped so one bulk tick reads as ONE batch. Each tick and each batch has
✓ Confirm and ✕ Clear; a clear of more than one asks first; another PC's shadow is read only; nothing is cleared on its own.
A board that cannot answer is UNKNOWN, and a console that cannot say what it has seen keeps every row (never fewer).

Node: the lane's own code cut from tv/control_ui.html and run against a stand-in board and console. RED_PROOF below.
"""
import io
import json
import os
import subprocess
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

from cb_node_harness import node_path  # noqa: E402

NODE = node_path()
UI = os.path.join(HERE, "control_ui.html")
START = "  /* ══ #163 (REG-3011, his ruling 2026-10-29 Q6)"
END = "  function chModalRender(){\n"
D = "Aug 1, 2026 · 16:57"


def _ui():
    return io.open(UI, encoding="utf-8").read()


def lane_code():
    s = _ui()
    if s.count(START) != 1 or s.count(END) != 1:
        raise AssertionError("PREMISE: the lane's code is not where this law cuts it")
    return s[s.index(START):s.index(END)]


HARNESS = r"""
var window = globalThis;
var CH = { open: false, items: [], ledger: [], mode: 'unconf', q: '', selected: {} };
var LOG = { toast: [], asked: [], confirm: [], clear: [], paints: 0, fetches: 0 };
function toast(m){ LOG.toast.push(String(m)); }
function esc(s){ return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
function chArtHtml(){ return ''; }
function paintChronicleInbox(){ LOG.paints++; }
function chModalRender(){}
var ASK = null; function chAsk(text, yes, onYes){ LOG.asked.push(text); ASK = onYes; }
var SHADOW = false; window._consoleShadowUp = function(){ return SHADOW; };
var BOARD = { ok: true, readOnly: false, rows: %(rows)s };
var W = {
  _unconfirmedTicks: function(){ return BOARD.ok ? { ok: true, rows: BOARD.rows.slice(), readOnly: BOARD.readOnly } : { ok: false, why: 'the found log would not read' }; },
  _ticksConfirm: function(items){ LOG.confirm.push(items); return { ok: true, confirmed: items.map(function(i){ return i.name; }), skipped: [] }; },
  _ticksClear: function(items){ LOG.clear.push(items); return { ok: true, cleared: items.map(function(i){ return i.name; }), skipped: [] }; }
};
function _engWin(){ return W; }
var FETCH = { ok: true, has: %(has)s };
globalThis.fetch = function(url, opt){
  LOG.fetches++; LOG.lastFetch = { url: url, body: JSON.parse(opt.body) };
  return Promise.resolve({ json: function(){ return Promise.resolve(FETCH.ok ? { ok: true, has: FETCH.has } : { ok: false, why: 'the evidence ledger could not be read' }); } });
};
%(lane)s
function refresh(){ return new Promise(function(res){ chUnconfRefresh(res); }); }
(async function(){
  var OUT = {}, body = { innerHTML: '' };
  await refresh();
  OUT.list = CH.unconf.map(function(r){ return r.store + ':' + r.name; });
  OUT.fetch = LOG.lastFetch;
  OUT.shown = chUnconfRender(body); OUT.html = body.innerHTML;
  OUT.groups = (CH._uGroups || []).map(function(g){ return [g.date, g.rows.length]; });
  chUnconfAct('confirm', chUnconfRowsOf([chUnconfKey(CH.unconf[0])]));
  OUT.confirmCalls = JSON.parse(JSON.stringify(LOG.confirm));
  await refresh();
  var big = CH._uGroups[0].rows;
  chUnconfClear(big);
  OUT.askedForBatch = LOG.asked.length; OUT.clearedBeforeYes = LOG.clear.length;
  ASK(); OUT.clearedAfterYes = LOG.clear.length; OUT.batchItems = LOG.clear[0];
  await refresh();
  var asked = LOG.asked.length;
  chUnconfClear(chUnconfRowsOf([chUnconfKey(CH.unconf[CH.unconf.length - 1])]));
  OUT.askedForOne = LOG.asked.length - asked; OUT.clearedOne = LOG.clear.length;
  await refresh();
  SHADOW = true;
  chUnconfRender(body); OUT.roHtml = body.innerHTML;
  var c0 = LOG.confirm.length, x0 = LOG.clear.length;
  chUnconfAct('confirm', CH.unconf.slice(0, 1)); chUnconfAct('clear', CH.unconf.slice(0, 1));
  OUT.roWrites = (LOG.confirm.length - c0) + (LOG.clear.length - x0);
  SHADOW = false;
  FETCH.ok = false; await refresh();
  OUT.keepAll = CH.unconf.length; OUT.warn = CH.unconfEvWhy;
  FETCH.ok = true; BOARD.ok = false; await refresh();
  OUT.unknown = CH.unconf; OUT.unknownWhy = CH.unconfWhy; chUnconfRender(body); OUT.unknownHtml = body.innerHTML;
  BOARD.ok = true; BOARD.rows = []; await refresh();
  chUnconfRender(body); OUT.noneHtml = body.innerHTML;
  OUT.autoWrites = { confirm: LOG.confirm.length, clear: LOG.clear.length };
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stdout.write(JSON.stringify({ err: String(e && e.stack || e) })); });
"""

ROWS = [{"name": "Aldur's Advance (boots)", "store": "sets", "date": D},
        {"name": "Sigon's Gage (gloves)", "store": "sets", "date": D},
        {"name": "Authority", "store": "runewords", "date": D},
        {"name": "Wormskull", "store": "uniques", "date": "Jun 2, 2026 · 10:00"},
        {"name": "Grief", "store": "runewords", "date": D},
        {"name": "Nightsmoke", "store": "uniques", "date": None}]
HAS = {"Aldur's Advance (boots)": False, "Sigon's Gage (gloves)": False, "Authority": None, "Wormskull": False,
       "Grief": True, "Nightsmoke": False}

_RUN = {}


def run():
    if "o" not in _RUN:
        if not NODE:
            raise unittest.SkipTest("node is absent on this machine - UNMEASURED here, never a pass")
        js = HARNESS % {"rows": json.dumps(ROWS), "has": json.dumps(HAS), "lane": lane_code()}
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8", timeout=120)
        if r.returncode != 0:
            raise AssertionError("the lane would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        o = json.loads(r.stdout)
        if o.get("err"):
            raise AssertionError("the lane threw: %s" % o["err"])
        _RUN["o"] = o
    return _RUN["o"]


class TheUnconfirmedLaneAsksBeforeItClears(unittest.TestCase):

    def test_the_console_drops_only_what_it_has_seen(self):
        o = run()
        self.assertEqual(o["fetch"]["url"], "/api/evidence_names")
        self.assertEqual(sorted(o["fetch"]["body"]["names"]), sorted(r["name"] for r in ROWS))
        self.assertNotIn("runewords:Grief", o["list"], "a tick the console has seen is still asked about")
        self.assertIn("runewords:Authority", o["list"], "a tick whose evidence is UNKNOWN was dropped as if seen")
        self.assertEqual(len(o["list"]), 5)

    def test_one_bulk_tick_reads_as_one_batch(self):
        o = run()
        self.assertEqual(o["groups"][0], [D, 3], "the same-minute ticks are not one batch, biggest first: %r" % o["groups"])
        self.assertIn("3 ticked in one minute · " + D, o["html"])
        self.assertIn("2 set pieces · 1 runeword", o["html"])
        self.assertIn("no date", o["html"])
        for cls in ("ch-u-gok", "ch-u-gno", "ch-u-ok", "ch-u-no", "ch-u-chk"):
            self.assertIn(cls + '"', o["html"], "the lane lost its %s control" % cls)

    def test_confirm_hands_the_board_each_tick_with_its_store(self):
        calls = run()["confirmCalls"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(sorted(calls[0][0]), ["name", "store"])

    def test_a_batch_clear_asks_first_and_one_clear_does_not(self):
        o = run()
        self.assertEqual((o["askedForBatch"], o["clearedBeforeYes"], o["clearedAfterYes"]), (1, 0, 1),
                         "a batch clear did not wait for his answer")
        self.assertEqual(len(o["batchItems"]), 3)
        self.assertEqual((o["askedForOne"], o["clearedOne"]), (0, 2))

    def test_a_shadow_is_read_only(self):
        o = run()
        self.assertIn("read-only", o["roHtml"])
        for cls in ("ch-u-gok", "ch-u-ok", "ch-u-no", "ch-u-chk"):
            self.assertNotIn(cls + '"', o["roHtml"], "a shadow draws %s" % cls)
        self.assertEqual(o["roWrites"], 0, "a shadow pressed a confirm or a clear")

    def test_an_unanswered_console_keeps_every_row_and_says_so(self):
        o = run()
        self.assertEqual(o["keepAll"], len(ROWS))
        self.assertIn("could not say", o["warn"])

    def test_a_board_that_cannot_answer_is_unknown_never_none(self):
        o = run()
        self.assertIsNone(o["unknown"])
        self.assertIn("UNKNOWN", o["unknownHtml"])
        self.assertIn("Every tick on this board has evidence", o["noneHtml"])

    def test_nothing_is_confirmed_or_cleared_by_reading(self):
        self.assertEqual(run()["autoWrites"], {"confirm": 1, "clear": 2}, "a refresh pressed a door")

    def test_the_lane_is_wired_into_the_inbox(self):
        s = _ui()
        for needle in ('id="ch-mode-unconf"', 'id="ch-u-confirm-sel"', 'id="ch-u-clear-sel"',
                       "      if (chUnconfClick(t)) return;   /* #163 REG-3011 */\n",
                       "    btn.hidden = nPend < 1 && nLed < 1 && nUnc < 1;\n",
                       "    if (CH.mode === 'unconf'){\n"):
            self.assertEqual(s.count(needle), 1, "the inbox lost the lane's %r" % needle[:60])


RED_PROOF = [
    {"why": "REG-3011 - the console asks about ticks its own ledgers have seen",
     "file": "tv/control_ui.html",
     "find": "          CH.unconf = rows.filter(function(x){ return j.has[x.name] !== true; });\n",
     "replace": "          CH.unconf = rows.slice();\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - a tick whose evidence is UNKNOWN is dropped as if seen",
     "file": "tv/control_ui.html",
     "find": "          CH.unconf = rows.filter(function(x){ return j.has[x.name] !== true; });\n",
     "replace": "          CH.unconf = rows.filter(function(x){ return j.has[x.name] === false; });\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - an unanswered console hides every row",
     "file": "tv/control_ui.html",
     "find": "        CH.unconf = rows.slice();\n          CH.unconfEvWhy = 'the console could not say",
     "replace": "        CH.unconf = [];\n          CH.unconfEvWhy = 'the console could not say",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - the batches are not grouped by the minute",
     "file": "tv/control_ui.html",
     "find": "      var k = r.date || '';\n",
     "replace": "      var k = r.name;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - a batch clear does not ask",
     "file": "tv/control_ui.html",
     "find": "    if (rows.length < 2){ chUnconfAct('clear', rows); return; }\n",
     "replace": "    if (true){ chUnconfAct('clear', rows); return; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - a shadow draws the buttons",
     "file": "tv/control_ui.html",
     "find": "    var ro = chUnconfReadOnly(), q = (CH.q || '').toLowerCase().trim();\n",
     "replace": "    var ro = false, q = (CH.q || '').toLowerCase().trim();\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - a shadow presses the board's doors",
     "file": "tv/control_ui.html",
     "find": "    if (chUnconfReadOnly()){ toast('Read only: this is another PC\u2019s console'); return; }\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3011 - a board that cannot answer reads as none",
     "file": "tv/control_ui.html",
     "find": "    if (!r || r.ok !== true){ CH.unconf = null; CH.unconfWhy = (r && r.why) || 'the board did not answer'; done(); return; }\n",
     "replace": "    if (!r || r.ok !== true){ CH.unconf = []; done(); return; }\n",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()
