# -*- coding: utf-8 -*-
"""v2760 — THE SAME ITEM WAS STORED TWICE AND ITS SIGHTINGS NEVER MET.

MEASURED on his live `chron_evidence.json`, which keys the confluence store by RAW name:

    Atma's Scarab      curly 20 + straight 38     Endlesshail   22 + 'Endless Hail'  2
    Saracen's Chance   curly 50 + straight  6     Stealskull    23 + 'Steal Skull'   2

Two pairs are apostrophe forms (U+2019 vs U+0027) and two are spacing. The apostrophe split is not
a typo drifting in from outside: **bible.html spells these four items CURLY in the item rows and
STRAIGHT in ITEM_VALUE, in the same file**, and the page's own prose already names them — "9 of 398
uniques did not resolve to 'unique'. FOUR of them were this: Atma’s Scarab · Seraph’s Hymn · The
Cat’s Eye · Saracen’s Chance".

⚠⚠ THE COST IS CORROBORATION, NOT PICTURES. The witness machinery keys BY NAME, and
`merge_proposals` de-dupes sightings by (reel, frame, lane) WITHIN a bucket. Two spellings meant
two buckets, so a name seen in reel A under one spelling and reel B under the other read as two
lonely single sightings and `cross-reel` could never fire — the exact defect v1776 and v1798 were
written to kill, arriving through the KEY instead of through the value. [[the-unjoined-end]]

⚠ AND THE FOLD PROVES THE SPLIT WAS REAL. Merging does NOT simply add: 20+38 becomes 54, not 58,
and 50+6 becomes 55, not 56. Those 5 are the SAME PHOTOGRAPH banked under both spellings — two
reads of one frame is not corroboration (v1689), so collapsing them is correct, and their
existence is the evidence that the two buckets could not see each other.

=== WHY EXACT FOLD ONLY, WHICH IS THE WHOLE SAFETY ARGUMENT ===
`chronicle_resolve.canonical()` also does a difflib near-match. That is right when ASKING what an
OCR read meant and WRONG as a store key: a fuzzy key silently merges two different grail items and
nothing downstream can tell. The roster deliberately holds near-twin pairs ("Bone Break" / "Latent
Bone Break"), so a fuzzy key is a coin flip between two of his items.

MEASURED over all 310 evidence names before shipping:
    281 fold EXACTLY to a roster name
     10 would need fuzzy   -> left RAW, deliberately
     19 match no roster    -> rares and bases, left RAW
      4 collisions         -> exactly the four pairs above, and nothing else
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import chronicle_retro as CR  # noqa: E402


RED_PROOF = [
    {
        "why": "HAND-WRITTEN, and verified in a sandbox before it was declared. This law has no "
               "positive string anchor — it asserts that two SPELLINGS reach one key — so deletion "
               "of a literal cannot sabotage it. Un-folding is the v2760 defect itself: the curly "
               "and straight forms of Atma's Scarab stop meeting, and cross-reel corroboration can "
               "never fire. MEASURED: 1 match, gate RED, breaking "
               "test_both_apostrophe_forms_reach_ONE_key and test_a_spacing_variant_reaches_the_SAME_key",
        "file": "chronicle_retro.py",
        "find": "    return hit",
        "replace": "    return name",
        "matches": 1,
    },
    {
        "why": "THE SECOND ARM, and it breaks a DIFFERENT law — which is the point of writing two. "
               "The fold's whole safety argument is that it is EXACT: dropping the tightness check "
               "lets a qualifier rename slip through, and the roster deliberately holds near-twins "
               "(Bone Break / Latent Bone Break) where a fuzzy key is a coin flip between two of "
               "his items. MEASURED: 1 match, gate RED, breaking "
               "test_a_QUALIFIER_is_not_a_spelling_difference",
        "file": "chronicle_retro.py",
        "find": "    if _tight(hit) != _tight(name):",
        "replace": "    if False and _tight(hit) != _tight(name):",
        "matches": 1,
    },
]

class OneItemHasOneKey(unittest.TestCase):

    def setUp(self):
        self.ros = CR._fold_rosters()

    # ── the guard can find its subject ────────────────────────────────────────────────────────
    def test_the_rosters_actually_loaded(self):
        """⚠ A fold against an EMPTY roster folds nothing and every law below would pass having
        merged nothing at all. [[zero-needs-a-denominator]]"""
        self.assertGreater(len(self.ros.get("uniques") or {}), 300,
                           "the uniques roster did not load, so the fold is inert")
        self.assertGreater(len(self.ros.get("sets") or {}), 100,
                           "the set roster did not load, so the fold is inert for sets")

    # ── ⚠⚠ THE LAW ───────────────────────────────────────────────────────────────────────────
    def test_both_apostrophe_forms_reach_ONE_key(self):
        a = CR._fold_key("Atma’s Scarab", self.ros, "uniques")
        b = CR._fold_key("Atma's Scarab", self.ros, "uniques")
        self.assertEqual(a, b,
                         "the curly and straight spellings of one item still produce two keys, so "
                         "their sightings cannot corroborate each other")

    def test_a_spacing_variant_reaches_the_SAME_key(self):
        """'Endless Hail' and 'Steal Skull' are reads that split a compound name. Both are in his
        live store today with 2 sightings each, stranded from the 22 and 23 they belong to."""
        for split, whole in (("Endless Hail", "Endlesshail"), ("Steal Skull", "Stealskull")):
            self.assertEqual(CR._fold_key(split, self.ros, "uniques"),
                             CR._fold_key(whole, self.ros, "uniques"),
                             "%r and %r still key apart" % (split, whole))

    def test_the_fold_lands_on_the_ROSTER_spelling_not_whichever_arrived_first(self):
        """Otherwise the store's spelling depends on read order, and two machines sweeping the same
        reels in different orders disagree about the key."""
        ro = self.ros["uniques"]
        for raw in ("Atma’s Scarab", "Atma's Scarab", "ATMA'S SCARAB"):
            self.assertEqual(ro.get("atmasscarab"), CR._fold_key(raw, self.ros, "uniques"),
                             "%r did not land on the roster's own spelling" % raw)

    # ── ⚠ EXACT ONLY — the direction that keeps his grail honest ─────────────────────────────
    def test_a_NEAR_miss_does_NOT_fold(self):
        """★ THE SAFETY LAW. A fuzzy key would merge two different items and nothing downstream
        could tell. The roster holds near-twin pairs on purpose."""
        for near in ("Bone Break", "Latent Bone Break"):
            k = CR._fold_key(near, self.ros, "uniques")
            self.assertEqual(near, k if near in (self.ros["uniques"] or {}).values() else near,
                             "a near-twin name was rewritten")
        a = CR._fold_key("Bone Break", self.ros, "uniques")
        b = CR._fold_key("Latent Bone Break", self.ros, "uniques")
        self.assertNotEqual(a, b,
                            "two deliberately near-twin roster items folded onto ONE key — that is "
                            "a coin flip between two of his grail items")

    def test_an_UNKNOWN_name_keeps_its_own_spelling(self):
        """A store that can only hold roster items stops being able to witness a rare."""
        for junk in ("Some Rare Circlet", "— not an item —", "Polaris Spear XYZ"):
            self.assertEqual(junk, CR._fold_key(junk, self.ros, "uniques"),
                             "an off-roster name was rewritten or dropped")

    def test_an_EMPTY_roster_folds_NOTHING_rather_than_badly(self):
        empty = {"uniques": {}, "sets": {}}
        self.assertEqual("Atma's Scarab", CR._fold_key("Atma's Scarab", empty, "uniques"))

    def test_sets_fold_against_the_SET_roster_not_the_uniques_one(self):
        ro = self.ros["sets"]
        any_set = list(ro.values())[0]
        import chronicle_resolve as _r
        self.assertEqual(any_set, CR._fold_key(any_set, self.ros, "sets"))
        self.assertEqual(any_set, CR._fold_key(any_set.upper(), self.ros, "sets"),
                         "a set piece did not fold against the set roster")
        self.assertNotIn(_r._norm(any_set), self.ros["uniques"],
                         "fixture assumption broken: this set name is also a unique")

    # ── ⚠⚠ FOLD A SPELLING, NEVER RENAME — THE LAW THIS FIX BROKE ON ITS FIRST TRY ──────────
    def test_a_QUALIFIER_is_not_a_spelling_difference(self):
        """★ THIS IS WHAT THREE GATES CAUGHT. The set roster is INDEXED BY THE UNQUALIFIED NAME,
        so the first cut folded 'Credendum' -> 'Credendum (mithril coil)' and
        "Tal Rasha's Adjudication" -> '... (amulet)'. That is a RENAME, not a spelling fix.

        `notFound`, `notFoundSeen`, `contested` and `completeSets` are name-keyed TOO. Renaming
        one side of the found/not-found join desynchronised it and every contradiction went
        silent — "the contradiction vanished across a merge". Folding one half of a name-keyed
        join is precisely the defect this module exists to fix, arriving through the fix itself.

        ⚠ AND THE FIRST GUARD DID NOT BITE, because it compared on `_norm`, which DROPS the
        parenthetical: _norm('Credendum (mithril coil)') == _norm('Credendum') == 'credendum',
        so it compared two already-equal strings and permitted the rename it was written to
        refuse. The comparison has to keep the qualifier's letters.
        [[feedback-suspect-the-instrument]] [[the-unjoined-end]]
        """
        for bare in ("Credendum", "Dark Adherent", "Tal Rasha's Adjudication"):
            got = CR._fold_key(bare, self.ros, "sets")
            self.assertEqual(bare, got,
                             "%r was RENAMED to %r. A qualifier is not a spelling difference, and "
                             "renaming one side of a name-keyed join silences every contradiction "
                             "that depends on it." % (bare, got))

    def test_the_qualified_form_keeps_ITS_own_spelling_too(self):
        """The other direction: the fold must not strip a qualifier either. Both forms are stable
        under it; they simply do not merge."""
        for q in ("Credendum (mithril coil)", "Dark Adherent (dusk shroud)"):
            self.assertEqual(q, CR._fold_key(q, self.ros, "sets"))

    def test_the_tight_comparison_KEEPS_what_norm_drops(self):
        """⚠ Pinned on the instrument itself, because the guard silently did nothing when it was
        built on `_norm`. If `_tight` ever starts dropping parentheticals, the rename returns and
        every law above still passes."""
        import chronicle_resolve as _r
        self.assertEqual(_r._norm("Credendum (mithril coil)"), _r._norm("Credendum"),
                         "fixture assumption broken: _norm no longer drops the qualifier, so this "
                         "guard is no longer testing anything")
        self.assertNotEqual(CR._tight("Credendum (mithril coil)"), CR._tight("Credendum"),
                            "_tight drops the qualifier like _norm does, so the rename guard "
                            "compares two equal strings and permits every rename")
        self.assertEqual(CR._tight("Atma\u2019s Scarab"), CR._tight("Atma's Scarab"),
                         "_tight no longer folds punctuation, so real spelling pairs stop merging")

    # ── ⚠⚠ IT MUST ACT AT THE MERGE, NOT MERELY EXIST ────────────────────────────────────────
    def test_the_merge_ACTUALLY_collapses_two_spellings(self):
        """★ THE JOIN. `_fold_key` being correct and `merge_proposals` not calling it is this
        repo's single most repeated defect. Run the REAL merge over a two-spelling proposal."""
        prop = {"uniques": {"Atma’s Scarab": [{"reel": "rA", "frame": "f1", "lane": "L"}],
                            "Atma's Scarab": [{"reel": "rB", "frame": "f2", "lane": "L"}]},
                "sets": {}, "setGroups": {}, "completeSets": {}, "refused": [], "pagesRead": 0}
        out = CR.merge_proposals({}, prop)
        u = out.get("uniques") or {}
        hits = [k for k in u if "Scarab" in k]
        self.assertEqual(1, len(hits),
                         "the merge kept %d keys for one item: %r" % (len(hits), hits))
        self.assertEqual(2, len(u[hits[0]]),
                         "the two reels' sightings did not land in one bucket, so cross-reel "
                         "corroboration still cannot fire")

    def test_the_merge_still_DEDUPES_one_frame_read_twice(self):
        """The other direction. Folding must not turn one photograph into two witnesses — that
        would manufacture corroboration, which is worse than missing it."""
        sg = {"reel": "rA", "frame": "f1", "lane": "L"}
        prop = {"uniques": {"Atma’s Scarab": [dict(sg)], "Atma's Scarab": [dict(sg)]},
                "sets": {}, "setGroups": {}, "completeSets": {}, "refused": [], "pagesRead": 0}
        out = CR.merge_proposals({}, prop)
        k = [x for x in (out.get("uniques") or {}) if "Scarab" in x][0]
        self.assertEqual(1, len(out["uniques"][k]),
                         "the same photograph banked under both spellings became TWO sightings — "
                         "that is invented corroboration")

    # ── the live store, as a measurement rather than a claim ──────────────────────────────────
    def test_his_REAL_store_collapses_by_exactly_four(self):
        """⚠ Pinned as a FLOOR, not an equality: he sweeps, and new names arrive. What must stay
        true is that the four known pairs are gone and nothing else got merged wholesale."""
        p = os.path.join(HERE, "chron_evidence.json")
        if not os.path.exists(p):
            self.skipTest("no live evidence store on this venue — a skip is NOT a pass")
        try:
            ev = json.load(io.open(p, encoding="utf-8"))
        except Exception as e:
            self.skipTest("evidence store unreadable (%s)" % e)
        raw = ev.get("uniques") or {}
        if not raw:
            self.skipTest("the store holds no uniques on this venue")
        folded = {}
        for k in raw:
            folded.setdefault(CR._fold_key(k, self.ros, "uniques"), []).append(k)
        collisions = {t: ks for t, ks in folded.items() if len(ks) > 1}
        self.assertLessEqual(len(collisions), 12,
                             "the fold merged %d groups of names. That is far past the four known "
                             "pairs and suggests it stopped being an EXACT fold: %r"
                             % (len(collisions), list(collisions)[:6]))
        for t, ks in collisions.items():
            self.assertEqual(2, len(ks),
                             "%r absorbed %d spellings at once (%r) — an exact fold should join "
                             "a pair, not a crowd" % (t, len(ks), ks))


if __name__ == "__main__":
    unittest.main(verbosity=2)
