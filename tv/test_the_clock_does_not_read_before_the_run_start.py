# -*- coding: utf-8 -*-
"""REG-2162 (#252) - the T+ clock does not read a wall time before the run start.

Session 175 showed T+0:03.704 beside a wall time six seconds before the run
start. The film axis can open on a pre-roll frame. _clockSay floors a known
start: a wall before it prints as the start at T+0:00.000. A missing wall
stays UNKNOWN and does not borrow the start. A measured moment at the start
still prints. A missing start is not invented.

Drives the shipped function, cut from control_ui.html and run in node.
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


def _say(cases):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    src = _src()
    js = (
        "%s\nconsole.log(JSON.stringify(%s.map(function(c){"
        " return _clockSay(c[0], c[1], c[2]); })));\n"
    ) % (
        _fn(src, "_clockSay(wallTs, origin, runStart){"),
        json.dumps(cases),
    )
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("_clockSay did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheClockDoesNotReadBeforeTheRunStart(unittest.TestCase):

    def test_a_wall_before_the_start_prints_as_the_start_and_a_missing_wall_does_not_borrow_it(self):
        start = 1750000000000
        origin = start - 10000
        # 3.704s into a film whose origin is 10s before the run, so the wall is still early
        early_wall = origin + 3704
        at_start, early, later, missing, no_start, null_wall = _say([
            [start, start, start],
            [early_wall, origin, start],
            [start + 3704, start, start],
            [0, origin, start],
            [early_wall, origin, None],
            [None, origin, start],
        ])
        self.assertEqual(early, at_start)
        self.assertTrue(early.startswith("T+0:00.000 · "), early)
        self.assertNotIn("UNKNOWN", early)
        self.assertTrue(later.startswith("T+0:03.704 · "), later)
        self.assertNotEqual(later, early)
        self.assertEqual(missing, "T+UNKNOWN · —")
        self.assertEqual(null_wall, "T+UNKNOWN · —")
        self.assertNotEqual(missing, at_start)
        # no known start: the early wall is printed, T+ stays on the film origin
        self.assertTrue(no_start.startswith("T+0:03.704 · "), no_start)
        self.assertNotEqual(no_start, early)

    def test_a_pre_roll_origin_does_not_jump_T_plus_at_the_start(self):
        # #96 — the film axis opens 10s before the run start (a pre-roll frame), so origin < start AND
        # the wall is AT/AFTER the start. The old law only tested origin==start, so it was blind to the
        # jump: at HEAD T+ read 0:00 on the pre-roll frame then 0:10 the instant the run began. T+ must
        # be measured from the run start and climb from 0 there.
        start = 1750000000000
        origin = start - 10000
        at_start, after = _say([
            [start, origin, start],
            [start + 5000, origin, start],
        ])
        self.assertTrue(at_start.startswith("T+0:00.000 · "), at_start)
        self.assertTrue(after.startswith("T+0:05.000 · "), after)

    def test_the_theatre_clock_asks_the_one_sentence(self):
        s = _src()
        self.assertEqual(s.count("function _clockSay(wallTs, origin, runStart){"), 1)
        self.assertEqual(s.count("_clockSay("), 2,
                         "thClock must ask _clockSay, and nobody else copies it")
        self.assertIn("el.textContent = _clockSay(wallTs, origin, meta.t0) + modeTag;", s,
                      "the T+ clock went back to printing the playhead wall raw")


RED_PROOF = [
    {
        "why": "REG-2162 - a wall time before the run start is printed on the T+ clock",
        "file": "tv/control_ui.html",
        "find": "    if (start > 0 && shown < start){\n      shown = start;\n      relFrom = start;\n    }\n",
        "replace": "    if (false && start > 0 && shown < start){\n      shown = start;\n      relFrom = start;\n    }\n",
        "matches": 1,
    },
    {
        "why": "REG-2162 - the theatre clock stops asking _clockSay and prints the raw wall",
        "file": "tv/control_ui.html",
        "find": "    el.textContent = _clockSay(wallTs, origin, meta.t0) + modeTag;\n",
        "replace": "    el.textContent = 'T+0:03.704 · ' + new Date(wallTs).toLocaleTimeString() + modeTag;\n",
        "matches": 1,
    },
    {
        "why": "#96 (REG-2162 returns) - a pre-roll film origin jumps T+ by the pre-roll length at the start",
        "file": "tv/control_ui.html",
        "find": "    var relFrom = (start > 0) ? start : ((org > 0) ? org : wall);\n",
        "replace": "    var relFrom = (org > 0) ? org : wall;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
