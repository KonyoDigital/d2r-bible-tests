# -*- coding: utf-8 -*-
"""#41 rank 14 (2026-09-29) — THE console-tabs RENDER GATE CLICKS EVERY BOARD DOOR THE CONSOLE HEADER OFFERS, AND A
COLLAPSED PANE BEHIND ANY OF THEM TURNS IT RED.

The heart audit (#256, ranked 26 gaps) found render_check.py's console-tabs target still routing SIX tabs
(forge, crafts, funi, fsets, tools, vault) after v3518 gave the console header a 👤 Characters door: no gate clicked
that door in a real browser and checked that #tab-chars PAINTS in app context. The Characters law asserts the app-ctx
re-show list by source text, so a pixel-only defect (the pane collapsed or hidden) was uncaught, and the target's own
why still said "Six tabs".

WHAT THIS LAW DRIVES: the target's REAL `activate` program - render_check.TARGETS["console-tabs"]["activate"], the very
string Chrome evaluates - run in node over a stub console + board (the console's #head-tabs buttons, the board iframe's
.tab.active and #tab-<name> panes with rects), never a re-typed copy of it:
  · on a fully painted board it returns true, and the board doors it CLICKED are exactly the doors control_ui.html's
    #head-tabs offers minus the console-native pair (session, tvd) - derived from the real header, so a door added to
    the console and not to ROUTING goes red here without a browser;
  · the runnable sabotage: with #tab-chars collapsed to 0x0 (what a CSS rule hiding the pane in app context does) it
    returns false; and as a BASELINE the same collapse on #tab-vault (routed since v2092) returns false too, so the
    stub is proven to carry a collapse at all;
  · the target's why counts what ROUTING counts ("Seven tabs" for seven), so the label cannot outlive the list.
⚠ WHAT IT CANNOT SEE: pixels. Whether the real #tab-chars paints on his console is the gate's own job, on Chrome, on
GitHub (browser suites never run on his Mac - [[test-venue]]); this proves the gate would notice if it did not.
RED_PROOF below: every sabotage turns this law red for its own reason.
"""
import json
import os
import re
import shutil
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

import render_check as RC  # noqa: E402

NODE = shutil.which("node")
NATIVE = ("session", "tvd")
WORDS = {5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}

STUB = r"""
var DOORS = __DOORS__, NATIVE = { session: 1, tvd: 1 }, COLLAPSED = __COLLAPSED__;
var ACTIVE = 'session', CLICKED = [], DEMOTED = false;
function rect(t){
  if (COLLAPSED[t]) return { left: 0, top: 0, width: 0, height: 0 };
  if (t === 'vault' && DEMOTED) return { left: 0, top: 0, width: 0, height: 122 };   /* showSessions() demotes the pane */
  return { left: 0, top: 0, width: 1384, height: 600 };
}
var boardDoc = {
  querySelector: function(sel){ return sel === '.tab.active' ? { getAttribute: function(k){ return k === 'data-tab' ? ACTIVE : null; } } : null; },
  getElementById: function(id){ if (String(id).indexOf('tab-') !== 0) return null; var t = String(id).slice(4);
    if (DOORS.indexOf(t) < 0 || NATIVE[t]) return null; return { getBoundingClientRect: function(){ return rect(t); } }; }
};
var document = {
  body: { dataset: {} },
  getElementById: function(id){ return id === 'tvd-eng' ? { contentWindow: { document: boardDoc } } : null; },
  querySelector: function(sel){ var m = /^#head-tabs \.ht\[data-tab="([a-z]+)"\]$/.exec(sel); if (!m) return null; var t = m[1];
    if (DOORS.indexOf(t) < 0) return null;
    return { click: function(){ CLICKED.push(t); document.body.dataset.shellTab = t; if (NATIVE[t]) DEMOTED = true; else { ACTIVE = t; DEMOTED = false; } } }; },
  querySelectorAll: function(sel){ if (sel !== '#head-tabs .ht') return [];
    return DOORS.map(function(t){ return { querySelectorAll: function(){ return [{ getBoundingClientRect: function(){ return { width: 20, height: 20 }; } }]; } }; }); }
};
function getComputedStyle(){ return { display: 'block', visibility: 'visible' }; }
var RESULT = null, ERR = null;
try { RESULT = eval(__ACTIVATE__); } catch (e) { ERR = String(e && e.stack || e); }
process.stdout.write(JSON.stringify({ result: RESULT, err: ERR, clicked: CLICKED }));
"""


def _doors():
    """the console header's doors, in order, from the real control_ui.html #head-tabs"""
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    i = ui.index('id="head-tabs"')
    nav = ui[i:ui.index("</nav>", i)]
    return re.findall(r'<button class="ht[^"]*"[^>]*data-tab="([a-z]+)"', nav)


def _drive(collapsed=()):
    spec = RC.TARGETS["console-tabs"]
    prog = (STUB.replace("__DOORS__", json.dumps(_doors())).replace("__COLLAPSED__", json.dumps(dict((c, 1) for c in collapsed)))
            .replace("__ACTIVATE__", json.dumps(spec["activate"])))
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-1500:])
    out = json.loads(r.stdout)
    if out["err"]:
        raise AssertionError("the target's activate threw over the stub: " + out["err"][:600])
    return out


@unittest.skipIf(NODE is None, "node is absent - the gate's activate was not driven; UNMEASURED, not passing")
class TheGateRoutesEveryBoardDoor(unittest.TestCase):

    def test_the_doors_it_clicks_are_the_console_headers_board_doors(self):
        doors = _doors()
        self.assertIn("chars", doors, "BASELINE: the console header offers no Characters door (v3518)")
        board = [d for d in doors if d not in NATIVE]
        self.assertGreaterEqual(len(board), 7, "PRINT THE DENOMINATOR: the header offers %d board doors: %s" % (len(board), board))
        out = _drive()
        self.assertIs(out["result"], True, "a fully painted board did not pass the gate: clicked %s" % out["clicked"])
        seen = []
        for t in out["clicked"]:
            if t not in NATIVE and t not in seen:
                seen.append(t)
        self.assertEqual(sorted(seen), sorted(board),
                         "the gate routes %s, the console header offers %s - a door the gate never clicks is a pane "
                         "nothing proves painted" % (seen, board))
        for n in NATIVE:
            self.assertIn(n, out["clicked"], "the console-native pair was not driven: %s" % out["clicked"])

    def test_a_collapsed_characters_pane_turns_the_gate_red(self):
        """the runnable sabotage - what a CSS rule collapsing #tab-chars in app context does to the gate"""
        base = _drive(collapsed=("vault",))
        self.assertIs(base["result"], False, "BASELINE: a collapsed #tab-vault must fail the gate (the stub carries no collapse)")
        out = _drive(collapsed=("chars",))
        self.assertIs(out["result"], False,
                      "a collapsed #tab-chars PASSES the gate - the Characters door is not routed or its pane is not measured")
        self.assertIn("chars", out["clicked"], "the gate never clicked the Characters door")

    def test_the_targets_why_counts_what_routing_counts(self):
        spec = RC.TARGETS["console-tabs"]
        m = re.search(r'var ROUTING = \[([^\]]*)\];', spec["activate"])
        self.assertIsNotNone(m, "the activate program no longer declares ROUTING as a literal list")
        n = len([x for x in m.group(1).split(",") if x.strip()])
        self.assertEqual(n, len([d for d in _doors() if d not in NATIVE]), "ROUTING holds %d doors, the header %d" % (n, len(_doors()) - 2))
        word = WORDS.get(n)
        self.assertIsNotNone(word, "no word for %d" % n)
        self.assertTrue(spec["why"].startswith(word + " tabs"),
                        "the why says %r while ROUTING holds %d - a label that outlived its list" % (spec["why"][:24], n))


RED_PROOF = [
    {
        "why": "#41 rank 14 - the Characters door leaves ROUTING again (no gate proves #tab-chars paints)",
        "file": "render_check.py",
        "find": '            var ROUTING = ["forge","crafts","funi","fsets","tools","chars","vault"];\n',
        "replace": '            var ROUTING = ["forge","crafts","funi","fsets","tools","vault"];\n',
        "matches": 1,
    },
    {
        "why": "#41 rank 14 - the why says Six tabs over a seven-door list",
        "file": "render_check.py",
        "find": '        "why": ("Seven tabs in the console header ROUTE THE BOARD and must PAINT what they route "\n',
        "replace": '        "why": ("Six tabs in the console header ROUTE THE BOARD and must PAINT what they route "\n',
        "matches": 1,
    },
    {
        "why": "#41 rank 14 - the gate stops measuring the destination pane's rect (a routed tab over a collapsed pane passes)",
        "file": "render_check.py",
        "find": "                var pr = paneRect(t);                                      /* AND it is really there */\n                if (!pr || pr.width <= 2 || pr.height <= 2) return false;\n",
        "replace": "                var pr = paneRect(t);                                      /* AND it is really there */\n                if (!pr) return false;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP - node is not on this machine, so the gate's activate was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
