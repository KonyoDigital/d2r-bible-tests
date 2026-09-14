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

try:
    from console_safe import enable
    enable()
except Exception:
    pass

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

    def test_the_weakest_lane_is_by_SCORE_not_by_each_number_separately(self):
        """The second eye's High on v3145. min(k) and min(n) taken independently invent a pair no
        lane holds: (2,5) and (2,2) -> (2,2) -> 0.3424, while the (2,5) lane's own evidence
        supports 0.1176. A three-fold overstatement out of the organ written to refuse it.

        ⚠ Every live lane is (2,2) today, so componentwise and by-score agree on the real tree.
        Driven, or this law would be green against its own defect. [[unknown-stays-unknown]]"""
        a, b = self.lanes[0], self.lanes[1]
        row = _drive({a: (2, 5), b: (2, 2)})
        self.assertEqual(
            (row.get("proofK"), row.get("proofN")), (2, 5),
            "published %r/%r — the (2,5) lane holds the weakest evidence and must set the score, "
            "but componentwise minima hand it the (2,2) lane's."
            % (row.get("proofK"), row.get("proofN")))
        self.assertAlmostEqual(row.get("score"), wilson_lower(2, 5), places=4)
        self.assertLess(row.get("score"), wilson_lower(2, 2),
                        "the published score is not below the stronger lane's — nobody is "
                        "protected from inheriting evidence they never earned")

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
        "why": "takes min(k) and min(n) INDEPENDENTLY, which invents a pair no lane holds: a "
               "(2,5) lane beside a (2,2) lane publishes (2,2) = 0.3424 while the first lane's "
               "own evidence supports 0.1176 — a three-fold overstatement out of the organ "
               "written to refuse overstatement",
        "file": "health_engine.py",
        "find": "    _weak = min(_proven,\n"
                "                key=lambda l: _conf.wilson_lower(_lanes[l][0], _lanes[l][1])) if _proven else None\n"
                "    _k, _n = _lanes[_weak] if _weak else (None, None)",
        "replace": "    _k = min((_lanes[l][0] for l in _proven), default=None)\n"
                   "    _n = min((_lanes[l][1] for l in _proven), default=None)",
        "matches": 1,
    },
    {
        "why": "names every lane in the ledger as a surface, so a lane ATTACKED AND NEVER REFUSED "
               "inherits the proven lanes' score and reads as supervised",
        "file": "health_engine.py",
        "find": "                k=_k, n=_n, surfaces=_proven,",
        "replace": "                k=_k, n=_n, surfaces=sorted(_lanes),",
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
