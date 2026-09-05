#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CF-13's READING AID IS DYING, AND `actionable: 0` WOULD NEVER HAVE SAID SO.

⚠⚠ WHAT WAS MEASURED, 2026-09-05. `scope_reach_state` marks a row `narrow` when its reach is
`<= 10`, and calls the narrow-and-unpermitted rows `actionable` — *"the readable signal"*. But
reach is a three-deep walk over **`control_app.py`'s own call graph**, so it tracks THIS MODULE's
growth and not the lanes at all. Three dated snapshots of the same four lanes:

    2026-09-01    6 / 23 / 34 / 71     auto_scope's own docstring
    2026-09-02    6 / 24 / 34 / 72     the paragraph that stood in `scope_reach_state`
    2026-09-05    7 / 25 / 35 / 74     live

**Every number rose and none can fall while the module grows.** `tvd-ledger-backup` is the only row
that has ever been narrow, and it went **6 -> 7 in four days** against a threshold of **10**. When
it crosses, `narrow` is False for every row for ever and `actionable` stays 0 — while `0` goes on
reading as *"nothing needs you"* when it has come to mean *"this instrument can no longer tell the
rows apart"*. Two different facts under one number, which is the collapse this console keeps paying
for. [[unknown-stays-unknown]] [[label-outlived-referent]]

⚠ THE THRESHOLD IS NOT TOUCHED, DELIBERATELY. `auto_scope`'s author ruled that honest narrowing is
*"real work, not a parameter tweak"*; raising the number to keep a row underneath would make the
aid LOOK alive while measuring less. The death is published instead: `signal` is LIVE / DEAD /
UNKNOWN, and `narrowHeadroom` says how close the nearest row is to falling out. Measured today:
**LIVE, headroom 3.**

⚠⚠ AND THE GUARD ENFORCING THE AUTHOR'S RULING WAS ONE PROSE BLURB FROM LYING. It read
`assertNotIn("scope_reach", <run_gates.py source>)`, so writing the words into any `why=`
explanation in that file would have turned it red while nothing was registered — and deleting the
check would have looked like the fix. `scope_reach` occurs ZERO times there today, so it was latent
rather than lying: a guard that simply had not been caught out yet. It asks the GATE REGISTRY now.
[[source-reading-guard]]

⚠ NOTHING IS GATED AND NO NUMBER MOVES. This reports; `may()` is still never called and the reach
rows are still not a gate — which is itself checked, in `test_heart_surface`.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import auto_scope as AS  # noqa: E402
import control_app as CA  # noqa: E402


def _with_reach(delta):
    """Run scope_reach_state with every row's reach shifted by `delta`. -> dict

    ⚠ It shifts the AUDITOR's answer, not the threshold — so it reproduces what module growth
    actually does rather than what a parameter tweak would do.
    """
    real = AS.undeclared_reach_abilities

    def _shifted(mod):
        out = []
        for r in (real(mod) or []):
            fns = r.get("functions")
            n = len(fns) if isinstance(fns, (list, tuple)) else fns
            if not isinstance(n, int):
                out.append(r)
                continue
            r = dict(r)
            r["functions"] = max(0, n + delta)
            out.append(r)
        return out
    try:
        AS.undeclared_reach_abilities = _shifted
        return CA.scope_reach_state()
    finally:
        AS.undeclared_reach_abilities = real


class TheAidSaysWhetherItCanStillSeparateAnything(unittest.TestCase):

    def test_every_return_carries_the_same_keys(self):
        """REG-546 — a shape that changes with the verdict is not a shape, and the UNKNOWN paths
        are exactly the ones a consumer hits when nothing was established."""
        real = AS.undeclared_reach_abilities
        try:
            AS.undeclared_reach_abilities = lambda mod: (_ for _ in ()).throw(RuntimeError("x"))
            broke = CA.scope_reach_state()
        finally:
            AS.undeclared_reach_abilities = real
        live = CA.scope_reach_state()
        for k in ("ok", "rows", "why"):
            self.assertIn(k, broke, "the failure path drops %r" % k)
            self.assertIn(k, live)
        for k in ("signal", "narrowHeadroom", "narrowMax", "total", "actionable"):
            self.assertIn(k, live, "the success path does not publish %r" % k)

    def test_it_is_LIVE_while_some_row_is_still_narrow(self):
        r = CA.scope_reach_state()
        if not r.get("ok"):
            self.skipTest("the auditor could not be asked on this tree — not a pass")
        self.assertEqual(r["signal"], "LIVE")
        self.assertIsInstance(r["narrowHeadroom"], int)

    def test_it_goes_DEAD_when_NOTHING_can_be_narrow_any_more(self):
        """★★ RED PROOF, and it is not hypothetical — this is what a few more days of growth in
        `control_app.py` does. The only ever-narrow row has THREE functions of headroom."""
        r = _with_reach(+5)
        self.assertEqual(r["signal"], "DEAD",
                         "every row is now above the threshold and the aid still reports LIVE")
        self.assertEqual(r["actionable"], 0)
        self.assertIn("no longer means", r["why"],
                      "`actionable 0` is printed with nothing saying it stopped meaning "
                      "'nothing needs you'")

    def test_an_UNCOUNTABLE_reach_is_UNKNOWN_and_not_a_dead_aid(self):
        """⚠ [[unknown-stays-unknown]]. 'the walk gave no number' and 'the aid can no longer
        separate anything' are different facts and must not share a word."""
        real = AS.undeclared_reach_abilities
        try:
            AS.undeclared_reach_abilities = lambda mod: [
                {"lane": "x", "ability": "delete", "functions": None, "permitted": False}]
            r = CA.scope_reach_state()
        finally:
            AS.undeclared_reach_abilities = real
        self.assertEqual(r["signal"], "UNKNOWN")
        self.assertIsNone(r["narrowHeadroom"])

    def test_headroom_measures_the_NEAREST_row_not_the_worst(self):
        """The aid dies when the LAST narrow row crosses, so the distance that matters is the
        smallest reach. Taking the max would report years of headroom on the day it died."""
        r = CA.scope_reach_state()
        if not r.get("ok") or not r.get("rows"):
            self.skipTest("no rows on this tree — not a pass")
        reaches = [x["reach"] for x in r["rows"] if isinstance(x["reach"], int)]
        self.assertEqual(r["narrowHeadroom"], r["narrowMax"] - min(reaches))

    def test_headroom_goes_NEGATIVE_rather_than_clamping_at_zero(self):
        """⚠ A clamp would make 'just crossed' and 'crossed long ago' render identically, which is
        the same collapse one layer down."""
        self.assertLess(_with_reach(+5)["narrowHeadroom"], 0)


class TheThresholdIsNotQuietlyTuned(unittest.TestCase):
    """⚠⚠ THE ONE WAY THIS FIX COULD BECOME A LIE. Raising `_SCOPE_NARROW_MAX` to keep a row
    underneath is the 'parameter tweak' `auto_scope`'s author refused in favour of real narrowing
    work — it would make the aid look alive while measuring strictly less."""

    def test_the_threshold_is_a_NAMED_constant_and_still_ten(self):
        self.assertEqual(CA._SCOPE_NARROW_MAX, 10,
                         "the reach threshold moved. If that was deliberate narrowing work, say so "
                         "and re-measure; if it was to keep a row narrow, it is the tweak the "
                         "ruling refuses")

    def test_the_row_predicate_QUOTES_the_constant(self):
        """A second copy of `10` in the predicate would drift from the one the report publishes,
        and the panel would then describe a threshold nothing uses. [[copy-drift]]

        ⚠⚠ MY FIRST CUT OF THIS CASE WAS `assertNotIn("reach <= 10", src)` AND IT WENT RED ON MY
        OWN DOCSTRING — the sentence three screens up that reads *"`narrow` is `reach <= 10`, an
        ABSOLUTE count"*, written to EXPLAIN the defect. That is the seventh guard in this session
        satisfied by prose rather than behaviour, and the second inside the very change that fixes
        the same shape elsewhere. Reading source text cannot tell an explanation from an
        instruction; the AST can. [[source-reading-guard]]
        """
        import ast
        import inspect
        import textwrap
        tree = ast.parse(textwrap.dedent(inspect.getsource(CA.scope_reach_state)))
        names, literals = set(), []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            if isinstance(node, ast.Compare):
                for c in node.comparators:
                    if isinstance(c, ast.Constant) and c.value == CA._SCOPE_NARROW_MAX:
                        literals.append(node.lineno)
        self.assertIn("_SCOPE_NARROW_MAX", names,
                      "the predicate no longer reads the named constant")
        self.assertEqual(literals, [],
                         "a comparison against the literal %r is back in the code at line(s) %s — "
                         "a second copy drifts from the one the report publishes"
                         % (CA._SCOPE_NARROW_MAX, literals))


class TheRulingIsStillHonoured(unittest.TestCase):
    """`auto_scope`'s author: *"DO NOT PROMOTE THIS TO A FAILING GATE."*"""

    def test_it_reports_ok_TRUE_even_with_four_unexplained_rows(self):
        r = CA.scope_reach_state()
        if not r.get("ok"):
            self.skipTest("the auditor could not be asked — not a pass")
        self.assertTrue(r["ok"], "the reach rows started refusing")
        self.assertGreater(r["total"], 0, "no rows at all — the fixture proves nothing")

    def test_a_DEAD_aid_still_does_not_refuse(self):
        """★ The whole point: the aid dying must make the report LOUDER, never REFUSING."""
        r = _with_reach(+5)
        self.assertTrue(r["ok"], "a dead reading aid turned the report into a refusal")

    def test_the_reach_rows_are_not_registered_as_a_gate(self):
        """Asked of the REGISTRY, never of run_gates.py's source text — the source-text form of
        this check would have gone red on a prose blurb naming the thing it forbids."""
        import run_gates as RG
        names = [str(getattr(g, "name", "")) for g in getattr(RG, "GATES", [])]
        self.assertTrue(names, "no gates declared — this is measuring nothing")
        self.assertEqual([n for n in names if "scope_reach" in n], [])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
