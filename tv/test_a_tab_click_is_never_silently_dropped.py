# -*- coding: utf-8 -*-
"""REG-1946 - A HEADER-TAB CLICK THAT CANNOT OPEN ITS PANE YET SAYS SO, AND KEEPS TRYING LONG ENOUGH.

GrokBot (#230 tick 377, v3601, his live console on a 93%-busy machine): the first Vault click lit the tab while the TV.D
body stayed, and only a SECOND click opened it; tick 378 the Vault painted ~6 s after one click. shellOpen routed the
board iframe with switchTab and retried 50 x 80 ms = 4 s, then stopped without a word - and switchTab no-ops while the
board is still building its panes, which on that machine takes longer than 4 s.

The law drives the REAL shellOpen (lifted from tv/control_ui.html) against a board that answers late, never, or after
he went elsewhere: a board that moves at 9.6 s still opens (the old 4 s gave up); a board that never moves ends at 20 s
with a toast and one ui_fault; the tab is marked opening while it waits and unmarked after; leaving for another tab
stops the retry silently.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

START = "  function shellOpen(tab){"


def _lift():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        src = fh.read()
    i = src.find(START)
    if i < 0:
        return None
    j = src.find("\n  }\n", i)
    return src[i:j + 4] if j > i else None


HARNESS = r"""
var cfg = %s;
var out = {toasts: [], faults: [], ticks: 0, openingDuring: null};
function Cls(){ var s = {}; return {add: function(c){ s[c] = 1; }, remove: function(c){ delete s[c]; },
                                    contains: function(c){ return !!s[c]; }}; }
var btn = {classList: Cls()};
var document = {getElementById: function(id){ return id === 'tvd-eng' ? {} : null; },
                querySelector: function(){ return btn; }, body: {classList: Cls()}};
var _shellTab = 'tvd', _shellRouteTimer = null;
function _glide(){} function _shellSizePane(){} function _shellLight(){}
var calls = 0;
function _shellRoute(){ calls++; return cfg.okAt > 0 && calls >= cfg.okAt; }
function toast(m){ out.toasts.push(m); }
function fetch(u, o){ out.faults.push(JSON.parse(o.body).kind); return {then: function(){ return this; }}; }
var q = null;
function setInterval(fn){ q = fn; return 7; }
function clearInterval(id){ if (id === 7) q = null; }
%s
shellOpen('vault');
out.openingDuring = btn.classList.contains('ht-opening');
while (q && out.ticks < 2000) {
  if (cfg.leaveAt && out.ticks === cfg.leaveAt) _shellTab = 'session';
  q(); out.ticks++;
}
out.openingAfter = btn.classList.contains('ht-opening');
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ATabClickIsNeverSilentlyDropped(unittest.TestCase):

    def drive(self, ok_at=0, leave_at=0):
        fn = _lift()
        self.assertIsNotNone(fn, "shellOpen is gone from tv/control_ui.html")
        js = HARNESS % (json.dumps({"okAt": ok_at, "leaveAt": leave_at}), fn)
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, "the shipped shellOpen would not run: %s" % p.stderr[-800:])
        return json.loads(p.stdout)

    def test_a_board_that_moves_after_four_seconds_still_opens(self):
        out = self.drive(ok_at=121)          # the first call is shellOpen's own; 120 retries x 80 ms = 9.6 s
        self.assertEqual(out["toasts"], [], "a board that moved at 9.6 s was given up on (REG-1946): %s" % out)
        self.assertEqual(out["ticks"], 120, "the retry did not run until the board moved: %s" % out)
        self.assertFalse(out["openingAfter"], "the tab still says it is opening after the pane opened")

    def test_the_tab_says_it_is_opening_while_it_waits(self):
        self.assertTrue(self.drive(ok_at=30)["openingDuring"], "the first click left no mark that anything is happening")

    def test_a_board_that_never_moves_says_so_at_twenty_seconds(self):
        out = self.drive(ok_at=0)
        self.assertEqual(out["ticks"], 251, "the give-up is not at 20 s: %s" % out["ticks"])
        self.assertEqual(len(out["toasts"]), 1, "a route that gave up said nothing on screen")
        self.assertIn("did not open vault", out["toasts"][0])
        self.assertEqual(out["faults"], ["shell-route-gave-up"], "the give-up was not recorded")
        self.assertFalse(out["openingAfter"])

    def test_leaving_for_another_tab_stops_quietly(self):
        out = self.drive(ok_at=0, leave_at=10)
        self.assertEqual((out["toasts"], out["faults"]), ([], []), "a retry he walked away from still complained")
        self.assertLessEqual(out["ticks"], 12)
        self.assertFalse(out["openingAfter"])


RED_PROOF = [
    {
        "why": "REG-1946 - the retry gives up at 4 s again: a board that moves at 9.6 s never opens and the click is dead",
        "file": "tv/control_ui.html",
        "find": "      if (n > 250) {",
        "replace": "      if (n > 50) {",
        "matches": 1,
    },
    {
        "why": "REG-1946 - a route that gave up says nothing again",
        "file": "tv/control_ui.html",
        "find": "        try { toast('The board did not open ' + tab + ' in 20 s - it may still be loading. Click the tab again.'); } catch (_t) {}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1946 - the first click leaves no mark while the pane is still opening",
        "file": "tv/control_ui.html",
        "find": "if (_btn) _btn.classList.add('ht-opening'); } catch (_b) {}",
        "replace": "} catch (_b) {}",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
