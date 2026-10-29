# -*- coding: utf-8 -*-
"""#200 + #218 (REG-3035, GrokBot v3836 glass pass, #230 6485132266) - NOTHING SITS UNDER THE SHADOW BAR.

Two looks, one defect class: a box placed from a number while the bar it must clear moved or grew.
  - #200: in the ALT shadow's Sessions tab "the top of the hub (MY HUNT) is scrolled under the shadow bar". Sessions in a
    shadow is this console's own hub with shell-open off (showShadowSessions -> _shellRestoreConsole), so the header is
    back in the page and shorter than the fixed one the bar was last placed under, and nothing placed the bar again: it
    kept the old height, over the hub's top, and the hub kept no room for it.
  - #218 (cosmetic, from #220): at 860 and 700 px the world band's top edge (their frame's top row) tucked under the bar.
    The frame was placed at h + bar.offsetHeight, a rounded number read once; anything that moved or grew the bar after
    that, or a fractional bar height rounded down, left the frame's top under the bar's painted bottom.

Now: in the hub the bar sits on the header's real bottom and the header keeps the bar's height free under itself
(--shadow-bar-h, set by _shadowPlace, read by the rule beside #shadow-bar); their frame starts at the bar's painted bottom
rounded up; and a ResizeObserver on the bar and the header places both again whenever either changes size.

Driven: _shadowPlace and the observer hook cut out of control_ui.html and run in node over a mock DOM; the CSS rule and
the Sessions call sites read from the file. The pixels are CI's and GrokBot's (no Chrome on his Mac). RED_PROOF below.
"""
import io
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
NODE = shutil.which("node")
with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as _fh:
    UI = _fh.read()

PLACE = ("  function _shadowPlace(h){\n", "      sf.style.height = 'calc(100vh - ' + below + 'px)';\n    }\n  }\n")
HOOK = ("  (function () {\n    if (typeof ResizeObserver !== 'function') return;\n", "  })();\n")


def _cut(start, end):
    if UI.count(start) != 1:
        raise AssertionError("%r occurs %d times - this law cannot see its subject" % (start[:60], UI.count(start)))
    i = UI.index(start)
    return UI[i:UI.index(end, i) + len(end)]


HARNESS = r"""
const CFG = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = {};
for (const sc of CFG.scenes) {
  const S = Object.assign({}, sc);
  const classes = new Set(S.classes), vars = {};
  const body = { classList: { contains: (c) => classes.has(c) }, style: { setProperty: (k, v) => { vars[k] = v; } } };
  const bar = { hidden: !!S.hidden, style: {}, offsetHeight: S.barOffsetH,
    getBoundingClientRect: function () { const t = parseFloat(this.style.top || '0') + (S.barShift || 0); return { top: t, bottom: t + S.barRealH }; } };
  const sf = { style: {} };
  const tb = { getBoundingClientRect: () => ({ top: S.tbTop, bottom: S.tbBottom, height: S.tbBottom - S.tbTop }) };
  const document = { body: body, getElementById: (id) => id === 'shadow-bar' ? bar : (id === 'shadow-eng' ? sf : null),
                     querySelector: (q) => q === '.topbar' ? tb : null };
  let roCb = null; const observed = [];
  function ResizeObserver(cb) { roCb = cb; }
  ResizeObserver.prototype.observe = function (el) { observed.push(el === bar ? 'bar' : (el === tb ? 'topbar' : '?')); };
  function _shellHeadH() { return S.headH; }
  const window = {};
  const run = new Function('document', 'window', 'ResizeObserver', '_shellHeadH',
    CFG.code + '\nreturn _shadowPlace;');
  const place = run(document, window, ResizeObserver, _shellHeadH);
  place(S.headH);
  const r = { bar: bar.style.top, frame: sf.style.top, height: sf.style.height, reserve: vars['--shadow-bar-h'], observed: observed };
  if (S.growTo) {
    S.barRealH = S.growTo;
    if (roCb) roCb([]);
    r.frameAfterGrow = sf.style.top;
    r.reserveAfterGrow = vars['--shadow-bar-h'];
  }
  out[S.name] = r;
}
console.log(JSON.stringify(out));
"""

SCENES = [
    # Sessions in a shadow: shell-open off, the header in the page ends at 66 px; the last placement was for the fixed 100 px
    {"name": "hub", "classes": ["shadow-on", "shadow-hub"], "headH": 100, "tbTop": 0, "tbBottom": 66,
     "barOffsetH": 41, "barRealH": 41.4},
    # their board in a frame: the bar is 41.4 px tall, offsetHeight says 41
    {"name": "frame", "classes": ["shell-open", "shadow-on", "shadow-snap"], "headH": 100, "tbTop": 0, "tbBottom": 100,
     "barOffsetH": 41, "barRealH": 41.4},
    # a bar painted 3 px lower than its top says, for any reason: the frame still starts under its painted bottom
    {"name": "lower", "classes": ["shell-open", "shadow-on", "shadow-snap"], "headH": 100, "tbTop": 0, "tbBottom": 100,
     "barOffsetH": 41, "barRealH": 41, "barShift": 3},
    # the bar wraps to a second line after it was placed (a narrower window, new words)
    {"name": "grow", "classes": ["shell-open", "shadow-on", "shadow-snap"], "headH": 100, "tbTop": 0, "tbBottom": 100,
     "barOffsetH": 41, "barRealH": 41, "growTo": 60},
    # no shadow: the reserve is zero
    {"name": "gone", "classes": [], "headH": 100, "tbTop": 0, "tbBottom": 100, "barOffsetH": 0, "barRealH": 0,
     "hidden": True},
]


def _drive():
    if not NODE:
        raise AssertionError("node is not on this machine - this law does not skip")
    code = _cut(*PLACE) + "\n" + _cut(*HOOK)
    r = subprocess.run([NODE, "-"], input=HARNESS.replace("CFG = JSON.parse(require('fs').readFileSync(0, 'utf8'))",
                                                          "CFG = " + json.dumps({"code": code, "scenes": SCENES})),
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed: %s" % r.stderr[-900:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class NothingSitsUnderTheShadowBar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_in_the_hub_the_bar_sits_on_the_header_and_the_header_keeps_its_room(self):
        h = self.o["hub"]
        self.assertEqual(h["bar"], "66px", "in Sessions the bar kept the fixed header's height, over MY HUNT: %r" % h)
        self.assertEqual(h["reserve"], "42px", "the hub keeps no room for the bar: %r" % h)

    def test_their_frame_starts_under_the_bars_painted_bottom(self):
        self.assertEqual(self.o["frame"]["frame"], "142px", "a 41.4 px bar rounded to 41 put the frame under it: %r"
                         % self.o["frame"])
        self.assertEqual(self.o["lower"]["frame"], "144px", "a bar painted lower than placed covered the frame's top: %r"
                         % self.o["lower"])

    def test_a_bar_that_grows_after_it_was_placed_moves_the_frame(self):
        g = self.o["grow"]
        self.assertEqual(g["frame"], "141px")
        self.assertIn("bar", g["observed"], "nothing watches the bar's size")
        self.assertIn("topbar", g["observed"], "nothing watches the header's size")
        self.assertEqual((g["frameAfterGrow"], g["reserveAfterGrow"]), ("160px", "60px"),
                         "the frame stayed placed for the old bar: %r" % g)

    def test_no_shadow_no_reserve(self):
        self.assertEqual(self.o["gone"]["reserve"], "0px")

    def test_the_hub_rule_reads_the_variable_the_placement_sets(self):
        set_names = re.findall(r"document\.body\.style\.setProperty\('(--[\w-]+)'", _cut(*PLACE))
        self.assertEqual(len(set_names), 1, set_names)
        rule = re.findall(r"^\s*body\.shadow-hub:not\(\.shell-open\) \.topbar \{ margin-bottom: var\((--[\w-]+), 0px\); \}$",
                          UI, re.M)
        self.assertEqual(rule, set_names, "the hub's reserve does not read the variable _shadowPlace sets: %r" % rule)

    def test_sessions_in_a_shadow_places_the_bar_once_the_header_is_back(self):
        body = _cut("  function showShadowSessions(){\n", "    _shellPaintAgain(")
        tail = _cut("  function showShadowSessions(){\n", "\n  }\n")
        i_restore = body.rindex("    _shellRestoreConsole();\n")
        self.assertIn("_shadowPlace(_shellHeadH())", body[i_restore:],
                      "Sessions in a shadow restores the in-page header and never places the bar under it")
        again = tail[tail.index("    _shellPaintAgain("):]
        self.assertLess(again.index("_shellRestoreConsole();"), again.find("_shadowPlace(_shellHeadH())"),
                        "the repaint restores the header after the bar was placed, and places nothing after it")


RED_PROOF = [
    {"why": "REG-3035 - in Sessions the bar keeps the fixed header's height, over MY HUNT",
     "file": "tv/control_ui.html",
     "find": "    if (shown && cl && cl.contains('shadow-hub') && !cl.contains('shell-open')) {\n",
     "replace": "    if (false) {\n", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - the placement never says how tall the bar is",
     "file": "tv/control_ui.html",
     "find": "    try { document.body.style.setProperty('--shadow-bar-h', barH + 'px'); } catch (eV) {}\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - the hub keeps no room for the bar",
     "file": "tv/control_ui.html",
     "find": "  body.shadow-hub:not(.shell-open) .topbar { margin-bottom: var(--shadow-bar-h, 0px); }\n",
     "replace": "", "matches": 1},
    {"why": "REG-3035 - the frame is placed from the rounded offsetHeight again",
     "file": "tv/control_ui.html",
     "find": "barH = Math.ceil(r.bottom - r.top); barBottom = Math.ceil(r.bottom);",
     "replace": "barH = bar.offsetHeight; barBottom = 0;", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - a bar painted lower than placed covers the frame's top",
     "file": "tv/control_ui.html",
     "find": "      if (barBottom > below) below = barBottom;\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - nothing watches the bar's size",
     "file": "tv/control_ui.html",
     "find": "    ro.observe(bar);\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - a size change places nothing again",
     "file": "tv/control_ui.html",
     "find": "    var ro = new ResizeObserver(function () { try { _shadowPlace(_shellHeadH()); } catch (eRo) {} });\n",
     "replace": "    var ro = new ResizeObserver(function () {});\n", "matches": 1, "needs": "node"},
    {"why": "REG-3035 - Sessions in a shadow never places the bar under the restored header",
     "file": "tv/control_ui.html",
     "find": "    try { _shadowPlace(_shellHeadH()); } catch (ePl) {}   /* REG-3035 - the header is back in the page: the bar goes under it */\n",
     "replace": "", "matches": 1},
    {"why": "REG-3035 - the repaint restores the header and places the bar nowhere after it",
     "file": "tv/control_ui.html",
     "find": "_shellRestoreConsole(); try { _shadowPlace(_shellHeadH()); } catch (ePl2) {} });",
     "replace": "_shellRestoreConsole(); });", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
