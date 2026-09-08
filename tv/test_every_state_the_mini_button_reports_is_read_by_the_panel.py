#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2802 — THE SERVER GREW A THIRD STATE AND THE PANEL STILL HAD TWO.

v2801 fixed a real defect: `/api/mini_auto` ran a full-screen lattice scan on the HTTP request
thread, so the POST hung with zero bytes for 8-25s and the button looked dead. The fix moved the
scan to a thread and answered immediately with **`planning: true, running: false`**.

⚠⚠ AND THAT MADE IT WORSE, because `control_ui.html` reads `j.running` and nothing else:

    _miniPaint(j)                      -> j.running false  -> paints the IDLE label
    _miniWatch(!!(j && j.running))     -> false            -> the 900ms poller never starts

So the outcome the plan thread computed — "the newest frame is 3124s old", the exact sentence
v2798 was written to surface — was never fetched by anything. Measured on the shipped bytes:
**`grep -c planning control_ui.html` = 0.** The button now promised "this panel updates" and then
did not update. A silent failure is bad; a failure that makes a claim is worse.

★ NO GATE CAUGHT IT. Two new laws shipped in the same commit — one behavioural, one AST — and both
were about the SERVER. `test_the_screen_read_never_blocks_the_button` proves the handler does not
block, which was true and insufficient: it asserts the sender sends, never that the receiver reads.
That is [[the-unjoined-end]] in its purest form, and it was found by a cross-family review of the
pushed diff rather than by anything in this tree.

THE LAW IS THE GENERAL SHAPE, NOT THIS ONE FIELD. Every state key the mini_auto routes put on the
wire must appear in the panel that renders them. A law naming `planning` alone would be a patch for
one field and would sit silent for the fourth state, exactly as the two-state panel sat silent for
the third.

⚠ It PARSES control_app.py rather than grepping it — the keys are read out of the AST of the actual
`self._json(...)` calls in the mini_auto branches, so a renamed field cannot slip past a string
match. [[source-reading-guard]]
"""
import os
import ast
import io
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

APP = os.path.join(HERE, "control_app.py")
UI = os.path.join(HERE, "control_ui.html")

# Keys that are plumbing, not state the panel is expected to render.
IGNORE = {"ok"}


def _src(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def _mini_auto_response_keys():
    """Every field name the /api/mini_auto handlers put on the wire. -> set[str]"""
    tree = ast.parse(_src(APP))
    keys = set()
    # ⚠⚠ SCOPE IT TO THE BRANCH, NOT THE HANDLER. The first cut walked all of do_GET/do_POST —
    # which dispatch EVERY route in the console — and harvested 91 keys from `/api/status`,
    # `/api/river`, `/api/update` and the rest, then reported eleven of them as unread by the mini
    # panel. Every one of those was correct and irrelevant: `unparsed` and `rowMeta` have no
    # business in this button. A law that fails for reasons unrelated to its subject is a law
    # nobody can act on, and it would have been switched off within a week.
    # The dispatch here is a chain of `if path == "/api/mini_auto":`, so the branch is an ast.If
    # whose test compares against that literal — walk THAT, and nothing else.
    # [[feedback-suspect-the-instrument]] [[sabotage-is-usually-the-wrong-one]]
    branches = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        t = n.test
        if not (isinstance(t, ast.Compare) and len(t.ops) == 1
                and isinstance(t.ops[0], ast.Eq)):
            continue
        left_is_path = isinstance(t.left, ast.Name) and t.left.id == "path"
        rhs = t.comparators[0]
        if left_is_path and isinstance(rhs, ast.Constant) and rhs.value == "/api/mini_auto":
            branches.append(n)
    if not branches:
        return set()
    for br in branches:
        for n in ast.walk(br):
            if isinstance(n, ast.Call):
                f = n.func
                is_json = isinstance(f, ast.Attribute) and f.attr == "_json"
                is_dict = isinstance(f, ast.Name) and f.id == "dict"
                if is_json or is_dict:
                    for kw in n.keywords:
                        if kw.arg:
                            keys.add(kw.arg)
                    for a in n.args:
                        if isinstance(a, ast.Dict):
                            for k in a.keys:
                                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                    keys.add(k.value)
            # _st["planning"] = True  — the GET half assembles its answer by subscript
            if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
               and n.value.id == "_st" and isinstance(n.slice, ast.Constant) \
               and isinstance(n.slice.value, str):
                keys.add(n.slice.value)
    return keys - IGNORE


class TestEveryMiniStateIsRead(unittest.TestCase):

    def setUp(self):
        self.keys = _mini_auto_response_keys()
        self.ui = _src(UI)

    def test_the_key_extraction_actually_found_the_handlers(self):
        """THE INSTRUMENT FIRST. An empty key set would make every assertion below pass over
        nothing, which is the failure mode this whole file exists to name."""
        self.assertTrue(self.keys,
                        "no mini_auto response keys were extracted — this law measures nothing")
        for expect in ("planning", "running", "why"):
            self.assertIn(expect, self.keys,
                          "%r is on the wire but the extractor did not find it — the parser is "
                          "wrong, and a wrong parser here reads as a clean bill of health"
                          % expect)
        print("\n   mini_auto wire keys (%d): %s" % (len(self.keys), sorted(self.keys)))

    def test_every_state_on_the_wire_is_read_by_the_panel(self):
        missing = sorted(k for k in self.keys if k not in self.ui)
        self.assertEqual(
            missing, [],
            "the mini_auto route reports these and control_ui.html never reads them, so the "
            "panel cannot render a state the server is in: %s\n"
            "This is how v2801 shipped a button that answered instantly and still showed nothing."
            % ", ".join(missing))

    def test_the_poller_survives_the_planning_window(self):
        """`planning` merely APPEARING is not enough — it has to keep the 900ms poll alive, or the
        plan's outcome is computed and never fetched."""
        self.assertNotIn(
            "_miniWatch(!!(j && j.running))", self.ui,
            "the watcher is still armed on `running` alone, so it stops during the plan — the "
            "exact window it exists to report on")
        self.assertIn(
            "j.running || j.planning", self.ui,
            "nothing arms the poller on a plan in flight")

    def test_the_panel_paints_planning_as_its_own_state(self):
        """Reading the field is not rendering it. A panel that polls and paints the idle label is
        the same silence with more network traffic."""
        self.assertIn("if (j.planning){", self.ui,
                      "_miniPaint has no branch for a plan in flight, so it falls through to the "
                      "idle label while the console is working")


if __name__ == "__main__":
    unittest.main(verbosity=2)
