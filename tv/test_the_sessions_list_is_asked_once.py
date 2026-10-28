# -*- coding: utf-8 -*-
"""GrokBot's v3817 pass - THE CONSOLE ASKS FOR THE SESSIONS LIST ONCE AT A TIME.

Opening the Shelf sent the theatre's bounded wait (thSessionsWait) and the Shelf's own refresh (thShelf) at the same moment:
a second /api/sessions request at 3.0 s while the first was still pending, five in 30 s, ~270 KB each - on a Mac already
slow enough to need REG-2698's 45 s wait. Every caller (the theatre's wait, the Shelf, the Sessions hub) now shares the
request in flight (_sessionsJson); it is bounded where it is sent (_sessionsFetchOnce, TH_SESSIONS_BOUND_MS), and once it
settles - answered or failed - the next caller asks afresh. Driven in node on the shipped functions. RED_PROOF below.
"""
import json
import os
import re
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
A = "  var _sessFlight = null;\n"
B = "  window._sessionsJson = _sessionsJson;\n"


def _ui():
    with open(UI, encoding="utf-8") as fh:
        return fh.read()


def _block(s):
    assert s.count(A) == 1 and s.count(B) == 1, "the shared fetch is not where this law cuts it"
    i = s.index(A)
    return s[i:s.index(B, i) + len(B)]


@unittest.skipIf(NODE is None, "node is not on this machine - UNMEASURED here, not passing")
class TheSessionsListIsAskedOnce(unittest.TestCase):

    def run_js(self, body):
        js = ("var window = {}, API = '', TH_SESSIONS_BOUND_MS = 45000, CALLS = 0, PENDING = [];\n"
              "function AbortController(){ this.signal = {}; this.abort = function(){}; }\n"
              "function fetch(url){ CALLS++; return new Promise(function(res, rej){ PENDING.push({ ok: function(v){ "
              "res({ json: function(){ return Promise.resolve(v); } }); }, bad: rej }); }); }\n"
              + _block(_ui()) + "\nvar OUT = {};\n(async function(){\n" + body
              + "\n})().then(function(){ process.stdout.write(JSON.stringify(OUT)); }, function(e){ process.stderr.write(String(e)); process.exit(3); });")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise AssertionError("the shipped shared fetch would not run in node: %s" % r.stderr[-500:])
        return json.loads(r.stdout)

    def test_two_callers_at_once_share_one_request_and_the_next_asks_afresh(self):
        o = self.run_js("""
var a = _sessionsJson(), b = _sessionsJson();
OUT.callsWhilePending = CALLS; OUT.same = (a === b);
PENDING[0].ok({ sessions: [1, 2] });
var ja = await a, jb = await b; OUT.both = [ja.sessions.length, jb.sessions.length];
await new Promise(function(r){ setTimeout(r, 0); });
var c = _sessionsJson(); OUT.callsAfter = CALLS; PENDING[1].ok({ sessions: [] }); await c;""")
        self.assertEqual((o["callsWhilePending"], o["same"]), (1, True), "two callers sent two requests: %r" % o)
        self.assertEqual(o["both"], [2, 2])
        self.assertEqual(o["callsAfter"], 2, "a caller after the request settled was handed a stale answer")

    def test_a_failed_request_is_not_kept_for_the_next_caller(self):
        o = self.run_js("""
var a = _sessionsJson();
PENDING[0].bad(new Error('down'));
try { await a; OUT.threw = false; } catch (e) { OUT.threw = true; }
await new Promise(function(r){ setTimeout(r, 0); });
var b = _sessionsJson(); OUT.calls = CALLS; PENDING[1].ok({ sessions: [1] }); OUT.n = (await b).sessions.length;""")
        self.assertTrue(o["threw"], "a failed request was answered as if it worked")
        self.assertEqual((o["calls"], o["n"]), (2, 1), "a failed request was kept and served to the next caller")

    def test_every_caller_asks_the_shared_request_and_none_fetches_on_its_own(self):
        s = _ui()
        code = "\n".join(l for l in s.split("\n") if not l.strip().startswith(("/*", "*", "//")))
        own = re.findall(r"fetch\((?:API \+ )?'/api/sessions'", code)
        self.assertEqual(len(own), 1, "a caller fetches /api/sessions on its own again: %d sites" % len(own))
        self.assertIn("      return await _sessionsJson();\n", s, "the theatre's wait does not share the request")
        self.assertIn("    window._sessionsJson().then(function(j){", s, "the Shelf's refresh does not share the request")
        self.assertIn("      var j = await window._sessionsJson();", s, "the Sessions hub does not share the request")


RED_PROOF = [
    {"why": "GrokBot v3817 - every caller sends its own /api/sessions request again",
     "file": "tv/control_ui.html",
     "find": "    if (!_sessFlight) {\n",
     "replace": "    if (true) {\n",
     "matches": 1, "needs": "node"},
    {"why": "GrokBot v3817 - a settled (or failed) request is served to every later caller",
     "file": "tv/control_ui.html",
     "find": "      var done = function(){ if (_sessFlight === p) _sessFlight = null; };\n",
     "replace": "      var done = function(){};\n",
     "matches": 1, "needs": "node"},
    {"why": "GrokBot v3817 - the Shelf's refresh fetches on its own beside the theatre's wait",
     "file": "tv/control_ui.html",
     "find": "    window._sessionsJson().then(function(j){   /* GrokBot v3817 - the theatre's wait and this share one request */\n",
     "replace": "    fetch('/api/sessions').then(function(r){ return r.json(); }).then(function(j){\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
