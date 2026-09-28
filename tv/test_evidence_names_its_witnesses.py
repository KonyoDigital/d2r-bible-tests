# -*- coding: utf-8 -*-
"""GET /api/evidence names its witnesses. It never answers null for a name it could read.

MEASURED 2026-09-28 (Ledger P0): `witnesses` was None for EVERY name on /api/evidence.
evidence_for asked counter_ledger for `.witnesses` behind a hasattr check, and counter_ledger
has no such function — the real one is chronicle_retro.witnesses (the independence verdict the
chronicle gate itself uses). The hasattr turned a wrong module into a silent None, and a null
reads exactly like "nobody has corroborated this", which is a claim about the item that was
never measured. [[the-unjoined-end]] [[unknown-stays-unknown]]

THE LAW: a name with 3 sightings in 2 reels reads witnesses 2 — the INDEPENDENT reels — and its
witnessTags are chronicle_retro's own tags. When the independence engine cannot be read, the
answer is None WITH a reason, never a bare null.

Fixtures only: _chron_evidence_load is patched; his chron_evidence.json is never opened.
"""
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as CA
import chronicle_retro as CR

THREE_IN_TWO = {"uniques": {"Shako": [
    {"reel": "s_1787000000001_11111", "frame": "f_1.jpg", "lane": "claude", "conf": 0.91},
    {"reel": "s_1787000000001_11111", "frame": "f_2.jpg", "lane": "claude", "conf": 0.88},
    {"reel": "reel_s_1787000000002_22222", "frame": "f_9.jpg", "lane": "grok", "conf": 0.80},
]}, "sets": {}}


def _ask(prop, name="Shako"):
    with mock.patch.object(CA, "_chron_evidence_load", lambda: prop):
        return CA.evidence_for(name)


class EvidenceNamesItsWitnesses(unittest.TestCase):

    def test_three_sightings_in_two_reels_read_two_witnesses_never_null(self):
        got = _ask(THREE_IN_TWO)
        self.assertTrue(got["ok"], got)
        self.assertIsNotNone(got["witnesses"], "witnesses came back null for a name it read")
        self.assertEqual(2, got["witnesses"],
                         "3 sightings in 2 reels must read 2 independent witnesses")
        self.assertEqual(3, got["count"])

    def test_the_tags_are_chronicle_retros_own_verdict(self):
        got = _ask(THREE_IN_TWO)
        expect = list(CR.witnesses(THREE_IN_TWO["uniques"]["Shako"]))
        self.assertEqual(expect, got["witnessTags"],
                         "the route re-derived independence instead of asking the one engine")
        for tag in ("cross-reel", "cross-frame", "cross-lane"):
            self.assertIn(tag, got["witnessTags"])
        self.assertIsNone(got["witnessWhy"])

    def test_one_sighting_is_one_witness_and_an_empty_tag_list_not_null(self):
        one = {"uniques": {"Shako": [{"reel": "s_5", "frame": "f_1.jpg", "lane": "claude",
                                      "conf": 0.9}]}}
        got = _ask(one)
        self.assertEqual(1, got["witnesses"])
        self.assertEqual([], got["witnessTags"],
                         "a measured 'no independence' is [], never None")

    def test_rows_with_no_reel_make_the_witness_count_unknown_never_zero(self):
        # 2026-09-28 (Ledger fix, finding 6): `witnesses = len(reels)` read 0 for a name whose
        # rows exist but carry no reel. A count of known reels beside rows from unknown ones is a
        # floor, not the count — UNKNOWN is never 0. [[unknown-stays-unknown]]
        none = {"uniques": {"Shako": [
            {"frame": "f_1.jpg", "lane": "claude", "conf": 0.9},
            {"reel": None, "frame": "f_2.jpg", "lane": "claude", "conf": 0.8}]}}
        got = _ask(none)
        self.assertTrue(got["ok"], got)
        self.assertEqual(2, got["count"], "baseline: both rows were read, so this is not an empty book")
        self.assertIsNone(got["witnesses"],
                          "2 rows with no reel read witnesses %r — an unknown shown as a count"
                          % got["witnesses"])
        self.assertIn("UNKNOWN", got["witnessWhy"] or "")
        self.assertEqual((0, 2), (got["witnessesKnown"], got["unplaced"]))
        self.assertNotIn("across 0 reels", got["say"])
        mixed = {"uniques": {"Shako": [
            {"reel": "s_1787000000001_11111", "frame": "f_1.jpg", "lane": "claude", "conf": 0.9},
            {"frame": "f_2.jpg", "lane": "grok", "conf": 0.8}]}}
        got = _ask(mixed)
        self.assertIsNone(got["witnesses"], "one known reel plus an unplaced row read as exactly 1")
        self.assertEqual((1, 1), (got["witnessesKnown"], got["unplaced"]))
        self.assertIn("1 of 2 sighting row(s) carry no reel", got["witnessWhy"])

    def test_an_unreadable_engine_is_unknown_with_a_reason(self):
        real_import = __import__

        def _no_cr(name, *a, **k):
            if name == "chronicle_retro":
                raise ImportError("chronicle_retro unavailable in this probe")
            return real_import(name, *a, **k)

        with mock.patch("builtins.__import__", _no_cr):
            got = _ask(THREE_IN_TWO)
        self.assertTrue(got["ok"], got)
        self.assertIsNone(got["witnesses"])
        self.assertIsNone(got["witnessTags"])
        self.assertIn("UNKNOWN", got["witnessWhy"] or "",
                      "an engine that could not be read left a bare null with no reason")


RED_PROOF = [
    {
        "why": "a row with no reel is counted as zero reels, so an unknown reads as a witness count",
        "file": "control_app.py",
        "find": "        if _unplaced and wit is not None:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "the route asks the wrong module again, so every name reads witnesses null",
        "file": "control_app.py",
        "find": "                wit_tags = list(_cr.witnesses(uniq))\n                wit = len(reels)\n",
        "replace": "                wit_tags = None\n                wit = None\n",
        "matches": 1,
    },
    {
        "why": "the tags are dropped, so the independence verdict never reaches the route",
        "file": "control_app.py",
        "find": "\"witnesses\": wit, \"witnessTags\": wit_tags, \"witnessWhy\": wit_why,",
        "replace": "\"witnesses\": wit, \"witnessTags\": None, \"witnessWhy\": wit_why,",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
