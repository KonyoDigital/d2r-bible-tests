# -*- coding: utf-8 -*-
"""REG-2563 - A GATE NEVER CALLS THE CLAUDE CLI.

Elad 2026-10-22: his Claude plan sits at ~98%, and no gate may spend it. A run_gates --changed on the V1 worktree logged
"test_screen_parity not stored - the gate started claude": traced with a logging fake `claude` first on PATH, the gate's
console import (control_app._claude_auth_state -> claude_signin.status) ran `claude auth status --json`.
THE RULE: every gate runs in law_env, which sets D2R_NO_CLAUDE=1 (claude_signin answers UNKNOWN without spawning) and puts
tv/no_claude_bin first on PATH - a `claude` that logs, says so and exits 1.
Cases: law_env's PATH and flag; the screen-parity gate run in law_env calls no claude (the fake's log stays empty);
claude_signin.status refuses to spawn under the flag.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import run_gates as RG  # noqa: E402
import claude_signin as CS  # noqa: E402


class NoGateCallsTheClaudeCli(unittest.TestCase):

    def test_1_law_env_puts_the_refusing_claude_first_and_sets_the_flag(self):
        env = RG.law_env(False, base={"PATH": "/usr/bin:/bin"})
        self.assertEqual(env.get("D2R_NO_CLAUDE"), "1", env)
        first = env["PATH"].split(os.pathsep)[0]
        self.assertEqual(first, os.path.join(HERE, "no_claude_bin"), env["PATH"])
        self.assertTrue(os.access(os.path.join(first, "claude"), os.X_OK))

    def test_2_the_screen_parity_gate_calls_no_claude(self):
        fd, log = tempfile.mkstemp(prefix="no_claude_")
        os.close(fd)
        try:
            env = RG.law_env(False)
            env["D2R_NO_CLAUDE_LOG"] = log
            subprocess.run([sys.executable, "-B", os.path.join(HERE, "test_the_screen_bills_the_same_rows_the_engine_does.py")],
                           env=env, cwd=os.path.dirname(HERE), capture_output=True, timeout=240)
            with open(log) as fh:
                calls = fh.read().strip()
            self.assertEqual(calls, "", "a gate called the Claude CLI: %r" % calls)
        finally:
            os.unlink(log)

    def test_3_status_never_spawns_under_the_flag(self):
        old = os.environ.get("D2R_NO_CLAUDE")
        os.environ["D2R_NO_CLAUDE"] = "1"
        try:
            r = CS.status(os.path.join(HERE, "no_claude_bin", "claude"))
        finally:
            if old is None:
                os.environ.pop("D2R_NO_CLAUDE", None)
            else:
                os.environ["D2R_NO_CLAUDE"] = old
        self.assertIsNone(r["loggedIn"], r)
        self.assertIn("D2R_NO_CLAUDE", r["why"], r)


RED_PROOF = [
    {"why": "REG-2563 - claude_signin spawns `claude auth status` again under a gate",
     "file": "tv/claude_signin.py",
     "find": "    if _run is None and os.environ.get(\"D2R_NO_CLAUDE\") == \"1\":",
     "replace": "    if False and _run is None and os.environ.get(\"D2R_NO_CLAUDE\") == \"1\":",
     "matches": 1},
    {"why": "REG-2563 - law_env no longer puts the refusing claude first on a gate's PATH",
     "file": "tv/run_gates.py",
     "find": "        env[\"PATH\"] = _ncb + os.pathsep + env.get(\"PATH\", \"\")\n",
     "replace": "        pass\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
