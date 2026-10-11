# -*- coding: utf-8 -*-
"""REG-2174 (#236) - a short shelf does not hide BEST RUN / STREAK to show a reel.

The highlight row is built above the cards. The opening scroll used to put the
first card near the top, which carried that row off a short shelf. _shOpenScroll
moves only as far as the card needs when any of the row still meets the
viewport. A row that would leave entirely keeps the old head scroll, so the
reel stays on screen. No row keeps that head scroll. A card already in view
does not move.

Drives the shipped function, cut from control_ui.html and run in node.
The count disagreement on the same task is not this law.
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


def _src():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _fn(src, name):
    needle = "function %s" % name
    start = src.find(needle)
    if start < 0:
        raise AssertionError("%s is gone" % name)
    if src.find(needle, start + 1) != -1:
        raise AssertionError("%s is declared more than once" % name)
    i = src.find("{", start)
    depth = 0
    for j in range(i, len(src)):
        ch = src[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    raise AssertionError("%s never closed" % name)


def _scroll(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    src = _src()
    js = (
        "%s\nconsole.log(JSON.stringify(%s.map(function(c){"
        " return _shOpenScroll(c[0], c[1], c[2], c[3]); })));\n"
    ) % (
        _fn(src, "_shOpenScroll(top, ovH, hiTop, hiBot){"),
        json.dumps(cases),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_shOpenScroll did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class AShortShelfKeepsTheHighlightRow(unittest.TestCase):

    def test_a_row_that_still_meets_the_viewport_is_not_scrolled_away(self):
        # measured furniture: highlight 197..371, card at 708, viewport 660.
        # the old head scroll was 708 - round(660*0.18) = 589, which hid the row.
        measured, short, partial = _scroll([
            [708, 660, 197, 371],
            [420, 390, 20, 190],
            [400, 390, 10, 180],
        ])
        self.assertEqual(measured, 49)
        self.assertNotEqual(measured, 589)
        self.assertEqual(short, 31)
        self.assertNotEqual(short, 350)
        self.assertEqual(partial, 11)
        self.assertLess(partial, 70)

    def test_a_card_already_in_view_does_not_move_and_a_gone_row_keeps_the_head(self):
        visible, unlaid, bare, gone = _scroll([
            [200, 660, 10, 180],
            [708, 0, 197, 371],
            [708, 660, None, None],
            [1200, 400, 50, 220],
        ])
        self.assertIsNone(visible)
        self.assertIsNone(unlaid)
        self.assertEqual(bare, 589)
        self.assertEqual(gone, 1128)
        self.assertNotEqual(gone, 801)

    def test_the_opening_scroll_asks_the_one_function(self):
        s = _src()
        self.assertEqual(s.count("function _shOpenScroll(top, ovH, hiTop, hiBot){"), 1)
        self.assertEqual(s.count("_shOpenScroll("), 2,
                         "the below-fold branch must ask _shOpenScroll, and nobody else copies it")
        self.assertIn("var _to = _shOpenScroll(_top, _ovH, _hiTop, _hiBot);", s)
        self.assertIn("if (_ovH > 0 && _top >= _ovH){", s)


RED_PROOF = [
    {
        "why": "REG-2174 - a short shelf goes back to the head scroll and hides the highlight row",
        "file": "tv/control_ui.html",
        "find": "        if (visible > 0) return minScroll;\n",
        "replace": "        if (false) return minScroll;\n",
        "matches": 1,
    },
    {
        "why": "REG-2174 - the opening scroll stops asking _shOpenScroll and jumps to the head",
        "file": "tv/control_ui.html",
        "find": "          var _to = _shOpenScroll(_top, _ovH, _hiTop, _hiBot);\n          if (_to != null) ov.scrollTop = _to;\n",
        "replace": "          ov.scrollTop = Math.max(0, _top - Math.round(_ovH * 0.18));\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
