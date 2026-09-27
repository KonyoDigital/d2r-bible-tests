# -*- coding: utf-8 -*-
"""A reset puts back only what the evidence proved, or what does not vanish on its own."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import vault_evidence as VE


def _item(name, successes, trials, **kw):
    row = {"name": name, "successes": successes, "trials": trials}
    row.update(kw)
    return row


class TheTierTableIsTheOnlyBar(unittest.TestCase):
    def test_twelve_clean_looks_are_proven_and_come_back(self):
        got = VE.tier(12, 12)
        self.assertEqual(VE.PROVEN, got["tier"], got)
        plan = VE.rebuild_plan([_item("Shako", 12, 12)])
        self.assertEqual(["Shako"], [r["name"] for r in plan["rebuilt"]])
        self.assertFalse(plan["rebuilt"][0]["locked"], "twelve looks were treated as hardened")
        self.assertEqual([], plan["held"])

    def test_twenty_one_clean_looks_are_hardened_and_locked(self):
        got = VE.tier(21, 21)
        self.assertEqual(VE.HARDENED, got["tier"], got)
        plan = VE.rebuild_plan([_item("Arachnid Mesh", 21, 21)])
        self.assertTrue(plan["rebuilt"][0]["locked"])

    def test_twelve_looks_with_five_misses_stay_watched(self):
        # 7 successes in 12 trials. The cell was empty or held something else five times.
        got = VE.tier(7, 12)
        self.assertEqual(VE.WATCHED, got["tier"], got)
        plan = VE.rebuild_plan([_item("War Traveler", 7, 12)])
        self.assertEqual([], plan["rebuilt"])
        self.assertEqual(["War Traveler"], [r["name"] for r in plan["held"]])

    def test_two_witnesses_stay_cleared(self):
        plan = VE.rebuild_plan([_item("Chance Guards", 2, 2)])
        self.assertEqual(VE.WATCHED, plan["held"][0]["tier"])
        self.assertEqual([], plan["rebuilt"])

    def test_an_equipped_item_and_a_sunder_come_back_below_the_bar(self):
        plan = VE.rebuild_plan([
            _item("Harlequin Crest", 2, 2, equipped=True),
            _item("Lightning Sunder Charm", 0, 0, kind="sunder"),
        ])
        names = [r["name"] for r in plan["rebuilt"]]
        self.assertEqual(["Harlequin Crest", "Lightning Sunder Charm"], names)
        self.assertEqual([], plan["held"])

    def test_unreadable_counts_are_unknown_and_not_rebuilt(self):
        got = VE.tier(None, 12)
        self.assertIsNone(got["tier"])
        plan = VE.rebuild_plan([_item("Shako", None, None)])
        self.assertEqual([], plan["rebuilt"])
        self.assertIn("UNKNOWN", plan["held"][0]["why"])

    def test_the_bound_rises_with_successes_and_falls_when_a_look_misses(self):
        clean = VE.tier(12, 12)["bound"]
        missed = VE.tier(7, 12)["bound"]
        self.assertGreater(clean, missed)
        self.assertGreater(VE.tier(21, 21)["bound"], clean)

    def test_evidence_that_is_not_a_list_rebuilds_nothing_and_does_not_say_empty(self):
        plan = VE.rebuild_plan(None)
        self.assertFalse(plan["ok"])
        self.assertEqual([], plan["rebuilt"])
        self.assertIn("could not be read", plan["why"])


RED_PROOF = [
    {
        "why": "hardened starts at 10 trials, so twelve clean looks are locked",
        "file": "vault_evidence.py",
        "find": "TRIALS_HARDENED = 20\n",
        "replace": "TRIALS_HARDENED = 10\n",
        "matches": 1,
    },
    {
        "why": "the Wilson bar dropped to zero, so misses no longer keep an item watched",
        "file": "vault_evidence.py",
        "find": "WILSON_BAR = 0.722\n",
        "replace": "WILSON_BAR = 0.0\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
