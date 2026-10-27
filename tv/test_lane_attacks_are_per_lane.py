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


class TheConsoleParsesEachSourceOnce(unittest.TestCase):
    """#172 (2026-10-27) - his console spent its memory re-parsing its own source: the attack tally ast.parsed ~1,100 gate
    files each time the census moved, and the doctor's swallow census ~1,500 files on every 10-min eagle tick. Each file's
    answer depends on its bytes alone, so it is parsed once and again only when its size or mtime moves."""

    def setUp(self):
        import tempfile
        import shutil
        self.d = tempfile.mkdtemp(prefix="parse_once_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self._rp = dict(HE._RP_FILE_CACHE)
        HE._RP_FILE_CACHE.clear()
        self.addCleanup(lambda: (HE._RP_FILE_CACHE.clear(), HE._RP_FILE_CACHE.update(self._rp)))

    def _write(self, name, text):
        with io.open(os.path.join(self.d, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _touch(self, name):
        p = os.path.join(self.d, name)
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write("\n# edited\n")
        st = os.stat(p)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 2000000000))

    def test_a_gate_files_red_proofs_are_read_once_until_it_changes(self):
        self._write("test_x.py", "RED_PROOF = []\n")
        calls = []

        class FakeHeart2(object):
            HERE = self.d

            @staticmethod
            def red_proofs_in(fn):
                calls.append(fn)
                return [{"file": "control_app.py", "find": "x"}]
        a = HE._red_proofs_cached(FakeHeart2, "test_x.py")
        b = HE._red_proofs_cached(FakeHeart2, "test_x.py")
        self.assertEqual(a, b)
        self.assertEqual(len(calls), 1, "an unchanged gate file was parsed again: %r" % calls)
        self._touch("test_x.py")
        HE._red_proofs_cached(FakeHeart2, "test_x.py")
        self.assertEqual(len(calls), 2, "an edited gate file was not read again: %r" % calls)

    def test_the_swallow_census_parses_each_file_once_until_it_changes(self):
        import ast as _ast
        import swallow_census as SC
        self._write("a.py", "try:\n    x = 1\nexcept Exception:\n    pass\n")
        self._write("b.py", "try:\n    y = 2\nexcept ValueError:\n    y = None\n")
        real, parsed = _ast.parse, []

        def counting(src, *a, **k):
            parsed.append(1)
            return real(src, *a, **k)
        SC.ast.parse = counting
        try:
            first = SC.scan(self.d)
            n1 = len(parsed)
            second = SC.scan(self.d)
            n2 = len(parsed) - n1
            self._touch("a.py")
            third = SC.scan(self.d)
            n3 = len(parsed) - n1 - n2
        finally:
            SC.ast.parse = real
        rows = lambda r: sorted((x["file"], x["line"], x["rank"], x["shape"]) for x in r["rows"])  # noqa: E731
        self.assertEqual(n1, 2, "PREMISE: the first census did not parse both files")
        self.assertEqual(rows(first), rows(second), "a cached census answered differently")
        self.assertEqual(n2, 0, "an unchanged tree was parsed again on the next tick")
        self.assertEqual(n3, 1, "editing one file did not re-parse exactly that file")
        self.assertEqual(len(third["rows"]), len(first["rows"]))


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
    {"why": "#172 - the attack tally parses every gate file again whenever the census moves",
     "file": "health_engine.py",
     "find": "    hit = _RP_FILE_CACHE.get(fn)\n    if hit is not None and hit[0] == key:\n        return hit[1]\n",
     "replace": "",
     "matches": 1},
    {"why": "#172 - an edited gate file keeps its old red-proof list for ever",
     "file": "health_engine.py",
     "find": "        key = (st.st_mtime_ns, int(st.st_size))\n    except OSError:\n        return h2.red_proofs_in(fn)\n",
     "replace": "        key = 0\n    except OSError:\n        return h2.red_proofs_in(fn)\n",
     "matches": 1},
    {"why": "#172 - the swallow census parses every file again on every eagle tick",
     "file": "swallow_census.py",
     "find": "    if hit is not None and hit[0] == key:\n        return hit[1], None\n",
     "replace": "",
     "matches": 1},
    {"why": "#172 - an edited file keeps its old swallow rows for ever",
     "file": "swallow_census.py",
     "find": "        key = (st.st_mtime_ns, int(st.st_size))\n    except OSError as e:\n",
     "replace": "        key = 0\n    except OSError as e:\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
