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


class TestV2373NothingCanLockIsNotNothingHasEarnedIt(unittest.TestCase):
    """`locked: 0` had two meanings and every surface reported both as OK.

    "No item has cleared the floor YET" invites him to keep farming and is fixed by farming.
    "No item can EVER clear it" is a defect no farming touches. They print identically.

    The second was the true one. `equip` increments only for lane == "equipment"
    (main_character.py:101); that lane comes from reel_segments.activity_at, whose ENTIRE
    vocabulary is stash · inventory · gameplay · town · transition. There is no equipment member,
    so no frame can yield it, `equip` is pinned at 0, and the Wilson floor cannot be cleared by
    evidence. MEASURED on his live ledger 2026-09-01: 4 items tracked (Dwarf Star, Sandstorm
    Trek, Tearhaunch, War Traveler), every row equip:0 seen:1 — and console_doctor answered OK
    while main() printed "that is an honest empty, not a failure".
    [[label-outlived-referent]] [[unknown-stays-unknown]] [[the-unjoined-end]]"""

    def setUp(self):
        self._real = MC._load, MC._save
        self.db = {}
        MC._load = lambda: self.db
        MC._save = lambda d: self.db.update(d)

    def tearDown(self):
        MC._load, MC._save = self._real

    def test_an_EMPTY_ledger_is_not_reported_as_blocked(self):
        """Nothing recorded at all is a different, honest empty — crying wolf there would make
        the real signal furniture."""
        self.assertIsNone(MC.blocked_why(),
                          "an empty ledger was reported as structurally blocked")

    def test_sightings_that_never_reach_the_equipment_lane_are_called_out(self):
        for i in range(6):
            MC.saw("Windforce", "stash", session="w%d" % i)
        self.assertEqual(MC.equip_sightings(), 0)
        why = MC.blocked_why()
        self.assertTrue(why, "6 stash sightings and 0 equipment ones reported nothing wrong — "
                             "that is the zero that reads as healthy")
        self.assertIn("equipment", why)
        r = MC.report()
        self.assertFalse(r["canEverLock"])
        self.assertEqual(r["equipSightings"], 0)

    def test_it_STOPS_complaining_once_the_lane_is_fed(self):
        """The mirror, and the one that stops this becoming a permanent red. A guard that cannot
        go quiet is one he learns to scroll past."""
        MC.saw("Shako", "equipment", session="a")
        self.assertEqual(MC.equip_sightings(), 1)
        self.assertIsNone(MC.blocked_why(),
                          "the lane IS being fed and it still reported a structural block")
        self.assertTrue(MC.report()["canEverLock"])

    def test_the_reason_NAMES_the_vocabulary_that_lacks_it(self):
        """A reason he cannot act on is a reason he ignores. It must say WHERE to look."""
        for i in range(3):
            MC.saw("Windforce", "stash", session="v%d" % i)
        why = MC.blocked_why() or ""
        self.assertIn("reel_segments", why,
                      "the reason does not name the module whose vocabulary is missing the lane")
        for word in ("stash", "inventory", "gameplay"):
            self.assertIn(word, why, "the reason does not print the vocabulary it checked")


if __name__ == "__main__":
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
