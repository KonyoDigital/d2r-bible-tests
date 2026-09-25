# -*- coding: utf-8 -*-
"""#145 — A HEADLESS CONSOLE SAYS IT HAS NO WINDOW.

The supervisor revives the console with `control_app.py --no-open` (tvd_supervisor.sh), which is headless by
construction. WITNESSED 2026-09-25 on a scratch port: the revived process answered /api/status and System Events
counted 0 windows for it - yet its boot banner read "... · mac · native window · ...". "I can't see it" then reads
as lost data when the truth is simply no window ([[headless-console-looks-like-lost-data]]). The banner now says
HEADLESS for --no-open, and drops the "close the app window" line there is no window to close.

  · DRIVEN: a real `control_app.py --no-open` boot on a free port, isolated from his stores (fixture world,
    TV_STUB, TV_CAPTURE=off, TV_PARENT_PID), its banner read off stdout, then killed by the PID it was given.
RED_PROOF below.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    if p in (17772, 17781, 9222, 9223):
        raise unittest.SkipTest("the OS handed out one of his ports - UNMEASURED, not passing")
    return p


class AHeadlessConsoleSaysItHasNoWindow(unittest.TestCase):

    def test_the_no_open_banner_says_headless(self):
        port = _free_port()
        d = tempfile.mkdtemp(prefix="headless-banner-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "hist"))
        env = dict(os.environ, TV_CONTROL_PORT=str(port), TV_PORT=str(port + 1), TV_STUB="1", TV_CAPTURE="off",
                   TV_HIST=os.path.join(d, "hist"), TV_SESSIONS=os.path.join(d, "sessions.jsonl"),
                   TV_PARENT_PID=str(os.getpid()), PYTHONUNBUFFERED="1")
        out_path = os.path.join(d, "out.log")
        with open(out_path, "w") as fh:
            p = subprocess.Popen([sys.executable, os.path.join(HERE, "control_app.py"), "--no-open"],
                                 cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT)
        try:
            banner = ""
            for _ in range(120):
                time.sleep(0.25)
                txt = open(out_path, encoding="utf-8", errors="replace").read()
                lines = [ln for ln in txt.splitlines() if "TV DIABLO Control" in ln]
                if lines:
                    banner = lines[0]
                    time.sleep(0.5)
                    txt = open(out_path, encoding="utf-8", errors="replace").read()
                    break
                if p.poll() is not None:
                    break
        finally:
            p.kill()
            p.wait(timeout=10)
        self.assertTrue(banner, "premise: the console printed its banner - UNKNOWN otherwise: %r" % txt[-400:])
        self.assertIn("HEADLESS", banner, "a --no-open console still claims a window: %r" % banner)
        self.assertNotIn("native window", banner)
        self.assertNotIn("close the app window", txt, "a headless console tells him to close a window it lacks")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#145 - a --no-open console claims a native window again: 'I can't see it' reads as lost data",
        "file": "control_app.py",
        "find": "    _win_word = \"HEADLESS - no window (--no-open)\" if no_open else \"native window\"\n",
        "replace": "    _win_word = \"native window\"\n",
        "matches": 1,
    },
]
