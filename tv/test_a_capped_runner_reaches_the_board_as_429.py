# -*- coding: utf-8 -*-
"""REG-2383 / REG-2382 — THE REAL RUNNER'S CAP REACHES THE BOARD AS A 429 THAT NAMES ITS LIMIT AND ITS SOURCE.

The join of the two halves: control_app's /api/intake handler spawns the REAL tv/intake_local.mjs (which reads its
limit through tv/pc_settings.mjs and drives the locked functions/api/intake.js) on a fixture ledger at its cap, and the
board must receive HTTP 429 with the runner's refusal - used, limit, and the limit's source - never 200 and never the
website. The handler's own branches (shadow failover, a dead Grok, an erroring Grok) are driven with stub runners in
test_a_capped_read_is_answered_429; the runner's rules in test_the_reader_cap_comes_from_this_pcs_settings.

A LAW OF ITS OWN, NODE-ONLY ON PURPOSE. In the handler law this was the one case that needed node, so on a PC without
node (Dean's) its proof stayed green "with 5 laws run" and was filed BLIND - and one BLIND shuts every lock on a PC.
Here every case skips without node, and such a tamper is ELSEWHERE there (heart2, REG-2354), never BLIND.

ITS PROOF KEY NAMES THE JAVASCRIPT IT RUNS (PROOF_NEEDS): the runner, the settings reader it imports and the pipeline
it drives. heart2's closure follows Python imports only, so without them a PROVEN banked for these bytes would be
served after an edit to tv/pc_settings.mjs that turns this law red (found by review: the source label edited, the
cache served PROVEN, the law failed).

DRIVEN on a private ThreadingHTTPServer with control_app.Handler (never :17772); the ledger and the settings file are
fixtures (TV_SUB_BUDGET, TV_PC_SETTINGS) and the claude CLI is a path that does not exist, so no case can spend a
read; the website proxy is stubbed shut. [[the-unjoined-end]]  RED_PROOF below.
"""
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import time
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

NODE = shutil.which("node")
RUNNER = "intake_local.mjs"
#: the JavaScript this law's verdict runs, which heart2's Python closure cannot see: part of its proof key
PROOF_NEEDS = ["intake_local.mjs", "pc_settings.mjs", "../functions/api/intake.js"]
SEAMS = ("TV_INTAKE_HOURLY_MAX", "TV_INTAKE_DAILY_MAX", "TV_PC_SETTINGS", "TV_SUB_BUDGET", "TVD_CLAUDE_BIN",
         "TV_INTAKE_LOCAL", "TV_INTAKE_LOCAL_STRICT", "TV_INTAKE_MIN_GAP_S", "TV_INTAKE_MODEL")


class _G5(object):
    """The G5 switch as the handler asks it: mode() and reader()."""

    def mode(self):
        return "off"

    def reader(self):
        return "claude"


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheRealRunnersCapReachesTheBoard(unittest.TestCase):

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
        p = mock.patch.object(ca, "_G5", _G5())
        p.start()
        self.addCleanup(p.stop)
        self.website = mock.patch.object(ca.urllib.request, "urlopen",
                                         side_effect=AssertionError("the website proxy was called after a cap"))
        self.web = self.website.start()
        self.addCleanup(self.website.stop)
        self.d = tempfile.mkdtemp(prefix="capped-runner-")
        self.addCleanup(shutil.rmtree, self.d, True)

    def post(self):
        """http.client, not urllib: urllib.request.urlopen is the website proxy's door, stubbed shut above."""
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        try:
            c.request("POST", "/api/intake", headers={"Content-Type": "application/json"},
                      body=json.dumps({"image": "aGk=", "media_type": "image/jpeg", "kind": "locate"}).encode())
            r = c.getresponse()
            return r.status, r.read(), dict(r.getheaders())
        finally:
            c.close()

    def test_the_real_runner_at_its_cap_is_answered_429(self):
        ledger = os.path.join(self.d, "ledger.json")
        now = time.time() * 1000.0
        with open(ledger, "w") as fh:
            json.dump({"calls": [now - 60000.0 * (i + 1) for i in range(20)]}, fh)
        os.environ.update(TV_SUB_BUDGET=ledger, TV_PC_SETTINGS=os.path.join(self.d, "absent.json"),
                          TVD_CLAUDE_BIN=os.path.join(self.d, "no-such-claude"))
        self.assertTrue(os.path.isfile(os.path.join(HERE, RUNNER)), "premise: the runner is not beside the console")
        status, body, hdrs = self.post()
        self.assertEqual(status, 429, "the real runner's cap reached the board as %d: %r" % (status, body[:300]))
        self.assertEqual(hdrs.get("X-Intake-Lane"), "subscription")
        j = json.loads(body)
        self.assertEqual((j.get("error"), j.get("window"), j.get("used"), j.get("limit")),
                         ("subscription-cap", "hour", 20, 20))
        self.assertEqual(j.get("source"), "the code default", "the board is not told where the limit came from")
        self.assertIn("limit from the code default", j.get("message", ""))
        self.assertEqual(self.web.call_count, 0, "the console read on the website's API key after a cap")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2383 - the real runner reports its cap as a 200 again, and the board is told the read succeeded",
        "file": "intake_local.mjs",
        "find": "  process.stdout.write(JSON.stringify({\n    status: 429,\n",
        "replace": "  process.stdout.write(JSON.stringify({\n    status: 200,\n",
        "matches": 1,
    },
    {
        "why": "REG-2382 - the refusal that reaches the board stops naming where its limit came from (the reader's "
               "source label, read through tv/pc_settings.mjs)",
        "file": "pc_settings.mjs",
        "find": "  return { value: fallback, source: 'the code default', notes };\n",
        "replace": "  return { value: fallback, source: '', notes };\n",
        "matches": 1,
    },
]
