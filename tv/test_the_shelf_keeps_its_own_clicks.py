# -*- coding: utf-8 -*-
"""#86 + #87 (GrokBot's Shelf / Fleet passes) - THE SHELF KEEPS ITS OWN CLICKS, AND THE RAIL KEEPS ITS OWN WHEEL.

#86: a click on the Shelf's ACTIVITY chart closed the Shelf - any click that was not on a card was "click-outside",
and the chart, the shelf's head and its live strip are inside the shelf. #87: a wheel at the end of the console rail
scrolled the page behind it.

Read from tv/control_ui.html, comments dropped, by full expressions that exist once: the shelf's click handler asks
for the chart, head and live strip BEFORE its click-outside dismiss; the .rail rule contains its overscroll.
RED_PROOF below.
"""
import io
import os
import re
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

with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as _fh:
    UI = _fh.read()

KEEP = ("      if (e.target.closest && (e.target.closest('.sh-timeline') || e.target.closest('.sh-head') "
        "|| e.target.closest('.sh-live'))) return;\n")
# REG-2708 - only the backdrop dismisses now (test_only_the_shelf_backdrop_dismisses_it drives it); the named blocks are still
# asked first
DISMISS = "      if (!c){ if (e.target === ov || (e.target.classList && e.target.classList.contains('sh-grid'))) _shDismiss(); return; }"


class TheShelfKeepsItsOwnClicks(unittest.TestCase):

    def test_a_click_inside_the_shelf_is_not_a_click_outside(self):
        self.assertEqual(UI.count(KEEP), 1, "the shelf no longer keeps a click on its chart, head or live strip (#86)")
        self.assertEqual(UI.count(DISMISS), 1, "PREMISE: the click-outside dismiss moved")
        self.assertLess(UI.index(KEEP), UI.index(DISMISS), "the chart is asked AFTER the click-outside dismiss")

    def test_the_rail_contains_its_wheel(self):
        css = re.sub(r"/\*.{0,4000}?\*/", "", UI, flags=re.S)
        m = re.search(r"\n  \.rail \{([^}]*)\}", css)
        self.assertIsNotNone(m, "PREMISE: the .rail rule is gone")
        self.assertIn("overscroll-behavior: contain;", m.group(1), "a wheel at the rail's end scrolls the page (#87)")


RED_PROOF = [
    {"why": "#86 - a click on the ACTIVITY chart closes the Shelf again",
     "file": "tv/control_ui.html",
     "find": "      if (e.target.closest && (e.target.closest('.sh-timeline') || e.target.closest('.sh-head') || e.target.closest('.sh-live'))) return;\n",
     "replace": "", "matches": 1},
    {"why": "#87 - the rail lets its wheel through to the page again",
     "file": "tv/control_ui.html",
     "find": "    overscroll-behavior: contain;   /* #87 (GrokBot) - a wheel at the rail's end no longer scrolls the page behind it */\n",
     "replace": "", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
