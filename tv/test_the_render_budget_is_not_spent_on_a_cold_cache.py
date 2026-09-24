# -*- coding: utf-8 -*-
"""#236 — THE RENDER STEP DOES NOT SPEND ITS 300s CEILING WAITING ON A COLD CACHE.

MEASURED 2026-09-24 inside a push: /api/heart cost 30.4s on its first call to the render gate's fresh
private console — a tenth of the step's ceiling, paid serially at load 6 — and the render was killed
four targets short. `_prewarm` starts every declared warm endpoint ONCE, in the background, the moment
the console answers, so the heart targets (rendered later) find it warm. The per-target warm still
runs before each is judged, so nothing is ever measured cold. DRIVEN with a stubbed network.
RED_PROOF below.
"""
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import render_check as rc  # noqa: E402


class TheColdCostIsPaidEarlyAndOnce(unittest.TestCase):

    def test_every_declared_endpoint_is_warmed_once_in_the_background(self):
        import urllib.request
        hit, real = [], urllib.request.urlopen
        gate = threading.Event()

        class _R(object):
            def read(self, *a):
                return b""

        def _fake(url, timeout=None):
            hit.append(url)
            gate.wait(2)              # a slow endpoint must not block the caller
            return _R()
        try:
            urllib.request.urlopen = _fake
            t0 = time.time()
            eps = rc._prewarm("http://127.0.0.1:1/")
            returned_in = time.time() - t0
            gate.set()
            for _ in range(50):
                if len(hit) >= len(eps):
                    break
                time.sleep(0.02)
        finally:
            urllib.request.urlopen = real
        declared = []
        for s in rc.TARGETS.values():
            for w in (s.get("warm") or ()):
                if w not in declared:
                    declared.append(w)
        self.assertTrue(declared, "premise: some target declares a warm endpoint")
        self.assertEqual(eps, declared, "the prewarm does not cover every declared endpoint, once each")
        self.assertLess(returned_in, 0.5, "the prewarm blocked the render instead of running beside it")
        self.assertEqual(sorted(hit), sorted("http://127.0.0.1:1" + w for w in declared))

    def test_the_console_boot_starts_it(self):
        import inspect
        src = inspect.getsource(rc._serve_console)
        self.assertIn("_prewarm(origin)", src, "the private console answers and nothing starts the prewarm")


class AWarmupIsAnUpperBoundNotASleep(unittest.TestCase):
    """MEASURED 2026-09-24: the served targets' fixed warmups summed to 164s of a 282-304s render and
    the step (ceiling 300s) was killed at load 6; bounded by readiness, two full runs took 200s and
    213s at load 6.6-7.8, every target green. The full sleep survives only behind `warmup_fixed`."""

    def test_the_fixed_sleep_is_only_taken_on_request(self):
        import ast
        import inspect
        src = inspect.getsource(rc.check)
        tree = ast.parse(src.replace("\n    ", "\n") if src.startswith("    ") else src)
        gated = False
        for n in ast.walk(tree):
            if isinstance(n, ast.If) and isinstance(n.test, ast.Call) \
                    and getattr(n.test.func, "attr", "") == "get" and n.test.args \
                    and isinstance(n.test.args[0], ast.Constant) and n.test.args[0].value == "warmup_fixed":
                gated = True
        self.assertTrue(gated, "the warmup is a fixed sleep for every target again (the 164s that starved the render)")
        self.assertIn("document.readyState !== 'complete'", rc._READY_DEFAULT)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#236 - every served target sleeps its full warmup again: 164s of fixed sleep in a 300s render step",
        "file": "render_check.py",
        "find": "            if spec.get(\"warmup_fixed\"):\n                time.sleep(_cap)\n",
        "replace": "            if True:\n                time.sleep(_cap)\n",
        "matches": 1,
    },
    {
        "why": "#236 - the render step pays the 30s cold /api/heart inside its 300s ceiling again (killed four targets short at load 6)",
        "file": "render_check.py",
        "find": "            _prewarm(origin)\n",
        "replace": "",
        "matches": 1,
    },
]
