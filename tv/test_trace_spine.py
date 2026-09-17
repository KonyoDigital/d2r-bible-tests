# -*- coding: utf-8 -*-
"""#99 — THE SPINE, AND THE HALF OF IT THAT PROVES A FILTER EXISTS.

HIS ORDER, 2026-09-15, the negative half: *"or a chronicle scenario or a farming scenario it can
not be vaulted.. so we will hope to see that it does work and doesnt vault things it shouldnt"*.

★ A FILTER THAT ONLY EVER SAYS YES IS INDISTINGUISHABLE FROM NO FILTER AT ALL, and this one has
never been asked the question that matters. extract_gap's own docstring says so out loud:

    "of the four sealed reels carrying names, 1 is chronicle-only and 0 are floor-only. The floor
     arm is real law and is currently unwitnessed on this store — said out loud rather than left
     to look covered."  [[gate-blind-to-unexercised-input]]

So the FLOOR road has never been driven by his data. An observational test over his store would
pass the floor law having examined ZERO floor-only names — a clean green with an empty
denominator. Every negative law below therefore DRIVES the real predicates with a constructed
scenario, and the observational pass publishes its denominator beside its verdict.

★ WHAT IS PINNED, AND WHAT IS DELIBERATELY NOT
Pinned: the LAWS — a floor scenario cannot vault, a chronicle scenario cannot vault, independence
is counted on normalised reels, an unreadable source is UNKNOWN rather than zero, and the vault
whitelist is READ from bible.html rather than copied.
NOT pinned: the numbers. `tv/test_a_seal_is_per_session.py` says why — a gate pinned to the bytes
of a fix holds the spelling of that fix in place and grades nothing about the behaviour. The one
figure asserted is a FLOOR (>0), never an equality. [[regression-guard]]

⚠ AND THE SUBJECT COMES FIRST. A law that cannot find what it grades passes having examined
nothing, which is the most convincing green there is.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import live_store as _LS
import trace_spine as TS


#: A sighting shaped exactly as the chronicle sweep writes one.
def _sg(reel, frame, lane="claude", conf=0.9):
    return {"reel": reel, "frame": frame, "lane": lane, "conf": conf}


class TheSubjectExists(unittest.TestCase):
    """⚠ FIRST. Every law below is vacuous if these are gone."""

    def test_the_spine_can_find_its_four_hops(self):
        self.assertEqual(("reel", "ledger", "routing", "endpoint"), TS.HOPS)
        for fn in ("hop_reel", "hop_ledger", "hop_routing", "hop_endpoint", "spine", "negative"):
            self.assertTrue(callable(getattr(TS, fn, None)), "trace_spine.%s is gone" % fn)

    def test_the_vault_whitelist_is_READ_from_bible_html_not_copied(self):
        """A copy of `_VAULT_LANES` here would drift silently in the direction that matters — a
        lane added in bible.html and not here reads as REFUSED in this trace while the real door
        lets it through. [[copy-drift]]"""
        lanes, why = TS._vault_lanes()
        self.assertIsNotNone(lanes, why)
        self.assertIn("stash", lanes, "the parsed whitelist has no 'stash' — it is not the real "
                                      "list, and every routing verdict below is judged against a "
                                      "list nobody uses")
        src = io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()
        self.assertIn("window._VAULT_LANES", src,
                      "bible.html no longer declares the whitelist this gate parses")
        # the module must not carry its own copy of the lane names
        mine = io.open(os.path.join(HERE, "trace_spine.py"), encoding="utf-8").read()
        body = mine.split('"""', 2)[-1]          # past the module docstring
        self.assertNotIn("'equipped', 'stash'", body)
        self.assertNotIn('"equipped", "stash"', body)

    def test_extract_gaps_law_is_CALLED_not_reimplemented(self):
        import extract_gap as EG
        self.assertTrue(callable(getattr(EG, "holding_possible", None)),
                        "extract_gap.holding_possible is gone — the routing law this gate drives "
                        "no longer exists and every negative law below grades nothing")


# ══════════════════════════════════════════════════════════════════════════════════════════════
# THE NEGATIVE LAWS — the ones that prove a filter is there
# ══════════════════════════════════════════════════════════════════════════════════════════════
class AFarmingScenarioCannotVault(unittest.TestCase):

    def test_a_FLOOR_scenario_produces_NO_vault_row(self):
        """HIS RULING, quoted in extract_gap: "if its a FLOOR ITEM with no stash/inventory open
        then obviously it cant be in the same exact route". An item on the ground has no cell, so
        there is no location to claim, so there is no holding.

        ⚠ DRIVEN, NOT OBSERVED. His store has ZERO floor-only reels, so nothing real exercises
        this arm.

        ⚠⚠ AND IT IS DRIVEN WITH `loc='stash'` ON PURPOSE — THE FIRST CUT OF THIS TEST WAS
        DECORATIVE. It passed `loc=None`, so `may_vault` refused on its own and `allowed` was
        False whatever the scenario said. Measured: FIFTEEN sabotages of the routing code — `or`
        for `and`, the scenario ignored entirely, the filter refusing everything — and this test
        stayed GREEN through all of them, because the half it exists to grade was never
        load-bearing. Handing it a real vault lane makes the SCENARIO the only thing that can
        refuse. [[feedback-blind-fixture-green-gate]] [[regression-guard]]
        """
        r = TS.negative([_sg("s_farm_1", "f_1.jpg")],
                        {"panel": 0, "floor": 12, "chronicle": 0}, loc="stash")
        self.assertEqual("FLOOR", r["scenario"])
        self.assertIs(True, r["mayVault"],
                      "the lane half is refusing, so the scenario half is not being graded — "
                      "this test would pass on a filter that does not exist")
        self.assertIs(False, r["holdingPossible"],
                      "a farming reel was told a holding is possible: %s" % r["why"])
        self.assertIs(False, r["allowed"],
                      "A FARMING SCENARIO WAS ALLOWED TO VAULT. %s" % r["why"])

    def test_a_CHRONICLE_scenario_produces_NO_vault_row(self):
        """A Chronicle page is a checklist of items he mostly does not own — never a possession.
        Backfilling those into the vault would not be a join; it would invent holdings.

        ⚠ Same correction as the floor law above: driven with a real vault lane, so the scenario
        is the only predicate that can refuse."""
        r = TS.negative([_sg("s_chron_1", "f_1.jpg")],
                        {"panel": 0, "floor": 0, "chronicle": 45}, loc="stash")
        self.assertEqual("CHRONICLE", r["scenario"])
        self.assertIs(True, r["mayVault"],
                      "the lane half is refusing, so this law is not grading the scenario")
        self.assertIs(False, r["holdingPossible"],
                      "a Chronicle page was told a holding is possible: %s" % r["why"])
        self.assertIs(False, r["allowed"],
                      "A CHRONICLE SCENARIO WAS ALLOWED TO VAULT. %s" % r["why"])

    def test_a_FLOOR_scenario_cannot_be_rescued_by_handing_it_a_vault_LANE(self):
        """⚠⚠ THE TWO PREDICATES MUST BOTH HOLD, AND THIS IS THE ONE THAT CATCHES AN `or`.
        A floor name arriving with loc='stash' — a misread, or a name seen in two places — must
        still be refused. If either predicate alone could pass it, the scenario filter would be
        decorative."""
        r = TS.negative([_sg("s_farm_1", "f_1.jpg")],
                        {"panel": 0, "floor": 12, "chronicle": 0}, loc="stash")
        self.assertIs(True, r["mayVault"], "the lane half of this test is not exercising anything")
        self.assertIs(False, r["allowed"],
                      "a FLOOR scenario carrying a vault lane was allowed through — the two "
                      "predicates are being combined with `or`, not `and`. %s" % r["why"])

    def test_a_PANEL_scenario_with_a_vault_lane_IS_allowed(self):
        """⚠ THE POSITIVE CONTROL. Without it every law above passes on a filter that refuses
        EVERYTHING, which is just as broken and much harder to notice."""
        r = TS.negative([_sg("s_stash_1", "f_1.jpg")],
                        {"panel": 5, "floor": 0, "chronicle": 0}, loc="stash")
        self.assertEqual("PANEL", r["scenario"])
        self.assertIs(True, r["allowed"],
                      "a real stash panel sighting was refused — the filter now says no to "
                      "everything, which no test above could tell from working. %s" % r["why"])

    def test_a_PANEL_scenario_with_NO_established_location_is_still_refused(self):
        """An unestablished provenance is refused, never guessed. `_sighting_loc` returns None for
        'not established' and that must never read as 'nowhere he keeps things' OR as a pass."""
        r = TS.negative([_sg("s_stash_1", "f_1.jpg")],
                        {"panel": 5, "floor": 0, "chronicle": 0}, loc=None)
        self.assertIs(False, r["allowed"],
                      "a name with NO location claimed a vault row: %s" % r["why"])

    def test_an_UNREADABLE_journal_is_UNKNOWN_and_not_a_refusal(self):
        """`names_known=False` means the journal ring could not be read. Nobody measured zero
        holdings — nobody asked. It must not come back False, which would read as a clean
        refusal. [[unknown-stays-unknown]]"""
        r = TS.negative([], {"panel": 0, "floor": 0, "chronicle": 0}, names_known=False)
        self.assertIsNone(r["holdingPossible"],
                          "an unreadable journal answered %r — a measured refusal, from a "
                          "question nobody could ask" % (r["holdingPossible"],))
        self.assertIsNone(r["allowed"], "the route came back %r on an UNKNOWN input"
                          % (r["allowed"],))


# ══════════════════════════════════════════════════════════════════════════════════════════════
# INDEPENDENCE — the 83/83 defect, aimed at this spine
# ══════════════════════════════════════════════════════════════════════════════════════════════
class IndependenceIsIndependentOfItself(unittest.TestCase):

    def test_one_reel_under_TWO_SPELLINGS_is_ONE_reel(self):
        """MEASURED on his store: 25 distinct reel strings are 15 real reels, and 318 of 324 names
        carry a reel under both spellings. An independence count on the raw string sees up to
        twice the reels that exist — the 83/83 shape (2 attacks x 40 reels, true 0.5655)."""
        sl = [_sg("reel_s_1_2", "f_a.jpg"), _sg("s_1_2", "f_b.jpg")]
        ind = TS.independence(sl)
        self.assertEqual(1, ind["independentReels"],
                         "the same reel spelled two ways counted as %d independent reels: %s"
                         % (ind["independentReels"], ind["reels"]))

    def test_a_duplicate_ROW_is_reported_beside_the_raw_count_never_instead_of_it(self):
        """⚠ BOTH NUMBERS OR NEITHER. Publishing only `rows` inflates; publishing only `deduped`
        hides that the store is duplicating. A reader needs to see the gap. [[zero-needs-a-denominator]]"""
        sl = [_sg("reel_s_1_2", "f_a.jpg"), _sg("s_1_2", "f_a.jpg"), _sg("s_9_9", "f_c.jpg")]
        ind = TS.independence(sl)
        self.assertEqual(3, ind["rows"])
        self.assertEqual(2, ind["deduped"])
        self.assertEqual(1, ind["duplicateRows"])
        for k in ("rows", "deduped", "duplicateRows", "independentReels"):
            self.assertIn(k, ind, "independence() stopped publishing %r" % k)

    def test_two_LANES_on_one_reel_are_still_two_lanes(self):
        """cross-lane is a real witness — a different eye read the same row. Collapsing on reel
        alone would throw it away."""
        ind = TS.independence([_sg("s_1_2", "f_a.jpg", lane="claude"),
                               _sg("s_1_2", "f_a.jpg", lane="grok")])
        self.assertEqual(2, ind["deduped"], "a second lane on the same frame was deduped away")
        self.assertEqual(1, ind["independentReels"])

    def test_the_apostrophe_glyph_does_not_break_the_join(self):
        """MEASURED 2026-09-06: "Saracen's Chance" is STRAIGHT (U+0027) in d2r_owned and CURLY
        (U+2019) in foundLog, gameFound and the evidence ledger. It has testimony in all three and
        an exact-string join finds none of it."""
        self.assertEqual(TS.name_key("Saracen’s Chance"), TS.name_key("Saracen's Chance"))
        self.assertEqual(TS.name_key("Bul-Kathos’ Wedding Band"),
                         TS.name_key("Bul-Kathos' Wedding Band"))


# ══════════════════════════════════════════════════════════════════════════════════════════════
# THE WALK — where it stopped, and that an unknown stops it differently from a refusal
# ══════════════════════════════════════════════════════════════════════════════════════════════
class TheWalkSaysWhereItStopped(unittest.TestCase):

    def test_a_name_no_reel_ever_saw_stops_at_HOP_ONE(self):
        r = TS.spine("Totally Not A Real Item", counts={"panel": 1}, loc="stash")
        self.assertEqual("reel", r["stoppedAt"],
                         "a name with no sighting walked past the first hop: %s" % r["stoppedWhy"])
        self.assertFalse(r["complete"])

    def test_an_UNREADABLE_store_stops_the_walk_as_UNKNOWN_not_as_a_refusal(self):
        """⚠ THE TWO STOPS ARE DIFFERENT FACTS. False = measured and refused. None = nobody could
        ask. A spine that folds them reports a broken road as a clean one."""
        empty = {"chron": None, "vault_accum": None, "vault_seen": None,
                 "unreadable": ["chron_evidence.json is not on disk"]}
        r = TS.spine("Harlequin Crest", counts={"panel": 1}, loc="stash", stores=empty)
        self.assertEqual("reel", r["stoppedAt"])
        self.assertTrue(r["stoppedWhy"].startswith("UNKNOWN"),
                        "an unreadable store reported %r — that reads as a measured refusal"
                        % r["stoppedWhy"])
        self.assertTrue(r["unreadable"], "the walk did not carry WHICH source was unreadable")

    def test_the_endpoint_admits_the_chronicle_side_is_not_on_disk(self):
        """⚠ THE SPINE IS ASYMMETRIC AND MUST SAY SO. board_tally.json carries totals per route
        and no name list, so per-name chronicle membership cannot be answered from disk. Reporting
        False there would be a clean answer to an unasked question."""
        h = TS.hop_endpoint("harlequin crest", TS._stores())
        self.assertIsNone(h["chronicle"],
                          "the endpoint claimed to know per-name chronicle membership (%r) — it "
                          "is not on disk" % (h["chronicle"],))
        self.assertIn("UNKNOWN", h["chronicleWhy"])


# ══════════════════════════════════════════════════════════════════════════════════════════════
# HIS REAL STORE — observational, and every verdict carries its denominator
# ══════════════════════════════════════════════════════════════════════════════════════════════
class OnHisRealStore(unittest.TestCase):
    """⚠⚠ EVERY LAW HERE READS HIS LIVE STORES — the class says so in its own header, and all
    three call `TS._stores()`. `chron_evidence.json` (2.2 MB), `vault_accum.json` and
    `vault_seen.json` are untracked and exist only on his Mac, so on a runner they come back empty
    and these fail with sentences that read as product defects: "chron_evidence.json unreadable",
    "the vault bank holds no named rows". Neither is a statement about the code.

    ⚠ A CLASS-LEVEL SKIP IS CORRECT *HERE* AND WAS WRONG AN HOUR AGO. In
    test_the_admission_bar_knows_what_it_would_admit I put the same call in setUp while four of
    its five laws STUB the loader — so the whole gate stood down and reported green having run
    nothing (REG-1053). The difference is not style, it is whether every law in the class actually
    needs the data. Here it is declared in the class docstring and confirmed by reading all three.
    [[regression-guard]] [[unknown-stays-unknown]]"""

    def setUp(self):
        _LS.require(self, "chron_evidence.json", "vault_accum.json", "vault_seen.json",
                    why="every law in this class is observational over HIS real store; without it "
                        "there are no names to walk and no bank to check them against")

    def test_the_evidence_store_is_READABLE_and_not_empty(self):
        st = TS._stores()
        self.assertIsNotNone(st["chron"], "chron_evidence.json unreadable: %s" % st["unreadable"])
        n = len((st["chron"].get("uniques") or {}))
        self.assertGreater(n, 0, "the evidence store holds no uniques, so every observational "
                                 "law below would grade ZERO names")

    def test_a_real_name_walks_at_least_to_the_LEDGER(self):
        """A FLOOR, never an equality — his ledger grows. Pinning the count would fail on the next
        sweep and say nothing about the law. [[regression-guard]]"""
        st = TS._stores()
        names = list((st["chron"].get("uniques") or {}))
        self.assertTrue(names, "no name to walk")
        walked = 0
        for nm in names[:25]:
            r = TS.spine(nm, counts={"panel": 1}, loc="stash", stores=st)
            if r["hops"][0]["reached"] and r["hops"][1]["reached"]:
                walked += 1
        self.assertGreater(walked, 0,
                           "not one of 25 real names reached the ledger hop — the join between "
                           "the evidence store and this spine is broken")

    def test_no_name_reaches_the_vault_WITHOUT_a_vault_row_behind_it(self):
        """THE NEGATIVE, OBSERVED. Whatever the routing decision says, hop 4 reports the vault
        only when a row for that name is actually in the bank. A trace that says VAULT with no
        row is the 'plumbing with no tap' shape: a decision nobody executed."""
        # the class-level require above covers this — its own message already said "UNKNOWN,
        # not a clean surface"; it simply failed instead of standing down.
        st = TS._stores()
        rows = list((st["vault_accum"] or {}).get("owned") or []) + \
               list((st["vault_seen"] or {}).get("rows") or [])
        banked = {TS.name_key(r.get("name")) for r in rows if isinstance(r, dict)}
        # ⚠ the denominator, published with the verdict
        self.assertGreater(len(banked), 0,
                           "the vault bank holds no named rows at all, so this law examined ZERO "
                           "candidates — UNKNOWN, not a clean surface")
        bad = []
        for nm in list((st["chron"].get("uniques") or {}))[:60]:
            h = TS.hop_endpoint(TS.name_key(nm), st)
            if h["vault"] and TS.name_key(nm) not in banked:
                bad.append(nm)
        self.assertEqual([], bad, "hop 4 reported VAULT for names with no bank row: %s" % bad[:5])
        print("   ℹ examined 60 names against %d banked vault names" % len(banked))


if __name__ == "__main__":
    unittest.main(verbosity=2)
