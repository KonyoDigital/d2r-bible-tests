# -*- coding: utf-8 -*-
"""v3401 — A PROBE MAY ONLY LICENSE THE MECHANISM IT TESTED.

⚠⚠ THIS WEDGED THREE CONSECUTIVE PUSHES and the bound took the blame for all of them.

`browser_can_load_localhost` answers "can this machine load an http://127.0.0.1 page". When
`--dump-dom` times out it falls back to a CDP probe, and records WHICH path worked in
LOOPBACK_PATH. Nothing ever read it. `check()` asked only the boolean, so "CDP works" flattened
into "loopback works" and licensed the --dump-dom loads below - a DIFFERENT MECHANISM. The
module's own docstring says so: "Playwright drives the same binaries over the same loopback fine,
so it is THIS LAUNCH PATH on this machine, not the network and not the page." CDP working is
exactly compatible with --dump-dom hanging.

MEASURED on his Mac 2026-09-20:
    browser_can_load_localhost -> True   path='cdp'   13.9s   (12s dump-dom timeout + ~2s CDP)
    each of 2 targets then burned its full 90s and fell through to node anyway  = ~180s a run
    after the join: check() returns in 0.6s with the same verdict (0 problems, not skipped)
The pre-push ceiling is 1500s, and a heart row predicted this word for word that morning:
"it will pass every quiet run and then hang a push, and the bound will take the blame."

Three defects, one version: the probe exercised DIFFERENT FLAGS than it licensed; a cached True
was never retired by a real timeout; and the path knowledge was recorded and unread.
[[the-unjoined-end]] [[unknown-stays-unknown]] [[stale-reading]]
"""
import io
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import js_syntax_gate as g  # noqa: E402

RED_PROOF = [
    {
        "why": "without this the CDP fallback licenses --dump-dom again - a different mechanism - "
               "and every target burns its full 90s before falling through to node anyway",
        "file": "tv/js_syntax_gate.py",
        "find": '    if loopback_path() != "dump-dom":\n        return check_with_node(targets)',
        "replace": '    if False:\n        return check_with_node(targets)',
        "matches": 1,
    },
    {
        "why": "without retiring the cached verdict, a browser that already timed out on target "
               "one is still trusted for target two, which pays another full 90s",
        "file": "tv/js_syntax_gate.py",
        "find": "                    _LOOPBACK_OK[:] = [False]",
        "replace": "                    pass",
        "matches": 1,
    },
]


class TestAProbeLicensesOnlyWhatItTested(unittest.TestCase):

    def setUp(self):
        self._ok = list(g._LOOPBACK_OK)
        self._path = list(g.LOOPBACK_PATH)
        # ⚠⚠ SEED THE CACHE SO NO CASE EVER RUNS THE REAL PROBE. The first cut let one case call
        # the live check(), which pays browser_can_load_localhost in full — 12s of --dump-dom
        # timing out plus a CDP attempt, and more in a cold sandbox. heart2 bounds each proof at
        # 180s and BOTH runs came back UNPROVABLE, the CLEAN one too. That is not a weak law, it
        # is a test too expensive to prove, and an unprovable law is not a law. The JOIN is what
        # these cases are about; the probe itself is not under test here.
        g._LOOPBACK_OK[:] = [True]
        g.LOOPBACK_PATH[:] = ["cdp"]

    def tearDown(self):
        g._LOOPBACK_OK[:] = self._ok
        g.LOOPBACK_PATH[:] = self._path

    def test_BASELINE_the_path_is_one_of_three_named_answers(self):
        g._LOOPBACK_OK[:] = [True]
        g.LOOPBACK_PATH[:] = ["cdp"]
        self.assertEqual(g.loopback_path(), "cdp")
        g.LOOPBACK_PATH[:] = []
        self.assertIsNone(g.loopback_path(),
                          "an unrecorded path must be None - never a guess")

    def test_a_CDP_only_machine_does_NOT_license_dump_dom(self):
        """THE JOIN. This is the whole defect."""
        g._LOOPBACK_OK[:] = [True]
        g.LOOPBACK_PATH[:] = ["cdp"]
        launched = []
        real = g._run_browser_bounded
        try:
            g._run_browser_bounded = lambda cmd, t: launched.append(cmd)
            problems, skipped = g.check()
            self.assertEqual(
                launched, [],
                "check() launched a --dump-dom browser on a machine where only CDP works - "
                "that is %d wasted launch(es), 90s each" % len(launched))
        finally:
            g._run_browser_bounded = real

    def test_a_dump_dom_machine_IS_still_licensed(self):
        """⚠ THE MIRROR. If nothing is ever licensed the browser check is dead, not fixed."""
        code = io.open(os.path.join(HERE, "js_syntax_gate.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        self.assertIn('loopback_path() != "dump-dom"', code,
                      "the guard must compare against dump-dom specifically, so a machine where "
                      "dump-dom DOES work still gets the stronger browser check")

    def test_ONE_launch_path_serves_the_probe_and_the_real_load(self):
        """A probe that tests different flags than it licenses is measuring something else."""
        code = io.open(os.path.join(HERE, "js_syntax_gate.py"), encoding="utf-8").read()
        stripped = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        self.assertGreaterEqual(
            stripped.count("_dump_dom_cmd("), 3,
            "the probe and the real load no longer share one argv builder")
        self.assertNotIn(
            '"--headless=new", "--disable-gpu", "--no-sandbox",\n                 f"--user-data-dir',
            code, "the dump-dom probe drifted back to its own flag list")

    def test_a_real_timeout_RETIRES_the_cached_verdict(self):
        code = io.open(os.path.join(HERE, "js_syntax_gate.py"), encoding="utf-8").read()
        stripped = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        self.assertIn("_LOOPBACK_OK[:] = [False]", stripped,
                      "a real load timing out no longer invalidates the probe's cached True, so "
                      "the next target pays its own 90s for a capability already disproved")

    def test_a_CDP_only_machine_answers_FAST_because_it_never_launches(self):
        """The saving, asserted as a BOUND on time with the browser made unreachable.

        ⚠ This used to call the live check() and time it. That made the gate itself cost more
        than heart2's 180s proof bound, so the law could not be demonstrated at all. The seeded
        cache (setUp) plus a raising launcher means any attempt to start a browser is an instant,
        loud failure rather than a 90s wait - which is a STRONGER assertion than a stopwatch.
        """
        import time
        real = g._run_browser_bounded
        try:
            def explode(cmd, t):
                raise AssertionError("check() launched a browser on a CDP-only machine")
            g._run_browser_bounded = explode
            t0 = time.time()
            problems, skipped = g.check()
            took = time.time() - t0
            self.assertIsInstance(problems, list)
            self.assertLess(took, 30.0,
                            "check() took %.0fs without launching anything - something else in "
                            "the fall-through is slow" % took)
        finally:
            g._run_browser_bounded = real


if __name__ == "__main__":
    unittest.main(verbosity=2)
