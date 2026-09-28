# -*- coding: utf-8 -*-
"""GET /api/evidence counts a reel once, whichever way its id was spelled.

read_reel takes `sid = idx.get("sessionId") or os.path.basename(reel_dir)`, so one reel lands in
chron_evidence.json as both "s_…" and "reel_s_…". trace_spine MEASURED it: 3,914 of his 8,517
sightings are the same row under both spellings, 318 of 324 names carry a reel twice, worst case
Bloodmoon at 136 reported for 114 real. evidence_for deduped reels on the RAW string and counted
`len(sightings)`, so the board's "seen N times across R reels" ran about 2x.

THE LAW: rows that differ only in how the reel was spelled are ONE row (trace_spine.independence's
key, through chronicle_retro._reel_key), `count` is the deduped rows, `rows` keeps the raw figure
BESIDE it, and `reels` lists each reel once. [[copy-drift]] [[unknown-stays-unknown]]

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
import trace_spine as TS

# One reel, spelled both ways. Two frames of it — one of them recorded under BOTH spellings.
TWICE = {"uniques": {"Bloodmoon": [
    {"reel": "s_1787000000009_99999", "frame": "f_1.jpg", "lane": "claude", "conf": 0.9},
    {"reel": "reel_s_1787000000009_99999", "frame": "f_1.jpg", "lane": "claude", "conf": 0.9},
    {"reel": "reel_s_1787000000009_99999", "frame": "f_2.jpg", "lane": "claude", "conf": 0.7},
]}, "sets": {}}


def _ask(prop, name="Bloodmoon"):
    with mock.patch.object(CA, "_chron_evidence_load", lambda: prop):
        return CA.evidence_for(name)


class EvidenceCountsAReelOnce(unittest.TestCase):

    def test_a_reel_spelled_two_ways_is_one_reel_and_one_witness(self):
        got = _ask(TWICE)
        self.assertTrue(got["ok"], got)
        self.assertEqual(1, len(got["reels"]),
                         "one reel under two spellings was listed as %r" % (got["reels"],))
        self.assertEqual(1, got["witnesses"])
        self.assertNotIn("cross-reel", got["witnessTags"],
                         "one reel under two spellings scored as two independent reels")
        self.assertIn("across 1 reel,", got["say"])

    def test_the_same_row_twice_counts_once_and_the_raw_figure_rides_beside_it(self):
        got = _ask(TWICE)
        self.assertEqual(2, got["count"], "a duplicate row inflated the sighting count")
        self.assertEqual(3, got["rows"], "the raw row count was dropped rather than shown beside")
        self.assertEqual(1, got["duplicateRows"])
        self.assertEqual(2, len(got["sightings"]))
        self.assertIn("2 sightings", got["say"])

    def test_the_route_agrees_with_the_spine(self):
        # trace_spine.independence is the reader that measured the inflation. Same rows, same key.
        got = _ask(TWICE)
        ind = TS.independence(TWICE["uniques"]["Bloodmoon"])
        self.assertEqual(ind["deduped"], got["count"])
        self.assertEqual(ind["rows"], got["rows"])
        self.assertEqual(ind["independentReels"], got["witnesses"])


RED_PROOF = [
    {
        "why": "the dedupe key reads the raw reel string again: one reel spelled two ways counts twice",
        "file": "control_app.py",
        "find": "            _k = (_rk(sg.get(\"reel\")), sg.get(\"frame\"), sg.get(\"lane\"), sg.get(\"conf\"))\n",
        "replace": "            _k = (sg.get(\"reel\"), sg.get(\"frame\"), sg.get(\"lane\"), sg.get(\"conf\"))\n",
        "matches": 1,
    },
    {
        "why": "the reel list keys on the raw spelling, so one reel is listed and witnessed twice",
        "file": "control_app.py",
        "find": "            if r and _rk(r) not in _reel_keys:\n                _reel_keys.add(_rk(r))\n",
        "replace": "            if r and r not in _reel_keys:\n                _reel_keys.add(r)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
