#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3389 (#133) - A COUNT THAT WAS NEVER SYNCED IS NOT A MEASUREMENT.

Konyo, on his new PC's row: *"ok: True with have: 0 - a confident zero - while the mask says the
board has handed over nothing... join it connect it the heart properly just like everything else"*

MEASURED on his live roster (GET /api/fleet, 33,954 bytes, ok=True, fromCache=False, 6 rows),
row "Konyo ALT TEST":
    tally.ok               = True
    tally.sets/uniques/runewords = {"have": 0, "total": 135/403/99}
    tally.ledgerVerdict.ok = False, all three provenance=UNSYNCED
    why: "that board declared a ledger of its own, so the owner's seed never landed - and its own
          store is EMPTY, so nothing has been synced"

THE DEFECT, to the line - and there were TWO COPIES of it, 129 lines apart:
    tv/control_app.py:2241  inside _tally_from_board_store
    tv/control_app.py:2370  inside grail_tally
        out["ok"] = any(out[k] for k in ("sets", "uniques", "runewords"))

`{"have": 0, "total": 135}` is a NON-EMPTY DICT, and a non-empty dict is truthy in Python. So the
test is True whether have is 0 or 135, and regardless of what ledgerVerdict decided six lines
above. `ok` has only ever meant "the row carries ledger KEYS" - both call sites' own `why` strings
prove that intent, since they can fire only when _pair() returned None.

⚠ I FOUND THE SECOND COPY ONLY BY PRINTING THE MATCH COUNT. src.count() said 2 where an exact-line
compare said 1; they differ only by indentation. Patching on a single-match assumption would have
fixed one and left the other making the same claim. [[regression-guard]] 5a [[copy-drift]]

⚠ THE ANSWER WAS ALREADY COMPUTED. ledgerVerdict sits in the same object saying ok:False with
three UNSYNCED provenances, and control_ui.html:24315 already RENDERS those rows. Nothing needed
deriving - the outer claim never consulted it. v3343's scar exactly. [[the-unjoined-end]]

⚠ `ok` KEEPS ITS MEANING. v2815 settled this: two questions get two answers rather than one
redefined field, so a reader on an older build keeps working.

WHAT THIS FILE PINS - behaviour first:
  * his real row: ok stays True, measured is False, and the reason NAMES the ledgers
  * THE BASELINE: a synced, genuinely empty board keeps an honest 0 with measured True
  * no verdict at all -> measured is None, never a cheerful True
  * no ledger keys -> ok False
  * ONE writer: both sites go through the helper, and the old truthiness test is gone
  * the card suppresses the number only on an explicit False, never on absent
"""

import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

import control_app as CA

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _code_only(src):
    """Code with comments AND docstrings gone, line count preserved.

    ⚠ A DOCSTRING IS NOT A COMMENT and stripping "#" does not touch one - this file's own
    docstring quotes the defect it bans. [[source-reading-guard]] 4b
    """
    lines = [l.split("#", 1)[0] for l in src.split("\n")]
    try:
        tree = ast.parse(src)
    except Exception:
        return "\n".join(lines)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not (isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        for i in range(first.lineno - 1, min(getattr(first, "end_lineno", first.lineno), len(lines))):
            lines[i] = ""
    return "\n".join(lines)


UNSYNCED = {"ok": False, "ledgers": [
    {"ledger": "uniques", "store": "d2r_foundLog", "provenance": "UNSYNCED"},
    {"ledger": "sets", "store": "d2r_setPieces", "provenance": "UNSYNCED"},
    {"ledger": "runewords", "store": "d2r_rwMade", "provenance": "UNSYNCED"},
]}


def _row(verdict=None, have=0):
    out = {"sets": {"have": have, "total": 135}, "uniques": {"have": have, "total": 403},
           "runewords": {"have": have, "total": 99}}
    if verdict is not None:
        out["ledgerVerdict"] = verdict
    return out


class ATallySaysWhetherItIsAMeasurement(unittest.TestCase):

    # ---------- behaviour ----------

    def test_his_real_row_is_not_called_a_measurement(self):
        """THE WHOLE POINT, on the shape his console actually published."""
        out = CA._seal_tally_verdict(_row(UNSYNCED), "carried no counts")
        self.assertIs(out["measured"], False,
                      "a board that never synced still reports its zeros as a measurement")
        for led in ("sets", "uniques", "runewords"):
            self.assertIn(led, out["measuredWhy"],
                          "the reason does not name %s, so he cannot tell WHICH ledger is "
                          "unsynced: %r" % (led, out["measuredWhy"]))

    def test_ok_keeps_meaning_the_board_answered(self):
        """An older reader branches on `ok`; redefining it would break every one of them."""
        out = CA._seal_tally_verdict(_row(UNSYNCED), "carried no counts")
        self.assertIs(out["ok"], True,
                      "ok changed meaning - it answers whether the board REPLIED, not whether "
                      "the reply is trustworthy")

    def test_a_synced_and_genuinely_empty_board_keeps_its_honest_zero(self):
        """THE BASELINE, and without it a fix that called EVERY zero unmeasured would pass.
        A new player must be able to report nothing found and be believed."""
        synced = {"ok": True, "ledgers": [{"ledger": "sets", "provenance": "EARNED"}]}
        out = CA._seal_tally_verdict(_row(synced, have=0), "carried no counts")
        self.assertIs(out["measured"], True,
                      "a genuinely synced, genuinely empty board was accused of not measuring")
        self.assertIs(out["ok"], True)

    def test_no_verdict_at_all_is_UNKNOWN_and_never_True(self):
        """grail_tally returns the board-store tally BEFORE the authority is consulted, so this
        path is reached in production and must not default cheerfully. [[unknown-stays-unknown]]"""
        out = CA._seal_tally_verdict(_row(None), "carried no counts")
        self.assertIsNone(out["measured"],
                          "a tally with no verdict claimed %r instead of UNKNOWN"
                          % (out["measured"],))
        self.assertTrue(out["measuredWhy"], "UNKNOWN arrived with no reason attached")

    def test_no_ledger_keys_at_all_is_not_ok(self):
        """The ONE case the old truthiness test answered correctly; it must survive."""
        out = CA._seal_tally_verdict({"sets": None, "uniques": None, "runewords": None},
                                     "the board answered but carried no counts")
        self.assertIs(out["ok"], False)
        self.assertIs(out["measured"], False)

    def test_a_full_board_is_measured(self):
        """Discrimination in the other direction: the fix must not suppress real progress."""
        synced = {"ok": True, "ledgers": [{"ledger": "sets", "provenance": "EARNED"}]}
        out = CA._seal_tally_verdict(_row(synced, have=128), "carried no counts")
        self.assertIs(out["measured"], True)
        self.assertEqual(out["sets"]["have"], 128, "the count itself was altered")

    # ---------- one writer ----------

    def test_both_tally_sites_go_through_the_one_helper(self):
        code = _code_only(SRC)
        n = code.count("_seal_tally_verdict(")
        self.assertGreaterEqual(n, 3,
                                "expected the definition plus both call sites; found %d" % n)
        self.assertEqual(code.count('out["ok"] = any(out[k] for k in ("sets", "uniques", "runewords"))'), 1,
                         "the truthiness test exists somewhere other than inside the helper - a "
                         "second copy is how this defect survived 129 lines apart")

    # ---------- the screen ----------

    def test_the_card_suppresses_the_number_only_on_an_explicit_false(self):
        """⚠ ANCHORED ON THE FULL GUARD, not the name: this file and control_ui.html both discuss
        `measured` in prose. [[source-reading-guard]] 4b"""
        self.assertEqual(UI.count("if (meas === false) {"), 1,
                         "the card no longer suppresses an unsynced number, or does it twice")
        self.assertNotIn("if (!meas) {", UI,
                         "a falsy test would swallow UNKNOWN and an older peer's absent field "
                         "too, accusing every pre-v3389 console of lying")

    def test_all_three_bars_are_told_the_verdict(self):
        """A field nobody reads is plumbing with no tap. [[the-unjoined-end]]"""
        self.assertEqual(UI.count("t.measured, t.measuredWhy"), 3,
                         "not all three ledger bars receive the verdict")


RED_PROOF = [
    {
        "why": "calling an unsynced board measured is the defect itself, and his real row must "
               "go red on it",
        "file": "tv/control_app.py",
        "find": '    out["measured"] = False\n    out["measuredWhy"] = (\n',
        "replace": '    out["measured"] = True\n    out["measuredWhy"] = (\n',
        "matches": 1,
    },
    {
        "why": "a tally with no verdict must stay UNKNOWN; defaulting it to True is the cheerful "
               "lie this whole version exists to end",
        "file": "tv/control_app.py",
        "find": '        out["measured"] = None\n        out["measuredWhy"] = ("no ledger verdict',
        "replace": '        out["measured"] = True\n        out["measuredWhy"] = ("no ledger verdict',
        "matches": 1,
    },
    {
        "why": "restoring the truthiness test at a call site is the exact regression, and the "
               "one-writer law must catch a second copy appearing again",
        "file": "tv/control_app.py",
        "find": '    return _seal_tally_verdict(out, "the board answered but carried no counts")',
        "replace": '    out["ok"] = any(out[k] for k in ("sets", "uniques", "runewords"))\n'
                   '    if not out["ok"]:\n'
                   '        out["why"] = "the board answered but carried no counts"\n'
                   '    return out',
        "matches": 1,
    },
    {
        "why": "without the card guard the unsynced zero is printed as a count again, which is "
               "the pixel he complained about",
        "file": "tv/control_ui.html",
        "find": "        if (meas === false) {",
        "replace": "        if (false) {",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
