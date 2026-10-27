# -*- coding: utf-8 -*-
"""#177 - A PRIVATE CONSOLE NEVER READS HIS PID FILES (his ruling 2026-10-22: "fix the demo").

A push's console demo (demo_console.mjs) and test_button_matrix start tv/control_app.py from HIS tv/ folder with TV_HIST
set. That moved the log and the state into the fixture's world, but control_agent.pid, control_capture.pid,
board_window.pid and .tvd_window.pid stayed in HERE. A private console's stop path reads PID_PATH, SIGTERMs then
SIGKILLs that pid and deletes the file - so a push could stop HIS ON AIR agent. REG-2123 closed the copy route
(safe_copy never carries a .pid); this closes the in-tree route.

Driven in a subprocess, the way a private console starts: TV_HIST set -> every pid path lives under the fixture's
world and none under tv/; TV_HIST unset (his console) -> every pid path is tv/<name>, exactly as before.
RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

NAMES = {"PID_PATH": "control_agent.pid", "CAP_PID_PATH": "control_capture.pid",
         "BOARD_PID_PATH": "board_window.pid", "WINDOW_PID_PATH": ".tvd_window.pid"}
PROBE = ("import json, sys; sys.path.insert(0, %r); import control_app as ca; "
         "print(json.dumps({k: getattr(ca, k) for k in %r}))")


def _paths(env_extra, drop=()):
    env = dict(os.environ)
    for k in drop:
        env.pop(k, None)
    for k in [k for k in env if k.startswith("GIT_")]:
        env.pop(k, None)          # a git hook's GIT_DIR must not reach the child
    env.update(env_extra)
    env.setdefault("TV_CONTROL_PORT", "17994")
    env.setdefault("TV_PORT", "17995")
    r = subprocess.run([sys.executable, "-c", PROBE % (HERE, sorted(NAMES))], env=env, capture_output=True,
                       text=True, timeout=240, cwd=HERE)
    if r.returncode != 0:
        raise AssertionError("control_app would not import: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class APrivateConsoleNeverReadsHisPidFiles(unittest.TestCase):

    def test_a_private_console_keeps_its_pid_files_in_its_own_world(self):
        world = tempfile.mkdtemp(prefix="tvd_pid_world_")
        hist = os.path.join(world, "frames", "hist")
        os.makedirs(hist)
        got = _paths({"TV_HIST": hist, "TVD_NO_BEACON": "1", "D2R_NO_CLAUDE": "1", "TV_SELF_PROVE": "0"})
        tv = os.path.realpath(HERE)
        for k, name in NAMES.items():
            p = os.path.realpath(got[k])
            self.assertEqual(os.path.basename(p), name, got)
            self.assertNotEqual(os.path.dirname(p), tv, "%s of a private console is HIS tv/%s (#177)" % (k, name))
            self.assertTrue(p.startswith(os.path.realpath(world) + os.sep),
                            "%s left the fixture's world: %s" % (k, p))

    def test_his_console_keeps_them_where_they_always_were(self):
        got = _paths({}, drop=("TV_HIST",))
        for k, name in NAMES.items():
            self.assertEqual(os.path.realpath(got[k]), os.path.realpath(os.path.join(HERE, name)), got)


RED_PROOF = [
    {"why": "#177 - a private console reads HIS control_agent.pid again, and its stop path kills his ON AIR agent",
     "file": "tv/control_app.py",
     "find": "PID_PATH = os.path.join(_fixture_root_for_state(), \"control_agent.pid\")\n",
     "replace": "PID_PATH = os.path.join(HERE, \"control_agent.pid\")\n",
     "matches": 1},
    {"why": "#177 - a private console reads HIS capture lease again",
     "file": "tv/control_app.py",
     "find": "CAP_PID_PATH = os.path.join(_fixture_root_for_state(), \"control_capture.pid\")\n",
     "replace": "CAP_PID_PATH = os.path.join(HERE, \"control_capture.pid\")\n",
     "matches": 1},
    {"why": "#177 - a private console reads HIS board window pid again",
     "file": "tv/control_app.py",
     "find": "BOARD_PID_PATH = os.path.join(_fixture_root_for_state(), \"board_window.pid\")",
     "replace": "BOARD_PID_PATH = os.path.join(HERE, \"board_window.pid\")",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
