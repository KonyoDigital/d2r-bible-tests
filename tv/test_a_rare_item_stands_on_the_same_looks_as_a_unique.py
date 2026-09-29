# -*- coding: utf-8 -*-
"""A MAGIC (blue) OR RARE (gold) ITEM STANDS ON THE SAME LOOKS, THE SAME TIER AND THE SAME ROUTE AS A UNIQUE.

His ask 2026-09-28 (#51): witnessed looks, Wilson tiers, a rebuild after a reset, clickable evidence
pictures and tallies for magic and rare items — the chain uniques already have, extended, not copied.

MEASURED before the change, on a fixture ledger shaped like his (every look carries `quality` since
v3369):
  · vault_evidence grouped rows by NAME and read no look's quality, so a plan row, the census and the
    doctor's line could not say what an item IS;
  · /api/evidence read the two chronicle books and nothing else — a rare ring's looks sat in
    vault_accum.json and the route answered "nothing banked for this name".

THE LAW, joint by joint, each DRIVEN through the real code on a temp ledger (his is never opened):
  store -> tier   rarity_of reads what the looks SAW (blue / gold / white through vault_retro's one
                  vocabulary) or what the roster names (unique / set); a tie or a blank is UNKNOWN,
                  never white; every plan row carries it.
  tier -> tally   tier_census splits the SAME count by rarity; the doctor's evidence-tiers row says
                  "by rarity: ... rarity UNKNOWN n"; the reset receipt's rebuiltByRarity is read and
                  said, and a receipt that does not say is UNKNOWN.
  tally -> route  evidence_for answers a vault-only name from the witness ledger in the route's one
                  shape (reel = the reel directory the board's click opens), with its tier and rarity
                  on the line; an unreadable ledger is UNKNOWN, never "nothing banked".
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

import console_doctor as CD
import control_app as CA
import vault_evidence as VE
import vault_retro as VR


def _looks(frame, n, quality=None, conf=0.91):
    """n looks, each its own visit (session#bucket) and its own frame — the shape the sweep banks."""
    out = []
    for i in range(n):
        row = {"session": "s_%s_%02d" % (frame.split(".")[0], i), "witness": "s_%s_%02d#0" % (frame.split(".")[0], i),
               "frame": "%s_%02d.jpg" % (frame.split(".")[0], i), "conf": conf, "lane": "stash"}
        if quality is not None:
            row["quality"] = quality
        out.append(row)
    return out


def _miss(frame, quality="rare"):
    return {"session": "s_miss_" + frame, "witness": "s_miss_" + frame + "#0", "frame": frame, "conf": 0.9,
            "lane": "stash", "saw": "empty", "quality": quality}


class ARareItemStandsOnTheSameLooksAsAUnique(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="magic-rare-")
        self.ledger = os.path.join(self.tmp, "vault_accum.json")
        self.doc = {"owned": [
            # a unique the roster names, whose looks (read before v3369) carry no quality
            {"name": "Harlequin Crest", "lane": "stash", "kind": "item", "witnesses": _looks("crest.jpg", 12)},
            # a rare: 12 clean looks that each read it as rare -> gold, PROVEN
            {"name": "Doom Grip", "lane": "stash", "kind": "item", "witnesses": _looks("doom.jpg", 12, "rare")},
            # a rare with a miss beside 12 hits: 12/13 by visits is under the bar -> WATCHED, still gold
            {"name": "Blood Loop", "lane": "stash", "kind": "item",
             "witnesses": _looks("blood.jpg", 12, "rare") + [_miss("blood_miss.jpg")]},
            # a magic: two looks -> blue, WATCHED
            {"name": "Jade Ring of Frost", "lane": "stash", "kind": "item", "witnesses": _looks("jade.jpg", 2, "magic")},
            # the looks disagree: one blue, one gold -> UNKNOWN, never averaged
            {"name": "Torn Thing", "lane": "stash", "kind": "item",
             "witnesses": _looks("torn.jpg", 1, "blue") + _looks("torn2.jpg", 1, "gold")},
            # a rolled name whose looks carry no quality and no roster names it -> UNKNOWN, never white
            {"name": "Old Row", "lane": "stash", "kind": "item", "witnesses": _looks("old.jpg", 12)},
            # a row whose looks cannot be read: tier UNKNOWN
            {"name": "Unread Thing", "lane": "stash", "witnesses": 4},
        ]}
        self.before = json.dumps(self.doc).encode("utf-8")
        with io.open(self.ledger, "wb") as fh:
            fh.write(self.before)
        self.shelf = os.path.join(self.tmp, "shelf")
        os.makedirs(self.shelf)
        for row in self.doc["owned"]:
            for w in (row["witnesses"] if isinstance(row["witnesses"], list) else []):
                with io.open(os.path.join(self.shelf, w["frame"]), "w", encoding="utf-8") as fh:
                    fh.write(w["frame"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _rows(self, name):
        return [r for r in self.doc["owned"] if r["name"] == name]

    def _unchanged(self, what):
        with io.open(self.ledger, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "%s wrote the witness ledger" % what)

    # ── store -> tier ─────────────────────────────────────────────────────────────────────────

    def test_the_looks_say_what_a_rolled_name_is_in_the_ledgers_one_vocabulary(self):
        self.assertEqual("gold", VR._quality_of("rare"), "PREMISE: the ledger's word for rare is gold")
        got = VE.rarity_of("Doom Grip", self._rows("Doom Grip"))
        self.assertEqual(("gold", "looks"), (got["rarity"], got["by"]), got)
        self.assertEqual({"gold": 12}, got["votes"])
        got = VE.rarity_of("Jade Ring of Frost", self._rows("Jade Ring of Frost"))
        self.assertEqual(("blue", "looks"), (got["rarity"], got["by"]), got)

    def test_the_roster_names_a_unique_even_when_its_looks_carry_no_quality(self):
        got = VE.rarity_of("Harlequin Crest", self._rows("Harlequin Crest"))
        self.assertEqual(("unique", "roster"), (got["rarity"], got["by"]), got)
        # the roster stands when the looks disagree with it, and says so
        rows = [{"name": "Harlequin Crest", "witnesses": _looks("x.jpg", 3, "rare")}]
        got = VE.rarity_of("Harlequin Crest", rows)
        self.assertEqual("unique", got["rarity"])
        self.assertEqual("gold", got.get("looksSay"), "the looks' disagreement was dropped: %r" % got)
        self.assertIn("the roster stands", got["why"])
        # a name that is a unique AND a runeword is not decided by the roster
        got = VE.rarity_of("Crescent Moon", [{"name": "Crescent Moon", "witnesses": []}])
        self.assertIsNone(got["rarity"], "a name on two rosters was decided by one of them: %r" % got)

    def test_a_tie_or_a_blank_is_unknown_never_white_and_never_averaged(self):
        tie = VE.rarity_of("Torn Thing", self._rows("Torn Thing"))
        self.assertIsNone(tie["rarity"], "a blue/gold tie was called %r" % tie["rarity"])
        self.assertEqual({"blue": 1, "gold": 1}, tie["votes"])
        self.assertIn("disagree", tie["why"])
        blank = VE.rarity_of("Old Row", self._rows("Old Row"))
        self.assertIsNone(blank["rarity"], "a row with no quality was painted %r" % blank["rarity"])
        self.assertNotEqual("white", blank["rarity"])
        self.assertIn("UNKNOWN", blank["why"])

    def test_every_plan_row_carries_its_rarity_rebuilt_or_held(self):
        plan = VE.plan_from_ledger(self.ledger)
        self.assertTrue(plan["ok"], plan.get("why"))
        rows = dict((r["name"], r) for r in plan["rebuilt"] + plan["held"])
        self.assertEqual(("PROVEN", "gold", "looks"),
                         (rows["Doom Grip"]["tier"], rows["Doom Grip"].get("rarity"), rows["Doom Grip"].get("rarityBy")),
                         "a rebuilt rare does not carry what it is: %r" % rows["Doom Grip"])
        self.assertIn("Doom Grip", [r["name"] for r in plan["rebuilt"]], "twelve clean rare looks were not rebuilt")
        self.assertEqual(("WATCHED", "gold"), (rows["Blood Loop"]["tier"], rows["Blood Loop"].get("rarity")),
                         "a miss did not count as a trial for a rare, or its rarity was dropped")
        self.assertEqual(("WATCHED", "blue"), (rows["Jade Ring of Frost"]["tier"], rows["Jade Ring of Frost"].get("rarity")))
        self.assertEqual(("PROVEN", "unique", "roster"),
                         (rows["Harlequin Crest"]["tier"], rows["Harlequin Crest"].get("rarity"), rows["Harlequin Crest"].get("rarityBy")))
        for name in ("Torn Thing", "Old Row", "Unread Thing"):
            self.assertIn("rarity", rows[name], "%s's row does not say its rarity is UNKNOWN" % name)
            self.assertIsNone(rows[name]["rarity"], "%s was given a rarity nothing measured" % name)
        self._unchanged("the plan")

    # ── tier -> tally ─────────────────────────────────────────────────────────────────────────

    def test_the_census_splits_the_same_count_by_rarity_and_keeps_unknown_apart(self):
        got = VE.tier_census(self.ledger)
        self.assertTrue(got["ok"], got)
        by = got["byRarity"]
        self.assertEqual({"watched": 1, "proven": 1, "hardened": 0, "unknown": 0}, by["gold"], by)
        self.assertEqual({"watched": 1, "proven": 0, "hardened": 0, "unknown": 0}, by["blue"], by)
        self.assertEqual({"watched": 0, "proven": 1, "hardened": 0, "unknown": 0}, by["unique"], by)
        self.assertEqual({"watched": 1, "proven": 1, "hardened": 0, "unknown": 1}, by["unknown"],
                         "the tie, the blank and the unreadable row are not all under UNKNOWN: %r" % by)
        self.assertNotIn("white", by, "a blank quality was folded into white")
        self.assertEqual(3, got["rarityUnknown"])
        # CORROBORATION: the split is the SAME count, never a second one
        for key in ("watched", "proven", "hardened", "unknown"):
            self.assertEqual(got[key], sum(b[key] for b in by.values()),
                             "the by-rarity buckets do not add up to the census's %s" % key)
        self._unchanged("the census")
        unread = VE.tier_census(os.path.join(self.tmp, "nope.json"))
        self.assertIsNone(unread["byRarity"], "an unread census split into zeros")
        self.assertIsNone(unread["rarityUnknown"])

    def test_the_doctor_line_says_the_tally_by_rarity(self):
        st, why = CD._check_the_evidence_tiers(path=self.ledger, root=self.shelf)
        self.assertEqual(CD.OK, st, why)
        self.assertIn("tiers by visit, never frame: WATCHED 3 · PROVEN 3 · HARDENED 0", why)
        self.assertIn("by rarity: unique W0/P1/H0 · rare (gold) W1/P1/H0 · magic (blue) W1/P0/H0 · rarity UNKNOWN 3", why,
                      "the doctor's line does not tally magic and rare like uniques: %s" % why)
        self.assertEqual("by rarity: UNKNOWN", VE.rarity_tally_say(None), "an unread split was said as zeros")
        st2, why2 = CD._check_the_evidence_tiers(path=os.path.join(self.tmp, "nope.json"), root=self.shelf)
        self.assertEqual(CD.UNKNOWN, st2, why2)
        self.assertNotIn("rarity UNKNOWN 0", why2)

    def test_the_reset_receipt_tallies_what_came_back_by_rarity_or_says_it_does_not_know(self):
        same = {"d2r_setPieces": "[1]"}
        said = VE.reset_receipt({"rebuilt": ["Harlequin Crest", "Doom Grip", "Jade Ring of Frost"], "held": [],
                                 "rebuiltFailed": [], "rebuiltByRarity": {"unique": 1, "gold": 1, "blue": 1}},
                                same, dict(same))
        self.assertTrue(said["ok"], said)
        self.assertEqual({"unique": 1, "gold": 1, "blue": 1}, said["byRarity"])
        self.assertIn("rebuilt by rarity: 1 unique · 1 rare (gold) · 1 magic (blue)", said["why"])
        st, why = CD._check_the_vault_reset({"rebuilt": ["Doom Grip"], "held": [], "rebuiltFailed": [],
                                             "rebuiltByRarity": {"gold": 1}}, same, dict(same))
        self.assertEqual(CD.OK, st, why)
        self.assertIn("rebuilt by rarity: 1 rare (gold)", why, "the heart's reset row does not say the tally")
        older = VE.reset_receipt({"rebuilt": ["Doom Grip"], "held": [], "rebuiltFailed": []}, same, dict(same))
        self.assertIsNone(older["byRarity"], "a receipt that does not say was read as a tally")
        self.assertIn("rebuilt by rarity UNKNOWN", older["why"])
        bad = VE.reset_receipt({"rebuilt": ["Doom Grip"], "held": [], "rebuiltFailed": [],
                                "rebuiltByRarity": {"gold": True, "blue": -1, "unique": 2}}, same, dict(same))
        self.assertEqual({"unique": 2}, bad["byRarity"], "a bool or a negative count was read as a count")

    # ── tally -> route ────────────────────────────────────────────────────────────────────────

    def _route(self, name, chron=None, ledger=None):
        with mock.patch.object(CA, "_chron_evidence_load", lambda: (chron if chron is not None else {})), \
                mock.patch.object(CA, "VAULT_LEDGER_PATH", self.ledger):
            return CA.evidence_for(name, ledger)

    def test_the_evidence_route_answers_a_rare_from_the_vault_ledger_with_its_tier_and_rarity(self):
        got = self._route("Doom Grip")
        self.assertTrue(got["ok"], got)
        self.assertEqual("vault", got["ledger"])
        self.assertEqual(("gold", "PROVEN", 12, 12), (got["rarity"], got["tier"], got["successes"], got["trials"]), got)
        self.assertEqual(12, got["count"])
        first = got["sightings"][0]
        self.assertEqual("reel_s_doom_00", first["reel"], "the reel is not the directory the board's click opens: %r" % first)
        self.assertEqual(("doom_00.jpg", "stash", 0.91, "rare"), (first["frame"], first["lane"], first["conf"], first["quality"]))
        self.assertIn("rare (gold)", got["say"])
        self.assertIn("PROVEN 12/12 by visits", got["say"])
        self.assertEqual(12, got["witnesses"], "twelve distinct reels were not twelve witnesses")
        self._unchanged("the evidence route")

    def test_a_miss_is_a_trial_on_the_route_too_and_unknowns_are_said(self):
        got = self._route("Blood Loop")
        self.assertEqual(("WATCHED", 12, 13), (got["tier"], got["successes"], got["trials"]), got)
        self.assertEqual("empty", got["sightings"][-1].get("saw"), "the miss lost its 'saw' in the re-spelling")
        self.assertIn("WATCHED 12/13 by visits", got["say"])
        old = self._route("Old Row")
        self.assertTrue(old["ok"], old)
        self.assertIsNone(old["rarity"])
        self.assertIn("rarity UNKNOWN", old["say"])
        unread = self._route("Unread Thing")
        self.assertFalse(unread["ok"], "a row whose looks cannot be read answered with sightings: %r" % unread)

    def test_the_chronicle_books_still_answer_first_and_vault_can_be_asked_alone(self):
        book = {"uniques": {"Harlequin Crest": [{"reel": "s_1", "frame": "f_1.jpg", "lane": "claude", "conf": 0.9}]}}
        got = self._route("Harlequin Crest", chron=book)
        self.assertEqual("uniques", got["ledger"], "the vault answered before the chronicle book")
        self.assertNotIn("tier", got, "a chronicle answer grew a vault tier")
        only = self._route("Harlequin Crest", chron=book, ledger="vault")
        self.assertEqual(("vault", "unique", "roster"), (only["ledger"], only["rarity"], only["rarityBy"]), only)
        book_only = self._route("Harlequin Crest", chron=book, ledger="uniques")
        self.assertEqual("uniques", book_only["ledger"])
        nothing = self._route("Nope", chron=book)
        self.assertFalse(nothing["ok"])
        self.assertIn("vault witness ledger holds no look", nothing["why"])
        empty = self._route("Nope")
        self.assertFalse(empty["ok"])
        self.assertIn("no evidence ledger has been banked yet", empty["why"])
        self.assertIn("vault witness ledger", empty["why"])

    def test_the_proven_names_the_board_asks_for_say_what_each_is(self):
        """/api/vault_proven marks the board's tiles by name; a rolled name it proves must say what it is, from the
        same resolver, so the board never needs a second table to tell a rare from a unique. UNKNOWN stays None."""
        with mock.patch.object(CA, "VAULT_LEDGER_PATH", self.ledger):
            got = CA.vault_proven_names(min_witnesses=2)
        self.assertTrue(got["ok"], got)
        by = dict((r["name"], r) for r in got["proven"])
        self.assertIn("Doom Grip", by, "PREMISE: twelve looks clear the keep bar")
        self.assertEqual(("gold", "looks"), (by["Doom Grip"].get("rarity"), by["Doom Grip"].get("rarityBy")), by["Doom Grip"])
        self.assertEqual(("unique", "roster"), (by["Harlequin Crest"].get("rarity"), by["Harlequin Crest"].get("rarityBy")))
        self.assertIn("rarity", by["Old Row"], "a proven name of UNKNOWN rarity does not say so")
        self.assertIsNone(by["Old Row"]["rarity"])
        self._unchanged("the proven-names route")

    def test_an_unreadable_vault_ledger_is_unknown_never_nothing_banked(self):
        with io.open(self.ledger, "wb") as fh:
            fh.write(b"{")
        got = self._route("Doom Grip")
        self.assertFalse(got["ok"])
        self.assertIn("UNKNOWN", got["why"])
        self.assertNotIn("nothing banked for this name", got["why"])
        with mock.patch.object(CA, "_chron_evidence_load", lambda: {}), \
                mock.patch.object(CA, "VAULT_LEDGER_PATH", os.path.join(self.tmp, "absent.json")):
            absent = CA.evidence_for("Doom Grip")
        self.assertFalse(absent["ok"])
        self.assertNotIn("UNKNOWN", absent["why"], "an absent ledger (nothing swept here) was called unreadable")


RED_PROOF = [
    {
        "why": "#51 - the looks no longer say what a rolled name is, so every rare and magic row reads rarity UNKNOWN",
        "file": "vault_evidence.py",
        "find": "    if seen:\n        return {\"rarity\": seen, \"by\": \"looks\", \"votes\": votes,\n",
        "replace": "    if False:\n        return {\"rarity\": seen, \"by\": \"looks\", \"votes\": votes,\n",
        "matches": 1,
    },
    {
        "why": "#51 - a blue/gold tie is averaged to whichever colour came first instead of UNKNOWN",
        "file": "vault_evidence.py",
        "find": "        seen = lead[0] if len(lead) == 1 else \"\"\n",
        "replace": "        seen = lead[0]\n",
        "matches": 1,
    },
    {
        "why": "#51 - the plan row drops its rarity, so the board's door cannot send a rare to the MAGIC & RARE locker",
        "file": "vault_evidence.py",
        "find": "        if \"rarity\" in it:\n            # #51",
        "replace": "        if False:\n            # #51",
        "matches": 1,
    },
    {
        "why": "#51 - the census stops splitting the count by rarity",
        "file": "vault_evidence.py",
        "find": "        bucket[key.lower()] += 1\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "#51 - the doctor's evidence-tiers line drops the by-rarity tally",
        "file": "console_doctor.py",
        "find": "               _ve.rarity_tally_say(got.get(\"byRarity\")), retro, pic))\n",
        "replace": "               \"by rarity: n/a\", retro, pic))\n",
        "matches": 1,
    },
    {
        "why": "#51 - the reset receipt's by-rarity tally is never read, so the heart says UNKNOWN over a receipt that said",
        "file": "vault_evidence.py",
        "find": "    by_rarity = _rebuilt_by_rarity(receipt)\n",
        "replace": "    by_rarity = None\n",
        "matches": 1,
    },
    {
        "why": "#51 - /api/evidence stops asking the vault witness ledger, so a rare's looks read as nothing banked again",
        "file": "control_app.py",
        "find": "    got = _vault_evidence_for(n)\n    if got is not None:\n        yield got\n",
        "replace": "    got = None\n    if got is not None:\n        yield got\n",
        "matches": 1,
    },
    {
        "why": "#51 - the proven names the board asks for stop saying what each is",
        "file": "control_app.py",
        "find": "                _rarity, _rarity_by = _rar.get(\"rarity\"), _rar.get(\"by\")\n",
        "replace": "                _rarity, _rarity_by = None, None\n",
        "matches": 1,
    },
    {
        "why": "#51 - an unreadable vault ledger reads as nothing banked instead of UNKNOWN",
        "file": "control_app.py",
        "find": "    if state != \"ok\" or not isinstance(doc, dict):\n        return (\"vault\", None, \"the vault witness ledger exists and could not be read (%s), so whether it \"\n",
        "replace": "    if state != \"ok\" or not isinstance(doc, dict):\n        return None\n        return (\"vault\", None, \"the vault witness ledger exists and could not be read (%s), so whether it \"\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
