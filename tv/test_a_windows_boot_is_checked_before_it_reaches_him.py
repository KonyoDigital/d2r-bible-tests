# -*- coding: utf-8 -*-
"""#229 — A WINDOWS BOOT IS CHECKED BEFORE IT REACHES HIM.

tv/windows_boot_check.py boots a scratch console and asks it which build it runs; CI runs it on
windows-latest (.github/workflows/tv-windows-boot.yml). Proven on the ALT over SSH before it shipped.

  · DRIVEN against fake trees (TVD_BOOT_CHECK_TREE): a console that answers with the shipped build -> 0;
    a console running a DIFFERENT build than WINDOWS_SHIP.json -> 1; a console that dies at boot -> 1
    with its last words; no shipped version -> 77 (could not run), never 0.
  · JOINED: the workflow runs the script on windows-latest and watches its own file.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

CHECK = os.path.join(HERE, "windows_boot_check.py")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "tv-windows-boot.yml")

FAKE_OK = r"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        b = json.dumps({"ver": os.environ.get("FAKE_VER"), "identity": {"platform": "windows"}}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", int(os.environ["TV_CONTROL_PORT"])), H).serve_forever()
"""
FAKE_DIES = "import sys\nprint('Traceback: a boot that dies')\nsys.exit(3)\n"


def _port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class AWindowsBootIsChecked(unittest.TestCase):

    def setUp(self):
        self.tree = tempfile.mkdtemp(prefix="bootcheck-law-")

    def tearDown(self):
        shutil.rmtree(self.tree, ignore_errors=True)

    def _tree(self, app, shipped):
        with io.open(os.path.join(self.tree, "control_app.py"), "w", encoding="utf-8") as f:
            f.write(app)
        if shipped is not None:
            with io.open(os.path.join(self.tree, "WINDOWS_SHIP.json"), "w", encoding="utf-8") as f:
                json.dump({"ver": shipped}, f)

    def _run(self, fake_ver="v1"):
        env = dict(os.environ, TVD_BOOT_CHECK_TREE=self.tree, TVD_BOOT_CHECK_PORT=str(_port()),
                   TVD_BOOT_CHECK_BOUND_S="20", FAKE_VER=fake_ver, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, CHECK], env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=90)

    def test_the_shipped_build_passes(self):
        self._tree(FAKE_OK, "v1")
        r = self._run("v1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_different_build_fails(self):
        self._tree(FAKE_OK, "v2")
        r = self._run("v1")
        self.assertEqual(r.returncode, 1, "a console running v1 passed against a v2 ship: " + r.stdout)
        self.assertIn("WINDOWS_SHIP.json ships v2", r.stdout)

    def test_a_boot_death_fails_with_its_last_words(self):
        self._tree(FAKE_DIES, "v1")
        r = self._run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("EXITED", r.stdout)
        self.assertIn("a boot that dies", r.stdout)

    def test_no_shipped_version_is_could_not_run(self):
        self._tree(FAKE_OK, None)
        self.assertEqual(self._run().returncode, 77, "no manifest must be UNKNOWN (77), never a pass")

    def test_the_workflow_runs_it_on_windows_and_watches_itself(self):
        with io.open(WORKFLOW, encoding="utf-8") as f:
            wf = "\n".join(l.split("#", 1)[0] for l in f.read().split("\n"))
        self.assertIn("runs-on: windows-latest", wf)
        self.assertIn("run: python tv/windows_boot_check.py", wf)
        self.assertIn("'.github/workflows/tv-windows-boot.yml'", wf, "the workflow does not watch itself")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#229 - the boot check stops comparing builds: a half-bumped Windows ship boots green",
        "file": "windows_boot_check.py",
        "find": "        if ver != want:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "#229 - a console that dies at boot is waited out as 'no answer' instead of named",
        "file": "windows_boot_check.py",
        "find": "                err = \"the console EXITED during boot (code %s)\" % proc.returncode\n",
        "replace": "                pass\n",
        "matches": 1,
    },
]
