# -*- coding: utf-8 -*-
"""#80 — a watcher lane is as proven as ITS OWN sabotages, never as its neighbours'.

MEASURED, and the reason this law exists: 163 RED_PROOFs name control_app.py and exactly 6 of
them land inside one of the twelve watcher-loop def spans. Crediting every lane with the file's
tally would have published FLOWING 20/20 out of evidence that never touched nine of them. An n
inflated by REPETITION is fake confluence — the 83/83 that was really 0.5655.

⚠ EVERY CASE HERE IS DRIVEN, NOT OBSERVED. The sibling law in test_flowing_is_unmeasured_not_zero
went BLIND the day #80 made the live census scorable, because it could only reach its branch when
the live tree happened to be in the right state. A law that waits for its input is a law with an
expiry date. [[gate-blind-to-unexercised-input]] [[unknown-stays-unknown]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import health_engine as HE  # noqa: E402
from confidence import wilson_lower  # one home for the maths — never a copy  # noqa: E402


def _drive(per_lane):
    """Run the organ against a CONSTRUCTED ledger, restoring the real one whatever happens."""
    _roll, _cache = HE._attack_rollup, HE._ATK_CACHE
    try:
        HE._attack_rollup = lambda: ({}, True)
        HE._ATK_CACHE = {"per_lane": dict(per_lane)}
        return HE.check_lane_attacks()
    finally:
        HE._attack_rollup, HE._ATK_CACHE = _roll, _cache


class TestLaneAttacksArePerLane(unittest.TestCase):

    def setUp(self):
        self.spans, self.src = HE._lane_spans()
        self.lanes = sorted(set(l for (l, _a, _b) in self.spans.values()))
        self.assertGreaterEqual(len(self.lanes), 2,
                                "fewer than two watcher lanes parsed — this law reads the wrong "
                                "registry, so its greens mean nothing")

    def test_the_published_score_is_the_weakest_named_lane_not_the_sum(self):
        """The fake-confluence guard. Two lanes at (2,2) and (6,6) must publish 2/6-of-the-weakest,
        never 8 — because heart.scored hands ONE row's score to EVERY surface it names."""
        a, b = self.lanes[0], self.lanes[1]
        row = _drive({a: (2, 2), b: (6, 6)})
        self.assertEqual(
            (row.get("proofK"), row.get("proofN")), (2, 2),
            "published %r/%r for lanes at (2,2) and (6,6). The sum would credit the weaker lane "
            "with six sabotages it never survived." % (row.get("proofK"), row.get("proofN")))
        self.assertAlmostEqual(
            row.get("score"), wilson_lower(2, 2), places=4,
            msg="the score is not the weakest lane's — %r" % (row.get("score"),))

    def test_a_lane_attacked_and_never_refused_is_never_named_as_a_surface(self):
        """(0, n) is INERT — tested and never refused. Naming it would hand it the group's earned
        score, turning the most damning reading in the system into a passing one."""
        a, b = self.lanes[0], self.lanes[1]
        row = _drive({a: (2, 2), b: (0, 3)})
        self.assertEqual(list(row.get("surfaces") or []), [a],
                         "surfaces %r — an inert lane must not inherit a proven lane's score"
                         % (row.get("surfaces"),))
        self.assertIn(b, row["line"], "the inert lane is not even named in the line")
        self.assertEqual(row["state"], HE.WARN,
                         "a lane attacked and never refused is a WARN, not %r" % (row["state"],))

    def test_a_lane_never_attacked_is_unmeasured_and_says_so(self):
        """UNPROVEN and INERT must not collapse: one is work owed, the other is a dead watcher."""
        a = self.lanes[0]
        row = _drive({a: (2, 2)})
        self.assertEqual(row["state"], HE.UNKNOWN,
                         "%d lane(s) never attacked and the organ reported %r"
                         % (len(self.lanes) - 1, row["state"]))
        self.assertIn("never been attacked", row["line"])
        self.assertEqual(list(row.get("surfaces") or []), [a])

    def test_a_sabotage_credits_only_the_lane_whose_code_it_lands_in(self):
        """The attribution itself. A proof landing inside lane A's def span must move A and
        NOTHING else — this is the line between 6 real attacks and 163 borrowed ones."""
        name = sorted(self.spans)[0]
        lane, a, b = self.spans[name]
        inside = ""
        for ln in self.src.split("\n")[a - 1:b]:
            t = ln.strip()
            if len(t) > 30 and self.src.count(ln) == 1:
                inside = ln
                break
        self.assertTrue(inside, "no uniquely-anchorable line inside %s — cannot drive this" % name)
        per = HE._attribute_to_lanes([(True, True, True, inside)])
        self.assertEqual(per, {lane: (1, 1)},
                         "a proof landing inside %s credited %r instead of only %s"
                         % (name, per, lane))
        # and a find that matches nothing strikes nothing
        self.assertEqual(HE._attribute_to_lanes([(True, True, True, "zzz_no_such_anchor_zzz")]), {},
                         "a DEAD anchor earned a lane real credit — a sabotage that hits nothing "
                         "is not evidence of anything")


RED_PROOF = [
    {
        "why": "sums the named lanes instead of taking the weakest, so three lanes at (2,2) each "
               "publish (6,6) and every one of them is credited with the other two's sabotages — "
               "the exact fake-confluence this organ was built to refuse",
        "file": "health_engine.py",
        "find": "    _k = min((_lanes[l][0] for l in _proven), default=None)\n"
                "    _n = min((_lanes[l][1] for l in _proven), default=None)",
        "replace": "    _k = sum((_lanes[l][0] for l in _proven))\n"
                   "    _n = sum((_lanes[l][1] for l in _proven))",
        "matches": 1,
    },
    {
        "why": "names every lane in the ledger as a surface, so a lane ATTACKED AND NEVER REFUSED "
               "inherits the proven lanes' score and reads as supervised",
        "file": "health_engine.py",
        "find": "                k=_k, n=_n, surfaces=_proven)",
        "replace": "                k=_k, n=_n, surfaces=sorted(_lanes))",
        "matches": 1,
    },
    {
        "why": "drops the def-span test, so the FIRST lane in the registry is credited with every "
               "sabotage anywhere in control_app.py — 163 borrowed attacks instead of 6 real ones",
        "file": "health_engine.py",
        "find": "            if _a <= _ln <= _b:",
        "replace": "            if True:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
