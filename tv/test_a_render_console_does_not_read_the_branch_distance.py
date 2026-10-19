# -*- coding: utf-8 -*-
"""Vault L1 (render gate root cause) - the render harness console does not photograph how far the pushing branch is
behind origin/main.

MEASURED 2026-10-19: `shelf-cards` was red on every checkout behind origin/main (the #246 branch, the L1 branch, and the
old main 69817adf) and green on main 74ddf4bc. The covering element was #fault-banner, "BEHIND FLEET - 32 commits on
GitHub", drawn over .shc-hero and .shc-sess. fleet_origin_status counts HEAD..origin/main in the checkout the harness
serves from. `advanced-fleet` was red only under `unshare -rn`, because the fleet roster needs the network.

Now render_check gives its stub console TV_FLEET_BEHIND_PIN=0, and fleet_origin_status honours the pin only when
TV_STUB=1. His real console still counts and fetches. RED_PROOF below. [[regression-guard]]
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


class ARenderConsoleDoesNotReadTheBranchDistance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def _ask(self, env):
        ca = self.ca
        calls = []
        old_env = {k: os.environ.get(k) for k in ("TV_STUB", "TV_FLEET_BEHIND_PIN")}
        old_run = ca._git_run
        old_kick = getattr(ca, "_fleet_fetch_kick", None)
        def fake_run(args, **kw):
            calls.append(list(args))
            class R(object):
                returncode = 0
                stdout = "32\n"
            return R()
        try:
            for k in old_env:
                os.environ.pop(k, None)
            os.environ.update(env)
            ca._git_run = fake_run
            if old_kick is not None:
                ca._fleet_fetch_kick = lambda *a, **k: calls.append(["kick"])
            ca._FLEET_CACHE["val"] = None
            ca._FLEET_CACHE["t"] = 0
            out = ca.fleet_origin_status(force_fetch=False)
        finally:
            ca._git_run = old_run
            if old_kick is not None:
                ca._fleet_fetch_kick = old_kick
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            ca._FLEET_CACHE["val"] = None
            ca._FLEET_CACHE["t"] = 0
        return out, calls

    def test_a_stub_console_with_the_pin_reports_zero_and_asks_no_git(self):
        out, calls = self._ask({"TV_STUB": "1", "TV_FLEET_BEHIND_PIN": "0"})
        self.assertEqual(out["behind"], 0, out)
        self.assertTrue(out["ok"], out)
        self.assertFalse([c for c in calls if "rev-list" in c], "the pinned console still counted commits: %r" % calls)

    def test_his_real_console_still_counts_even_if_the_pin_is_set(self):
        out, calls = self._ask({"TV_FLEET_BEHIND_PIN": "0"})
        self.assertEqual(out["behind"], 32, "a console that is not a stub obeyed the pin: %r" % out)
        self.assertTrue([c for c in calls if "rev-list" in c], calls)

    def test_render_check_pins_its_console(self):
        src = open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        m = re.search(r"env = dict\(os\.environ, TV_CONTROL_PORT=str\(port\).*?\)\n", src, re.S)
        self.assertTrue(m, "the harness console env was not found")
        self.assertIn('TV_FLEET_BEHIND_PIN="0"', m.group(0), "render_check does not pin its console's fleet distance")


RED_PROOF = [
    {"why": "render_check stops pinning, so a branch behind main draws BEHIND FLEET over the shelf cards.",
     "file": "tv/render_check.py",
     "find": "               TV_FLEET_BEHIND_PIN=\"0\",  # L1: the pushing branch's distance from origin/main is not a render fact",
     "replace": "               # L1: the pushing branch's distance from origin/main is not a render fact",
     "matches": 1},
    {"why": "The console ignores the pin.",
     "file": "tv/control_app.py",
     "find": "    if _pin is not None and os.environ.get(\"TV_STUB\") == \"1\":",
     "replace": "    if False and _pin is not None and os.environ.get(\"TV_STUB\") == \"1\":",
     "matches": 1},
    {"why": "His real console obeys the pin too, so a real lag is hidden.",
     "file": "tv/control_app.py",
     "find": "    if _pin is not None and os.environ.get(\"TV_STUB\") == \"1\":",
     "replace": "    if _pin is not None:",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
