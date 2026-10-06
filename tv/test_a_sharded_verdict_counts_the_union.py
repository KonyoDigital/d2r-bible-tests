# -*- coding: utf-8 -*-
"""REG-1915 - A SHARDED SUITE'S VERDICT COUNTS THE UNION, NEVER ONE SHARD AND NEVER "?".

suite_verdict read its case count only from unittest's "Ran N tests". test_control runs as shards (shard_suite.py),
whose summary is "<ran> of <want> case(s) across <k> shard(s)": v3601's pre-run printed "test_control GREEN in 238.6s
(? cases)", and the red run before it printed "(1333 cases)" - one shard's tail - for a 2,260-case suite. A count is
what tells "every case ran" from "a sample ran", so a wrong one is a verdict claiming a different reach.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import suite_verdict as SV  # noqa: E402

GREEN = "  shard 1: 40 class(es), ran 1130 of 1130, rc=0\n  shard 2: 41 class(es), ran 1130 of 1130, rc=0\n" \
        "test_control GREEN: 2260 of 2260 case(s) across 2 shard(s) in 238.6s\n"
RED = "── shard 1 (last lines) ──\nRan 1333 tests in 390.9s\nFAILED (failures=1)\n" \
      "test_control RED: 2259 of 2260 case(s) across 2 shard(s) in 390.9s\n"


class AShardedVerdictCountsTheUnion(unittest.TestCase):

    def test_a_green_sharded_run_counts_its_union(self):
        self.assertEqual(SV.ran_cases(GREEN), 2260, "a green sharded run reported '?' cases (REG-1915)")

    def test_a_red_sharded_run_is_not_one_shards_tail(self):
        self.assertEqual(SV.ran_cases(RED), 2259, "one shard's 'Ran 1333' was reported as the suite (REG-1915)")

    def test_a_plain_run_still_reads_unittests_line(self):
        self.assertEqual(SV.ran_cases("Ran 265 tests in 9.7s\nOK\n"), 265)

    def test_two_plain_tails_are_not_passed_off_as_the_whole(self):
        self.assertIsNone(SV.ran_cases("Ran 10 tests\nRan 12 tests\n"))

    def test_the_verdict_uses_it(self):
        src = io.open(os.path.join(HERE, "suite_verdict.py"), encoding="utf-8").read()
        self.assertEqual(src.count("    cases = ran_cases(out)\n"), 1, "the verdict no longer counts through ran_cases")


RED_PROOF = [
    {
        "why": "REG-1915 - the union line is ignored again: a green sharded run reads '?' and a red one one shard's tail",
        "file": "tv/suite_verdict.py",
        "find": "    if m:\n        return int(m.group(1))\n",
        "replace": "    if False:\n        return int(m.group(1))\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
