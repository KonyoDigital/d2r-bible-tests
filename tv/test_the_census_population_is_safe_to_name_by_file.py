# -*- coding: utf-8 -*-
"""v3433 (#177) — THE FILENAME RULE IS SAFE ONLY WHILE NO PRODUCTION MODULE IS NAMED LIKE A TEST.

v3427 made `lane_census._package_files()` skip `test_*.py` / `*_test.py`, because a test FIXTURE
defining `def wait(self)` had flipped the live thread target `target=wp.wait` from FOREIGN to
UNKNOWN. The second eye (#177) then said, correctly, that classifying by FILENAME is the wrong
axis: a production module that happens to be named that way would be silently dropped.

⚠⚠ I WAS ABOUT TO REPLACE IT WITH AN IMPORT-GRAPH RULE AND MEASURED FIRST. Walking imports from
`control_app` / `tv_diablo` / `console_doctor` / `health_engine`:

    local modules                      705
    reachable from production roots     110
    kept by the FILENAME rule           199
    reachable but EXCLUDED by name    NONE
    census targets whose answer changes   0   <- of 33

**The graph rule changes nothing today, and it adds a failure mode the filename rule does not
have: sensitivity to which roots you pick.** `conftest` lands INSIDE the production graph purely
because `run_gates` imports it. Shipping it would have looked more principled while measuring the
same thing and giving the next reader a new way to be wrong. [[feedback-verify-not-proxy]]

So the rule stays, and what was an UNEXAMINED ASSUMPTION becomes a pinned invariant: the filename
rule is correct exactly while no production-reachable module is named like a test. This file fails
the moment that stops being true — which is the only moment the rule would start lying.
"""
import ast
import glob
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import lane_census as LC  # noqa: E402

ROOTS = ("control_app", "tv_diablo", "console_doctor", "health_engine")


def _local_modules():
    return {os.path.basename(f)[:-3] for f in glob.glob(os.path.join(HERE, "*.py"))}


def _imports_of(mod, local):
    try:
        with io.open(os.path.join(HERE, mod + ".py"), encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module and n.level == 0:
                out.add(n.module.split(".")[0])
    return {m for m in out if m in local}


def _production_reachable():
    local = _local_modules()
    seen, stack = set(), [r for r in ROOTS if r in local]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        stack.extend(_imports_of(m, local) - seen)
    return seen


def _looks_like_a_test(name):
    return name.startswith("test_") or name.endswith("_test")


class TestTheCensusPopulationIsSafeToNameByFile(unittest.TestCase):

    def test_no_PRODUCTION_reachable_module_is_named_like_a_test(self):
        """THE INVARIANT THE FILENAME RULE RESTS ON. The moment a module that production actually
        imports is called `test_*`, `_package_files()` drops it from `_defined_anywhere`, and a
        real lane defined there is waved through as FOREIGN — "not ours, stop watching"."""
        offenders = sorted(m for m in _production_reachable() if _looks_like_a_test(m))
        self.assertEqual(offenders, [],
                         "%r is reachable from %r AND named like a test, so lane_census drops it "
                         "from the population it uses to decide FOREIGN. Either rename it or stop "
                         "classifying by filename — the rule is only safe while this list is empty."
                         % (offenders, list(ROOTS)))

    def test_the_roots_this_law_walks_actually_exist(self):
        """⚠ A REACHABILITY LAW OVER A ROOT THAT IS GONE IS A LAW OVER NOTHING — it would return an
        empty set and pass forever. [[zero-needs-a-denominator]]"""
        local = _local_modules()
        missing = [r for r in ROOTS if r not in local]
        self.assertEqual(missing, [], "root module(s) %r are gone, so this law walks nothing" % missing)
        reach = _production_reachable()
        self.assertGreater(len(reach), 20,
                           "only %d module(s) are reachable from the roots — the walk broke, and an "
                           "empty population cannot refuse anything" % len(reach))

    def test_the_exclusion_still_drops_the_fixture_that_caused_v3427(self):
        """The rule must still do the job it was added for: the Popen double with `def wait` lives
        in a `test_*` file and must NOT count as a definition."""
        kept = {os.path.basename(p)[:-3] for p in LC._package_files()}
        self.assertNotIn("test_a_broken_pipe_must_not_skip_the_reap", kept,
                         "the fixture whose `def wait` flipped a live lane is back in the "
                         "population — v3427's defect returns")
        self.assertIn("control_app", kept, "production modules were dropped from the population")

    def test_wait_is_still_FOREIGN_on_this_tree(self):
        """The live reading the whole thing exists to protect."""
        kinds = {r["fn"]: r["kind"] for r in LC.census()}
        self.assertEqual(kinds.get("wait"), "FOREIGN",
                         "`wait` is %r — a test fixture has re-entered the population, or the "
                         "population broke" % kinds.get("wait"))
        self.assertEqual(sorted(f for f, k in kinds.items() if k == "UNKNOWN"), [],
                         "unclassified thread target(s) appeared")


RED_PROOF = [
    {
        "why": "v3433 - THE EXCLUSION REMOVED. Without it the test fixture that defines `def wait` "
               "re-enters the population, `_defined_anywhere('wait')` turns True, and the live "
               "thread target `target=wp.wait` stops being FOREIGN - which is exactly the "
               "misclassification v3427 was built to end.",
        "file": "lane_census.py",
        "find": "                  if not os.path.basename(f).startswith(\"test_\")\n                  and not os.path.basename(f).endswith(\"_test.py\"))",
        "replace": "                  if True)",
        "matches": 1,
    },
    {
        "why": "v3433 - THE ROOT LIST EMPTIED. A reachability law whose roots resolve to nothing "
               "walks an empty graph and passes forever - a zero with no denominator wearing the "
               "shape of a clean bill.",
        "file": "test_the_census_population_is_safe_to_name_by_file.py",
        "find": "ROOTS = (\"control_app\", \"tv_diablo\", \"console_doctor\", \"health_engine\")",
        "replace": "ROOTS = (\"no_such_root_module\",)",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
