#!/usr/bin/env python3
"""Guards for the cross-reference. A count he ACTS on must be the count of what would change."""
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chronicle_crossref as X

HERE = os.path.dirname(os.path.abspath(__file__))


class TestUnreadableIsNotZeroAndNotEverything(unittest.TestCase):
    """⚠ THE LAW. "I could not ask" must never render as a number. 347 printed after no ledger read
    is the same lie as 0. [[unknown-stays-unknown]]"""

    def test_no_ledger_gives_newCount_None(self):
        r = X.crossref({"uniques": ["A", "B"], "sets": []}, None)
        self.assertFalse(r["measured"])
        self.assertIsNone(r["newCount"])
        self.assertIsNone(r["alreadyCount"])

    def test_no_ledger_never_says_a_number_out_loud(self):
        r = X.crossref({"uniques": ["A", "B"], "sets": []}, None)
        said = X.say(r)
        self.assertNotIn("2", said)
        self.assertIn("not yet checked", said)

    def test_a_junk_ledger_is_unreadable_not_empty(self):
        for junk in ("", [], 0, "null"):
            r = X.crossref({"uniques": ["A"], "sets": []}, junk)
            self.assertFalse(r["measured"], "%r read as a ledger with nothing in it" % (junk,))


class TestTheApostropheDoesNotFileOneItemAsTwo(unittest.TestCase):
    """202 of his names carry a straight apostrophe and 4 a curly one, and bible.html holds BOTH
    byte forms of Atma’s Scarab, Cat’s Eye and Death’s Web — measured 2026-08-29.
    [[d2r-curly-apostrophe-class]]"""

    def test_curly_and_straight_are_one_item(self):
        self.assertEqual(X.canon("Atma’s Scarab"), X.canon("Atma's Scarab"))

    def test_a_curly_proposal_matches_a_straight_ledger(self):
        r = X.crossref({"uniques": ["Atma’s Scarab"], "sets": []},
                       {"foundLog": ["Atma's Scarab"]})
        self.assertEqual(r["newCount"], 0, "the same item in two byte forms read as new")

    def test_the_same_item_twice_in_one_proposal_counts_once(self):
        r = X.crossref({"uniques": ["Cat’s Eye", "Cat's Eye"], "sets": []}, {"foundLog": []})
        self.assertEqual(r["newCount"], 1)
        self.assertEqual(r["dupesInProposal"], 1)

    def test_it_does_NOT_collapse_genuinely_different_items(self):
        # a canon that over-normalises would hide real finds — the opposite failure, and worse
        r = X.crossref({"uniques": ["Bloodrise", "Bloodfist"], "sets": []}, {"foundLog": []})
        self.assertEqual(r["newCount"], 2)


class TestItReadsEveryShapeAStoreArrivesIn(unittest.TestCase):
    def test_dict_rows_list_of_names_and_dict_keyed_stores_all_work(self):
        prop = {"uniques": [{"name": "Windforce", "why": "corroborated"}], "sets": ["Tal's Mask"]}
        for led in ({"foundLog": ["Windforce", "Tal's Mask"]},
                    {"foundLog": {"Windforce": "Jun 1", "Tal's Mask": "Jun 2"}},
                    {"owned": [{"name": "Windforce"}], "setPieces": ["Tal's Mask"]}):
            r = X.crossref(prop, led)
            self.assertEqual(r["newCount"], 0, "shape %r was not read" % (led,))

    def test_a_row_with_no_name_is_dropped_not_counted(self):
        r = X.crossref({"uniques": [{"why": "no name here"}, {"name": "Windforce"}], "sets": []},
                       {"foundLog": []})
        self.assertEqual(r["newCount"], 1)


class TestItCanStillSayNEW(unittest.TestCase):
    """⚠ A CROSS-REFERENCE THAT ALWAYS ANSWERS 'you have it' IS THE SAME DEFECT AS ONE THAT ALWAYS
    ANSWERS 347. Both have stopped carrying information. [[regression-guard]]"""

    def test_the_negative_control(self):
        r = X.crossref({"uniques": ["Zzz Not A Real Item"], "sets": []},
                       {"foundLog": ["Windforce", "Stormlash"]})
        self.assertEqual(r["newCount"], 1)
        self.assertIn("1 not in your chronicle yet", X.say(r))


class TestAgainstHisRealProposal(unittest.TestCase):
    """★ THE MEASUREMENT THIS WHOLE SHIP CAME FROM. His console showed
    '📜 347 find(s) read from your reels — not in your ledger yet'. He asked: "did it cross
    reference what i currently already own? im pretty sure i alread have those items". He was
    right, and more right than I first said — I reported 28 new and the real answer is ZERO."""

    def _load(self):
        p = os.path.join(HERE, "chron_last_result.json")
        if not os.path.isfile(p):
            self.skipTest("no saved chronicle result on this venue")
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        wa = ((d.get("result") or {}).get("wouldAdd")) or {}
        if not (wa.get("uniques") or wa.get("sets")):
            self.skipTest("the saved result proposes nothing")
        return wa

    def test_his_proposal_is_read_as_names_not_as_dicts(self):
        # ⚠ the trap that cost me a wrong verdict tonight: wouldAdd rows are DICTS
        # ({name, why, witnesses, seen}), and canon() of a whole dict matches nothing, so a
        # careless check reports "0 of 347 covered" while the truth is 347 of 347.
        # [[feedback-suspect-the-instrument]]
        wa = self._load()
        names = X._names(wa.get("uniques")) + X._names(wa.get("sets"))
        self.assertTrue(names)
        for n in names[:20]:
            self.assertIsInstance(n, str)
            self.assertNotIn("{", n, "a dict leaked through as a name")

    def test_a_proposal_fully_covered_by_his_ledger_reports_ZERO_new(self):
        wa = self._load()
        names = X._names(wa.get("uniques")) + X._names(wa.get("sets"))
        r = X.crossref(wa, {"foundLog": names})       # his foundLog covered all 347, measured live
        self.assertEqual(r["newCount"], 0)
        self.assertEqual(r["alreadyCount"], len(names))
        self.assertIn("already have every one", X.say(r))


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
