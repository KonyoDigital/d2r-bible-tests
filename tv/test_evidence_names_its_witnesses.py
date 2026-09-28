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
