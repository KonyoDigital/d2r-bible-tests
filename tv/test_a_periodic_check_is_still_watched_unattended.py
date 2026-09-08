#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2802 — "RUNS SOMEWHERE" AND "RUNS UNWATCHED" ARE DIFFERENT PROPERTIES, AND ONLY ONE WAS GUARDED.

v2801 measured `engines corroborate` at 6,638-13,038 ms inside console_doctor's every-tick subset
and moved it into SLOW. The measurement was right. The move deleted a supervision loop, because
`_eagle_once` calls `run(include_slow=False)` — so in the unattended path SLOW does not mean "less
often", it means **never**. That check is the only caller of `corroborate.verdict()`, which holds
every cross-engine invariant the console has: owned-is-contained, chronicle-owed,
swept-split-adds-up, evidence-survived-its-sweep. After that commit a 19-vs-2 or 1263-vs-403
disagreement could only be found by Konyo pressing the eagle button himself.

⚠⚠ AND THE EXISTING MIRROR GATE WAS GREEN THROUGHOUT. `test_a_check_moved_to_SLOW_is_still_RUN_
somewhere` asks whether the FULL run still performs it. It does — that is true, and it is not the
question. The property that was removed is whether anything performs it WITH NOBODY WATCHING, and
no law in this tree asked that. It took a cross-family review of the pushed diff to say so.
[[build-the-heart-and-census-everywhere]] [[the-unjoined-end]]

THE TIER: SLOW keeps its meaning — on demand only, ~2 minutes, a human is waiting. PERIODIC is for
a check too expensive for every ten-minute tick and too important to go unwatched; it runs
unattended on a longer cadence instead of not at all.

THIS LAW GUARDS THE PROPERTY, NOT THE MEMBERSHIP. It does not care which checks are periodic. It
asserts that whatever is in PERIODIC is genuinely reached by the unattended loop, within a bounded
number of ticks, and that the loop passes a real argument rather than a constant.
"""
import os
import ast
import io
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd  # noqa: E402

APP = os.path.join(HERE, "control_app.py")


def _app_src():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


def _eagle_fn():
    tree = ast.parse(_app_src())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "_eagle_once":
            return n
    return None


class TestPeriodicIsStillWatched(unittest.TestCase):

    def test_the_tiers_are_disjoint(self):
        """A name in BOTH is in SLOW as far as the unattended loop is concerned — the skip for
        SLOW runs first — so the periodic promise would be silently void."""
        both = sorted(set(cd.PERIODIC) & set(cd.SLOW))
        self.assertEqual(both, [],
                         "these are in SLOW and PERIODIC at once, and SLOW wins in run(): %s"
                         % both)

    def test_every_periodic_name_is_a_real_check(self):
        names = [n for n, _ in cd.CHECKS]
        for p in cd.PERIODIC:
            self.assertIn(p, names,
                          "%r is PERIODIC and not on the roster at all — it runs nowhere" % p)
        print("\n   PERIODIC: %s  every %d tick(s)" % (list(cd.PERIODIC), cd.PERIODIC_EVERY))

    def test_the_unattended_loop_passes_a_real_argument(self):
        """The eagle must pass include_periodic, and must not pass a constant False — which would
        be the same 'never' wearing a keyword."""
        fn = _eagle_fn()
        self.assertIsNotNone(fn, "_eagle_once not found")
        passed = []
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
               and n.func.attr == "run":
                for kw in n.keywords:
                    if kw.arg == "include_periodic":
                        passed.append(kw.value)
        self.assertTrue(passed,
                        "_eagle_once never passes include_periodic, so PERIODIC checks are "
                        "unreachable unattended — the exact regression this tier exists to undo")
        for v in passed:
            self.assertFalse(isinstance(v, ast.Constant) and v.value is False,
                             "_eagle_once passes include_periodic=False — a constant 'never'")

    def test_a_periodic_check_is_reached_within_the_cadence(self):
        """THE PROPERTY ITSELF, driven rather than read. Replaying the eagle's own tick arithmetic
        must include the periodic tier at least once inside one cadence — and on the FIRST tick,
        because a console restarted more often than the cadence would otherwise never reach one."""
        every = int(cd.PERIODIC_EVERY)
        self.assertGreaterEqual(every, 1)
        hits = [t for t in range(1, every + 1) if (t == 1) or (t % every == 0)]
        self.assertTrue(hits,
                        "no tick in a full cadence of %d includes the periodic tier" % every)
        self.assertIn(1, hits,
                      "the first tick after a restart skips the periodic tier, so a console that "
                      "restarts more often than the cadence never runs it at all")

    def test_run_actually_skips_and_includes_on_the_flag(self):
        """Drive run() itself with a stubbed roster, so this measures the function rather than
        a reading of it."""
        seen = []
        real_checks, real_slow, real_periodic = cd.CHECKS, cd.SLOW, cd.PERIODIC
        try:
            cd.CHECKS = [("cheap-one", lambda: (cd.OK, "fine")),
                         ("costly-one", lambda: (cd.OK, "fine"))]
            cd.SLOW = ()
            cd.PERIODIC = ("costly-one",)
            names = [r["check"] for r in cd.run(include_slow=False, include_periodic=False)]
            self.assertIn("cheap-one", names)
            self.assertNotIn("costly-one", names,
                             "include_periodic=False still ran the periodic check")
            names = [r["check"] for r in cd.run(include_slow=False, include_periodic=True)]
            self.assertIn("costly-one", names,
                          "include_periodic=True did NOT run the periodic check — the tier is "
                          "unreachable in both directions, which is worse than the regression")
        finally:
            cd.CHECKS, cd.SLOW, cd.PERIODIC = real_checks, real_slow, real_periodic
        del seen


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# A constant False is the same "never" the tier exists to undo, wearing a keyword.
RED_PROOF = [{
    "why": "include_periodic=False returns the corroborator to never-runs-unattended",
    "file": "control_app.py",
    "find": "        rows = _cd.run(include_slow=_include_slow, include_periodic=_include_periodic)",
    "replace": "        rows = _cd.run(include_slow=_include_slow, include_periodic=False)",
    "matches": 1,
}]


if __name__ == "__main__":
    unittest.main(verbosity=2)
