# -*- coding: utf-8 -*-
"""#297 (REG-2065) - A TIP FOR A CONTROL INSIDE THE SHELF OVERLAY PAINTS BESIDE THAT CONTROL, NOT BELOW THE OVERLAY.

GrokBot tick 422 on #230 (v3622, K08): the River gallery's top-row tips (⚖ COMPARE, AREAS, the sort box, ☆, TRIAGE / UNKNOWN /
SEAL / RELEASED / "8 RUNS") painted ~400 px below their controls, beside "⋯ more" at the gallery's bottom - and 421 had
reported several of them as having no tip at all. v2452's _clampBelowOverlay pushes any tip whose top is above an open
#th-shelfov's bottom edge to just below it; meant for the TRANSPORT under the overlay (whose tips open upward), it also
caught every control that lives ON the overlay.

  * a control inside #th-shelfov keeps the top its anchor computed;
  * a control outside it (the transport) is still clamped below the overlay;
  * the anchor path hands the control to the clamp.
Drives the SHIPPED _clampBelowOverlay, cut from control_ui.html and run in node. A missing node raises.
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
FN = ("      _clampBelowOverlay: function(top, h, node){\n", "        } catch (e) { return top; }\n      },\n")


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _clamp(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    start, end = FN
    if s.count(start) != 1:
        raise AssertionError("_clampBelowOverlay's anchor matched %d times - re-point this law" % s.count(start))
    i = s.index(start)
    body = s[i:s.index(end, i) + len(end)].rstrip().rstrip(",")
    js = """
var window = { innerHeight: 900 };
var ON = { inside: true }, UNDER = { inside: false };
var OV = { hidden: false, getBoundingClientRect: function(){ return { height: 700, bottom: 700 }; },
           contains: function(n){ return !!(n && n.inside); } };
var document = { getElementById: function(id){ return id === 'th-shelfov' ? OV : null; } };
var T = { %s };
console.log(JSON.stringify(%s.map(function(c){ return T._clampBelowOverlay(c[0], c[1], c[2] === 'on' ? ON : c[2] === 'under' ? UNDER : undefined); })));
""" % (body, json.dumps(cases))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut method did not run in node: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ATipInsideTheShelfStaysByItsChip(unittest.TestCase):

    def test_a_chip_on_the_overlay_keeps_its_place(self):
        self.assertEqual(_clamp([[120, 40, "on"]]), [120], "a River chip's tip was pushed below the whole overlay")

    def test_the_transport_under_it_is_still_clamped(self):
        self.assertEqual(_clamp([[650, 40, "under"], [650, 40, None]]), [706, 706],
                         "the transport's tip may cross the open shelf again")

    def test_the_anchor_path_hands_the_control_along(self):
        self.assertEqual(_src().count("        el.style.top = this._clampBelowOverlay(y, h, node) + 'px';"), 1,
                         "anchor() no longer tells the clamp which control the tip belongs to")


RED_PROOF = [
    {"why": "REG-2065 - a River chip's tip is pushed ~400 px below the overlay again",
     "file": "control_ui.html",
     "find": "          if (node && ov.contains(node)) return top;\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
