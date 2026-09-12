#!/usr/bin/env python3
"""v3008 (#77) — A CORRECT HOLD WAS WEARING A FAULT'S CLOTHES.

One name clears two witnesses and sits unbanked: Crescent Moon. The refusal is CORRECT — the name
has multiple referents (two uniques share it, plus the Shael+Um+Tir runeword), and two witnesses
corroborate a NAME, not an ITEM. But `ledger_of` returns the FIRST roster hit, so nothing
downstream could ever know about the second referent — and the doctor reported the hold as owed
work ("the auto door can take those for free").

`referents_of` returns EVERY hit; split() separates autoHeld from autoOwed; the doctor names the
hold and its reasons. HELD IS NOT OWED. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import read_names_lane as RNL  # noqa: E402

#: a fixture roster in the exact shape rosters() returns: {norm: canonical} per ledger
def _rost():
    import chronicle_resolve as CR
    return {
        "UNIQUE": {CR._norm("Crescent Moon"): "Crescent Moon",
                   CR._norm("Shako"): "Shako"},
        "SET": {CR._norm("Sigon's Guard"): "Sigon's Guard"},
        "RUNEWORD": {CR._norm("Crescent Moon"): "Crescent Moon",
                     CR._norm("Lionheart"): "Lionheart"},
    }


class TheAutoDoorSaysWhyItHoldsAName(unittest.TestCase):

    # ── the reader reports every referent ─────────────────────────────────────────────────────
    def test_referents_of_returns_every_hit_not_the_first(self):
        got = RNL.referents_of("Crescent Moon", _rost())
        self.assertEqual(got, ["UNIQUE", "RUNEWORD"],
                         "ledger_of's first-match is where the ambiguity hides; the referent "
                         "reader must report ALL of them, got %r" % got)

    def test_a_single_referent_name_reports_one(self):
        self.assertEqual(RNL.referents_of("Shako", _rost()), ["UNIQUE"])
        self.assertEqual(RNL.referents_of("Lionheart", _rost()), ["RUNEWORD"])

    def test_no_roster_is_unknown_not_empty(self):
        self.assertIsNone(RNL.referents_of("Shako", None),
                          "no roster means nothing was classified — None, never []")

    # ── the split separates held from owed ────────────────────────────────────────────────────
    def _split_rows(self, auto_rows):
        """Drive ONLY the aggregation: rebuild autoHeld/autoOwed the way split() does."""
        held = [{"name": r["name"], "referents": r.get("referents") or []}
                for r in auto_rows
                if r.get("ledger") not in (None, "NEITHER", "FURNITURE")
                and len(r.get("referents") or []) > 1]
        owed = [r["name"] for r in auto_rows
                if r.get("ledger") not in (None, "NEITHER", "FURNITURE")
                and len(r.get("referents") or []) <= 1]
        return held, owed

    def test_the_live_split_holds_crescent_moon(self):
        """PINNED ON THE REAL DATA: the one live auto-lane name is held, with the runeword hit
        that first-match reading had been swallowing."""
        sp = RNL.split()
        if not (isinstance(sp, dict) and sp.get("ok")):
            self.fail("the lane could not measure: %s" % str((sp or {}).get("why"))[:100])
        if sp.get("autoHeld") is None:
            self.fail("the rosters could not be read — held/owed is UNKNOWN, not a pass")
        held_names = [h.get("name") for h in sp["autoHeld"]]
        self.assertIn("Crescent Moon", held_names,
                      "the one name clearing the bar has multiple referents and must be HELD")
        cm = [h for h in sp["autoHeld"] if h.get("name") == "Crescent Moon"][0]
        self.assertIn("RUNEWORD", cm.get("referents") or [],
                      "the runeword referent is the one first-match swallowed")
        self.assertNotIn("Crescent Moon", sp.get("autoOwed") or [],
                         "held and owed are different answers; a name may not be both")

    # ── the doctor's voice ────────────────────────────────────────────────────────────────────
    def _verdict(self, held, owed, auto_t=1):
        import console_doctor as cd
        real = getattr(cd, "_RNL", None)
        import read_names_lane as rnl
        orig = rnl.split
        rnl.split = lambda *a, **k: {"ok": True, "tickable": 5, "furniture": 3, "names": 42,
                                     "minWitnesses": 2, "autoTickable": auto_t,
                                     "autoHeld": held, "autoOwed": owed, "rosterWhy": ""}
        try:
            return cd._check_read_names_lane()
        finally:
            rnl.split = orig

    def test_a_held_name_is_OK_with_its_reasons_named(self):
        st, why = self._verdict([{"name": "Crescent Moon",
                                  "referents": ["UNIQUE", "RUNEWORD"]}], [])
        self.assertEqual(st, "ok",
                         "a correct hold reported as a fault teaches him the row cries wolf")
        self.assertIn("HOLDING", why)
        self.assertIn("Crescent Moon", why)
        self.assertIn("UNIQUE/RUNEWORD", why, "the voice must NAME the referents")

    def test_an_owed_name_is_still_missing(self):
        st, why = self._verdict([], ["Shako"])
        self.assertEqual(st, "missing",
                         "a single-referent name clearing the bar unbanked IS owed work")
        self.assertIn("Shako", why)

    def test_an_old_lane_without_the_split_falls_back_honestly(self):
        st, why = self._verdict(None, None, auto_t=1)
        self.assertEqual(st, "missing")
        self.assertIn("cannot be told", why,
                      "an older lane cannot say held-vs-owed and must SAY it cannot")


RED_PROOF = [
    {
        "why": "early-returning the first roster hit swallows the runeword referent again — "
               "Crescent Moon reads single-referent, the hold becomes owed work, and the door "
               "goes back to being silently wrong about why",
        "file": "read_names_lane.py",
        "find": "    if CR.canonical(name, rost.get(\"UNIQUE\") or {}):\n        out.append(\"UNIQUE\")",
        "replace": "    if CR.canonical(name, rost.get(\"UNIQUE\") or {}):\n        return [\"UNIQUE\"]",
        "matches": 1,
    },
    {
        "why": "a threshold no name can reach empties autoHeld, so every held name reads as owed",
        "file": "read_names_lane.py",
        "find": "                          and len(r.get(\"referents\") or []) > 1]),",
        "replace": "                          and len(r.get(\"referents\") or []) > 999]),",
        "matches": 1,
    },
    {
        "why": "dropping the held branch silences the voice — the hold falls through to the "
               "generic all-clear and nobody is told why the name sits",
        "file": "console_doctor.py",
        "find": "        if _held:",
        "replace": "        if False:",
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
