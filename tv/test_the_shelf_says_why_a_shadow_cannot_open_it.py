# -*- coding: utf-8 -*-
"""REG-2700 (#86/#218, GrokBot's v3816 pass, 2026-10-28) - THE SHELF SAYS WHY A SHADOW CANNOT OPEN IT.

GrokBot, Mac viewing the ALT: clicking THE SHELF "did nothing visible: the theatre stayed hidden and there was no toast".
In a shadow the owner's board fills the shell and the button opened THIS PC's theatre underneath it - a silent door, and
the wrong PC's reels besides. Their reels stay on their PC (his 2026-10-07 ruling), so while any shadow is up the button
says so and opens nothing; with no shadow it opens exactly as before.

Drives the SHIPPED _consoleShadowUp and _shelfShadowRefusal, cut from control_ui.html and run in node; and reads that the
button asks the refusal before it opens anything. RED_PROOF below.
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
UP = ("  function _consoleShadowUp(){\n", "\n  }\n")
REFUSE = ("  function _shelfShadowRefusal(){\n", "\n    return null;\n  }\n")
CLICK = "  if (_bshelf) _bshelf.onclick = async function(){\n"


def _src():
    with open(UI, encoding="utf-8") as fh:
        return fh.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start.strip()[:40], s.count(start)))
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j + len(end)]


def _run():
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var CLASSES = [];
var document = { body: { classList: { contains: function(c){ return CLASSES.indexOf(c) >= 0; } } } };
var window = {};
%s
window._consoleShadowUp = _consoleShadowUp;
%s
var out = {};
[[], ['shell-open'], ['shadow-on'], ['shadow-hub'], ['shadow-snap']].forEach(function(c){
  CLASSES = c; out[c.join('+') || 'none'] = _shelfShadowRefusal();
});
console.log(JSON.stringify(out));
""" % (_cut(s, UP), _cut(s, REFUSE))
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut functions did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheShelfSaysWhyAShadowCannotOpenIt(unittest.TestCase):

    def test_a_shadow_refuses_in_words_and_no_shadow_opens(self):
        o = _run()
        self.assertIsNone(o["none"], "with no shadow the Shelf was refused: %r" % o)
        self.assertIsNone(o["shell-open"], "an open board (no shadow) refused the Shelf")
        for c in ("shadow-on", "shadow-hub", "shadow-snap"):
            self.assertTrue(o[c], "in a shadow (%s) the Shelf said nothing - a silent door (GrokBot v3816)" % c)
            self.assertIn("their reels stay on their PC", o[c])

    def test_the_button_asks_before_it_opens_anything(self):
        s = _src()
        self.assertEqual(s.count(CLICK), 1, "PREMISE: the Shelf button's handler moved")
        i = s.index(CLICK) + len(CLICK)
        head = s[i:s.index("\n  };\n", i)]
        ask = head.find("    var _shR = _shelfShadowRefusal();\n")
        self.assertGreaterEqual(ask, 0, "the Shelf button no longer asks whether a shadow is up")
        self.assertIn("    if (_shR) { try { toast(_shR, 6000); } catch (eT) {} return; }", head)
        opens = head.find("thOpen(")
        self.assertTrue(opens < 0 or ask < opens, "the Shelf opens this PC's theatre before it asks about the shadow")


RED_PROOF = [
    {"why": "REG-2700 - in a shadow the Shelf opens this PC's theatre under the board again, silently",
     "file": "tv/control_ui.html",
     "find": "      if (typeof window._consoleShadowUp === 'function' && window._consoleShadowUp())\n",
     "replace": "      if (false)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2700 - the Shelf button stops asking about the shadow",
     "file": "tv/control_ui.html",
     "find": "    var _shR = _shelfShadowRefusal();\n",
     "replace": "    var _shR = null;\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
