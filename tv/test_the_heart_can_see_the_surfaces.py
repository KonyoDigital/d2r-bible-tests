#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""♥ THE RENDER VERDICT WAS NOT DURABLE, SO THE HEART COULD NOT READ IT.

Konyo, 2026-09-09: *"when we hit 100% on heart 2.0 its also a VISUAL PASS right? ... the lock and
everything still derives from the heart and visually seen"*.

v2858 made the census admit the split — 269 gates, only TEN import render_check, so 100% would be
~96% backend. This closes the other half of that finding: WHY the visual share could not even be
measured. `render_check` wrote PNGs and, only on --bless, a coverage FLOOR. Which targets actually
REPORTED on a run existed nowhere but the push log and the terminal. `.render_shots` cannot stand in
— it is gitignored and held 425 files mixing the 16 live targets with ad-hoc shots back to v2262, so
it cannot answer "did `locks` report this run?". A verdict nobody records is a verdict nobody can
supervise. [[the-unjoined-end]] [[stale-reading]]

MEASURED after the join, on a full run: 16 of 16 targets reported, coverageMissing 0,
renderFailures 0, and heart2.surface_verdict() reads state OK at an age of 8s.
"""
import ast
import io
import time
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints ♥ ⚠ ★
console_safe.enable()

import heart2 as H  # noqa: E402

RC = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()


RED_PROOF = [
    {
        "why": "un-writing the verdict returns the render result to the push log and the terminal, "
               "which is exactly the state that made the visual share unmeasurable",
        "file": "render_check.py",
        "find": '            _fh.write(json.dumps(_v, indent=2, sort_keys=True, ensure_ascii=False) + "\\n")',
        "replace": '            pass',
        "matches": 1,
    },
    {
        "why": "letting an ABSENT verdict read as OK is the whole defect in miniature: a surface "
               "nobody photographed reporting as one that passed",
        "file": "heart2.py",
        "find": '        return {"state": "UNMEASURED", "why": "render_check has never written a verdict here — "',
        "replace": '        return {"state": "OK", "why": "render_check has never written a verdict here — "',
        "matches": 1,
    },
    {
        "why": "v2871's CI condition made permanent: a render that reported ZERO targets grades "
               "PARTIAL instead of UNMEASURED. An empty container returning a clean-looking "
               "verdict is the exact shape CI was in for four ships while nobody could say why",
        "file": "heart2.py",
        "find": '                      "PARTIAL" if rep else "UNMEASURED"),',
        "replace": '                      "PARTIAL"),',
        "matches": 1,
    },
    {
        "why": "dropping the count comparison lets a 2-of-6 SUBSET run grade OK — a partial "
               "render speaking for the four surfaces it never looked at",
        "file": "heart2.py",
        "find": '    return {"state": ("OK" if (v.get("full") and tot and len(rep) >= tot) else',
        "replace": '    return {"state": ("OK" if (v.get("full") and tot) else',
        "matches": 1,
    },
]


class TheHeartCanSeeTheSurfaces(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_an_ABSENT_verdict_is_UNMEASURED_never_OK(self):
        """★★ The dangerous direction. A surface nobody looked at must not report as looked at."""
        got = H.surface_verdict(os.path.join(tempfile.gettempdir(), "no_such_render_verdict.json"))
        self.assertEqual(
            "UNMEASURED", got.get("state"),
            "an absent render verdict reported %r. Nothing was photographed and the heart said it "
            "was fine — a zero-that-is-really-unknown, on the one axis he asked about."
            % got.get("state"))

    def test_an_UNREADABLE_verdict_is_UNMEASURED_too(self):
        """★ A broken record is not an empty one."""
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        f.write("{ this is not json")
        f.close()
        try:
            got = H.surface_verdict(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual("UNMEASURED", got.get("state"),
                         "a verdict that would not parse reported %r" % got.get("state"))

    def test_render_check_actually_WRITES_the_verdict(self):
        """★★ Parsed, not grepped: the writer must be a real call, not prose about one."""
        tree = ast.parse(RC)
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                names.add(n.value)
        self.assertIn(
            ".render_verdict.json", names,
            "render_check.py no longer names the verdict file, so which surfaces reported is once "
            "again recorded nowhere the heart can read")
        # ⚠⚠ AND IT MUST ACTUALLY WRITE. The first cut of this law stopped at the line above, and
        # its own red-proof came back BLIND: replacing the write with `pass` left the FILENAME
        # constant sitting there and the law still passed. Naming a file is not writing one — the
        # same shape as the census law that checked an AST walk existed while the decision ignored
        # it. A law has to reach the ACT. [[the-unjoined-end]] [[sabotage-is-usually-the-wrong-one]]
        writes = []
        for n in ast.walk(tree):
            if isinstance(n, ast.With):
                seg = ast.unparse(n)
                if ".render_verdict.json" in seg:
                    for inner in ast.walk(n):
                        if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
                                and inner.func.attr == "write"):
                            writes.append(ast.unparse(inner)[:60])
        self.assertTrue(
            writes,
            "render_check opens the verdict file and never writes to it. The record would be "
            "created empty on every run and the heart would read UNMEASURED for ever, while the "
            "harness looked like it was reporting.")

    def test_the_census_carries_the_surfaces(self):
        """★★ Computing it and not writing it is the defect this repo calls plumbing with no tap."""
        keys = set()
        for n in ast.walk(H_write_state_node()):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                keys.add(n.value)
        self.assertIn("surfaces", keys,
                      "the census no longer writes `surfaces`, so the render verdict is measured "
                      "and then dropped on the floor")

    def test_a_full_clean_run_reads_OK_and_carries_its_AGE(self):
        """★ A verdict is a fact about a MOMENT — an OK with no age cannot be told from a stale one.

        ⚠⚠ v2871 — THIS FAILED ON CI FOR FOUR SHIPS, AND THE LAW WAS THE WRONG ONE. It read the
        MACHINE'S OWN `.render_verdict.json` and skipped only when that file was ABSENT. On the
        runner the file is present — the CI render step writes one — and its `reported` list is
        EMPTY, because Chrome never came up. `surface_verdict()` graded that UNMEASURED, exactly
        right, and this law failed with "a verdict exists but reads 'UNMEASURED'".

        A file existing is not a full clean run. The precondition and the assertion were about
        different things, so the law could only pass on a machine that had just rendered.
        `surface_verdict(path=...)` exists for precisely this — its own comment says so — and a
        law that grades a fixture it built is deterministic everywhere, which is what a law is for.
        The live file gets its own, separate law below.
        [[feedback-fixtures-never-touch-live-data]] [[feedback-blind-fixture-green-gate]]"""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"ranAt": time.time() * 1000 - 8000, "full": True, "totalTargets": 3,
                       "reported": ["console", "inbox", "locks"],
                       "coverageMissing": 0, "renderFailures": 0}, f)
            _p = f.name
        try:
            got = H.surface_verdict(_p)
        finally:
            os.unlink(_p)
        self.assertEqual("OK", got.get("state"),
                         "a full run reporting every one of its targets did not read OK: %r" % got)
        self.assertIsNotNone(got.get("ageS"), "the verdict carries no age, so a reading from last "
                                              "week is indistinguishable from one from this minute")
        self.assertGreaterEqual(got.get("ageS") or 0, 7,
                                "the age is not derived from ranAt: 8s in, %r out" % got.get("ageS"))

    def test_a_run_that_REPORTED_NOTHING_is_UNMEASURED_not_OK(self):
        """★★ The state CI was actually in, made into a law instead of a mystery. A verdict file
        written by a render that measured nothing must never grade as a clean run."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"ranAt": time.time() * 1000, "full": True, "totalTargets": 3,
                       "reported": [], "coverageMissing": 0, "renderFailures": 0}, f)
            _p = f.name
        try:
            got = H.surface_verdict(_p)
        finally:
            os.unlink(_p)
        self.assertEqual("UNMEASURED", got.get("state"),
                         "a run that reported ZERO targets graded %r — an empty container "
                         "returning a clean-looking verdict [[zero-needs-a-denominator]]" % got)

    def test_a_PARTIAL_run_cannot_speak_for_the_rest(self):
        """★ A subset run is not a clean bill of health for the targets it skipped."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"ranAt": time.time() * 1000, "full": False, "totalTargets": 6,
                       "reported": ["console", "inbox"],
                       "coverageMissing": 0, "renderFailures": 0}, f)
            _p = f.name
        try:
            got = H.surface_verdict(_p)
        finally:
            os.unlink(_p)
        self.assertEqual("PARTIAL", got.get("state"),
                         "a 2-of-6 subset run graded %r" % got)

    def test_THIS_machines_verdict_if_it_has_one(self):
        """★ The live reading, kept separate. It skips when there is genuinely nothing to say —
        and, unlike the law this replaced, a PRESENT-but-empty verdict counts as nothing to say
        rather than as a failure of the grader."""
        got = H.surface_verdict()
        if got.get("state") == "UNMEASURED":
            self.skipTest("no usable render verdict here (%s) — UNMEASURED, not a failure"
                          % str(got.get("why") or "reported nothing")[:60])
        self.assertIn(got.get("state"), ("OK", "PARTIAL"))
        self.assertIsNotNone(got.get("ageS"))


def H_write_state_node():
    src = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == "_write_state":
            return n
    raise AssertionError("heart2.py has no _write_state()")


if __name__ == "__main__":
    unittest.main(verbosity=2)
