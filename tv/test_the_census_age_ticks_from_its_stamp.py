# -*- coding: utf-8 -*-
"""#284 (REG-2073) - THE HEART'S "census taken N ago" TICKS FROM THE MOMENT ITS ANSWER LANDED; IT NEVER FREEZES.

GrokBot ticks 418, 422 and 423 on #230 (K16/K17): "census taken 14 s ago" read the same for 26 s and longer. The age
arrived right - ageMs at the moment of the answer - and was painted ONCE; a settled panel asks nothing more, so the number
froze at the value it rendered. The line now keeps the moment its answer landed and adds the time since, every second
while the panel is open. [[stale-reading]]

Drives the SHIPPED _hrtAgo, _hrtStatusLine and _hrtAgeTick, cut from control_ui.html and run in node over a fake panel and
a fake clock. A missing node raises; this law does not skip.
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
CUTS = [("  function _hrtAgo(ms){\n", "\n  }\n"),
        ("  function _hrtStatusLine(d, sinceMs){\n", "    return line;\n  }\n"),
        ("  function _hrtAgeTick(){\n", "\n  }\n")]
ARM = "    if (!_hrtAgeT) _hrtAgeT = setInterval(_hrtAgeTick, 1000);\n"
STAMP = "    el.__hrtD = d; el.__hrtAt = Date.now();"


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start.strip()[:40], s.count(start)))
    i = s.index(start)
    fn = s[i:s.index(end, i) + len(end)]
    if fn.count("{") != fn.count("}"):
        raise AssertionError("the cut %r is not a whole function - its end anchor stopped inside it" % start.strip()[:40])
    return fn


def _run(d, steps_ms):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var window = {}, NOW = 1000000, _hrtAgeT = 1;
var Date = { now: function(){ return NOW; } };
function clearInterval(){}
var EL = { textContent: '', __hrtD: null, __hrtAt: 0 };
var OV = { hidden: false, querySelector: function(q){ return q === '#hrt-age' ? EL : null; } };
var document = { getElementById: function(id){ return id === 'heart-ov' ? OV : null; } };
%s
var D = %s;
EL.__hrtD = D; EL.__hrtAt = NOW; EL.textContent = _hrtStatusLine(D, 0);
var OUT = [EL.textContent];
%s.forEach(function(ms){ NOW += ms; _hrtAgeTick(); OUT.push(EL.textContent); });
console.log(JSON.stringify(OUT));
""" % ("\n".join(_cut(s, c) for c in CUTS), json.dumps(d), json.dumps(steps_ms))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheCensusAgeTicksFromItsStamp(unittest.TestCase):

    def test_the_age_advances_with_the_clock(self):
        out = _run({"ok": True, "ageMs": 14000}, [1000, 11000, 60000])
        self.assertEqual(out[0], "census taken 14 s ago")
        self.assertEqual(out[1], "census taken 15 s ago", "the age did not move after a second: %r" % out)
        self.assertEqual(out[2], "census taken 26 s ago", "the age froze at the value it rendered: %r" % out)
        self.assertEqual(out[3], "census taken 86 s ago", out)

    def test_an_unknown_age_stays_unknown_while_it_ticks(self):
        out = _run({"ok": True, "ageMs": None}, [5000])
        self.assertEqual(out, ["census taken at an unknown time"] * 2, "an unknown age was given a number: %r" % out)

    def test_the_status_line_stamps_and_arms_the_tick(self):
        s = _src()
        self.assertEqual(s.count(STAMP), 1, "the status line no longer keeps the moment its answer landed")
        self.assertEqual(s.count(ARM), 1, "nothing ticks the census age while the panel is open")


RED_PROOF = [
    {"why": "REG-2073 - the census age is painted once and freezes again (the time since it landed is dropped)",
     "file": "tv/control_ui.html",
     "find": "_hrtAgo(d.ageMs + Math.max(0, sinceMs || 0))",
     "replace": "_hrtAgo(d.ageMs)",
     "matches": 1},
    {"why": "REG-2073 - nothing ticks the age while the panel is open",
     "file": "tv/control_ui.html",
     "find": "    if (!_hrtAgeT) _hrtAgeT = setInterval(_hrtAgeTick, 1000);\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
