# -*- coding: utf-8 -*-
"""REG-1617 — CLAUDE SIGNS IN FROM THE CONSOLE: A SIGN IN BUTTON UNDER THE LAMPS, ON THE PC THAT NEEDS IT.

His ask, 2026-09-30: "make a button there so i can click within the console.. where we said it should render if we are
still connected because this happens monthly i think it just disconnects sometimes". MEASURED the same evening on his
ALT: `claude auth status --json` answered "authMethod": "none" while every read failed with "OAuth session expired" -
and the only way back in was a terminal he had to find and type into.

Driven, joint by joint, never by grepping prose:
  1. claude_signin.status - the CLI's own loggedIn; no CLI / no answer / garbage is UNKNOWN (None), never "signed out".
  2. claude_signin.start - the ONE fixed command (`claude auth login`) in a window HE CAN SEE: on Windows a new console
     with SW_SHOWNORMAL that the console's own no-window door (win_quiet, REG-1307) leaves visible - driven through that
     door, because a hidden sign-in would hang for ever; on the Mac, Terminal. One sign-in in flight at a time.
  3. control_app - the route answers only this console's own page (Origin), starts the sign-in and re-arms the CLI
     probe; the lamp learns "signed out" from the CLI itself (so the button shows before a read has to fail), a read
     that just succeeded outranks it, and an UNKNOWN probe changes nothing.
  4. the header - the SIGN IN pill exists under the lamps, the page's own painter shows it only for needsLogin and says
     when a sign-in is already open, and the click POSTs the route.
Nothing here opens a window or spawns the CLI: every spawn is a recorded fake. RED_PROOF below.
"""
import html.parser
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import claude_signin as CS  # noqa: E402
import win_quiet as WQ  # noqa: E402

NODE = shutil.which("node")
UI = os.path.join(HERE, "control_ui.html")

RED_PROOF = [
    {"why": "REG-1617 - the sign-in opens hidden: win_quiet's door would hide a console that hands in no STARTUPINFO",
     "file": "claude_signin.py",
     "find": "            kw.update(creationflags=CREATE_NEW_CONSOLE, startupinfo=si)\n",
     "replace": "            kw.update(creationflags=CREATE_NEW_CONSOLE)\n", "matches": 1},
    {"why": "REG-1617 - a second click opens a second sign-in window while the first is still open",
     "file": "claude_signin.py",
     "find": "        if inflight():\n",
     "replace": "        if False:\n", "matches": 1},
    {"why": "REG-1617 - any web page may pop a sign-in window on his machine: the origin guard is gone",
     "file": "control_app.py",
     "find": "    if not origin or origin not in ok_origins:\n        return 403, {\"ok\": False, \"started\": False, \"reason\": \"origin\",\n",
     "replace": "    if False:\n        return 403, {\"ok\": False, \"started\": False, \"reason\": \"origin\",\n", "matches": 1},
    {"why": "REG-1617 - the lamp never learns 'signed out' from the CLI: no button until a read has failed",
     "file": "control_app.py",
     "find": "    if isinstance(_au, dict) and _au.get(\"loggedIn\") is False and lamp.get(\"state\") != \"on\":\n",
     "replace": "    if False:\n", "matches": 1},
    {"why": "REG-1617 - the painter never shows SIGN IN",
     "file": "control_ui.html",
     "find": "      sb.hidden = !need;\n",
     "replace": "      sb.hidden = true;\n", "matches": 1},
]


class _Proc(object):
    def __init__(self, alive=True):
        self.alive = alive

    def poll(self):
        return None if self.alive else 0


class _SI(object):
    """A stand-in for subprocess.STARTUPINFO (it exists only on Windows)."""
    def __init__(self):
        self.dwFlags = 0
        self.wShowWindow = 0


class TheCliIsAskedAndDriven(unittest.TestCase):

    def setUp(self):
        CS._PROC.update(proc=None, at=None)

    def _run(self, out):
        return lambda *a, **k: mock.Mock(stdout=out, returncode=0)

    def test_status_is_the_clis_own_word_and_unknown_is_never_signed_out(self):
        self.assertIs(CS.status("/x/claude", _run=self._run('{"loggedIn": false, "authMethod": "none"}'))["loggedIn"], False)
        self.assertIs(CS.status("/x/claude", _run=self._run('{"loggedIn": true, "authMethod": "claude.ai"}'))["loggedIn"], True)
        for bad in ("", "not json", '{"authMethod": "none"}', '["x"]'):
            self.assertIsNone(CS.status("/x/claude", _run=self._run(bad))["loggedIn"], "%r read as a verdict" % bad)
        self.assertIsNone(CS.status(None)["loggedIn"], "no CLI read as signed out")

        def boom(*a, **k):
            raise OSError("gone")
        self.assertIsNone(CS.status("/x/claude", _run=boom)["loggedIn"])

    def test_the_command_is_fixed_per_os(self):
        argv, how = CS.command("C:\\u\\claude.exe", "win32")
        self.assertEqual((argv, how), (["C:\\u\\claude.exe", "auth", "login"], "window"))
        argv, how = CS.command("/Users/x/.local/bin/claude", "darwin")
        self.assertEqual(argv[0], "osascript")
        self.assertIn("'/Users/x/.local/bin/claude' auth login", " ".join(argv))
        argv, why = CS.command("/usr/bin/claude", "linux")
        self.assertIsNone(argv)
        self.assertIn("claude auth login", why, "a PC with no window is not told what to type")
        self.assertIsNone(CS.command(None, "win32")[0])

    def test_the_windows_sign_in_is_visible_through_the_consoles_own_no_window_door(self):
        calls = []
        with mock.patch.object(CS.subprocess, "STARTUPINFO", _SI, create=True):
            r = CS.start("C:\\u\\claude.exe", "win32", _popen=lambda argv, **kw: calls.append((argv, kw)) or _Proc())
        self.assertTrue(r["started"], r)
        argv, kw = calls[0]
        self.assertEqual(argv, ["C:\\u\\claude.exe", "auth", "login"])
        seen = WQ._quiet_kwargs(kw, mock.Mock(STARTUPINFO=_SI))
        self.assertFalse(seen["creationflags"] & WQ.CREATE_NO_WINDOW, "the door made the sign-in windowless")
        self.assertTrue(seen["creationflags"] & WQ.CREATE_NEW_CONSOLE)
        self.assertEqual(seen["startupinfo"].wShowWindow, CS.SW_SHOWNORMAL, "the door hid the sign-in window")

    def test_one_sign_in_at_a_time_and_none_without_a_cli(self):
        calls = []
        pop = lambda argv, **kw: calls.append(argv) or _Proc(alive=True)   # noqa: E731
        with mock.patch.object(CS.subprocess, "STARTUPINFO", _SI, create=True):
            first = CS.start("C:\\u\\claude.exe", "win32", _popen=pop)
            second = CS.start("C:\\u\\claude.exe", "win32", _popen=pop)
        self.assertTrue(first["started"])
        self.assertEqual((second["started"], second["reason"]), (False, "in-flight"))
        self.assertEqual(len(calls), 1, "a second click opened a second sign-in window")
        CS._PROC.update(proc=None)
        none = CS.start(None, "win32", _popen=pop)
        self.assertEqual((none["started"], none["reason"]), (False, "no-cli"))
        self.assertEqual(len(calls), 1)


class TheConsoleAnswersOnlyItsOwnPage(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self.origin = "http://127.0.0.1:%d" % ca.CONTROL_PORT

    def test_the_route_is_origin_guarded_and_rearms_the_probe(self):
        ca, seen = self.ca, []
        code, out = ca.claude_login("https://evil.example", _start=lambda b: seen.append(b) or {"started": True})
        self.assertEqual((code, out["reason"]), (403, "origin"))
        code, out = ca.claude_login(None, _start=lambda b: seen.append(b) or {"started": True})
        self.assertEqual(code, 403)
        self.assertEqual(seen, [], "a foreign page reached the sign-in")
        with mock.patch.dict(ca._CLAUDE_AUTH, {"at": 12345.0}):
            code, out = ca.claude_login(self.origin, _start=lambda b: seen.append(b) or {"ok": True, "started": True},
                                        _bin="/x/claude")
            self.assertEqual((code, out["started"]), (200, True))
            self.assertEqual(seen, ["/x/claude"])
            self.assertEqual(ca._CLAUDE_AUTH["at"], 0.0, "a started sign-in did not re-arm the CLI probe")

    def test_the_real_post_route_reaches_it(self):
        ca, got = self.ca, {}
        h = ca.Handler.__new__(ca.Handler)
        h.path = "/api/claude_login"
        h.headers = {"Origin": self.origin, "Content-Length": "2"}
        h.rfile = io.BytesIO(b"{}")
        h._json = lambda code, obj: got.update(code=code, obj=obj)
        with mock.patch.object(CS, "start", lambda b, **k: {"ok": True, "started": True, "reason": "spawned", "why": "x"}), \
                mock.patch.object(ca, "_find_claude_bin", lambda *a, **k: "/x/claude"):
            h.do_POST()
        self.assertEqual((got.get("code"), (got.get("obj") or {}).get("started")), (200, True), got)

    def test_the_lamp_learns_signed_out_from_the_cli_and_a_good_read_outranks_it(self):
        ca = self.ca
        rd = ca._reader_health(rows=[], g5={}, auth={"loggedIn": False, "why": "claude auth status: signed out (none)"})
        c = rd["claude"]
        self.assertEqual((c["state"], c["needsLogin"]), ("off", True), c)
        self.assertIn("SIGN IN", c["why"])
        self.assertIn("/login", c["why"])
        now = 1790000000000
        good = [{"lane": "deep", "family": "claude", "reader": "claude", "model": "claude-sonnet", "completedTs": now - 60000}]
        rd2 = ca._reader_health(now_ms=now, rows=good, g5={}, auth={"loggedIn": False})
        if rd2["claude"]["state"] == "on":
            self.assertFalse(rd2["claude"]["needsLogin"], "a read that just succeeded was overruled by the probe")
        rd3 = ca._reader_health(rows=[], g5={}, auth={"loggedIn": None, "why": "UNKNOWN"})
        self.assertEqual(rd3["claude"]["state"], "unknown", "an UNKNOWN probe was read as signed out")

    def test_the_probe_runs_off_the_request_path_and_is_not_repeated(self):
        """the thread seam CAPTURES the job instead of running it, so this can see the caller did not wait"""
        ca, runs, pending = self.ca, [], []
        with mock.patch.dict(ca._CLAUDE_AUTH, {"at": 0.0, "val": None, "busy": False}):
            probe = lambda b: runs.append(b) or {"loggedIn": False, "why": "x"}   # noqa: E731
            first = ca._claude_auth_state(now=1000.0, _probe=probe, _thread=pending.append)
            self.assertIsNone(first, "the caller waited on the CLI instead of reading the last answer")
            self.assertEqual(runs, [], "the CLI ran on the caller's own path")
            self.assertEqual(len(pending), 1, "no background ask was started")
            pending.pop()()                                   # the daemon thread runs
            again = ca._claude_auth_state(now=1001.0, _probe=probe, _thread=pending.append)
            self.assertEqual(again["loggedIn"], False)
            self.assertEqual((pending, len(runs)), ([], 1), "the CLI was asked again inside its window")


class _Find(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.hit, self.stack, self.parent_of = None, [], {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id") == "rl-signin":
            self.hit = (tag, a, [x.get("class") for x in self.stack])
        if tag not in ("br", "img", "input", "meta", "link"):
            self.stack.append(a)

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()


class TheHeaderOffersIt(unittest.TestCase):

    def test_the_button_sits_under_the_lamps_and_calls_the_click(self):
        p = _Find()
        p.feed(io.open(UI, encoding="utf-8").read())
        self.assertIsNotNone(p.hit, "there is no SIGN IN button in the page")
        tag, a, parents = p.hit
        self.assertEqual(tag, "button")
        self.assertIn("head-right", parents, "the button is not in the header's right corner, under the lamps")
        self.assertIn("hidden", a, "the button shows before anything said Claude is signed out")
        self.assertEqual(a.get("onclick"), "window._claudeSignIn(this)")

    @unittest.skipUnless(NODE, "node drives the page's own painter and click")
    def test_the_painter_shows_it_only_when_signed_out_and_the_click_posts(self):
        ui = io.open(UI, encoding="utf-8").read()
        a = ui.index("  function _paintReaderLamps(rd) {")
        b = ui.index("  window._claudeSignIn = _claudeSignIn;", a)
        prog = r"""
var ELS = {}, POSTS = [];
function El(){ this.attrs = {}; this.title = ''; this.hidden = true; this.disabled = false; this.textContent = ''; }
El.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); };
var document = { getElementById: function(id){ return ELS[id] || (ELS[id] = new El()); } };
var window = {};
function fetch(u, o){ POSTS.push([u, o && o.method]); return Promise.resolve({ json: function(){ return { ok: true, started: true, why: 'opened' }; } }); }
""" + ui[a:b] + r"""
var out = {}, sb = function(){ return ELS['rl-signin']; };
function snap(){ return [sb().hidden, sb().textContent]; }
_paintReaderLamps({ claude: { state: 'off', needsLogin: true }, grok: { state: 'off' } }); out.signedOut = snap();
_paintReaderLamps({ claude: { state: 'off', needsLogin: true, signInOpen: true } }); out.open = snap();
_paintReaderLamps({ claude: { state: 'on', needsLogin: false } }); out.on = snap();
_paintReaderLamps({ claude: { state: 'off', needsLogin: false, why: 'timeout' } }); out.failedRead = snap();
_paintReaderLamps(null); out.none = snap();
_claudeSignIn(sb()).then(function(){ out.posts = POSTS; out.after = snap(); process.stdout.write(JSON.stringify(out)); });
"""
        r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        o = json.loads(r.stdout)
        self.assertEqual(o["signedOut"], [False, "SIGN IN"], o)
        self.assertEqual(o["open"], [False, "SIGNING IN…"], "an open sign-in offered a second one")
        for k in ("on", "failedRead", "none"):
            self.assertTrue(o[k][0], "%s showed SIGN IN" % k)
        self.assertEqual(o["posts"], [["/api/claude_login", "POST"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
