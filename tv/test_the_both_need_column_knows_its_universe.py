#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A "both need" list may only be shown when the roster IS the universe.

His ask, 2026-09-12: a third column on the fleet cross-reference — "tell me the items we BOTH need
combined not only the items we each have that the other doesnt".

⚠⚠ WHY THIS FILE EXISTS AT ALL, because the feature looked like pure arithmetic and is not. The two
columns that panel already shows are DIFFERENCES — "in their mask, not in mine" — and a difference
is true whatever exists OUTSIDE the roster, because a name nobody enrolled never enters the
question. "Neither of us has it" is a COMPLEMENT, and a complement is a claim about the WHOLE
UNIVERSE. It is the first thing in this panel that a wrong denominator can falsify, and the two
beside it never were.

MEASURED on his tree the day it was built:

    sets     roster 135  ·  his board posts total 135   -> equal; the roster is the universe
    uniques  roster 398  ·  his board posts total 403   -> FIVE of his own pinned names sit outside
                                                           the roster and could never appear

So on the uniques tab an unguarded column would confidently name "everything neither of you has"
while being structurally unable to mention five of his own items. That is not a rounding error, it
is a lie with a number on it. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

⚠ EVERY LAW HERE ASSERTS A REFUSAL AS WELL AS A PASS. A guard only ever seen say yes is not a guard.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import control_app as CA      # noqa: E402
import fleet_mask as FM       # noqa: E402


class TheBothNeedColumnKnowsItsUniverse(unittest.TestCase):

    # ── the complement itself ───────────────────────────────────────────────────────────────
    def test_the_complement_is_the_names_in_neither_mask(self):
        roster = ["a", "b", "c", "d", "e"]
        fp = "testfp"
        r = FM.compare(FM.encode(["a", "b"], roster, fp),
                       FM.encode(["b", "c"], roster, fp), roster, fp)
        self.assertTrue(r.get("ok"), r.get("why"))
        self.assertEqual(r["neitherHas"], ["d", "e"],
                         "the complement named %r; it must be exactly the roster names in NEITHER "
                         "mask" % (r["neitherHas"],))

    def test_the_four_buckets_account_for_every_roster_name(self):
        """⚠ THE ARITHMETIC IS THE PROOF THE LIST IS COMPLETE. If both + theirs-only + mine-only +
        neither does not equal the roster, one of the four is dropping names silently — and the
        complement is the one that would look right while doing it."""
        roster = ["a", "b", "c", "d", "e", "f", "g"]
        fp = "testfp"
        r = FM.compare(FM.encode(["a", "b", "c"], roster, fp),
                       FM.encode(["c", "d"], roster, fp), roster, fp)
        self.assertTrue(r.get("ok"), r.get("why"))
        total = (r["both"] + len(r["theyHaveIDont"]) + len(r["iHaveTheyDont"])
                 + len(r["neitherHas"]))
        self.assertEqual(total, r["rosterN"],
                         "the four buckets sum to %d over a roster of %d — names are being "
                         "dropped or double counted" % (total, r["rosterN"]))

    def test_the_complement_ships_with_the_denominator_it_is_valid_against(self):
        """A list that cannot be rendered without rosterN must carry rosterN. Otherwise a caller
        shows it beside whatever number is nearest. [[zero-needs-a-denominator]]"""
        roster = ["a", "b", "c"]
        fp = "testfp"
        r = FM.compare(FM.encode(["a"], roster, fp), FM.encode(["b"], roster, fp), roster, fp)
        self.assertEqual(r.get("rosterN"), 3,
                         "compare() no longer publishes rosterN beside neitherHas")

    # ── the guard ───────────────────────────────────────────────────────────────────────────
    def test_an_agreeing_total_lets_the_column_through(self):
        ok, why = CA._neither_is_publishable(135, 135, "sets")
        self.assertTrue(ok, "a roster that matches the posted total was refused: %s" % why)

    def test_a_DISAGREEING_total_refuses_and_names_BOTH_numbers(self):
        """⚠ THE MEASURED CASE. 398 vs 403 is real and live on his tree."""
        ok, why = CA._neither_is_publishable(398, 403, "uniques")
        self.assertFalse(ok, "a roster 5 short of the posted universe was allowed through")
        self.assertIn("398", why, "the refusal does not say the roster size")
        self.assertIn("403", why, "the refusal does not say the posted total")
        self.assertIn("5", why, "the refusal does not say how many names sit outside the roster")

    def test_an_UNKNOWN_total_refuses_rather_than_assuming_agreement(self):
        """⚠ THE DIRECTION THAT MATTERS. 'The board never posted a total' and 'the totals agree'
        are opposite facts, and only one of them may show the column."""
        ok, why = CA._neither_is_publishable(398, None, "uniques", "board_tally is unreadable")
        self.assertFalse(ok, "a MISSING posted total was treated as agreement")
        self.assertIn("UNKNOWN", why, "an unreadable total must be reported as UNKNOWN")

    def test_an_UNKNOWN_roster_size_refuses_too(self):
        ok, why = CA._neither_is_publishable(None, 403, "uniques")
        self.assertFalse(ok, "an unknown roster size was treated as agreement")
        self.assertIn("UNKNOWN", why)

    def test_a_non_numeric_total_is_UNKNOWN_not_a_crash_and_not_a_pass(self):
        ok, why = CA._neither_is_publishable(398, "four hundred", "uniques")
        self.assertFalse(ok, "a total that is not a number was treated as agreement")

    # ── ⚠ the guard must not damage what already worked ─────────────────────────────────────
    def test_refusing_the_complement_leaves_the_two_DIFFERENCE_columns_intact(self):
        """⚠⚠ THE REGRESSION THIS GUARD COULD CAUSE. A difference is true over ANY roster, so
        refusing the complement must never blank the two columns that have always been correct.
        Measured as a shape law: compare() returns both lists regardless of any totals question,
        because it is not the thing that knows about totals."""
        roster = ["a", "b", "c", "d"]
        fp = "testfp"
        r = FM.compare(FM.encode(["a"], roster, fp), FM.encode(["b"], roster, fp), roster, fp)
        self.assertIsInstance(r.get("theyHaveIDont"), list)
        self.assertIsInstance(r.get("iHaveTheyDont"), list)
        self.assertEqual(r["theyHaveIDont"], ["b"])
        self.assertEqual(r["iHaveTheyDont"], ["a"])

    # ── the live reading, so the law fails when his own tree changes shape ───────────────────
    def test_his_two_ledgers_still_read_the_way_this_guard_was_built_for(self):
        """⚠ NOT A FIXTURE. If sets stops agreeing, or uniques starts agreeing, the situation this
        guard was designed around has changed and somebody should look — an UNKNOWN here is
        reported, never rounded to a pass. [[feedback-blind-fixture-green-gate]]"""
        import io as _io
        import json as _json
        seen = {}
        for fname, key, led in (("set_roster.json", "pieces", "sets"),
                                ("unique_roster.json", "names", "uniques")):
            path = os.path.join(HERE, fname)
            if not os.path.exists(path):
                self.skipTest("%s is not on this venue, so his live shape cannot be read" % fname)
            try:
                doc = _json.load(_io.open(path, encoding="utf-8"))
            except Exception as e:
                self.fail("%s would not parse (%s) — UNKNOWN, and this law must not pass on it"
                          % (fname, type(e).__name__))
            seen[led] = len(doc.get(key) or [])
        self.assertEqual(seen.get("sets"), 135,
                         "the sets roster now carries %r, not the 135 this guard was measured "
                         "against" % (seen.get("sets"),))
        self.assertEqual(seen.get("uniques"), 398,
                         "the uniques roster now carries %r, not the 398 this guard was measured "
                         "against" % (seen.get("uniques"),))


RED_PROOF = [
    {
        "why": "a guard that always says yes lets the uniques column claim to be exhaustive over a "
               "roster 5 names short of his own posted universe — the exact lie this file exists "
               "to refuse",
        "file": "control_app.py",
        "find": "    if _s != _r:",
        "replace": "    if False:",
        "matches": 1,
    },
    {
        "why": "dropping the complement from compare() removes the list the whole column renders, "
               "and the arithmetic law can no longer account for every roster name",
        "file": "fleet_mask.py",
        "find": '            "neitherHas": [n for n in roster if n not in sa and n not in sb],',
        "replace": '            "neitherHas": [],',
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
