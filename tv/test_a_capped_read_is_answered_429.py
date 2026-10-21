# -*- coding: utf-8 -*-
"""REG-2383 — THE CONSOLE ANSWERS A CAPPED READ WITH 429, AND NEVER ROUTES AROUND THE CAP TO THE WEBSITE.

Before: a cap hit in the subscription runner came back from /api/intake as `200 {"error":"worker-exception"}` - a
success status for a read that never happened - and on /api/ask (and in shadow mode whenever the Grok failover also
failed) the console fell through to the website proxy, which reads on the site's API key: the spend the cap exists to
stop. The runner now reports the refusal as status 429 (tv/intake_local.mjs, law
test_the_reader_cap_comes_from_this_pcs_settings), and control_app's /api/intake handler:
  · forwards it as HTTP 429 with the runner's body (limit, source, retry_s) and X-Intake-Lane;
  · in shadow mode still lets the Grok failover read, and answers the 429 when no lane does;
  · never calls the website proxy after a cap.
DRIVEN on a private ThreadingHTTPServer with control_app.Handler (never :17772), with the node runners stubbed, so
every case runs on any PC - node or none; the website proxy is always stubbed, so no case can reach the network. The
join - the REAL runner at its cap, through this handler - is test_a_capped_runner_reaches_the_board_as_429, node-only
on purpose: here it was the one case a PC without node skipped, which filed its proof BLIND there.
[[the-unjoined-end]]  RED_PROOF below.
"""
import http.client
import json
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402

SEAMS = ("TV_INTAKE_HOURLY_MAX", "TV_INTAKE_DAILY_MAX", "TV_PC_SETTINGS", "TV_SUB_BUDGET", "TVD_CLAUDE_BIN",
         "TV_INTAKE_LOCAL", "TV_INTAKE_LOCAL_STRICT", "TV_INTAKE_MIN_GAP_S")
CAPPED = json.dumps({"error": "subscription-cap", "message": "subscription hourly cap hit (20/20, limit from the code "
                     "default) — intake paused this hour", "window": "hour", "used": 20, "limit": 20,
                     "source": "the code default", "retry_s": 600, "lane": "subscription"})


class _G5(object):
    """The G5 switch as the handler asks it: mode() and reader()."""

    def __init__(self, mode):
        self._mode = mode

    def mode(self):
        return self._mode

    def reader(self):
        return "claude"


class _PR(object):
    def __init__(self, returncode=0, out=None, err=b""):
        self.returncode, self.stdout, self.stderr = returncode, (json.dumps(out).encode() if out else b""), err


class _Console(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.addClassCleanup(cls.srv.server_close)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.addClassCleanup(cls.srv.shutdown)

    def setUp(self):
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for k in SEAMS:
            os.environ.pop(k, None)
        for name in ("_INTAKE_LAST_TS", "_INTAKE_INFLIGHT"):
            p = mock.patch.object(ca, name, 0, create=True)
            p.start()
            self.addCleanup(p.stop)
        self.website = mock.patch.object(ca.urllib.request, "urlopen",
                                         side_effect=AssertionError("the website proxy was called after a cap"))
        self.web = self.website.start()
        self.addCleanup(self.website.stop)

    def g5(self, mode):
        p = mock.patch.object(ca, "_G5", _G5(mode))
        p.start()
        self.addCleanup(p.stop)

    def runners(self, by_lane):
        """Stub the node runners: {"intake_local.mjs": _PR, "intake_grok_sub.mjs": _PR}."""
        seen = []

        def run(cmd, *a, **k):
            name = os.path.basename(str(cmd[-1]))
            seen.append(name)
            return by_lane[name]
        p = mock.patch.object(ca.subprocess, "run", run)
        p.start()
        self.addCleanup(p.stop)
        return seen

    def post(self, path="/api/intake", body=None):
        """http.client, not urllib: urllib.request.urlopen is the website proxy's door, stubbed shut above."""
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        try:
            c.request("POST", path, headers={"Content-Type": "application/json"},
                      body=json.dumps(body or {"image": "aGk=", "media_type": "image/jpeg", "kind": "locate"}).encode())
            r = c.getresponse()
            return r.status, r.read(), dict(r.getheaders())
        finally:
            c.close()

    def assertNoWebsite(self):
        self.assertEqual(self.web.call_count, 0, "the console read on the website's API key after a cap")


class AnOffModeCapIs429(_Console):

    def test_the_runners_429_is_the_consoles_429(self):
        self.g5("off")
        seen = self.runners({"intake_local.mjs": _PR(out={"status": 429, "body": CAPPED, "lane": "subscription"})})
        status, body, hdrs = self.post()
        self.assertEqual(seen, ["intake_local.mjs"])
        self.assertEqual(status, 429, "a capped read was answered %d: %r" % (status, body[:200]))
        self.assertEqual(hdrs.get("X-Intake-Lane"), "subscription")
        self.assertEqual(json.loads(body).get("source"), "the code default", "the runner's refusal was not passed on")
        self.assertNoWebsite()

    def test_an_ask_at_the_cap_is_429(self):
        self.g5("off")
        self.runners({"intake_local.mjs": _PR(out={"status": 429, "body": CAPPED, "lane": "subscription"})})
        status, _body, _h = self.post("/api/ask", {"question": "what can I make?"})
        self.assertEqual(status, 429)
        self.assertNoWebsite()


class AShadowModeCapStillLetsTheFailoverRead(_Console):

    def test_grok_reads_when_claude_is_capped(self):
        self.g5("shadow")
        seen = self.runners({
            "intake_local.mjs": _PR(out={"status": 429, "body": CAPPED, "lane": "subscription"}),
            "intake_grok_sub.mjs": _PR(out={"status": 200, "body": '{"found":false,"box":[0,0,0,0]}',
                                            "lane": "grok-subscription"})})
        status, body, hdrs = self.post()
        self.assertEqual(seen, ["intake_local.mjs", "intake_grok_sub.mjs"])
        self.assertEqual((status, hdrs.get("X-Intake-Lane")), (200, "grok-subscription"),
                         "the Grok failover stopped reading behind a capped Claude")
        self.assertNoWebsite()

    def test_when_the_failover_cannot_run_the_cap_is_the_answer(self):
        self.g5("shadow")
        self.runners({
            "intake_local.mjs": _PR(out={"status": 429, "body": CAPPED, "lane": "subscription"}),
            "intake_grok_sub.mjs": _PR(returncode=1, err=b"grok: not logged in")})
        status, body, hdrs = self.post()
        self.assertEqual(status, 429, "a capped Claude + a dead Grok answered %d: %r" % (status, body[:200]))
        self.assertEqual(hdrs.get("X-Intake-Lane"), "subscription")
        self.assertNoWebsite()

    def test_when_the_failover_errors_the_cap_is_still_the_answer(self):
        self.g5("shadow")
        self.runners({
            "intake_local.mjs": _PR(out={"status": 429, "body": CAPPED, "lane": "subscription"}),
            "intake_grok_sub.mjs": _PR(out={"status": 200, "body": '{"error":"worker-exception","message":"x"}',
                                            "lane": "grok-subscription"})})
        status, body, _h = self.post()
        self.assertEqual(status, 429, "no lane read, and the board was told 200: %r" % body[:200])
        self.assertEqual(json.loads(body).get("error"), "subscription-cap")
        self.assertNoWebsite()


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2383 - after a cap the console falls through to the website proxy (the API key) when no lane reads",
        "file": "control_app.py",
        "find": "                    if _cap_answer is not None:\n                        self.send_response(429)\n",
        "replace": "                    if False:\n                        self.send_response(429)\n",
        "matches": 1,
    },
    {
        "why": "REG-2383 - a runner's 429 is read as an ordinary error body: a capped Claude routes around to the website",
        "file": "control_app.py",
        "find": "                                if str(_out.get(\"status\")) == \"429\":\n",
        "replace": "                                if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2383 - a failover's error body after a cap is answered 200 again",
        "file": "control_app.py",
        "find": "(_lane_lab == _runners[-1][0] and _cap_answer is None)",
        "replace": "_lane_lab == _runners[-1][0]",
        "matches": 1,
    },
]
