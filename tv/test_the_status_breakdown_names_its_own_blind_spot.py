#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2808 — A BREAKDOWN THAT SUMS TO 100% OF A NUMBER IT ONLY PARTLY MEASURED IS A LIE.

`/api/status` answers in 0.024s idle and took ~52s under a recording session. v2320 already fought
this once and left the diagnosis in the source:

    "The cost was never 'computing the payload once'. Measured: warm 377 ms, and 11,887 ms only
     because ONE component — an uncached macOS TCC preflight at 1,934 ms cold — pushed each poll
     past the poll interval so threads stacked. CACHE THE EXPENSIVE COMPONENTS, leave the payload
     honest."

That ruling forecloses the obvious fix. v2319 cached the whole payload for one second and v2320
tore it out, because seven guards set state and read status back expecting it to be true NOW.

So the only honest move is to time the components — and the trap is in HOW. `status_payload` is a
243-line dict literal and only thirteen producers are wrapped. A breakdown built from those alone
would always account for 100% of itself and would therefore ALWAYS blame an instrumented name,
including when the real cost sits somewhere nobody wrapped.

★ SO THE TOTAL IS MEASURED SEPARATELY AND THE GAP IS PUBLISHED. `unattributedMs` is
`totalMs - sum(sections)`, and it is deliberately NOT clamped at zero: a negative gap means the
components double-counted, which is a broken instrument, and an instrument that hides its own
breakage is the thing this repo keeps rediscovering. [[zero-needs-a-denominator]]
[[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]
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

APP = os.path.join(HERE, "control_app.py")


def _app():
    with io.open(APP, encoding="utf-8") as fh:
        return fh.read()


def _fn(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


class TestTheStatusBreakdownNamesItsOwnBlindSpot(unittest.TestCase):

    def setUp(self):
        self.src = _app()
        self.tree = ast.parse(self.src)

    def test_the_payload_is_not_cached_v2320_still_stands(self):
        """The fix for slowness must never become the fix v2320 removed."""
        fn = _fn(self.tree, "status_payload")
        self.assertIsNotNone(fn, "status_payload is gone")
        # v2320: status is what is true NOW. A cache would return a stored dict instead of
        # building one, so the payload must be constructed fresh on every call.
        builds = [n for n in ast.walk(fn) if isinstance(n, ast.Dict) and len(n.keys) > 20]
        self.assertTrue(builds,
                        "status_payload no longer builds its payload — if it now returns a "
                        "stored one, that is the v2319 cache v2320 tore out")

    def test_the_name_is_the_interface(self):
        """⚠ v2810 — five gates broke because this body moved behind a shell.

        `_app_ver()` recovers the RUNNING version from `status_payload.__code__.co_consts`, on
        purpose, so a live process cannot report the version sitting on disk. Move the body to
        another name and the stamp silently becomes "v?" — the exact v2155 defect, re-created by
        a refactor that never touched its subject. [[regression-guard]]"""
        fn = _fn(self.tree, "status_payload")
        strings = [n.value for n in ast.walk(fn)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        vers = [v for v in strings if len(v) > 1 and v[0] == "v" and v[1:].isdigit()]
        self.assertTrue(vers,
                        "status_payload carries no vNNNN literal, so _app_ver() reading its "
                        "co_consts will report 'v?' — the body has been moved out from under it")

    def test_the_gap_is_published_and_never_clamped(self):
        """unattributedMs must exist, and must not be max()'d or abs()'d into looking healthy."""
        shell = _fn(self.tree, "status_payload")
        keys = [n.value for n in ast.walk(shell)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertIn("unattributedMs", keys,
                      "the shell computes no unattributedMs — a breakdown with no denominator")

        # find the assignment and prove it is a bare subtraction, not a clamped one
        gap = None
        for n in ast.walk(shell):
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant) and k.value == "unattributedMs":
                        gap = v
        self.assertIsNotNone(gap, "unattributedMs is named but never assigned a value")
        clamps = [c.func.id for c in ast.walk(gap)
                  if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                  and c.func.id in ("max", "abs")]
        self.assertEqual(clamps, [],
                         "unattributedMs is clamped with %s — a NEGATIVE gap means the components "
                         "double-counted, and hiding that hides a broken instrument" % clamps)

    def test_every_wrapped_producer_reaches_the_ledger(self):
        """A component timed under a name nothing publishes is a measurement nobody can read."""
        inner = _fn(self.tree, "status_payload")
        self.assertIsNotNone(inner, "status_payload is gone")
        named = set()
        for n in ast.walk(inner):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_t"
                    and n.args and isinstance(n.args[0], ast.Constant)):
                named.add(n.args[0].value)
        self.assertGreaterEqual(len(named), 10,
                                "only %d component(s) timed: %s. Thirteen were wrapped; a "
                                "breakdown this thin cannot name the slow one."
                                % (len(named), sorted(named)))
        # the two that the v2320 scar points at directly
        for must in ("pid", "captureProc"):
            self.assertIn(must, named,
                          "'%s' is not timed — it is a process/permission probe, which is exactly "
                          "the class that cost 1,934ms last time" % must)

    def test_an_unrun_ledger_says_unknown_not_zero(self):
        """Before any request completes there is no breakdown, and that is UNKNOWN."""
        fn = _fn(self.tree, "_status_timing_payload")
        self.assertIsNotNone(fn, "_status_timing_payload is gone")
        src = ast.get_source_segment(self.src, fn) or ""
        self.assertIn("UNKNOWN", src,
                      "the unrun state does not say UNKNOWN — a 0ms breakdown from a ledger that "
                      "has never been written reads as 'fast' and is 'unmeasured'")

    def test_the_reset_precedes_every_timed_producer(self):
        """⚠ v2812 — THE PREAMBLE SAT 113 LINES TOO LOW AND ATE TWO PRODUCERS.

        v2810 inlined the timing but put `_STATUS_TL.sect = {}` / `_t0` immediately above the
        return dict instead of at the top of the function. The first two `_t()` calls therefore
        recorded into the PREVIOUS request's dict, which the reset then wiped — so `agentAlive`
        (which is `_pid_cached` -> lsof, a prime suspect for the 52s) and `diskEyeAge` never
        appeared in the breakdown at all. And because `_t0` also started late, `totalMs` excluded
        their cost, so `unattributedMs` — the field whose whole job is to expose an unmeasured gap
        — could not reveal it either. A breakdown that drops a producer AND hides the drop.
        [[feedback-suspect-the-instrument]] [[zero-needs-a-denominator]]"""
        fn = _fn(self.tree, "status_payload")
        self.assertIsNotNone(fn, "status_payload is gone")
        resets = [st.lineno for st in ast.walk(fn)
                  if isinstance(st, ast.Assign)
                  and "sect" in ast.dump(st)
                  and "{}" in (ast.get_source_segment(self.src, st) or "")]
        timed = [n.lineno for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_t"]
        self.assertTrue(resets, "the per-request section dict is never reset")
        self.assertTrue(timed, "nothing is timed at all")
        self.assertLess(min(resets), min(timed),
                        "the reset is at line %d but the first timed producer is at line %d — "
                        "every _t() above the reset records into the previous request's dict and "
                        "is then wiped, so it never reaches the breakdown"
                        % (min(resets), min(timed)))

    def test_the_timing_reaches_the_wire(self):
        """Measured and never published is the [[the-unjoined-end]] shape."""
        inner = _fn(self.tree, "status_payload")
        pub = [n for n in ast.walk(inner)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "_status_timing_payload"]
        self.assertEqual(len(pub), 1,
                         "the timing ledger is called %d time(s) inside the payload — it must be "
                         "published exactly once or nothing can read it" % len(pub))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Heart 2.0 re-runs this in a sandbox and DISTRUSTS the law if it stays green.
RED_PROOF = [
    {
        "why": "clamping the gap at zero is the exact dishonesty this law exists to forbid",
        "file": "control_app.py",
        "find": '            "unattributedMs": round(_total - _sum, 1),',
        "replace": '            "unattributedMs": max(0.0, round(_total - _sum, 1)),',
        "matches": 1,
    },
    {
        "why": "moving the reset below the first producer silently drops it from the breakdown",
        "file": "control_app.py",
        "find": "    _STATUS_TL.sect = {}\n    _t0 = time.time()",
        "replace": "    _t0 = time.time()",
        "matches": 1,
    },
    {
        "why": "un-timing the process probe returns the breakdown to blaming whatever is left",
        "file": "control_app.py",
        "find": '        "pid": _t("pid", _pid_cached),',
        "replace": '        "pid": _pid_cached(),',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
