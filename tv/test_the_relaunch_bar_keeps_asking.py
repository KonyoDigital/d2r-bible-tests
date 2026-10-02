# -*- coding: utf-8 -*-
"""#150 - THE RELAUNCH BAR ASKS THE CONSOLE, KEEPS WATCHING, AND THE CONSOLE WRITES DOWN WHY IT WAITED.

His words, 2026-10-01: "still busy after 20 minutes? should i just hit relaunch? why didnt it auto relaunch itself".
MEASURED: the update bar's waiter (control_ui.html _updWaitForRead) waited while /api/chronicle_sweep said "running" and
only THEN asked /api/relaunch, and it stopped for good at ~20 minutes. His sweep read for 3 h 45 min; the console stops
counting a sweep past its 45-minute ceiling (control_app.log said so every 15 minutes), but the bar never asked it. And
the console's own reason for holding the relaunch lived only in memory, so his relaunch erased it.

What this law drives:
  * the REAL waiter function, cut from control_ui.html and run in node with a fake fetch and a fake timer:
      - it asks /api/relaunch while a sweep is still reading, and relaunches when the console says ok
      - a refusal shows the console's own reason
      - past ~20 minutes it keeps watching (one ask every 30 s) and never stops itself
  * control_app._drift_publish_relaunch writes one log line per CHANGE of decision, none per repeat
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
START = "    var _updWaitTimer = null;\n"
END = "      _updWaitTimer = setInterval(tick, 2500);\n    }\n"


def _waiter_src():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    assert ui.count(START) == 1 and ui.count(END) == 1, "the waiter's bounds moved"
    i = ui.index(START)
    return ui[i:ui.index(END, i) + len(END)]


HARNESS = r"""
var LOG = [], RELAUNCH_ANSWERS = %(answers)s, SWEEP = %(sweep)s, TICKS = %(ticks)d;
function el(){ return {hidden: true, textContent: '', disabled: false, style: {},
  classList: {add: function(){}, toggle: function(){}}, querySelector: function(){ return el(); }}; }
var ELS = {'fleet-eta': el(), 'fleet-eta-say': el()};
function $(id){ return ELS[id] || null; }
var txt = el(), go = el(), API = '';
var _interval = null, _cleared = 0;
function setInterval(fn){ _interval = fn; return 1; }
function clearInterval(){ _cleared += 1; _interval = null; }
var _posts = 0, _sweepAsks = 0;
async function fetch(url, opts){
  if (String(url).indexOf('/api/chronicle_sweep') >= 0) { _sweepAsks += 1;
    return {json: async function(){ return SWEEP; }}; }
  if (String(url).indexOf('/api/relaunch') >= 0) { _posts += 1;
    var a = RELAUNCH_ANSWERS[Math.min(_posts - 1, RELAUNCH_ANSWERS.length - 1)];
    return {json: async function(){ return a; }}; }
  throw new Error('unexpected ' + url);
}
%(src)s
(async function(){
  _updWaitForRead();
  var first = _interval;
  await new Promise(function(r){ setTimeout(r, 0); });
  for (var i = 0; i < TICKS && _interval; i++) { await _interval(); }
  console.log(JSON.stringify({posts: _posts, sweepAsks: _sweepAsks, cleared: _cleared, running: !!_interval,
                              txt: txt.textContent, tries: _updWaitTries}));
})();
"""


@unittest.skipIf(NODE is None, "node is absent - the waiter cannot be driven here, which is UNMEASURED, not passing")
class TheBarAsksTheConsole(unittest.TestCase):

    def run_waiter(self, answers, sweep, ticks):
        d = tempfile.mkdtemp(prefix="relaunch_bar_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "h.js")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(HARNESS % {"answers": json.dumps(answers), "sweep": json.dumps(sweep), "ticks": ticks,
                                "src": _waiter_src()})
        r = subprocess.run([NODE, p], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_it_asks_while_a_sweep_is_still_reading_and_relaunches_when_allowed(self):
        busy = {"ok": False, "busy": True, "why": "a chronicle sweep is reading"}
        out = self.run_waiter([busy, busy, {"ok": True}], {"running": True, "eta": {"pct": 40, "say": "reading"}}, 10)
        self.assertGreaterEqual(out["posts"], 3, "the bar never asked the console while the sweep was still reading")
        self.assertFalse(out["running"], "the console said ok and the bar kept waiting")
        self.assertEqual(out["cleared"], 1)

    def test_a_refusal_shows_the_consoles_own_reason(self):
        why = "only the shadow reader's reel is rolling - an update would be held"
        out = self.run_waiter([{"ok": False, "busy": True, "why": why}], {"running": False}, 3)
        self.assertIn(why, out["txt"])
        self.assertTrue(out["running"])

    def test_past_twenty_minutes_it_keeps_watching_and_never_stops_itself(self):
        busy = {"ok": False, "busy": True, "why": "a chronicle sweep is reading"}
        out = self.run_waiter([busy], {"running": True, "eta": {}}, 600)
        self.assertTrue(out["running"], "the bar stopped watching - he is left to relaunch by hand: %r" % out)
        self.assertEqual(out["cleared"], 0)
        self.assertIn("still watching", out["txt"])
        # REG-1708 (the v3553 eye) - "between 481 and 491" also passed a waiter that asked ONCE after try 480 and never
        # again. Every 12th try past 480 asks, so 600 ticks ask exactly 480 + the multiples of 12 in 481..600.
        want = 480 + len([t for t in range(481, 601) if t % 12 == 0])
        self.assertEqual(out["posts"], want, "past 20 minutes it must ask once every 30 s (every 12th tick): %r" % out)


class TheConsoleWritesDownWhy(unittest.TestCase):

    def test_one_line_per_change_of_decision(self):
        import control_app as ca
        saved = dict(ca._RELAUNCH_SAID)
        self.addCleanup(lambda: (ca._RELAUNCH_SAID.clear(), ca._RELAUNCH_SAID.update(saved)))
        ca._RELAUNCH_SAID["key"] = None
        buf = io.StringIO()
        with redirect_stdout(buf):
            ca._drift_publish_relaunch(False, "a chronicle sweep is reading", "work")
            ca._drift_publish_relaunch(False, "a chronicle sweep is reading", "work")
            ca._drift_publish_relaunch(False, "only the shadow reader's reel is rolling", "shadow")
            ca._drift_publish_relaunch(True, "nothing in flight", "clear")
        lines = [l for l in buf.getvalue().splitlines() if "relaunch" in l]
        self.assertEqual(len(lines), 3, lines)
        self.assertIn("HELD (work)", lines[0])
        self.assertIn("HELD (shadow)", lines[1])
        self.assertIn("MAY FIRE", lines[2])


RED_PROOF = [
    {
        "why": "REG-1708 - past 20 minutes the bar asks once and then never again",
        "file": "control_ui.html",
        "find": "          if (_slow && (_updWaitTries % 12)) return;   // past it: one ask every 30 s, never a stop\n",
        "replace": "          if (_slow && _updWaitTries > 481) return;\n",
        "matches": 1,
    },
    {
        "why": "#150 - the bar stops for good at 20 minutes again",
        "file": "control_ui.html",
        "find": "          if (_slow && (_updWaitTries % 12)) return;   // past it: one ask every 30 s, never a stop\n",
        "replace": "          if (_slow) { _updWaitStop('still busy after 20 minutes'); return; }\n",
        "matches": 1,
    },
    {
        "why": "#150 - the bar waits for the sweep to stop before it ever asks the console",
        "file": "control_ui.html",
        "find": "          var e = (st && st.eta) || {};\n          var rr = await fetch(API + '/api/relaunch', { method: 'POST' });\n",
        "replace": "          var e = (st && st.eta) || {};\n          if (st && st.running) return;\n          var rr = await fetch(API + '/api/relaunch', { method: 'POST' });\n",
        "matches": 1,
    },
    {
        "why": "#150 - a refusal stops naming the console's reason",
        "file": "control_ui.html",
        "find": "            txt.textContent = 'not now — ' + (rj.why || 'something is still running')\n",
        "replace": "            txt.textContent = 'not now'\n",
        "matches": 1,
    },
    {
        "why": "#150 - the console's reason for holding a relaunch is never written down",
        "file": "control_app.py",
        "find": "    if _key != _RELAUNCH_SAID.get(\"key\"):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
