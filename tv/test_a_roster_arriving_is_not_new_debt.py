# -*- coding: utf-8 -*-
"""v3328 — A ROSTER ARRIVING IS NOT NEW DEBT, AND THIS FILE ALREADY KNEW IT.

`verdict_provenance._verdict` defines REFERENCE as a row carrying no producer key AND no clock, and
the module's line 20 says what that means: *"a roster or lookup table — no clock, so the question
does not apply"*. A store the provenance question does not apply to cannot owe an answer to it.

`_compare`'s new-arrival branch reddened everything ranking below ANSWERS, so a roster arriving was
filed as "NEW store arrives REFERENCE — new debt". MEASURED 2026-09-18 on the live tree:

    🔴 engine_index.json:   NEW store arrives SILENT    — real debt, correctly red
    🔴 heart_floor.json:    NEW store arrives REFERENCE — FALSE
    🔴 test_reel_refs.json: NEW store arrives REFERENCE — FALSE

Two of the three reds were rosters being asked when they were last written and by whom.

⚠⚠ THE SAME FALSE RED ALREADY BIT ONCE AND WAS PATCHED BY NAME. The ratchet's OWN baseline arrived
REFERENCE and was reported as new debt on the very first clean run; the fix excluded that one
filename inside `_split`. That closed the instance and left the class open — and the class re-fired
the moment two more rosters landed, on a gate that was otherwise reporting 12 genuine improvements.
A rule learned once and generalised to nothing. [[copy-drift]] [[the-unjoined-end]]

⚠ SILENT AND PARTIAL STILL COUNT AS DEBT, AND THE BASELINE HALF BELOW PINS IT. SILENT means the row
HAS a clock and still names no writer — the question applies and went unanswered. Exempting that
too would turn a ratchet into an off switch, which is the failure this whole file exists to
prevent. The exemption is for inapplicability, never for inconvenience.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import verdict_provenance as VP  # noqa: E402


class TestARosterArrivingIsNotNewDebt(unittest.TestCase):

    def _new(self, state):
        """One store that did not exist at the baseline, arriving in `state`."""
        return VP._compare({}, {"newcomer.json": state})

    def test_a_roster_arriving_is_not_debt(self):
        reg, gain, new, gone = self._new("REFERENCE")
        self.assertEqual(
            reg, [],
            "a REFERENCE store — no producer key and NO CLOCK — was filed as new debt: %r. The "
            "module's own line 20 calls it 'a roster or lookup table, no clock, so the question "
            "does not apply'. Reddening it asks a lookup table when it was last written." % reg)
        self.assertTrue(
            any("ROSTER" in s for s in new),
            "the roster left the red list but says nothing in its place. A row that vanishes "
            "with no sentence is silencing, not classifying. Got: %r" % new)

    def test_a_SILENT_arrival_is_STILL_debt(self):
        """⚠ THE BASELINE. Without this, exempting REFERENCE could widen into an off switch."""
        reg, gain, new, gone = self._new("SILENT")
        self.assertTrue(
            any("newcomer.json" in s for s in reg),
            "a SILENT store stopped counting as debt. SILENT means the row HAS a clock and still "
            "names no writer — the question applies and went unanswered. That is exactly "
            "engine_index.json today, and it must stay red. Got reg=%r new=%r" % (reg, new))

    def test_a_PARTIAL_arrival_is_STILL_debt(self):
        reg, gain, new, gone = self._new("PARTIAL")
        self.assertTrue(
            any("newcomer.json" in s for s in reg),
            "a PARTIAL store stopped counting as debt. It names WHO but not WHICH VERSION, and "
            "that gap is real. Got reg=%r" % reg)

    def test_an_EMPTY_arrival_keeps_its_own_sentence(self):
        """UNKNOWN had the honest shape first; this change must not disturb it."""
        reg, gain, new, gone = self._new("UNKNOWN")
        self.assertEqual(reg, [], "an empty store is not debt yet")
        self.assertTrue(
            any("not debt yet" in s and "not clean either" in s for s in new),
            "the empty-store sentence changed. It was already right — a store that lost its rows "
            "did not improve, and it did not regress either. Got: %r" % new)

    def test_a_REGRESSION_between_existing_states_still_reddens(self):
        """The ratchet's whole job. Exempting an arrival must not touch a MOVE."""
        reg, gain, new, gone = VP._compare({"s.json": "ANSWERS"}, {"s.json": "SILENT"})
        self.assertTrue(
            any("s.json" in s for s in reg),
            "a store that FELL from ANSWERS to SILENT no longer reddens. That is the regression "
            "the ratchet exists for, and it is unrelated to how arrivals are classified. reg=%r"
            % reg)

    def test_the_SILENT_REFERENCE_tie_is_untouched(self):
        """SILENT and REFERENCE tie ON PURPOSE — a move between them is reported, never reddened."""
        self.assertEqual(
            VP.RANK["SILENT"], VP.RANK["REFERENCE"],
            "the deliberate tie was broken. The module's comment: ranking one over the other "
            "'would invent a distinction the census does not draw'.")
        reg, gain, new, gone = VP._compare({"s.json": "SILENT"}, {"s.json": "REFERENCE"})
        self.assertEqual(reg, [], "a SILENT->REFERENCE move reddened; it must be reported only")
        self.assertEqual(gain, [], "a SILENT->REFERENCE move was counted as an improvement")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the roster branch sends every arriving lookup table back to 'new debt'",
        "file": "tv/verdict_provenance.py",
        "find": '        elif after == "REFERENCE":',
        "replace": '        elif False:',
        "matches": 1,
    },
    {
        "why": "widening the exemption to every non-ANSWERS arrival turns the ratchet off",
        "file": "tv/verdict_provenance.py",
        "find": '            new.append("%s: NEW and a ROSTER — no clock, so provenance does not apply" % store)\n        elif RANK.get(after, 0) < RANK["ANSWERS"]:\n            reg.append("%s: NEW store arrives %s — new debt" % (store, after))',
        "replace": '            new.append("%s: NEW and a ROSTER — no clock, so provenance does not apply" % store)\n        elif RANK.get(after, 0) < 0:\n            reg.append("%s: NEW store arrives %s — new debt" % (store, after))',
        "matches": 1,
    },
]
