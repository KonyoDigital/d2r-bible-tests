# -*- coding: utf-8 -*-
"""#215 + #214 (GrokBot) - THE SHADOW BAR SITS BELOW THE HEADER, AND THE SHADOW SPEAKS ONE CLOCK.

#215: on the Mac and the ALT the shadow bar sat over the header's tab row (bar top ~66 px, topbar ~100 px).
_shadowSnapEnter measured the header BEFORE shell-open fixed the topbar with its extra padding, and nothing moved the bar
after. #214: the snapshot time was 12-hour AM/PM beside the header's 24-hour clock; "live" sat beside "uploaded 20 min
ago"; the dimming rule for shadow controls left labels (Load profile) out.

Driven: _shadowPlace (cut from control_ui.html) in node places the bar at the header height and the frame below the
bar; _shellSizePane calls it and _shadowSnapEnter calls it again once the shell is open; the snapshot time expression
(cut from _shadowSnapEnter) prints HH:MM with no AM/PM; the view says "online now · last upload"; labels are dimmed.
RED_PROOF below.
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


def _read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


UI = _read(os.path.join(HERE, "control_ui.html"))
BIBLE = _read(os.path.join(os.path.dirname(HERE), "bible.html"))


def _cut(src, start, end):
    assert src.count(start) == 1, start[:60]
    i = src.index(start)
    return src[i:src.index(end, i) + len(end)]


class TheShadowBarSitsBelowTheHeader(unittest.TestCase):

    def _node(self, js):
        if not NODE:
            raise AssertionError("node is absent - this law cannot run here, so it is UNMEASURED")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_bar_and_the_frame_are_placed_from_the_header(self):
        fn = _cut(UI, "  function _shadowPlace(h){\n", "      sf.style.height = 'calc(100vh - ' + below + 'px)';\n    }\n  }\n")
        js = ("var bar = { hidden: false, offsetHeight: 30, style: {} }, sf = { style: {} };\n"
              "var document = { getElementById: function (id) { return id === 'shadow-bar' ? bar : (id === 'shadow-eng' ? sf : null); } };\n"
              + fn + "\n_shadowPlace(100);\n"
              "console.log(JSON.stringify({ bar: bar.style.top, top: sf.style.top, h: sf.style.height }));\n")
        out = self._node(js)
        self.assertEqual(out, {"bar": "100px", "top": "130px", "h": "calc(100vh - 130px)"}, out)

    def test_it_is_placed_on_every_sizing_and_after_the_shell_opens(self):
        size = _cut(UI, "  function _shellSizePane(){\n", "    _shadowPlace(h);   /* #215 */\n  }\n")
        self.assertIn("_shadowPlace(h);", size, "sizing the shell pane no longer places the shadow bar")
        self.assertEqual(UI.count("    try { window._shadowPlace(window._shellHeadH()); } catch (ePl) {}"), 1,
                         "the shadow is not placed again once the shell is open")
        i = UI.index("    document.body.classList.add('shell-open', 'shadow-on', 'shadow-snap');")
        self.assertLess(i, UI.index("    try { window._shadowPlace(window._shellHeadH()); } catch (ePl) {}"),
                        "the bar is placed before shell-open changes the header's height")

    def test_one_clock_and_honest_words(self):
        line = _cut(UI, "    try { if (typeof d.t === 'number' && d.t > 0) { var _sd = new Date(d.t)",
                    "} } catch (e) { at = '';")
        out = self._node("var d = { t: Date.UTC(2026, 9, 27, 20, 7) }, at = '';\n" + line + " }\n"
                         "console.log(JSON.stringify({ at: at }));\n")
        self.assertRegex(out["at"], r"^ · snapshot \S+ \d{1,2} \d\d:\d\d$", out)
        self.assertIsNone(re.search(r"AM|PM", out["at"]), out)
        import console_snapshot as CS
        rec = None
        self.assertIn('"%s · online now · last upload %s"', _read(os.path.join(HERE, "console_snapshot.py")))
        del rec, CS
        self.assertEqual(BIBLE.count(":is(button, input, select, textarea, label, [contenteditable], .vault-chip)"), 1,
                         "a label (Load profile) is not dimmed in the shadow")


RED_PROOF = [
    {"why": "#215 - sizing the shell no longer places the shadow bar, so it sits over the header again",
     "file": "tv/control_ui.html",
     "find": "    _shadowPlace(h);   /* #215 */\n",
     "replace": "", "matches": 1},
    {"why": "#215 - the frame stops below the bar's real height",
     "file": "tv/control_ui.html",
     "find": "      var below = h + ((bar && !bar.hidden && bar.offsetHeight) || 34);\n      sf.style.top",
     "replace": "      var below = h;\n      sf.style.top", "matches": 1, "needs": "node"},
    {"why": "#214 - the snapshot time is 12-hour AM/PM again",
     "file": "tv/control_ui.html",
     "find": "' ' + _p2(_sd.getHours()) + ':' + _p2(_sd.getMinutes()); } }",
     "replace": "' ' + _sd.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }); } }",
     "matches": 1, "needs": "node"},
    {"why": "#214 - Load profile is not dimmed in the shadow again",
     "file": "bible.html",
     "find": ":is(button, input, select, textarea, label, [contenteditable], .vault-chip)",
     "replace": ":is(button, input, select, textarea, [contenteditable], .vault-chip)", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
