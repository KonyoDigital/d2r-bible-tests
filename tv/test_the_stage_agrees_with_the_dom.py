# -*- coding: utf-8 -*-
"""3,090 CARDS BUILT, THE CONSOLE CALLING ITSELF PAINTED, AND HE WAS LOOKING AT BLACK.

Konyo, 2026-09-07: *"shelf still obivously your on it right? its not rendering"*, then
*"connect it to the heart of the console too"*.

MEASURED on his live console at that moment via /api/status:

    shelf   {"open": true, "filled": true, "cards": 3090, "why": null}
    theatre {"open": true, "loaded": true, "painted": true, "ink": true, "why": null}
    hidden true · painting false · frozenBeats 8 · blankStrikes 0

⚠⚠ THE SHELF DOOR HAD ALREADY BEEN HARDENED THREE TIMES FOR THIS EXACT COMPLAINT:
    v2446  the swallowed shelf   -> catch a rejected thOpen
    v2451  the door toggles      -> clicking again must get him out
    v2666  "hidden === false IS NOT 'he can see it'" -> prove from the RECT and the CONTENT
Each moved one step closer and every one stayed on the same side of the glass. `painted` and `ink`
in the beat are computed from rects, styles and text — **DOM measurements wearing pixel names**. So
the single failure mode that leaves him staring at nothing is the one all of them call success.

AND THE PIXEL WITNESSES MISSED IT TOO: `paint_witness.look()` reads the WHOLE window and said
PAINTED, correctly — header, rail and footer were lit, only the room was dead. `region_witness` at
its shipped 3x2 could not see it either, because each cell is ~373x330 over a 1120x660 window and
therefore catches a lit edge. Measured on that dead window: 3x2 -> 0 blank · 4x3 -> 0 · 6x4 -> 0 ·
**8x5 -> 2** · 10x6 -> 7. That is why GRID is 8x5 and not a rounder number.

⇒ Neither side is evidence alone. **The finding is the disagreement.**
[[feedback-contradiction-is-the-finding]] [[feedback-verify-not-proxy]]
"""
import ast
import io
import re
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import stage_witness as SW  # noqa: E402

SRC = io.open(os.path.join(HERE, "stage_witness.py"), encoding="utf-8").read()


def _code_only(src):
    """The module with its DOCSTRINGS and comments removed.

    ⚠⚠ THIS EXISTS BECAUSE THE LAW BELOW FAILED ON ITS OWN SUBJECT'S PROSE. `stage_witness`'s
    docstring says, correctly, "No relaunch, no repair, no click. `/api/relaunch` under a window he
    is using is what produced the original sighting" — and a bare `assertNotIn("/api/relaunch",
    SRC)` matched THAT SENTENCE and reported the module as reaching for the endpoint it explicitly
    refuses to touch. A guard that greps prose grades prose, and this is the third time in one
    session. [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
    """
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None) or []
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body[0].value.value = ""
    stripped = ast.unparse(tree) if hasattr(ast, "unparse") else src
    return re.sub(r"(?m)#[^\n]*", "", stripped)


def _row():
    return dict(D.CHECKS)["stage shows the dom"]()


def _dom(theatre=None, shelf=None, **kw):
    d = {"hidden": True, "painting": False, "frozenBeats": 8, "blankStrikes": 0,
         "theatre": theatre, "shelf": shelf}
    d.update(kw)
    return d


class TheStageAgreesWithTheDom(unittest.TestCase):

    def test_the_row_is_registered(self):
        """⚠ Defined and unregistered runs never — this repo's smallest, most repeated defect."""
        self.assertIn("stage shows the dom", dict(D.CHECKS))

    # ── ⚠⚠ THE LAW: the disagreement is the finding ───────────────────────────────────────────
    def test_dom_says_painted_but_the_room_is_blank_is_a_FINDING(self):
        real_d, real_p = SW.dom_claim, SW.pixel_claim
        # ⚠⚠ v2881 — THE CONSOLE'S PID IS A THIRD SOURCE, AND IT WAS NEVER STUBBED.
        # `verdict()` looks the console's pid up BEFORE it calls pixel_claim, and
        # returns UNKNOWN — "the console's pid could not be found, so nothing was
        # looked at" — when there is none. On his Mac his console is running, so the
        # lookup succeeded and these laws graded the agreement logic. On a CI runner
        # there is no console at all, so every one of them returned UNKNOWN before the
        # stubbed claims were ever reached: 'ok' != 'unknown', 'missing' != 'unknown'.
        # A law that stubs two of three inputs is still measuring the machine.
        # [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
        real_pid = SW._console_pid
        SW._console_pid = lambda *a, **k: 424242   # never used: pixel_claim is stubbed
        SW.dom_claim = lambda *a, **k: (_dom(
            theatre={"open": True, "loaded": True, "painted": True, "ink": True},
            shelf={"open": True, "filled": True, "cards": 3090}), "")
        SW.pixel_claim = lambda *a, **k: ({"roomCells": 25, "blank": 2, "blankAt": [(1, 4), (2, 4)],
                                           "cols": 8, "rows": 5}, "")
        try:
            v = SW.verdict(pid="1")
            self.assertEqual("CONTRADICTION", v.get("state"),
                             "the console claiming 3,090 painted cards over a blank room was not "
                             "graded as a contradiction")
            st, say = _row()
            self.assertEqual(D.MISSING, st, "the heart did not flag it: %s" % say)
            self.assertIn("stale composite", say,
                          "the message does not name the mechanism, so it is not actionable")
        finally:
            SW.dom_claim, SW.pixel_claim = real_d, real_p
            SW._console_pid = real_pid

    def test_agreement_is_OK(self):
        """The other direction. A row that can only go red is as useless as one that can only be
        green, and this one must stay quiet on a healthy console."""
        real_d, real_p = SW.dom_claim, SW.pixel_claim
        # ⚠⚠ v2881 — THE CONSOLE'S PID IS A THIRD SOURCE, AND IT WAS NEVER STUBBED.
        # `verdict()` looks the console's pid up BEFORE it calls pixel_claim, and
        # returns UNKNOWN — "the console's pid could not be found, so nothing was
        # looked at" — when there is none. On his Mac his console is running, so the
        # lookup succeeded and these laws graded the agreement logic. On a CI runner
        # there is no console at all, so every one of them returned UNKNOWN before the
        # stubbed claims were ever reached: 'ok' != 'unknown', 'missing' != 'unknown'.
        # A law that stubs two of three inputs is still measuring the machine.
        # [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
        real_pid = SW._console_pid
        SW._console_pid = lambda *a, **k: 424242   # never used: pixel_claim is stubbed
        SW.dom_claim = lambda *a, **k: (_dom(shelf={"open": True, "filled": True, "cards": 12}), "")
        SW.pixel_claim = lambda *a, **k: ({"roomCells": 25, "blank": 0, "blankAt": [],
                                           "cols": 8, "rows": 5}, "")
        try:
            st, say = _row()
            self.assertEqual(D.OK, st, "a healthy room was graded as a fault: %s" % say)
        finally:
            SW.dom_claim, SW.pixel_claim = real_d, real_p
            SW._console_pid = real_pid

    # ── ⚠ IT MUST NOT CRY WOLF ────────────────────────────────────────────────────────────────
    def test_a_dark_room_with_NOTHING_OPEN_is_not_a_fault(self):
        """He is on the homepage most of the time. A row that reds whenever no theatre is open
        gets ignored within a week, and an ignored row is a switched-off one."""
        real_d = SW.dom_claim
        SW.dom_claim = lambda *a, **k: (_dom(theatre={"open": False}, shelf={"open": False}), "")
        try:
            v = SW.verdict(pid="1")
            self.assertEqual("AGREE", v.get("state"),
                             "a closed theatre with a dark room was graded a fault")
            st, _ = _row()
            self.assertEqual(D.OK, st)
        finally:
            SW.dom_claim = real_d

    def test_ONE_blank_cell_is_not_a_region(self):
        """A single quiet corner of a sparse panel is not a dead room. His real fault produced
        exactly 2 at 8x5, so the floor is the one his own fault clears."""
        real_d, real_p = SW.dom_claim, SW.pixel_claim
        # ⚠⚠ v2881 — THE CONSOLE'S PID IS A THIRD SOURCE, AND IT WAS NEVER STUBBED.
        # `verdict()` looks the console's pid up BEFORE it calls pixel_claim, and
        # returns UNKNOWN — "the console's pid could not be found, so nothing was
        # looked at" — when there is none. On his Mac his console is running, so the
        # lookup succeeded and these laws graded the agreement logic. On a CI runner
        # there is no console at all, so every one of them returned UNKNOWN before the
        # stubbed claims were ever reached: 'ok' != 'unknown', 'missing' != 'unknown'.
        # A law that stubs two of three inputs is still measuring the machine.
        # [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
        real_pid = SW._console_pid
        SW._console_pid = lambda *a, **k: 424242   # never used: pixel_claim is stubbed
        SW.dom_claim = lambda *a, **k: (_dom(shelf={"open": True, "cards": 9}), "")
        SW.pixel_claim = lambda *a, **k: ({"roomCells": 25, "blank": 1, "blankAt": [(0, 0)],
                                           "cols": 8, "rows": 5}, "")
        try:
            self.assertEqual("AGREE", SW.verdict(pid="1").get("state"))
        finally:
            SW.dom_claim, SW.pixel_claim = real_d, real_p
            SW._console_pid = real_pid

    # ── ⚠⚠ UNKNOWN IS NEVER COLLAPSED ─────────────────────────────────────────────────────────
    def test_an_unlookable_window_is_UNKNOWN_not_OK(self):
        """⚠ THE STATE HIS MACHINE WAS ACTUALLY IN while this was written: window_for answered
        'pid owns no on-screen window big enough to be his console, which is not the same as a
        blank one'. An unlookable window is neither painted nor blank."""
        real_d, real_p = SW.dom_claim, SW.pixel_claim
        # ⚠⚠ v2881 — THE CONSOLE'S PID IS A THIRD SOURCE, AND IT WAS NEVER STUBBED.
        # `verdict()` looks the console's pid up BEFORE it calls pixel_claim, and
        # returns UNKNOWN — "the console's pid could not be found, so nothing was
        # looked at" — when there is none. On his Mac his console is running, so the
        # lookup succeeded and these laws graded the agreement logic. On a CI runner
        # there is no console at all, so every one of them returned UNKNOWN before the
        # stubbed claims were ever reached: 'ok' != 'unknown', 'missing' != 'unknown'.
        # A law that stubs two of three inputs is still measuring the machine.
        # [[feedback-blind-fixture-green-gate]] [[feedback-fixtures-never-touch-live-data]]
        real_pid = SW._console_pid
        SW._console_pid = lambda *a, **k: 424242   # never used: pixel_claim is stubbed
        SW.dom_claim = lambda *a, **k: (_dom(shelf={"open": True, "cards": 3090}), "")
        SW.pixel_claim = lambda *a, **k: (None, "simulated: no window")
        try:
            v = SW.verdict(pid="1")
            self.assertEqual("UNKNOWN", v.get("state"))
            st, say = _row()
            self.assertEqual(D.UNKNOWN, st, "an unlookable window was graded: %s" % say)
        finally:
            SW.dom_claim, SW.pixel_claim = real_d, real_p
            SW._console_pid = real_pid

    def test_a_silent_console_is_UNKNOWN_not_OK(self):
        real_d = SW.dom_claim
        SW.dom_claim = lambda *a, **k: (None, "simulated: no answer")
        try:
            st, _ = _row()
            self.assertEqual(D.UNKNOWN, st, "a console that never answered was graded")
        finally:
            SW.dom_claim = real_d

    # ── the instrument must stay able to SEE ──────────────────────────────────────────────────
    def test_the_grid_is_fine_enough_to_see_a_dead_room(self):
        """⚠ THE TUNABLE THAT WOULD SILENTLY RE-BLIND THIS. Measured on his dead window:
        3x2 -> 0 blank, 4x3 -> 0, 6x4 -> 0, 8x5 -> 2. Dropping back toward the shipped 3x2 makes
        every cell catch a lit edge and the row can never fire again."""
        self.assertGreaterEqual(SW.GRID_COLS, 8,
                                "the grid coarsened to %d columns; at 6x4 his real dead room "
                                "produced ZERO blank cells" % SW.GRID_COLS)
        self.assertGreaterEqual(SW.GRID_ROWS, 5, "the grid coarsened to %d rows" % SW.GRID_ROWS)
        self.assertLess(SW.RAIL_FROM_COL, SW.GRID_COLS,
                        "the rail cutoff excludes every column, so no room cell is ever measured")

    # ── ⛔ IT READS AND NEVER ACTS ─────────────────────────────────────────────────────────────
    def test_it_never_relaunches_repairs_or_clicks(self):
        """/api/relaunch under a window he is using is what produced the original sighting."""
        tree = ast.parse(SRC)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                self.assertNotIn(nm, ("relaunch", "repair", "click", "restart"),
                                 "the stage witness calls %s() — it must only read" % nm)
        code = _code_only(SRC)
        for bad in ("/api/relaunch", "/api/repair", "vault_apply", "chronicle_apply"):
            self.assertNotIn(bad, code,
                             "the stage witness reaches for %s in CODE; it must only read" % bad)
        # ⚠ and prove the stripper actually stripped, or this law grades an empty string
        self.assertIn("def verdict(", code, "the code-only view lost the module's functions")
        self.assertNotIn("what produced the original sighting", code,
                         "the docstring survived the strip, so this law is still reading prose")

    def test_it_still_parses(self):
        ast.parse(SRC)



RED_PROOF = [
    {
        'why': 'losing the CONTRADICTION branch makes a blank room grade as merely UNKNOWN, so the row stops being able to report a fault at all',
        'file': 'console_doctor.py',
        'find': 'if st == "CONTRADICTION":',
        'replace': 'if st == "_HEART2_TAMPERED_":',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
