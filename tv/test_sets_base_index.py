#!/usr/bin/env python3
"""BASE -> SET PIECE: the index, and the copy of it embedded in the board.

Konyo asked for the sets side of something uniques already had — expanding a base name the
Chronicle prints back to what he still has to find. `_chUniquesOnBase` does it for uniques from
ITEM_CODEX; **ITEM_CODEX carries a base for only 14 of the 135 set pieces**, so there was nothing
to copy and the mapping had to come from the Remaining page he recorded.

That creates a second copy of one fact — the source JSON and the block embedded in bible.html — and
a copy that nothing compares is a copy that drifts. These tests are the comparison. [[copy-drift]]
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import sets_base_index as sbi  # noqa: E402
import chronicle_resolve as _res  # noqa: E402


def _embedded():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        s = fh.read()
    m = re.search(r"window\._SET_BASE_INDEX = (\{.*?\});\n", s, re.S)
    return json.loads(m.group(1)) if m else None


class TestTheIndexItself(unittest.TestCase):
    def test_it_is_read_data_not_derived_from_the_slot_suffix(self):
        """The rule I first believed — 'the suffix IS the base' — is true for some rows and false
        for others, and a rule that is quietly right half the time is worse than no rule."""
        b = sbi.build()
        self.assertIsNotNone(b, "no Remaining page on file")
        pairs = {v["base"]: v["pieces"] for v in b["index"].values()}
        # rows where the suffix genuinely IS the base
        self.assertIn("Ward", pairs)
        self.assertTrue(any(p.endswith("(ward)") for p in pairs["Ward"]))
        # ...and rows where it is a CATEGORY, which a suffix rule would have mis-resolved
        self.assertIn("Scissors Suwayyah", pairs)
        self.assertEqual(pairs["Scissors Suwayyah"], ["Natalya's Soul (claws)"],
                         "the suffix here is 'claws', a category — not the base")
        self.assertEqual(pairs["Occult Codex"], ["Horazon's Secrets (grimoire)"])
        self.assertEqual(pairs["Sacred Armor"], ["Immortal King's Soul Cage (armor)"])

    def test_one_base_may_carry_more_than_one_piece(self):
        b = sbi.build()
        pairs = {v["base"]: v["pieces"] for v in b["index"].values()}
        self.assertEqual(len(pairs.get("Amulet") or []), 2,
                         "two set pieces share the Amulet base; collapsing them to one would "
                         "silently drop a piece he still has to find")

    def test_every_indexed_piece_is_a_real_roster_piece(self):
        b = sbi.build()
        roster = _res.load_set_roster()
        bad = []
        for v in b["index"].values():
            for p in v["pieces"]:
                if _res.canonical(p, roster) is None:
                    bad.append(p)
        self.assertEqual(bad, [], "an indexed piece that is not on the roster would expand a base "
                                  "into a name that does not exist")

    def test_coverage_is_stated_rather_than_assumed(self):
        c = sbi.coverage()
        self.assertTrue(c["ok"])
        self.assertEqual(c["rosterTotal"], 135)
        self.assertLess(c["pieces"], c["rosterTotal"],
                        "this index covers only what is missing; if it ever claims the whole "
                        "roster, something has confused 'missing' with 'all'")
        self.assertIn("do not have", c["say"])

    def test_with_no_reading_it_refuses_rather_than_returning_an_empty_index(self):
        """An empty index and 'never read' are opposite facts. [[unknown-stays-unknown]]"""
        old = os.environ.get("TV_REMAINING_DIR")
        import tempfile
        os.environ["TV_REMAINING_DIR"] = tempfile.mkdtemp(prefix="nobase-")
        try:
            self.assertIsNone(sbi.build())
            self.assertIsNone(sbi.coverage()["ok"])
        finally:
            if old is None:
                os.environ.pop("TV_REMAINING_DIR", None)
            else:
                os.environ["TV_REMAINING_DIR"] = old


class TestTheBoardsCopyHasNotDrifted(unittest.TestCase):
    def test_the_embedded_block_exists_and_parses(self):
        e = _embedded()
        self.assertIsNotNone(e, "window._SET_BASE_INDEX is missing from bible.html — the board "
                                "cannot expand a set base without it")
        self.assertTrue(e.get("index"))

    def test_it_matches_the_source_exactly(self):
        e, b = _embedded(), sbi.build()
        self.assertEqual(e["index"], b["index"],
                         "the board's copy has drifted from tv/remaining — regenerate it")
        self.assertEqual(e.get("readAt"), b.get("readAt"),
                         "the embedded stamp must be the reading's own, or the board reports an "
                         "age that belongs to a different page")

    def test_the_board_carries_the_stamp_so_the_age_is_answerable(self):
        e = _embedded()
        self.assertTrue(e.get("readAt"), "an index with no date cannot be aged, and an age that "
                                         "cannot be established is UNKNOWN")
        self.assertTrue(e.get("reel"))

    def test_the_resolver_and_its_wiring_are_both_present(self):
        """Two halves each built right and never joined is the failure mode that costs most here."""
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            s = fh.read()
        self.assertIn("window._chSetPiecesOnBase = function", s, "the resolver is missing")
        self.assertIn("window._chSetPiecesOnBase(canon)", s,
                      "the resolver exists but d2rInboxEngine never calls it — a base would still "
                      "resolve to nothing, which is the whole defect [[the-unjoined-end]]")
        # TWO call sites, and the second is the one measurement found. The base branch only fires
        # when d2rResolveItem calls the string a base, and its catalogue does not hold the plain
        # slot words: live in a browser, "Ward" and "Occult Codex" resolved while **"Amulet" came
        # back not-in-game** — a name the game printed on his own Remaining page for two pieces he
        # is still hunting. Declaring an item the game itself listed to be "not an item in this
        # game" is the most confident possible way to be wrong.
        self.assertIn("window._chSetPiecesOnBase(canon || raw)", s,
                      "the not-in-game fallthrough must consult the index too, or a generic base "
                      "like Amulet is reported as not an item in this game")
        self.assertLess(s.index("window._chSetPiecesOnBase(canon || raw)"),
                        s.index("out.verdict = 'not-in-game'; out.action = 'reader';"),
                        "the fallback must run BEFORE the not-in-game verdict, or it can never "
                        "change it")


class TestTheSentenceNamesWhatItLists(unittest.TestCase):
    """A right list under a word naming half of it.

    "Ward" carries BOTH a unique he is missing (Spirit Ward) and a set piece (Taebaek's Glory). The
    first cut printed both names under "for a unique you have NOT found", which is how he ends up
    hunting one and not the other. Measured live in a browser before and after.
    [[label-outlived-referent]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_all_three_sentences_exist(self):
        s = self._src()
        for phrase in ("for a unique AND a set piece you have NOT found",
                       "for a SET PIECE you have NOT found",
                       "for a unique you have NOT found"):
            self.assertIn(phrase, s, "missing branch: %s" % phrase)

    def test_the_both_case_is_tested_before_the_single_cases(self):
        """An `if sets` that runs before `if uniques and sets` can never reach the both-branch."""
        # ⚠ The first version of THIS assertion grepped `? (sp.missing.length` — a spelling the
        # code does not use (it is `: (sp.missing.length`) — and errored instead of failing. Same
        # class as the guard it is guarding. Anchor on both real occurrences instead.
        s = self._src()
        both = s.index("u.missing.length && sp.missing.length")
        only = s.index("(sp.missing.length", both + 10)
        self.assertLess(both, only,
                        "the both-case must be tested first or it is unreachable, and every mixed "
                        "base silently reports as one catalogue")
        self.assertLess(only - both, 400,
                        "the two branches drifted apart; this check anchors on proximity and would "
                        "otherwise be measuring an unrelated occurrence [[source-reading-guard]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
