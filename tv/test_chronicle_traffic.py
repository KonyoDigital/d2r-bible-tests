#!/usr/bin/env python3
"""THE WHOLE GRAIL THROUGH THE CHRONICLE CHAIN, AND THEN ALL AT ONCE.

The symmetric half of test_vault_traffic.py. Konyo asked whether every item had been simulated
through the VAULT routing and whether it had been fed 300-500 at once; the same question is owed to
the CHRONICLE lane, which is the bigger one — 398 uniques + 135 set pieces = 533 names — and the one
whose numbers he checks against his game.

WHAT WAS ALREADY COVERED. test_chronicle_retro.py has 162 tests and they are thorough about the
LAWS: a verdict explains itself either way, every reel folds into one proposal, a scroll's later
pages are read and not just the first, two lanes agreeing are two witnesses. Every one of them uses
a handful of hand-made names. NOTHING drove the full universe, and nothing tested VOLUME.

WHAT THIS ADDS: the whole roster through proposal_from_pages -> gate_verdict -> merge_proposals, the
corroboration law at 533 names rather than three, order-independence across many reels at scale, and
a duplicate-heavy read that must not inflate anything.
"""
import json
import os
import random
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

import chronicle_retro as cr          # noqa: E402
import chronicle_resolve as res       # noqa: E402


def _pages(names, ledger="uniques", reel="s_sim", frames=2, lanes=("claude", "grok")):
    """The shape sweep_frames hands to proposal_from_pages: one entry per frame per lane."""
    out = []
    for f in range(frames):
        for ln in lanes:
            out.append({"reel": reel, "frame": "f%d.jpg" % f,
                        "resp": {"kind": "chronicle", "ledger": ledger, "lane": ln, "conf": 0.9,
                                 "stateVisible": True, "found": list(names), "notFound": [],
                                 "sets": [], "witness": "cross-frame"}})
    return out


class _Base(unittest.TestCase):
    @staticmethod
    def universe():
        roster = res.load_roster()
        sets = res.load_set_roster()
        return sorted(set(roster.values())), sorted(set(sets.values())) if sets else []


class TestTheWholeGrailGrounds(_Base):
    def test_every_unique_in_his_roster_reaches_a_verdict(self):
        uni, _ = self.universe()
        self.assertGreaterEqual(len(uni), 300, "the roster did not load — this would pass on nothing")
        prop = cr.proposal_from_pages(_pages(uni))
        self.assertEqual(len(prop["uniques"]), len(uni),
                         "%d name(s) went in and never reached the proposal"
                         % (len(uni) - len(prop["uniques"])))
        held = [n for n in uni if not cr.gate_verdict(n, prop["uniques"][n]).get("pass")]
        self.assertEqual(held, [], "%d corroborated name(s) were still held: %s"
                                   % (len(held), held[:5]))

    def test_every_set_piece_too(self):
        _, sets = self.universe()
        if not sets:
            self.skipTest("no set roster on this machine")
        prop = cr.proposal_from_pages(_pages(sets, ledger="sets"))
        self.assertEqual(len(prop["sets"]), len(sets))
        held = [n for n in sets if not cr.gate_verdict(n, prop["sets"][n]).get("pass")]
        self.assertEqual(held, [], "%d set piece(s) held: %s" % (len(held), held[:5]))

    def test_one_lane_on_one_frame_grounds_NOTHING(self):
        """The corroboration law at full scale, not on three names."""
        uni, _ = self.universe()
        prop = cr.proposal_from_pages(_pages(uni, frames=1, lanes=("claude",)))
        passed = [n for n in uni if cr.gate_verdict(n, prop["uniques"][n]).get("pass")]
        self.assertEqual(passed, [], "%d name(s) grounded on a single sighting" % len(passed))

    def test_every_held_verdict_still_says_why(self):
        uni, _ = self.universe()
        prop = cr.proposal_from_pages(_pages(uni[:40], frames=1, lanes=("claude",)))
        for n in uni[:40]:
            v = cr.gate_verdict(n, prop["uniques"][n])
            self.assertFalse(v.get("pass"))
            self.assertTrue(str(v.get("why") or "").strip(),
                            "a refusal with no reason reaches him as a shrug: %r" % n)


class TestTraffic(_Base):
    def test_the_whole_universe_in_one_proposal_is_fast_and_lossless(self):
        uni, sets = self.universe()
        every = uni + sets
        t0 = time.time()
        prop = cr.proposal_from_pages(_pages(uni) + _pages(sets, ledger="sets"))
        dt = time.time() - t0
        self.assertEqual(len(prop["uniques"]) + len(prop["sets"]), len(every),
                         "names were lost between the pages and the proposal")
        self.assertLess(dt, 20.0, "%d names took %.1fs — the fold is not linear" % (len(every), dt))

    def test_a_page_read_two_hundred_times_is_still_one_row_per_name(self):
        uni, _ = self.universe()
        names = uni[:50]
        prop = cr.proposal_from_pages(_pages(names, frames=100))     # 100 frames x 2 lanes
        self.assertEqual(len(prop["uniques"]), len(names))
        for n in names:
            self.assertTrue(cr.gate_verdict(n, prop["uniques"][n]).get("pass"))

    def test_many_reels_fold_into_one_answer_whatever_the_order(self):
        """merge_proposals across 12 reels, shuffled — order-independence at scale."""
        uni, _ = self.universe()
        chunks = [uni[i::12] for i in range(12)]
        props = [cr.proposal_from_pages(_pages(c, reel="s_%02d" % i)) for i, c in enumerate(chunks)]
        a = props[:]
        b = props[:]
        random.Random(7).shuffle(b)
        fold_a, fold_b = a[0], b[0]
        for p in a[1:]:
            fold_a = cr.merge_proposals(fold_a, p)
        for p in b[1:]:
            fold_b = cr.merge_proposals(fold_b, p)
        self.assertEqual(sorted(fold_a["uniques"]), sorted(fold_b["uniques"]),
                         "the order reels came off disk changed which names exist")
        self.assertEqual(sorted(fold_a["uniques"]), sorted(uni),
                         "folding twelve reels lost names")


class TestTheFoldOnRealMisreads(_Base):
    """The chronicle lane DOES near-match, deliberately — a Chronicle page is a closed list of grail
    names, so the nearest roster entry is very likely right. (The vault lane refuses near matches for
    the opposite reason; see test_vault_traffic.)"""

    def test_the_corrections_his_own_sweep_made_still_fold(self):
        roster = res.load_roster()
        for raw, want in (("Atma's Scarab", "Atma’s Scarab"),
                          ("Battlecage", "Rattlecage"),
                          ("Saracen's Chance", "Saracen’s Chance")):
            self.assertEqual(res.canonical(raw, roster), want,
                             "%r stopped folding onto %r" % (raw, want))

    def test_a_coin_flip_between_two_real_grails_stays_UNFOLDED(self):
        """His roster really does hold a pair one letter apart, and it was found by trying every
        single-letter deletion of every roster key rather than by imagining one:

            probe 'stormspie'  ->  Stormspire (0.947)  vs  Stormspike (0.947)

        Two REAL grail items, tied to three decimal places. A reader that drops one letter of
        Stormspike would otherwise be recorded as finding Stormspire — a find he never made — and
        merge-max would keep it. canonical() must return None here, and the ambiguity gap is what
        makes it. [[d2r-multiwitness-corroboration]]"""
        roster = res.load_roster()
        vals = set(roster.values())
        if not {"Stormspire", "Stormspike"} <= vals:
            self.skipTest("the Stormspire/Stormspike pair is not in this roster")
        self.assertIsNone(res.canonical("stormspie", roster),
                          "an ambiguous fold picked one of two real grail items")
        # and the mirror: each FULL name still folds onto itself, or the gap is just breaking things
        self.assertEqual(res.canonical("Stormspire", roster), "Stormspire")
        self.assertEqual(res.canonical("Stormspike", roster), "Stormspike")

    def test_no_probe_in_his_roster_can_be_folded_into_the_WRONG_twin(self):
        """The sweep behind the test above, kept as a standing check: every one-letter deletion of
        every roster key, and any that lands ambiguously must fold to None rather than to a name.
        Measured today: 398 keys, one ambiguous pair, folded to None."""
        import difflib
        roster = res.load_roster()
        keys = list(roster)
        wrong = []
        for k in keys:
            for i in range(len(k)):
                probe = k[:i] + k[i + 1:]
                m = difflib.get_close_matches(probe, keys, n=2, cutoff=res.NEAR_CUTOFF)
                if len(m) < 2:
                    continue
                a = difflib.SequenceMatcher(None, probe, m[0]).ratio()
                b = difflib.SequenceMatcher(None, probe, m[1]).ratio()
                if a - b < res.AMBIGUITY_GAP and res.canonical(probe, roster) is not None:
                    wrong.append((probe, res.canonical(probe, roster)))
        self.assertEqual(wrong, [], "an ambiguous probe was folded onto a name: %s" % wrong[:4])

    def test_pure_debris_folds_onto_nothing(self):
        roster = res.load_roster()
        for junk in ("Sort by", "Newest to Oldest", "zzzzqqqq"):
            self.assertIsNone(res.canonical(junk, roster),
                              "%r was folded onto a real grail item" % junk)


if __name__ == "__main__":
    unittest.main(verbosity=2)
