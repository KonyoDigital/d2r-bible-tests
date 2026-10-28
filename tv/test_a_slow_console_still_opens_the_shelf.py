# -*- coding: utf-8 -*-
"""REG-2698 (GrokBot's v3816 pass, #86, 2026-10-28) - A SLOW CONSOLE STILL OPENS THE SHELF, AND SAYS IT IS WAITING.

Measured on his Mac under load (load ~20): /api/sessions answered in 10.8 s and 21.6 s for 266 KB, and thOpen aborted it at
8 s and closed the stage on every try - "[theatre] /api/sessions did not answer - stage closed (AbortError)", four times -
so the Shelf never painted and read as dead. v2228's bound stays (an orphaned fetch must never leave a black stage forever),
but the wait is thSessionsWait: bounded at TH_SESSIONS_BOUND_MS with the body inside the bound, and from TH_SLOW_SAY_MS the
caption (and the shelf's own lead line) says the console is slow and for how long.

Drives the SHIPPED thSessionsWait, cut from control_ui.html and run in node on a virtual clock. A missing node raises;
this law does not skip. RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
CUT = ("  var TH_SESSIONS_BOUND_MS = ", "\n  async function thOpen(){")

PROGRAM = r"""
var NOW = 1000000, TIMERS = [], NEXT = 1;
var window = {}, API = '';   /* GrokBot v3817 - the cut now carries the shared /api/sessions fetch */
Date.now = function(){ return NOW; };
function setTimeout(fn, ms){ var id = NEXT++; TIMERS.push({ id: id, at: NOW + ms, fn: fn }); return id; }
function setInterval(fn, ms){ var id = NEXT++; TIMERS.push({ id: id, at: NOW + ms, fn: fn, every: ms }); return id; }
function clearTimeout(id){ TIMERS = TIMERS.filter(function(t){ return t.id !== id; }); }
var clearInterval = clearTimeout;
async function advance(ms){
  var end = NOW + ms;
  for (;;) {
    TIMERS.sort(function(a, b){ return a.at - b.at; });
    var t = TIMERS[0];
    if (!t || t.at > end) break;
    NOW = t.at;
    if (t.every) t.at = NOW + t.every; else TIMERS.shift();
    t.fn();
    await Promise.resolve(); await Promise.resolve();
  }
  NOW = end;
  await Promise.resolve(); await Promise.resolve();
}
var EL = {}, LEAD = { textContent: 'opening the shelf…' };
function $(id){ return EL[id] || (EL[id] = { id: id, textContent: '' }); }
var document = { querySelector: function(q){ return q === '#th-shelfov .she-lead' ? LEAD : null; } };
var TH = { gen: 1 };
var ANSWER_AT = null, ABORTED = false;
function fetch(url, opts){
  return new Promise(function(res, rej){
    if (opts && opts.signal) opts.signal.addEventListener('abort', function(){ ABORTED = true; rej(new Error('AbortError')); });
    if (ANSWER_AT != null) setTimeout(function(){ res({ json: function(){ return Promise.resolve({ sessions: [1, 2, 3] }); } }); }, ANSWER_AT);
  });
}
%s
(async function(){
  var SC = %s, out = {};
  ANSWER_AT = SC.answerAt;
  var settled = null, p = thSessionsWait(1, SC.shelf).then(function(j){ settled = { ok: j }; }, function(e){ settled = { err: String(e) }; });
  await advance(2000); out.at2 = $('th-caption').textContent;
  if (SC.overtake) TH.gen = 2;
  await advance(3000); out.at5 = $('th-caption').textContent; out.lead5 = LEAD.textContent;
  await advance(SC.until - 5000);
  await p;
  out.settled = settled; out.aborted = ABORTED; out.timersLeft = TIMERS.length;
  console.log(JSON.stringify(out));
})();
"""


def _cut():
    with open(UI, encoding="utf-8") as fh:
        s = fh.read()
    start, end = CUT
    if s.count(start) != 1:
        raise AssertionError("anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    return s[i:s.index(end, i)]


def _run(sc):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = PROGRAM % (_cut(), json.dumps(sc))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut thSessionsWait did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ASlowConsoleStillOpensTheShelf(unittest.TestCase):

    def test_a_12_second_answer_is_taken_not_aborted(self):
        o = _run({"answerAt": 12000, "until": 13000, "shelf": True})
        self.assertEqual(o["settled"], {"ok": {"sessions": [1, 2, 3]}},
                         "a 12 s answer was aborted and the stage closed (GrokBot measured 10.8 s and 21.6 s): %r" % o)
        self.assertFalse(o["aborted"])
        self.assertEqual(o["timersLeft"], 0, "the bound or the waiting line outlived the answer")

    def test_the_stage_says_it_is_waiting_and_for_how_long(self):
        o = _run({"answerAt": 12000, "until": 13000, "shelf": True})
        self.assertEqual(o["at2"], "", "a quick answer would have had a 'slow' caption at 2 s")
        self.assertIn("the console is slow to answer (5 s", o["at5"], o)
        self.assertIn("gives up at 45 s", o["at5"])
        self.assertIn("opening the shelf", o["lead5"], "the shelf's own lead line still read as a silent wait: %r" % o)

    def test_a_console_that_never_answers_still_closes_at_the_bound(self):
        o = _run({"answerAt": None, "until": 46000, "shelf": False})
        self.assertTrue(o["aborted"], "a fetch that never answers was waited on forever (v2228's black stage): %r" % o)
        self.assertIn("AbortError", (o["settled"] or {}).get("err") or "")
        self.assertIn("loading the reel", o["at5"])
        self.assertEqual(o["timersLeft"], 0)

    def test_an_overtaken_open_never_writes_the_caption(self):
        o = _run({"answerAt": 12000, "until": 13000, "shelf": True, "overtake": True})
        self.assertEqual(o["at5"], "", "an open that a later one overtook wrote over the winner's caption: %r" % o)


RED_PROOF = [
    {"why": "REG-2698 - the sessions wait is cut at 8 s again and a slow console closes the shelf",
     "file": "tv/control_ui.html",
     "find": "  var TH_SESSIONS_BOUND_MS = 45000, TH_SLOW_SAY_MS = 4000;\n",
     "replace": "  var TH_SESSIONS_BOUND_MS = 8000, TH_SLOW_SAY_MS = 4000;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2698 - the stage waits in silence again",
     "file": "tv/control_ui.html",
     "find": "      if (ms < TH_SLOW_SAY_MS) return;\n",
     "replace": "      return;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2698 - a fetch that never answers is waited on forever (v2228's black stage)",
     "file": "tv/control_ui.html",
     "find": "    var to = setTimeout(function(){ try { if (ac) ac.abort(); } catch (e) {} }, TH_SESSIONS_BOUND_MS);\n",
     "replace": "    var to = null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2698 - an overtaken open writes over the winner's caption",
     "file": "tv/control_ui.html",
     "find": "      if (gen !== TH.gen) return;\n      var ms = Date.now() - t0;\n",
     "replace": "      var ms = Date.now() - t0;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2698 - the waiting line keeps ticking after the answer",
     "file": "tv/control_ui.html",
     "find": "      return await _sessionsJson();\n    } finally {\n      clearInterval(tick);\n",
     "replace": "      return await _sessionsJson();\n    } finally {\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
