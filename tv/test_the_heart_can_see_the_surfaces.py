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
        "why": 'un-writing the verdict returns the render result to the push log and the terminal, which is exactly the state that made the visual share unmeasurable',
        "file": 'render_check.py',
        "find": '            _fh.write(json.dumps(_v, indent=2, sort_keys=True, ensure_ascii=False) + "\\n")',
        "replace": '            pass',
        "matches": 1,
    },
    {
        "why": 'letting an ABSENT verdict read as OK is the whole defect in miniature: a surface nobody photographed reporting as one that passed',
        "file": 'heart2.py',
        "find": '        return {"state": "UNMEASURED", "why": "render_check has never written a verdict here — "',
        "replace": '        return {"state": "OK", "why": "render_check has never written a verdict here — "',
        "matches": 1,
    },
    {
        "why": "v2871's CI condition made permanent: a render that reported ZERO targets grades PARTIAL instead of UNMEASURED. An empty container returning a clean-looking verdict is the exact shape CI was in for four ships while nobody could say why",
        "file": 'heart2.py',
        "find": '                      "PARTIAL" if rep else "UNMEASURED"),',
        "replace": '                      "PARTIAL"),',
        "matches": 1,
    },
    {
        "why": 'dropping the count comparison lets a 2-of-6 SUBSET run grade OK — a partial render speaking for the four surfaces it never looked at',
        "file": 'heart2.py',
        "find": '    return {"state": ("OK" if (v.get("full") and tot and len(rep) >= tot) else',
        "replace": '    return {"state": ("OK" if (v.get("full") and tot) else',
        "matches": 1,
    },
    {
        "why": 'drops the width names, so a revert at 375x800 (where REG-928 says the collisions are worst) reaches the heart as an empty list. #53 is a per-width question.',
        "file": 'heart2.py',
        "find": '    return [w for w in reading if fan[w].get("reverted") is True]\n',
        "replace": '    return []\n',
        "matches": 1,
    },
    {
        "why": 'counts {error}/{unread}/{unparsed} shapes as readings, so five failed reads grade as five clean widths. A failure to read is not a reading.',
        "file": 'heart2.py',
        "find": '    if any(k in rec for k in ("error", "unread", "unparsed")):\n        return "unread"\n',
        "replace": '    if any(k in rec for k in ("error", "unread", "unparsed")):\n        return "reading"\n',
        "matches": 1,
    },
    {
        "why": 'drops the caveat, so a reading filed under a width ASSERTS the fan solved at that width. MEASURED: _hrtFanFit has one call site and the only resize listener calls _shellSizePane().',
        "file": 'heart2.py',
        "find": '    stale = (" (each reading names the width it was READ at; the fan solves once at open, so the "\n             "width it was SOLVED at is UNKNOWN)")\n',
        "replace": '    stale = ""\n',
        "matches": 1,
    },
    {
        "why": 'v2928/F3 — publishes the TOTAL count under the readable name, so a consumer dividing by it disagrees with the sentence printed beside it.',
        "file": 'heart2.py',
        "find": '            "fanWidthsReadable": _fan_counts(v)[1],\n',
        "replace": '            "fanWidthsReadable": _fan_counts(v)[0],\n',
        "matches": 1,
    },
    {
        "why": "v2931/A — collapses a RAISE and a REFUSAL back into one state, so the heart tells the operator 'the solver FAILED' when the overlay merely opened before the SVG had layout. The page's own comment says the two need different fixes.",
        "file": 'heart2.py',
        "find": '    if "threw" in rec:\n        return "threw"\n',
        "replace": '    if False:\n        return "threw"\n',
        "matches": 1,
    },
    {
        "why": "v2931/B — drops the refusal sentence, so a solver that ran and declined is described only as 'no reading' and the timing/layout cause disappears from the one line a reader acts on.",
        "file": 'heart2.py',
        "find": '    if refused:\n        tail += (" · the solver RAN AND DECLINED at %d width(s) (%s) — ok:false with a reason, "\n                 "which is a timing or layout miss and not a crash"\n                 % (len(refused), ", ".join(refused)))\n',
        "replace": '    if False:\n        tail += ""\n',
        "matches": 1,
    },
    {
        "why": 'hands back [] when nothing was READABLE, so a run where every width failed reads as a fan that kept its placement. None and [] are different answers. ⚠ re-anchored at v2931 when _fan_buckets gained a fifth bucket.',
        "file": 'heart2.py',
        "find": '    rep, reading, _threw, _unread, _refused = _fan_buckets(v)\n    if rep is None or not reading:\n        return None\n',
        "replace": '    rep, reading, _threw, _unread, _refused = _fan_buckets(v)\n    if rep is None:\n        return None\n',
        "matches": 1,
    },
    {
        "why": "v2928/F1 — RESTORES THE SHIPPED DEFECT: control_ui.html writes {ok:false, threw:...} when _hrtFanFit raises, and treating that as a reading makes a CRASH print 'the lock fan kept its placement'. ⚠ re-anchored at v2931.",
        "file": 'heart2.py',
        "find": '    if rec.get("ok") is True:\n        return "reading"\n',
        "replace": '    if rec.get("ok") is not None:\n        return "reading"\n',
        "matches": 1,
    },
    {
        "why": "v2928/F2 — lets a PRESENT BUT EMPTY heart-fan publish a measured 0 beside fanRevertedAt None: two different answers to 'did anybody measure'. ⚠ re-anchored at v2931.",
        "file": 'heart2.py',
        "find": '    if not isinstance(fan, dict) or not fan:\n        # ⚠ v2928 — NOT `.get("heart-fan", {})`. The eye flagged a fabricated 0 here; measured, the\n        # isinstance guard already caught two of its three cases, but the third — `heart-fan`\n        # PRESENT AND EMPTY — really did publish `fanWidths: 0` beside `fanRevertedAt: None`, two\n        # different answers to "did anybody measure". `not fan` closes it for good.\n        return (None, [], [], [], [])\n',
        "replace": '    if not isinstance(fan, dict):\n        # ⚠ v2928 — NOT `.get("heart-fan", {})`. The eye flagged a fabricated 0 here; measured, the\n        # isinstance guard already caught two of its three cases, but the third — `heart-fan`\n        # PRESENT AND EMPTY — really did publish `fanWidths: 0` beside `fanRevertedAt: None`, two\n        # different answers to "did anybody measure". `not fan` closes it for good.\n        return (None, [], [], [], [])\n',
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

    # ── v2926 (#53) — THE FAN JOIN, from the cross-family eye on v2924 ──────────────────────────
    def _verdict(self, extra):
        """A fixture verdict with `extra` merged in, graded by the real surface_verdict(). -> dict"""
        base = {"ranAt": time.time() * 1000 - 1000, "full": True, "totalTargets": 1,
                "reported": ["heart-fan"], "coverageMissing": 0, "renderFailures": 0}
        base.update(extra)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(base, f)
            _p = f.name
        try:
            return H.surface_verdict(_p)
        finally:
            os.unlink(_p)

    def test_a_verdict_with_NO_reports_says_UNKNOWN_and_not_clean(self):
        """⚠⚠ THE MEASURED GAP. v2924 wrote `reports` into .render_verdict.json and MEASURED
        2026-09-11 heart2.py contained "fanfit" 0 times and "report" 0 times — the fan could revert
        at every photographed width and every automated supervisor still read OK. A verdict written
        before the tap existed must say so, not report a clean fan. [[the-unjoined-end]]"""
        got = self._verdict({})
        self.assertIsNone(got.get("fanRevertedAt"),
                          "an unmeasured fan came back as a list, which reads as 'nothing "
                          "reverted': %r" % (got.get("fanRevertedAt"),))
        self.assertIn("UNKNOWN", got.get("fanSay") or "",
                      "a verdict that never measured the fan does not say so: %r" % got.get("fanSay"))

    def test_a_fan_that_REVERTED_is_NAMED_by_width(self):
        """★★ #53 IS A PER-WIDTH QUESTION. A revert at 375x800 — where REG-928 says the collisions
        are worst — must reach the heart by name, not be averaged into a count."""
        # ⚠ v2928 — `ok: True` IS PART OF THE SHAPE. control_ui.html always stamps it, and the
        # v2926 fixtures omitted it — so they were asserting against a payload the page never
        # writes, and the reader could not tell a solve from a crash while they stayed green.
        got = self._verdict({"reports": {"heart-fan": {
            "375x800":  {"ok": True, "reverted": True,  "readAt": "375x800"},
            "1440x900": {"ok": True, "reverted": False, "readAt": "1440x900"}}}})
        self.assertEqual(["375x800"], got.get("fanRevertedAt"),
                         "the reverting width is not named: %r" % (got.get("fanRevertedAt"),))
        self.assertEqual(2, got.get("fanWidthsReadable"),
                         "the readable denominator is wrong: %r" % got)
        self.assertIn("375x800", got.get("fanSay") or "",
                      "the sentence does not name the width that reverted: %r" % got.get("fanSay"))

    def test_readings_that_FAILED_are_UNMEASURED_and_never_a_clean_fan(self):
        """★ An error is a failure to read, not a reading. Counting `{"error": …}` as 'did not
        revert' is [[zero-needs-a-denominator]] — the empty container returning a clean 0."""
        got = self._verdict({"reports": {"heart-fan": {
            "375x800":  {"error": "WebSocketTimeout"},
            "1440x900": {"unread": "the report expression returned null"}}}})
        self.assertIsNone(got.get("fanRevertedAt"),
                          "two failed reads graded as a fan that kept its placement: %r"
                          % (got.get("fanRevertedAt"),))
        self.assertIn("UNMEASURED", got.get("fanSay") or "",
                      "failed reads do not say UNMEASURED: %r" % got.get("fanSay"))

    def test_the_SOLVE_width_caveat_travels_with_the_number(self):
        """⚠⚠ THE OVER-CLAIM THE TAP WAS REWRITTEN TO REMOVE, arriving one layer up. MEASURED:
        `_hrtFanFit` has ONE call site and the page's only resize listener calls `_shellSizePane()`
        and nothing else — so the fan solves once at open. A per-width reading names where it was
        READ, never where it was SOLVED, and a heart that drops that caveat re-states v2923's
        defect with a better label. [[stale-reading]] [[inherited-claim-is-not-evidence]]"""
        got = self._verdict({"reports": {"heart-fan": {
            "375x800": {"ok": True, "reverted": False, "readAt": "375x800"}}}})
        say = got.get("fanSay") or ""
        self.assertIn("READ", say, "the sentence does not distinguish read-at from solved-at: %r" % say)
        self.assertIn("UNKNOWN", say,
                      "the solve width is asserted rather than left unknown: %r" % say)

    def test_a_solver_that_THREW_is_never_reported_as_a_KEEP(self):
        """⚠⚠ THE WORST OF THE THREE, and it shipped in v2926. MEASURED: control_ui.html writes
        `{ok:false, threw:"..."}` when `_hrtFanFit` raises, and `{ok:false, reverted:false, ...}`
        for its own `no fan` / `no layout yet` refusals. Neither carries error/unread/unparsed, so
        the v2926 reader counted both as readings, found `reverted` not True, and printed
        **"the lock fan kept its placement at all 1 readable width(s)"**.

        The page's own `catch` was written to stop a crash and a keep looking alike; the reader
        built to answer #53 reintroduced the collapse one layer up. [[unknown-stays-unknown]]"""
        for shape in ({"ok": False, "threw": "TypeError: x is null"},
                      {"ok": False, "reverted": False, "why": "no fan"}):
            got = self._verdict({"reports": {"heart-fan": {"375x800": shape}}})
            self.assertIsNone(got.get("fanRevertedAt"),
                              "a failed solve graded as a fan that kept its placement (%r): %r"
                              % (shape, got.get("fanRevertedAt")))
            self.assertNotIn("kept its placement", got.get("fanSay") or "",
                             "a crash is reported as a keep (%r): %r" % (shape, got.get("fanSay")))
            self.assertIn("UNMEASURED", got.get("fanSay") or "",
                          "a failed solve does not say UNMEASURED (%r): %r" % (shape, got.get("fanSay")))

    def test_a_solver_that_DECLINED_is_not_reported_as_one_that_CRASHED(self):
        """⚠ v2928 fixed the keep-lie and introduced a diagnosis-lie in the same breath, caught by
        the cross-family eye one ship later. control_ui.html writes `{ok:false, threw:"..."}` when
        `_hrtFanFit` RAISES, and `{ok:false, why:"the fan has no layout yet"}` when the solver RAN
        and declined — a timing or layout miss. v2928's rule was "ok present and not True ->
        threw", so the heart told the operator THE SOLVER FAILED for a layout miss. The page's own
        comment says the two need different fixes. [[label-outlived-referent]]"""
        crash = self._verdict({"reports": {"heart-fan": {
            "375x800": {"ok": False, "threw": "TypeError: x is null"}}}})
        decline = self._verdict({"reports": {"heart-fan": {
            "375x800": {"ok": False, "reverted": False, "why": "the fan has no layout yet"}}}})
        for g in (crash, decline):
            self.assertIsNone(g.get("fanRevertedAt"),
                              "neither shape produced a placement, so neither may report one")
        self.assertNotEqual(crash.get("fanSay"), decline.get("fanSay"),
                            "a crash and a refusal print the SAME sentence, so the operator gets "
                            "the wrong diagnosis for a layout miss: %r" % crash.get("fanSay"))
        self.assertIn("FAILED", crash.get("fanSay") or "",
                      "a raise is not named as a failure: %r" % crash.get("fanSay"))
        self.assertIn("DECLINED", decline.get("fanSay") or "",
                      "a refusal is not named as one: %r" % decline.get("fanSay"))

    def test_an_EMPTY_fan_report_publishes_no_fabricated_zero(self):
        """⚠ `heart-fan` PRESENT AND EMPTY published `fanWidths: 0` beside `fanRevertedAt: None` —
        two different answers to 'did anybody measure'. The eye named three cases here; measured,
        the isinstance guard already caught two and only this one was real. A finding is a
        measurement to earn, not an instruction to obey. [[zero-needs-a-denominator]]"""
        for extra in ({}, {"reports": {"console": {}}}, {"reports": {"heart-fan": {}}}):
            got = self._verdict(extra)
            self.assertIsNone(got.get("fanWidthsReported"),
                              "%r published a measured count where nothing was measured: %r"
                              % (extra, got.get("fanWidthsReported")))
            self.assertIsNone(got.get("fanWidthsReadable"),
                              "%r published a readable count out of nothing" % (extra,))

    def test_the_published_denominator_IS_the_one_the_sentence_uses(self):
        """⚠ v2926 published one `fanWidths` = len(all keys) while `_fan_say` divided by
        len(readable). MEASURED: five widths all returning {"error": …} gave `fanWidths: 5` beside
        a sentence saying NONE could be read. A consumer dividing by the published number gets a
        different answer from the published words. [[label-outlived-referent]]"""
        got = self._verdict({"reports": {"heart-fan": {
            w: {"error": "WebSocketTimeout"} for w in
            ("375x800", "901x900", "1120x628", "1120x900", "1440x900")}}})
        self.assertEqual(5, got.get("fanWidthsReported"), "the reported count is wrong: %r" % got)
        self.assertEqual(0, got.get("fanWidthsReadable"),
                         "five failed reads counted as readable: %r" % got.get("fanWidthsReadable"))
        self.assertIn("NONE produced a reading", got.get("fanSay") or "",
                      "the sentence disagrees with the numbers beside it: %r" % got.get("fanSay"))

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
