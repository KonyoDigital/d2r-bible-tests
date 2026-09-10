# -*- coding: utf-8 -*-
"""#44 — THE HARNESS COMES FIRST: nothing may be unified until every technique is accounted for.

Konyo, 2026-09-08: *"first make sure to harness every single technique and every single template
and every single thing related so no gaps are missing when you finally leave and unify the ON AIR
and MINI."*

★ THE ORDER IS THE INSTRUCTION. This gate is what makes it enforceable rather than remembered.
`unify_census.may_unify()` must return False while any technique is a measured gap OR an unasked
question, and this holds it to that — including the part that is easiest to lose, which is that
UNKNOWN blocks just as hard as a known gap.

MEASURED 2026-09-09 on his tree: 19 techniques — 4 reproduced, 8 measured gaps, 7 unasked. The
stream stamp `door` covers 25 of 3,926 journal rows (0.6%), and 19 of the 23 ON AIR rows are
`session_end` system rows carrying 2 names between them. So a per-scenario tally over that
population cannot tell "ON AIR never reaches CHRONICLE" from "ON AIR has barely run" — both read
0 — and the census says UNKNOWN rather than picking one. [[zero-needs-a-denominator]]

⚠ MINI AUTO (hover) is deliberately OUT OF SCOPE — his ruling, #17/#41, and folding it in here
would put a decision he reserved inside a gate he did not ask for.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import unify_census as UC  # noqa: E402


class TheCensusRefusesToGuess(unittest.TestCase):

    def test_an_unasked_question_blocks_as_hard_as_a_known_gap(self):
        """★ THE LAW. `None` is not a soft `True`."""
        rep = {"ok": True, "rows": [{"kind": "template", "technique": "stash",
                                     "reproduced": None, "why": "never checked"}],
               "total": 1, "reproduced": 0, "gaps": 0, "unknown": 1}
        ok, why = UC.may_unify(rep)
        self.assertFalse(ok, "the unify was authorised while a technique had never been checked — "
                             "an unasked question read as a yes")
        self.assertIn("never been checked", why)

    def test_a_census_that_could_not_be_read_refuses_rather_than_permits(self):
        """An instrument failure must never become permission."""
        ok, why = UC.may_unify({"ok": False, "why": "extract_gap would not import"})
        self.assertFalse(ok, "a census that failed to run AUTHORISED the removal it exists to gate")
        self.assertIn("nothing is established", why)

    def test_a_clean_census_does_authorise(self):
        """A gate that can only say no is not a gate. [[feedback-blind-fixture-green-gate]]"""
        ok, _ = UC.may_unify({"ok": True, "rows": [], "total": 3, "reproduced": 3,
                              "gaps": 0, "unknown": 0})
        self.assertTrue(ok, "a census with everything reproduced still refused — this gate can "
                            "never go green and therefore measures nothing")


class TheCensusIsDerivedNotRemembered(unittest.TestCase):

    def test_the_entry_points_still_exist(self):
        """A walk seeded on renamed functions reports a tidy 0 gaps over nothing."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        names = {n.name for n in ast.walk(ast.parse(src))
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for e in UC.MINI_ENTRIES + UC.ONAIR_ENTRIES:
            self.assertIn(e, names,
                          "%r is a census entry point and no longer exists in control_app.py — "
                          "the walk would be seeded on nothing and report a clean shelf" % e)

    def test_a_renamed_entry_point_is_a_refusal_not_a_zero(self):
        real = UC.MINI_ENTRIES
        try:
            UC.MINI_ENTRIES = ("a_function_that_does_not_exist_anywhere",)
            rows, why = UC.read_paths()
        finally:
            UC.MINI_ENTRIES = real
        self.assertIsNone(rows, "a walk seeded on a missing function returned ROWS instead of "
                                "refusing — it measured nothing and said nothing")
        self.assertIn("measured nothing", why)

    def test_the_templates_come_from_the_route_table(self):
        import reel_templates as RT
        rows, why = UC.templates()
        self.assertIsNotNone(rows, why)
        self.assertEqual(len(list(RT.ROUTES)), len(rows),
                         "the census names %d templates and reel_templates declares %d — a "
                         "hand-kept list has drifted from the real one"
                         % (len(rows), len(list(RT.ROUTES))))

    def test_the_scenarios_come_from_the_extractors_own_constants(self):
        import extract_gap as EG
        rows, why = UC.scenarios()
        self.assertIsNotNone(rows, why)
        self.assertEqual({"PANEL", "FLOOR", "CHRONICLE"}, {r["technique"] for r in rows})
        got = [r for r in rows if r["technique"] == "PANEL"][0]
        for scene in EG.PANEL_SCENES:
            self.assertIn(scene, got["why"],
                          "PANEL no longer names scene %r, so a scene added upstream would be "
                          "silently uncovered" % scene)

    def test_every_exemption_carries_its_reason(self):
        """An unexplained exemption list is how a real gap gets waved through."""
        for name, why in UC.NOT_A_TECHNIQUE.items():
            self.assertTrue(len(str(why)) > 20,
                            "%r is exempted from the census with no reason worth the name" % name)


class TheDenominatorIsPublished(unittest.TestCase):

    def test_a_thin_stream_is_unknown_and_never_a_measured_gap(self):
        """0 rows and 0 hits look identical. Only the denominator separates them."""
        real = UC._door_rows
        try:
            UC._door_rows = lambda: ({"onair": [{"scene": "loot", "names": ["x"]}]},
                                     {"stamped": 1, "total": 3926, "pct": 0.0}, "")
            got, why = UC._stream_verdict(lambda r: r.get("scene") == "chronicle", "CHRONICLE")
        finally:
            UC._door_rows = real
        self.assertIsNone(got, "one ON AIR row was enough to declare a MEASURED GAP — 'never "
                               "reaches it' and 'has barely run' both read 0 and this picked one")
        self.assertIn("barely run", why)

    def test_a_real_denominator_does_produce_a_verdict(self):
        real = UC._door_rows
        try:
            rows = [{"scene": "loot", "names": ["x"]} for _ in range(UC.MIN_ROWS_TO_JUDGE + 5)]
            UC._door_rows = lambda: ({"onair": rows},
                                     {"stamped": len(rows), "total": 4000, "pct": 1.0}, "")
            gap, gwhy = UC._stream_verdict(lambda r: r.get("scene") == "chronicle", "CHRONICLE")
            hit, hwhy = UC._stream_verdict(lambda r: r.get("scene") == "loot", "FLOOR")
        finally:
            UC._door_rows = real
        self.assertIs(False, gap, "a real denominator with zero hits did not produce a gap — this "
                                  "census could never turn an UNKNOWN into an answer")
        self.assertIn("measured gap", gwhy)
        self.assertIs(True, hit)

    def test_the_coverage_is_published_on_the_census_itself(self):
        rep = UC.census()
        self.assertIn("doorCoverage", rep,
                      "the census reports per-technique verdicts without publishing the stamped "
                      "population they are all bounded by")
        if rep.get("ok"):
            cov = rep["doorCoverage"]
            # ⚠⚠ v2881 — AN UNKNOWN COVERAGE IS ALLOWED; AN UNKNOWN COVERAGE WITH NO REASON IS NOT.
            # This asserted `cov is not None` on every ok census. But the per-technique verdicts come
            # from the technique families, and the stamped population comes from the journal — two
            # sources, and the second can be absent while the first is perfectly readable. The census
            # publishes `doorCoverageWhy` precisely so it can say ok about the verdicts and UNKNOWN
            # about their bound. Demanding a number there forced the census to invent a denominator
            # or go not-ok, which are the two failures this design already avoids.
            # MEASURED on CI: "unexpectedly None : no journal at sessions.jsonl, so nothing is
            # established about either stream" — a runner has no journal, so the law could only ever
            # pass on a machine that had run sessions. The contract is: a number, or a reason.
            # [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[feedback-blind-fixture-green-gate]]
            if cov is None:
                self.assertTrue(str(rep.get("doorCoverageWhy") or "").strip(),
                                "doorCoverage is None and doorCoverageWhy is empty — the population "
                                "every verdict is bounded by is unknown and nothing says why, which "
                                "is the one reading this field exists to prevent")
            else:
                self.assertIn("total", cov)
                self.assertIn("stamped", cov)


class TheLiveAnswerIsHonest(unittest.TestCase):

    def test_the_live_census_blocks_and_names_why(self):
        rep = UC.census()
        if not rep.get("ok"):
            self.skipTest("a technique family could not be read here — %s" % rep.get("why", ""))
        ok, why = UC.may_unify(rep)
        self.assertFalse(ok, "the census says MINI may be removed. If that is genuinely true this "
                             "gate should be retired with the merge — it is not true today: %s"
                             % why)
        self.assertTrue(rep["gaps"] or rep["unknown"],
                        "it refused with neither a gap nor an unknown, so the refusal has no cause")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "treating UNKNOWN as permission is the exact defect his 'first make sure' guards "
               "against — an unasked question is not a yes",
        "file": "unify_census.py",
        "find": """    if rep["unknown"]:""",
        "replace": """    if False:""",
        "matches": 1,
    },
    {
        "why": "a census that could not run must never authorise the removal it exists to gate — "
               "that turns an instrument failure into permission",
        "file": "unify_census.py",
        "find": """    if not rep.get("ok"):
        return False, ("the census could not be completed""",
        "replace": """    if not rep.get("ok"):
        return True, ("the census could not be completed""",
        "matches": 1,
    },
    {
        "why": "dropping the seed check lets the walk run on renamed entry points and report a "
               "tidy zero gaps over nothing at all",
        "file": "unify_census.py",
        "find": """    if missing:""",
        "replace": """    if False:""",
        "matches": 1,
    },
    {
        "why": "removing the denominator floor makes one ON AIR row enough to declare a MEASURED "
               "gap — 'never reaches it' and 'has barely run' both read 0",
        "file": "unify_census.py",
        "find": """    if len(bearing) < MIN_ROWS_TO_JUDGE:""",
        "replace": """    if False:""",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
