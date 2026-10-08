# -*- coding: utf-8 -*-
"""#142 (REG-2043) - ONLY A PRIMARY PRESS ON A TAB LABEL SWITCHES ROOMS.

GrokBot on #230, 2026-10-08, console v3621 (the eight checks): "one right-click on TV·D then switched to TV·D". #142's
fix (leave on the PRESS, so the first click outside the focused board iframe is not spent blurring it) listened to
pointerdown for every button, so a right press - and a Mac ctrl-click, which is a right-click arriving as button 0 -
moved him. Drives the SHIPPED _headTabGo, cut from control_ui.html and run in node with the rooms stubbed. A missing
node raises; this law does not skip.
"""
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

from cb_node_harness import NODE  # noqa: E402

START = "  function _headTabGo(e){\n"
END = "\n  if (_ht) {\n    _ht.addEventListener('pointerdown', _headTabGo);"


def _fn_src():
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as f:
        ui = f.read()
    if ui.count(START) != 1 or ui.count(END) != 1:
        raise AssertionError("_headTabGo's anchors moved (start %d, end %d) - re-point this law"
                             % (ui.count(START), ui.count(END)))
    i = ui.index(START)
    return ui[i:ui.index(END, i)]


def _run(events):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = """
var CALLS = [];
var document = { body: { removeAttribute: function(){}, classList: { contains: function(){ return false; } } },
                 getElementById: function(){ return null; } };
var window = {};
var _shellTab = 'session';
function shellHome(){ CALLS.push('tvd'); }
function showSessions(){ CALLS.push('session'); }
function shellOpen(t){ CALLS.push(t); }
%s
var EV = %s, OUT = [], TABS = {};
EV.forEach(function(ev){
  var tab = TABS[ev.tab] = TABS[ev.tab] || { dataset: { tab: ev.tab } };   // one element per label, as in the page
  var e = { type: ev.type, button: ev.button, ctrlKey: !!ev.ctrl, timeStamp: ev.t || 0,
            target: { closest: function(){ return tab; } },
            preventDefault: function(){}, stopPropagation: function(){} };
  var before = CALLS.length;
  _headTabGo(e);
  OUT.push(CALLS.slice(before));
});
console.log(JSON.stringify(OUT));
""" % (_fn_src(), json.dumps(events))
    # the program goes in on STDIN - a law never hands node its program on argv (test_no_law_hands_node_its_program_on_argv)
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut function did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ARightClickOnATabDoesNotSwitchRooms(unittest.TestCase):

    def test_a_right_press_does_not_switch(self):
        self.assertEqual(_run([{"type": "pointerdown", "button": 2, "tab": "tvd"}]), [[]],
                         "a right press on TV·D switched rooms")

    def test_a_mac_ctrl_click_does_not_switch(self):
        self.assertEqual(_run([{"type": "pointerdown", "button": 0, "ctrl": True, "tab": "tvd"}]), [[]])

    def test_a_middle_press_does_not_switch(self):
        self.assertEqual(_run([{"type": "pointerdown", "button": 1, "tab": "vault"}]), [[]])

    def test_a_primary_press_still_switches_once(self):
        out = _run([{"type": "pointerdown", "button": 0, "tab": "tvd", "t": 100},
                    {"type": "click", "button": 0, "tab": "tvd", "t": 180}])
        self.assertEqual(out, [["tvd"], []], "the primary press must move once and its click must not move again")


RED_PROOF = [
    {"why": "REG-2043 - a right-click on a tab label switches rooms again",
     "file": "control_ui.html",
     "find": "    if (e.type === 'pointerdown' && (e.button !== 0 || e.ctrlKey)) return;",
     "replace": "    if (false) return;",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
