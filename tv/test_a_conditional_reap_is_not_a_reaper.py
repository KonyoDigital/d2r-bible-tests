# -*- coding: utf-8 -*-
"""#177 — A HELPER IS A REAPER ONLY IF IT REAPS ON EVERY PATH IT CAN TAKE.

⚠ WHY: v3427 taught test_no_ASSIGNED_popen_goes_unreaped to follow a Popen into a helper
(close_ocr_worker) — and trusted any function whose FIRST PARAMETER was textually followed by
`.wait(` / `.poll(` / `target=<p>.wait`. The second eye on v3427 named the hole, and it is real:
`if x: wp.wait()` counts, `if x: return` before the reap counts, and a reap AFTER a statement in the
same `try` that can raise past it counts — which is the exact v3421 defect (a BrokenPipeError on
`stdin.close()` skipped the terminate and the reap, for three weeks). The call-site match was the
literal text `helper(name)`, so `helper(wp=name)` was not seen at all.

reap_shape.reaps_first_param reads the body as PATHS: a reap counts at the function's own level, as
the FIRST statement of a try body, in a finally, or in a with body — and never behind an exit.
Nested defs are not the function's own path. DRIVEN on source fixtures, then on control_app itself.
RED_PROOF below. [[source-reading-guard]] [[regression-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import reap_shape as R  # noqa: E402


def _fn(src):
    return ast.parse(src).body[0]


REAPERS = {
    "at its own level": "def h(wp):\n    wp.terminate()\n    wp.wait()\n",
    "first in its try": ("def h(wp):\n    try:\n        wp.stdin.close()\n    except Exception:\n"
                         "        pass\n    try:\n        threading.Thread(target=wp.wait, daemon=True)"
                         ".start()\n        return True\n    except Exception:\n        return False\n"),
    "in a finally": "def h(wp):\n    try:\n        wp.stdin.close()\n    finally:\n        wp.wait()\n",
    "in a with": "def h(wp):\n    with lock:\n        wp.poll()\n",
}

NOT_REAPERS = {
    "only on one branch": "def h(wp):\n    if x:\n        wp.wait()\n",
    "behind an early return": "def h(wp):\n    if x:\n        return\n    wp.wait()\n",
    "alive -> return": "def h(wp):\n    if wp.poll() is None:\n        return\n    wp.wait()\n",
    "after a raise in its try (v3421)": ("def h(wp):\n    try:\n        wp.stdin.close()\n"
                                         "        wp.wait()\n    except Exception:\n        pass\n"),
    "only in a nested def": "def h(wp):\n    def g():\n        wp.wait()\n    return g\n",
    "only in a loop": "def h(wp):\n    for _ in range(3):\n        wp.poll()\n",
    "only in an except": ("def h(wp):\n    try:\n        wp.terminate()\n    except Exception:\n"
                          "        wp.wait()\n"),
    "a different object": "def h(wp):\n    other.wait()\n",
    "no parameter": "def h():\n    wp.wait()\n",
}


class AConditionalReapIsNotAReaper(unittest.TestCase):

    def test_every_path_reap_is_a_reaper(self):
        for why, src in REAPERS.items():
            self.assertTrue(R.reaps_first_param(_fn(src)), "not credited: a reap %s" % why)

    def test_a_reap_some_path_skips_is_not(self):
        for why, src in NOT_REAPERS.items():
            self.assertFalse(R.reaps_first_param(_fn(src)), "credited as a reaper: %s" % why)

    def test_the_call_site_is_read_by_the_parser_not_by_the_text(self):
        helpers = {"close_it": "wp"}
        for src, want in (("close_it(p)", True), ("close_it(wp=p)", True), ("mod.close_it(p)", True),
                          ("close_it(other)", False), ("close_it(wp=other)", False),
                          ("close_it()", False), ("not_a_reaper(p)", False)):
            call = ast.parse(src).body[0].value
            self.assertEqual(R.passes_to(call, helpers, "p"), want, src)

    def test_the_real_helper_still_qualifies_and_the_real_worker_is_handed_to_it(self):
        """The subject is present: control_app's close_ocr_worker is a reaper on every path, and
        _kai_closer_loop hands it the Popen it assigns — so the sweep is judging real code."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        funcs = {f.name: f for f in ast.walk(tree)
                 if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertIn("close_ocr_worker", funcs, "premise: close_ocr_worker is gone")
        self.assertTrue(R.reaps_first_param(funcs["close_ocr_worker"]),
                        "close_ocr_worker no longer reaps its worker on every path")
        loop = funcs.get("_kai_closer_loop")
        self.assertIsNotNone(loop, "premise: _kai_closer_loop is gone")
        helpers = {n: f.args.args[0].arg for n, f in funcs.items()
                   if f.args.args and R.reaps_first_param(f)}
        self.assertTrue(any(R.passes_to(c, helpers, "wp") for c in ast.walk(loop)),
                        "_kai_closer_loop no longer hands its ocr worker to a reaper")

    def test_the_sweep_asks_this_module(self):
        """test_no_ASSIGNED_popen_goes_unreaped must use reap_shape, not its old text match."""
        import inspect
        import test_control as TC
        src = inspect.getsource(TC.TestV2352NothingIsSpawnedWithoutBeingReaped
                                .test_no_ASSIGNED_popen_goes_unreaped)
        self.assertIn("reaps_first_param", src)
        self.assertIn("passes_to", src)
        self.assertNotIn('"%s(%s)" % (h, name)', src, "the literal call-site text match is back")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#177 - any statement of a try body counts again: a reap after stdin.close() in one try (the v3421 BrokenPipe shape) is credited",
        "file": "reap_shape.py",
        "find": "            if st.body and _reaps(st.body[0], name) and not _branches(st.body[0]):\n",
        "replace": "            if any(_reaps(s, name) for s in st.body):\n",
        "matches": 1,
    },
    {
        "why": "#177 - an exit inside a branch no longer stops the path: a reap behind an early return is credited",
        "file": "reap_shape.py",
        "find": "        # an if / loop / match: a reap inside is conditional; an exit inside skips what follows\n        if _exits(st):\n            return \"exits\"\n",
        "replace": "        # an if / loop / match: a reap inside is conditional; an exit inside skips what follows\n        if _reaps(st, name):\n            return \"reaped\"\n",
        "matches": 1,
    },
    {
        "why": "#177 - the call site matched by position only: helper(wp=p) is not seen, so a keyword hand-off reads as unreaped",
        "file": "reap_shape.py",
        "find": "    return any(kw.arg == p0 and isinstance(kw.value, ast.Name) and kw.value.id == name\n",
        "replace": "    return False and any(kw.arg == p0 and isinstance(kw.value, ast.Name) and kw.value.id == name\n",
        "matches": 1,
    },
    {
        "why": "#177 - the real helper reaps only on one branch: close_ocr_worker's reap made conditional must lose its reaper status",
        "file": "control_app.py",
        "find": "        threading.Thread(target=wp.wait, daemon=True, name=\"tvd-ocr-reap\").start()\n",
        "replace": "        if say is not None:\n            threading.Thread(target=wp.wait, daemon=True, name=\"tvd-ocr-reap\").start()\n",
        "matches": 1,
    },
]
