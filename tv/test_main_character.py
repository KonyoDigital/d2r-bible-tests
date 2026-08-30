#!/usr/bin/env python3
"""WHAT IS ON HIS CHARACTER, AND WHY A LOCK HAS TO BE EARNED.

★ Konyo: "it should register the MAIN CHARACTER and its equipment and start locking in and
pinpointing using wilson score obviously and all techniques related for it".

The LANE rule (vault_retro.LOCKED_LANES) already protects anything in the equipment panel while
that panel is on screen. What it cannot do is recognise the same Harlequin Crest in a frame that
only shows the stash — so a helm he is WEARING could be proposed for a mule from a reel that never
saw his character. This ledger closes that, and it makes the lock EARNED because a wrong lock is
as damaging as a wrong move: it silently removes an item from everything the vault is for.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import main_character as MC


class TestALockIsEARNED(unittest.TestCase):

    def setUp(self):
        self._real = MC._load, MC._save
        self.db = {}
        MC._load = lambda: self.db
        MC._save = lambda d: self.db.update(d)

    def tearDown(self):
        MC._load, MC._save = self._real

    def test_one_sighting_locks_NOTHING(self):
        MC.saw("Shako", "equipment", session="a")
        locked, why = MC.is_locked("Shako")
        self.assertFalse(locked, "a single look locked an item — 1 frame is a fixture, not proof")
        self.assertIn("floor", why)

    def test_consistent_sightings_earn_the_lock(self):
        for i in range(4):
            MC.saw("Harlequin Crest", "equipment", session="s%d" % i)
        locked, why = MC.is_locked("Harlequin Crest")
        self.assertTrue(locked, why)
        self.assertIn("Wilson", why)

    def test_an_item_seen_only_in_the_STASH_never_locks(self):
        for i in range(6):
            MC.saw("Windforce", "stash", session="w%d" % i)
        locked, why = MC.is_locked("Windforce")
        self.assertFalse(locked, "a stash item was locked as his gear")
        self.assertIn("0 of 6", why)

    def test_ONE_SESSION_COUNTS_ONCE(self):
        """Twenty frames of one hover are ONE look at his character. Counting them separately
        would let a single pass lock an item outright — the double-count the vault's witness fold
        already exists to stop."""
        for _ in range(20):
            MC.saw("Tarnhelm", "equipment", session="same-session")
        row = self.db[MC._key("Tarnhelm")]
        self.assertEqual(row["seen"], 1,
                         "one session counted %d times" % row["seen"])
        self.assertFalse(MC.is_locked("Tarnhelm")[0],
                         "twenty frames of one session locked an item")

    def test_FURNITURE_is_locked_by_LAW_with_no_evidence_at_all(self):
        locked, why = MC.is_locked("Horadric Cube")
        self.assertTrue(locked, "the cube is furniture and must lock at zero sightings")
        self.assertIn("law", why)
        self.assertEqual(self.db, {}, "the law consulted the evidence ledger it should not need")

    def test_never_seen_is_UNKNOWN_not_unlocked_by_assertion(self):
        w, why = MC.confidence("Griffon's Eye")
        self.assertIsNone(w, "a score was invented for an item never seen")
        self.assertIn("never seen", why)

    def test_equipped_lists_only_what_actually_earned_it(self):
        for i in range(4):
            MC.saw("Andariel's Visage", "equipment", session="e%d" % i)
        for i in range(4):
            MC.saw("Ist Rune", "stash", session="r%d" % i)
        names = [r["name"] for r in MC.equipped()]
        self.assertIn("Andariel's Visage", names)
        self.assertNotIn("Ist Rune", names)


if __name__ == "__main__":
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
