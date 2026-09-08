#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2814 — THE FLEET PANEL SAID "HE HAS NOT REPORTED" ABOUT A MACHINE THAT HAD.

Konyo, 2026-09-09, with screenshots. Two sentences from one panel, minutes apart:

    "the fleet is unreachable — The read operation timed out"
    "Dean has not reported which set pieces it holds yet"

MEASURED against the live beacon in the same minute as the second one:

    Dean   ver=v2745   online=TRUE   masks: sets=76ch, uniques=118ch
                                     tally: sets 128/135, uniques 249/403

He had reported BOTH ledgers. Three separate defects sat behind those two sentences.

1. A FAILED FETCH DESTROYED THE GOOD ANSWER. `fleet_presence()` caches 60s and on a timeout did
   `_FLEET_PRESENCE_CACHE["d"] = out` where `out` is the ERROR — so one 6s timeout replaced a
   roster that was working. The card had already rendered from the cached success; the modal, 60
   seconds wide, got the refusal. Strictly worse than no cache: without it the modal would simply
   have re-tried.

2. A STALE ROSTER WAS TREATED AS AN UNREACHABLE FLEET. The cross-reference refused outright on any
   fetch failure, while the card beside it was rendering that same machine's real numbers.

3. "HE HAS NOT REPORTED" WAS CONCLUDED FROM A CACHE. This is a claim about ANOTHER machine — the
   one kind this console cannot check by looking inward — and it was made from a record that can
   be arbitrarily old when a fetch has failed in between. An absence in a cached record is not an
   absence in the world.

★ THE RULE: serve the last good roster with its AGE rather than an error, and make a miss earn one
authoritative re-read before the sentence is allowed to be said.
[[stale-reading]] [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
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


def _src():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


def _fn(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


class TestACachedAbsenceIsNotAnAbsence(unittest.TestCase):

    def setUp(self):
        self.src = _src()
        self.tree = ast.parse(self.src)

    def test_the_cache_keeps_a_slot_for_the_last_good_answer(self):
        """Without goodD there is nowhere for a good roster to survive a failed fetch."""
        for key in ('"goodD"', '"goodT"'):
            self.assertIn(key, self.src,
                          "the presence cache has no %s slot, so a failed fetch overwrites the "
                          "last good roster and the panel loses data it already had" % key)

    def test_a_failed_fetch_does_not_replace_the_good_answer(self):
        """The error must not be written over the roster."""
        fn = _fn(self.tree, "fleet_presence")
        self.assertIsNotNone(fn, "fleet_presence is gone")
        body = ast.get_source_segment(self.src, fn) or ""
        self.assertIn("goodD", body,
                      "fleet_presence never consults its last-good slot — a timeout still "
                      "destroys the roster")
        self.assertIn("staleAgeS", body,
                      "a served-from-cache roster carries no age, so a caller cannot tell it "
                      "from a live one — that is the stale-reading defect")

    def test_the_cross_reference_survives_a_stale_roster(self):
        """A stale roster is not an unreachable fleet."""
        fn = _fn(self.tree, "fleet_xref") or _fn(self.tree, "fleet_cross_reference")
        if fn is None:
            # resolve by the sentence it prints rather than by a name that may drift
            self.assertIn("the fleet is unreachable", self.src)
            i = self.src.index("the fleet is unreachable")
            region = self.src[max(0, i - 1200):i + 400]
        else:
            region = ast.get_source_segment(self.src, fn) or ""
        self.assertIn("_fleet_stale", region,
                      "the refusal does not distinguish a STALE roster from an unreachable "
                      "fleet, so a cached-but-real answer is thrown away")

    def test_a_missing_mask_earns_one_authoritative_reread(self):
        """The decisive law. 'He has not reported' must not be said from a cache."""
        self.assertIn("fleet_presence(force=True)", self.src,
                      "nothing ever forces a fresh read, so 'he has not reported which pieces it "
                      "holds' is concluded from a record that may predate his publishing them — "
                      "measured wrong on 2026-09-09 against a beacon carrying both masks")
        # ⚠ THE ENCLOSING FUNCTION, NOT A BYTE WINDOW. The first cut of this assertion read
        # `self.src[i-3000:i]` and went red on correct code, because the function's docstring is
        # longer than the guess. A window measured in characters measures my guess, not the file —
        # committed here, in the gate written to stop exactly this class of error.
        # [[source-window-shortcut]]
        owner = None
        for n in ast.walk(self.tree):
            if isinstance(n, ast.FunctionDef):
                seg = ast.get_source_segment(self.src, n) or ""
                if "has not reported which" in seg:
                    owner = (n, seg)
                    break
        self.assertIsNotNone(owner, "no function prints the 'has not reported' sentence")
        _n, seg = owner
        self.assertIn("force=True", seg,
                      "the forced re-read is not in the same function that prints the sentence, "
                      "so the claim is still made from the cached view")
        # ⚠ LINE NUMBERS FROM THE PARSE, NOT string.index(). The first cut compared
        # `seg.index(...)` offsets and failed on correct code: "has not reported which" occurs in a
        # COMMENT ~50 lines above the assignment that actually composes the sentence, so it
        # measured the wrong occurrence of a string that appears twice. Third time tonight that a
        # first-occurrence match has been the wrong one. [[source-reading-guard]]
        _reread = [c.lineno for c in ast.walk(_n)
                   if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                   and c.func.id == "fleet_presence"
                   and any(k.arg == "force" for k in (c.keywords or []))]
        _says = [a.lineno for a in ast.walk(_n)
                 if isinstance(a, ast.Assign)
                 and "has not reported which" in (ast.get_source_segment(self.src, a) or "")]
        self.assertTrue(_reread, "no forced re-read call inside the function")
        self.assertTrue(_says, "nothing in this function ASSIGNS the sentence")
        self.assertLess(min(_reread), min(_says),
                        "the forced re-read is at line %d and the sentence is composed at line %d "
                        "— the panel would state an absence it had not re-checked"
                        % (min(_reread), min(_says)))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "removing the last-good slot returns a timeout to destroying the roster",
        "file": "control_app.py",
        "find": '_FLEET_PRESENCE_CACHE = {"t": 0.0, "d": None, "goodT": 0.0, "goodD": None}',
        "replace": '_FLEET_PRESENCE_CACHE = {"t": 0.0, "d": None}',
        "matches": 1,
    },
    {
        "why": "without the forced re-read the panel again claims an absence it only cached",
        "file": "control_app.py",
        "find": "            _fresh = fleet_presence(force=True)",
        "replace": "            _fresh = None",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
