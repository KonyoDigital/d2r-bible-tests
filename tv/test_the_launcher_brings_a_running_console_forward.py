# -*- coding: utf-8 -*-
"""REG-1514 — A DOUBLE-CLICK BRINGS A RUNNING CONSOLE FORWARD; IT REPLACES ONLY A STALE OR WINDOWLESS ONE.

The second eye on v3523's bg-service merge (4e22a57a, #231): start_tvd_mac.sh asked a console forward only when its
window was in the BACKGROUND; a window that was simply UP fell through to the soft-kill of :17772, so a Desktop
double-click replaced a healthy console - and any session it was filming. The kill exists for v1379.1 alone (never
window-only onto a STALE console), and the console says whether it is stale itself.

DRIVEN: tv/launcher_decide.decide() against a fake console on an EPHEMERAL port (never :17772) that answers
/api/window and /api/status the way the real one does, and records every POST. RED_PROOF below.
"""
import io
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import launcher_decide as LD  # noqa: E402


class _Console(BaseHTTPRequestHandler):
    mode = "front"
    fresh = {"known": True, "stale": False}
    front_ok = True
    posts = []

    def _send(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/window"):
            self._send({"ok": True, "mode": _Console.mode})
        elif self.path.startswith("/api/status"):
            self._send({"moduleFreshness": _Console.fresh})
        else:
            self._send({})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        _Console.posts.append(json.loads(self.rfile.read(n).decode("utf-8") or "{}"))
        self._send({"ok": _Console.front_ok})

    def log_message(self, *a):
        pass


class TheDecision(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), _Console)
        cls.port = cls.srv.server_address[1]
        assert cls.port != 17772
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def _decide(self, mode, fresh, front_ok=True):
        _Console.mode, _Console.fresh, _Console.front_ok, _Console.posts = mode, fresh, front_ok, []
        done, why = LD.decide(self.port, "law", timeout=5.0)
        return done, why, list(_Console.posts)

    CURRENT = {"known": True, "stale": False}
    STALE = {"known": True, "stale": True}
    UNKNOWN = {"known": False}

    def test_a_window_that_is_up_on_current_code_is_brought_forward_not_replaced(self):
        done, why, posts = self._decide("front", self.CURRENT)
        self.assertTrue(done, "a healthy console with its window up was replaced by a double-click: %s" % why)
        self.assertEqual([{"do": "front", "from": "law"}], posts)

    def test_a_backgrounded_console_is_brought_forward_even_when_it_cannot_say_it_is_current(self):
        done, why, posts = self._decide("background", self.UNKNOWN)
        self.assertTrue(done, "a hidden console filming a reel was replaced: %s" % why)
        self.assertEqual(1, len(posts))

    def test_a_stale_console_is_replaced_and_never_asked(self):
        for mode in ("front", "background"):
            done, why, posts = self._decide(mode, self.STALE)
            self.assertFalse(done, "a console running OLDER code was kept (v1379.1): %s" % why)
            self.assertEqual([], posts, "a stale console was asked forward")
            self.assertIn("OLDER", why)

    def test_a_window_up_that_cannot_say_it_is_current_is_replaced(self):
        done, why, posts = self._decide("front", self.UNKNOWN)
        self.assertFalse(done)
        self.assertEqual([], posts)

    def test_a_windowless_console_is_replaced(self):
        for mode in ("headless", "window-only", ""):
            done, why, posts = self._decide(mode, self.CURRENT)
            self.assertFalse(done, "a console with no window to show was kept for a double-click (%r)" % mode)
            self.assertEqual([], posts)

    def test_a_console_that_does_not_come_forward_is_replaced(self):
        done, why, posts = self._decide("front", self.CURRENT, front_ok=False)
        self.assertFalse(done, "the icon would do nothing (v1460): %s" % why)
        self.assertIn("v1460", why)

    def test_no_console_means_replace(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dead = s.getsockname()[1]
        s.close()
        done, why = LD.decide(dead, "law", timeout=2.0)
        self.assertFalse(done)
        self.assertIn("did not answer", why)


class TheShellBlockRunsUnderSetE(unittest.TestCase):
    """v3525 — the law above drove launcher_decide.py and never the SHELL that calls it. start_tvd_mac.sh runs
    under `set -euo pipefail`, and `x=$(cmd)` whose cmd exits 1 ends the script on that line: with the console
    down ("replace it", rc 1) the launcher launched nothing and his Desktop icon did nothing (measured on his Mac,
    2026-09-29 21:03, `bash -x`: last line was the decide call). DRIVEN: the real block, cut from the real script,
    run by bash with the same flags against a fake launcher_decide.py."""

    def _run_block(self, rc):
        import subprocess, tempfile
        src = io.open(os.path.join(HERE, "start_tvd_mac.sh"), encoding="utf-8").read()
        i = src.index('if [ -z "${TV_FORCE_PORT:-}" ]; then\n', src.index("REG-1514"))
        j = src.index("\nfi\n", i) + 4
        block = src[i:j]
        self.assertIn("launcher_decide.py", block, "the cut missed the decide call")
        d = tempfile.mkdtemp(prefix="launcher_block_")
        try:
            io.open(os.path.join(d, "launcher_decide.py"), "w", encoding="utf-8").write(
                "import sys\nprint('fake decide')\nsys.exit(%d)\n" % rc)
            script = "set -euo pipefail\nHERE=%s\n%s\necho REACHED-THE-LAUNCH\n" % (d, block)
            import posix_shell as _PS   # REG-1632 - a real POSIX bash, never the WSL launcher
            _bash = _PS.bash()
            if _bash is None:           # REG-1642 - never whatever `bash` names (the WSL launcher runs nothing)
                self.skipTest("no real POSIX bash on this PC - the launcher block is UNMEASURED, not passing")
            r = subprocess.run([_bash, "-c", script], capture_output=True, text=True, timeout=30)
            return r
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_replace_it_goes_on_to_launch(self):
        r = self._run_block(1)
        self.assertIn("REACHED-THE-LAUNCH", r.stdout,
                      "with the console down the launcher stopped at the decide call and launched nothing "
                      "(rc=%s stderr=%r)" % (r.returncode, r.stderr[-200:]))

    def test_brought_forward_ends_the_launch(self):
        r = self._run_block(0)
        self.assertEqual(0, r.returncode)
        self.assertNotIn("REACHED-THE-LAUNCH", r.stdout, "a console brought forward was replaced anyway")


class TheWindowsClickUsesTheSameDecision(unittest.TestCase):
    """REG-1758 — opening the console is one rule on both machines. The Mac launcher already asks
    launcher_decide.py. The Windows launcher used to focus whatever was answering :17772, so an old
    process stayed up after the disk had moved. A click now asks the same function: exit 0 brings
    the window forward, anything else is his consent to replace it. A sign-in start still leaves
    a running console alone."""

    def test_the_click_asks_the_shared_decision_and_a_sign_in_does_not(self):
        with io.open(os.path.join(HERE, "start_tvd_win.ps1"), encoding="utf-8-sig") as fh:
            ps = fh.read()
        call = ps.find("--port 17772 --from win-launcher")
        self.assertEqual(ps.count("--from win-launcher"), 1, "the Windows launcher no longer names the one decision")
        bg = ps.find("sign-in start: control already up - left exactly as it is")
        self.assertGreater(call, bg, "a sign-in start reaches the decision and can replace a console that is filming")
        flag = ps.find("$script:TvdReplaceRunning = $true", call)
        self.assertGreater(flag, call, "a console older than the disk no longer falls through to an update")
        self.assertIn("Stop-TvdListenerOnControlPort", ps[flag:],
                      "the update was consented and the old process is still the one that would bind the port")
        self.assertTrue(all(ord(c) < 128 for c in ps), "non-ASCII in a file Windows PowerShell 5 reads")


RED_PROOF = [
    {
        "why": "2026-09-29 (REG-1514) - only a BACKGROUNDED console is asked forward; a window that is up is replaced",
        "file": "tv/launcher_decide.py",
        "find": "    if mode not in (\"front\", \"background\"):\n",
        "replace": "    if mode != \"background\":\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1514) - a console running older code is kept (v1379.1's reason for the kill)",
        "file": "tv/launcher_decide.py",
        "find": "    if fresh is False:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1514) - a console that did not come forward ends the launch anyway (v1460's dead icon)",
        "file": "tv/launcher_decide.py",
        "find": "    if not ok:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (v3525) - the decide call is bare again under set -e; 'replace it' ends the script",
        "file": "tv/start_tvd_mac.sh",
        "find": "  _tvd_why=$(python3 \"$HERE/launcher_decide.py\" --port 17772 --from mac-launcher 2>/dev/null) || _tvd_rc=$?\n",
        "replace": "  _tvd_why=$(python3 \"$HERE/launcher_decide.py\" --port 17772 --from mac-launcher 2>/dev/null)\n",
        "matches": 1,
    },
    {
        "why": "REG-1758 - the Windows click stops asking the shared decision and keeps whatever is already serving",
        "file": "tv/start_tvd_win.ps1",
        "find": "      $decideOut = & $decideCmd @decidePrefix $decideScript --port 17772 --from win-launcher 2>&1\n",
        "replace": "      $decideRc = 0\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
