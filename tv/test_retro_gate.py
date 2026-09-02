#!/usr/bin/env python3
"""THE GATE THAT GRADES A RETRO READ ON WHAT, WHERE AND HOW.

★ Konyo: "what maybe does need an extra layer of accuracy might be a double checker for these same
reels for when it does BYPASS THE WITNESSES based on my focusing this stash inventory run ... for
like if its right on the FIRST analysis of what it read and WHERE it read and HOW it read it".

THE BYPASS IS THE REASON. The witness rule buys accuracy with REPETITION — three separate looks
before a KEEP is believed. A focused MINI has no repetition to spend: he opens the stash, hovers
each item once, seals. It is trusted because he AIMED it, which is why it may skip the witnesses —
and skipping them removes the lane's only accuracy mechanism. This replaces it on the first look.

HIS OWN 2026-08-30 SESSION, WHERE ALL THREE FAILED INDEPENDENTLY:
    WHAT   "Rune Grip Ring" read SIX times, registered as "Rune Grip"
    WHERE  that same register carries loc "floor" for an item in his stash
    HOW    "Crescent Moon" read twice plus two garbles, registered nothing
One number — "registers: 4" — hid three different defects.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import retro_gate as G


class TestTheThreeDimensionsFailSEPARATELY(unittest.TestCase):

    def test_his_real_defect_is_caught_on_all_three(self):
        raw = {"name": "Rune Grip", "loc": "floor"}
        prep = {"name": "Rune Grip Ring", "loc": "stash"}
        g = G.grade_three(raw, prep, expect_loc="stash")
        self.assertEqual(g[G.WHAT][0], G.DISAGREE, "the truncated name graded as agreement")
        self.assertEqual(g[G.WHERE][0], G.DISAGREE,
                         "a stash-focused run registered an item on the FLOOR and it passed")
        self.assertEqual(g[G.HOW][0], G.DISAGREE)
        self.assertIn("floor", g[G.WHERE][1])
        self.assertIn("stash", g[G.WHERE][1])

    def test_a_clean_read_agrees_on_all_three(self):
        v = {"name": "Lionheart", "loc": "stash"}
        g = G.grade_three(v, dict(v), expect_loc="stash")
        for d in G.DIMENSIONS:
            self.assertEqual(g[d][0], G.AGREE, "%s flagged a clean read" % d)

    def test_WHERE_is_UNKNOWN_when_the_run_declared_no_focus(self):
        """An undeclared run has nothing to contradict. Assuming it correct would manufacture
        agreement out of an absent question."""
        g = G.grade_three({"name": "Shako"}, {"name": "Shako"}, expect_loc=None)
        self.assertEqual(g[G.WHERE][0], G.UNKNOWN)

    def test_HOW_says_when_the_ENLARGE_is_what_found_the_name(self):
        """The single most useful thing this gate can report: the toolkit earning its cost."""
        g = G.grade_three({"name": ""}, {"name": "Crescent Moon"}, expect_loc="stash")
        self.assertEqual(g[G.HOW][0], G.DISAGREE)
        self.assertIn("earning its cost", g[G.HOW][1])

    def test_HOW_also_says_when_the_enlarge_LOST_a_name(self):
        """The opposite direction must be just as loud, or the technique could degrade silently."""
        g = G.grade_three({"name": "Crescent Moon"}, {"name": ""}, expect_loc="stash")
        self.assertEqual(g[G.HOW][0], G.DISAGREE)
        self.assertIn("LOST", g[G.HOW][1])


class TestTheGateCannotManufactureEVIDENCE(unittest.TestCase):

    def setUp(self):
        """⚠ v2425 — DECLARE A WORLD. CI's per-gate attribution named this class as a writer of
        `retro_gate.json`, and instrumenting the writes named the exact tests. Production resolves that
        path through the fixture root now (v2423); this is the other half — a suite that writes
        state must say which world it is in, or the correct rule is applied to the wrong root.
        [[feedback-fixtures-never-touch-live-data]]"""
        import tempfile as _tf, shutil as _sh, os as _os
        _d = _tf.mkdtemp(prefix="rg_")
        self.addCleanup(_sh.rmtree, _d, True)
        _old = _os.environ.get("TV_HIST")
        _os.environ["TV_HIST"] = _d
        self.addCleanup(lambda: (_os.environ.__setitem__("TV_HIST", _old) if _old is not None
                                 else _os.environ.pop("TV_HIST", None)))

    def test_a_curly_apostrophe_is_not_a_disagreement(self):
        """202 straight and 4 curly in his roster; that split already cost a wrong mule for
        Gheed's Fortune. Two readers arguing about a quote mark are not arguing about the ITEM."""
        self.assertEqual(G.grade("Gheed’s Fortune", "Gheed's Fortune")[0], G.AGREE)

    def test_one_empty_side_is_UNKNOWN_not_DISAGREE(self):
        v, why = G.grade("Shako", "")
        self.assertEqual(v, G.UNKNOWN, "an unasked question was graded as a failed one")
        self.assertIn("unasked", why)

    def test_only_AGREE_and_DISAGREE_reach_the_denominator(self):
        real = G._load
        G._load = lambda: {"lane": {G.AGREE: 3, G.DISAGREE: 1, G.UNKNOWN: 99}}
        try:
            rep = G.report()["lane"]
        finally:
            G._load = real
        self.assertEqual(rep["judged"], 4, "UNKNOWN leaked into the Wilson denominator")
        self.assertEqual(rep["unknown"], 99, "the unknowns were dropped instead of reported")
        self.assertIsNotNone(rep["wilson"])

    def test_no_evidence_scores_None_not_zero(self):
        real = G._load
        G._load = lambda: {"lane": {}}
        try:
            self.assertIsNone(G.report()["lane"]["wilson"])
        finally:
            G._load = real

    def test_the_wrapper_returns_the_ORIGINAL_answer_always(self):
        """A grader, not a censor. A second opinion that silently overwrote the first would make
        every downstream number unattributable."""
        def reader(path, *a, **kw):
            return {"name": "Windforce"}
        wrapped = G.gated(reader, "stash", lane="t")
        self.assertEqual(wrapped("/nope/missing.jpg"), {"name": "Windforce"})

    def test_the_wrapper_NEVER_raises_into_a_sweep(self):
        """A retro sweep walks hundreds of frames; an exception here costs a whole reel."""
        def reader(path, *a, **kw):
            return "Shako"
        def boom(path, *a, **kw):
            raise RuntimeError("the second reader exploded")
        wrapped = G.gated(reader, "stash", lane="t", second=boom)
        self.assertEqual(wrapped("/nope/missing.jpg"), "Shako")

    def test_bypass_only_applies_to_an_AIMED_run(self):
        self.assertTrue(G.bypassed_witnesses(focus="stash"))
        self.assertFalse(G.bypassed_witnesses(focus=None),
                         "shadow and plain ON AIR are not aimed at anything and must keep the "
                         "witness rule")


class TestTheClustererOnHisOwnFrames(unittest.TestCase):
    """★ HIS ACTUAL FRAMES ARE THE FIXTURES. Every list below was read off his 2026-08-30 session.

    A tooltip paints the name AND its stats in one frame, so the noise is not scattered — it
    clusters around the item it came from. That is what makes a garble resolvable: it shares a
    frame with the clean name.
    """

    F_CRESCENT = ["Crescent Moon", "CkESCENT rn\u2022\u2022N", "'SHAELVmTIR'",
                  "EASED ArtACX SpEE", "1O% CNAHt"]
    F_DEATHMASK = ["Death Mask", "DffiffJE.. tts I", "'Ii'"]
    F_TWO_ITEMS = ["Rune Grip Ring", "Snowy Grand Charm", ",*-RuHE GRIP"]

    def test_the_clean_name_wins_over_its_own_garble(self):
        c = G.cluster(self.F_CRESCENT)
        self.assertEqual(c["name"], "Crescent Moon")
        self.assertIn("'SHAELVmTIR'", c["garbles"],
                      "the runeword's RUNES were promoted to an item instead of supporting text")

    def test_stat_lines_are_separated_from_names(self):
        c = G.cluster(self.F_CRESCENT)
        self.assertEqual(sorted(c["stats"]), sorted(["EASED ArtACX SpEE", "1O% CNAHt"]),
                         "stat lines were not separated — today they count as text seen and never "
                         "read, and one of them was briefly chosen AS the item name")

    def test_ONE_FRAME_CAN_HOLD_TWO_ITEMS(self):
        """The model that assumed one name per frame would have dropped Rune Grip Ring — the
        very item that registered truncated as 'Rune Grip'."""
        c = G.cluster(self.F_TWO_ITEMS)
        self.assertEqual(sorted(c["names"]), ["Rune Grip Ring", "Snowy Grand Charm"])
        self.assertIn(",*-RuHE GRIP", c["garbles"])

    def test_garbage_does_not_beat_a_short_clean_name(self):
        """The defect this class was written from: cleanliness was scored on the NORMALISED
        string, which strips the punctuation that made it dirty, and then multiplied by length —
        so 'DffiffJE.. tts I' out-scored 'Death Mask'."""
        c = G.cluster(self.F_DEATHMASK)
        self.assertEqual(c["name"], "Death Mask")
        self.assertGreater(G.cleanliness("Death Mask"), G.cleanliness("DffiffJE.. tts I"))

    def test_cleanliness_is_measured_on_the_RAW_string(self):
        """Normalising first destroys the evidence being judged."""
        self.assertLess(G.cleanliness("CkESCENT rn\u2022\u2022N"), G.cleanliness("Crescent Moon"))
        self.assertLess(G.cleanliness("'SHAELVmTIR'"), 0.62)

    def test_a_frame_of_pure_noise_promotes_NOTHING(self):
        c = G.cluster(["'Ii'", "\u2022)s&41", "vtL? lSr"])
        self.assertEqual(c["names"], [], "noise was promoted to an item name")
        self.assertTrue(c["why"], "it promoted nothing and did not say why")

    def test_the_session_contradicts_a_lone_wrong_location(self):
        """'Rune Grip' registered at loc 'floor' while everything around it said stash."""
        loc, why = G.corroborate_location(
            [{"loc": "stash"}, {"loc": "stash"}, {"loc": "floor"}, {"loc": "stash"}])
        self.assertEqual(loc, "stash")
        self.assertIn("second look", why,
                      "it corrected the outlier silently instead of flagging it")

    def test_no_location_anywhere_is_UNKNOWN_not_a_guess(self):
        loc, why = G.corroborate_location([{}, {}])
        self.assertIsNone(loc)
        self.assertIn("no read", why)


class TestTheNameFloorHoldsBOTHWays(unittest.TestCase):
    """★ TUNED AGAINST HIS OWN REELS, AND EVERY MOVE WAS A CORRECTION OF MY LAST ONE.

    Run over the 12 reels from his session, the clusterer promoted "REQ", "KING", "UNDEAD" and
    "RADIANCE" with a PERFECT 1.00 — higher than "Heart of the Oak" at 0.81 — because they are pure
    letters with no punctuation and no mid-word capital, which was everything the metric looked at.
    They are fragments of stat lines ("REQuired Level", "Area of KING Leoric").

    ⚠ THE FIRST FIX BROKE A REAL ITEM. Penalising any single word of <=6 characters knocked "Shako"
    — a genuine grail unique — to 0.55, below the floor. Length was never the signal; being
    SHOUTED was. Both conditions together, or neither.

    A guard that only checked one direction would have been satisfied by a metric that rejects
    everything, so both lists are asserted.
    """

    REAL = ("Crescent Moon", "Death Mask", "Blade of Ali Baba", "Heart of the Oak",
            "Shako", "Lionheart", "Windforce", "Tarnhelm", "The Grandfather")
    FRAGMENTS = ("REQ", "KING", "UNDEAD", "HEAR T \u2022F THE &AK")

    def test_every_real_item_name_clears_the_floor(self):
        for n in self.REAL:
            self.assertGreaterEqual(G.cleanliness(n), 0.62,
                                    "%r scores below the floor — a real grail item would be "
                                    "discarded as garble" % n)

    def test_every_stat_fragment_is_rejected(self):
        for n in self.FRAGMENTS:
            self.assertLess(G.cleanliness(n), 0.62,
                            "%r scores as an item name — it is a piece of a stat line" % n)

    def test_shako_specifically_survives_the_short_word_rule(self):
        """The regression this class exists to prevent: 5 letters, one word, and a real unique."""
        self.assertGreaterEqual(G.cleanliness("Shako"), 0.62)

    def test_a_shouted_fragment_and_a_titlecase_name_are_told_apart(self):
        self.assertLess(G.cleanliness("KING"), G.cleanliness("Shako"))

    def test_the_tooltip_CATEGORY_line_is_a_stat_not_a_name(self):
        """D2R prints "Sword Class" / "Staff Class" under the name. "STAff CLAs$" scored 0.82."""
        for t in ("STAff CLAs$", "Sw\u2022AO CLASS", "Required Level: 47",
                  "Ethereal (Cannot be Repaired), Socketed (3)"):
            self.assertTrue(G.looks_like_a_stat(t), "%r was not recognised as a stat line" % t)
        for t in ("Crescent Moon", "Shako", "Heart of the Oak"):
            self.assertFalse(G.looks_like_a_stat(t),
                             "%r was mistaken for a stat line — it is an ITEM" % t)

    def test_his_full_frame_separates_into_three_clean_buckets(self):
        c = G.cluster(["Crescent Moon", "CkESCENT rn\u2022\u2022N", "'SHAELVmTIR'",
                       "STAff CLAs$", "EASED ArtACX SpEE", "REQ"])
        self.assertEqual(c["names"], ["Crescent Moon"])
        self.assertIn("STAff CLAs$", c["stats"])
        self.assertIn("REQ", c["garbles"])


if __name__ == "__main__":
    # non-ascii lives in these docstrings; a CLI that prints it must say so or it dies on a
    # console whose encoding is not UTF-8 — the same guard every other suite here carries.
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
