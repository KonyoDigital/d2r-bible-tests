"""v2462 — A21b · his hand is a witness, and the tick that banks it.

His ruling, twice: *"YES its enough. manual anything is enough witness obivously :)"* and then
*"anything i manually do needs to ledgered as if there is proof.. same unified logic connected to
the leder proof of.. same style same unified logic as the rest of the console."*

Every tag `witnesses()` produced was derived from reels and frames. A manual tick has neither, so
his own testimony was the one signal that function could not count — while an OCR read of a blurry
row counted twice.

⚠ THIS IS DELIBERATELY NOT IN THE SELF-ARMING PROOF QUEUE. `self_arming.KINDS` weighs SABOTAGES,
and its denominator is sabotages ATTEMPTED, never agreements — that is the only reason the locks
cannot be talked open. A manual tick is testimony about what he OWNS; a sabotage is evidence that a
GUARD CAN REFUSE. Two different questions wearing the word "proof". A `manual` tier there would let
hand-ticking open a lock no sabotage ever tested. [[wilson-self-arming-lock]]

⚠ FIXTURES NEVER TOUCH LIVE DATA. Every test here swaps the evidence load/save for an in-memory
pair; none of them opens chron_evidence.json. [[feedback-fixtures-never-touch-live-data]]
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chronicle_retro as CR
import control_app as CA


class HisHandEarnsItsOwnTag(unittest.TestCase):

    def test_a_manual_sighting_is_a_witness_on_its_own(self):
        self.assertIn("hand", CR.witnesses([{"lane": "manual", "witness": "hand"}]),
                      "his hand produced no witness at all — the one signal he ruled was enough")

    def test_hand_is_never_a_synonym_for_another_tag(self):
        """A reader asking WHY a name is grounded must be able to see the answer is 'he says so',
        which is a different fact from 'two reels agree' and is weighed differently."""
        only = CR.witnesses([{"lane": "manual", "witness": "hand"}])
        self.assertEqual(sorted(only), ["hand"],
                         "a manual tick smuggled in another tag: %r" % sorted(only))
        reels = CR.witnesses([{"lane": "claude", "reel": "r1", "frame": "f1"},
                              {"lane": "claude", "reel": "r2", "frame": "f2"}])
        self.assertNotIn("hand", reels, "reels alone produced a `hand` tag — nobody ticked anything")

    def test_a_hand_and_a_reel_are_TWO_independent_witnesses(self):
        got = sorted(CR.witnesses([{"lane": "manual"},
                                   {"lane": "claude", "reel": "r1", "frame": "f1"}]))
        self.assertIn("hand", got)
        self.assertIn("cross-lane", got)


class TheTickBanksOnlyWhatHappened(unittest.TestCase):

    def setUp(self):
        self.store = {}
        self._load, self._save = CA._chron_evidence_load, CA._chron_evidence_save
        CA._chron_evidence_load = lambda: self.store
        CA._chron_evidence_save = lambda d: self.store.update(d or {})

    def tearDown(self):
        CA._chron_evidence_load, CA._chron_evidence_save = self._load, self._save

    def test_the_writer_calls_functions_that_actually_exist(self):
        """⚠ MY FIRST CUT DID NOT. It called `chronicle_retro._chron_evidence_load()` behind a
        `hasattr` guard; that name lives in control_app, so on every real tree the guard was False,
        the writer returned silently, and the `hand` tag would have been a tag nothing could ever
        produce. A defensive hasattr around a WRONG NAME is not defence, it is a silent no-op."""
        self.assertTrue(callable(getattr(CA, "_chron_evidence_load", None)))
        self.assertTrue(callable(getattr(CA, "_chron_evidence_save", None)))

    def test_a_tick_banks_a_manual_sighting_the_witness_counter_can_read(self):
        self.assertTrue(CA._bank_manual_sighting("Shako", "unique"))
        rows = self.store["uniques"]["Shako"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lane"], "manual")
        self.assertIsNone(rows[0].get("reel"), "a manual tick has no reel and must not invent one")
        self.assertIn("hand", CR.witnesses(rows),
                      "the row was written in a shape the witness counter cannot read — the two "
                      "halves would be built and never joined")

    def test_saying_it_twice_is_not_two_witnesses(self):
        CA._bank_manual_sighting("Shako", "unique")
        self.assertFalse(CA._bank_manual_sighting("Shako", "unique"))
        self.assertEqual(len(self.store["uniques"]["Shako"]), 1)

    def test_a_set_tick_lands_in_the_sets_ledger(self):
        CA._bank_manual_sighting("Tal Rasha's Adjudication (amulet)", "set")
        self.assertIn("Tal Rasha's Adjudication (amulet)", self.store.get("sets", {}))
        self.assertNotIn("Tal Rasha's Adjudication (amulet)", self.store.get("uniques", {}))

    def test_nothing_is_banked_for_an_item_nobody_ticked(self):
        """NO RULE MANUFACTURES TESTIMONY NEVER GIVEN. The 8 owned items with no log row stay
        UNKNOWN; ownership alone must never mint a witness."""
        self.assertEqual(self.store, {})
        self.assertEqual(CR.witnesses([]), [])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
