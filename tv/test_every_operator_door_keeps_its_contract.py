# -*- coding: utf-8 -*-
"""THE OPERATOR DOORS KEEP THEIR CONTRACT — and this law is their NAMED OWNER.

Routine I's v1550 audit ("every /api route in the console has a consumer, or a named owner") has been
red on four routes that no page calls BY DESIGN: they are doors a person or the GrokBot seat walks
through by hand, after something went wrong.

    /api/owned_restore      put owned names back          (writes his world - confirm required)
    /api/rw_restore         put made runewords back       (writes his world - confirm required)
    /api/vault_autosort     press the board's Auto-Sort   (writes his world - confirm required)
    /api/vault_route_probe  why is each item unsorted     (reads only)

Deleting them would delete the repair path; an allowlist entry with nothing behind it would excuse a
real orphan. So each gets an owner that DRIVES it.

  · DRIVEN through the REAL Handler on an ephemeral port, the board window replaced by a recorder:
    without `confirm`, no write door sends the board a single store write (setItem) and each answers
    applied:false; the probe never writes at all.
  · PREMISE: with `confirm`, every write door DOES send its write - so each no-confirm case can fail.
RED_PROOF below.
"""
import json
import os
import sys
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402

WRITE_DOORS = {
    "/api/owned_restore": {"names": ["Shako"]},
    "/api/rw_restore": {"entries": {"Enigma": "2026-01-01"}},
    "/api/vault_autosort": {},
}
READ_DOORS = {"/api/vault_route_probe": {}}


class _Board(object):
    """Stands in for his board window: records every script, answers like a board that obeyed."""

    def __init__(self):
        self.scripts = []

    def evaluate_js(self, js):
        self.scripts.append(js)
        return json.dumps({"ok": True, "applied": False, "preview": {"moves": 0}, "pool": 0,
                           "assigned": 0, "added": 0, "written": 0})

    def writes(self):
        # a store write, or the press of Auto-Sort itself (its preview only asks `typeof`)
        return [s for s in self.scripts if "setItem(" in s or "window.vaultAutoAssign();" in s]


class OperatorDoorsKeepTheirContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.board = _Board()
        self._saved = dict((k, getattr(ca, k, None)) for k in
                           ("_BOARD_WIN", "_MAIN_WIN", "_WINDOW_LIVE", "board_identity_drift"))
        ca._BOARD_WIN = self.board
        ca._MAIN_WIN = None
        ca._WINDOW_LIVE = True
        ca.board_identity_drift = lambda *a, **k: {"state": "ok"}

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)

    def _post(self, route, body):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, route),
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))

    def test_premise_every_confirmed_door_does_write(self):
        for route, body in WRITE_DOORS.items():
            self.board.scripts[:] = []
            out = self._post(route, dict(body, confirm=True))
            self.assertTrue(self.board.writes(), "premise: CONFIRMED %s sent no write - its no-confirm "
                            "case below would pass for the wrong reason (%r)" % (route, out))

    def test_no_write_door_writes_without_confirm(self):
        for route, body in WRITE_DOORS.items():
            self.board.scripts[:] = []
            out = self._post(route, body)
            self.assertIsNot(out.get("applied"), True, "%s applied without confirm: %r" % (route, out))
            self.assertEqual(self.board.writes(), [], "%s sent the board a WRITE without confirm" % route)

    def test_the_probe_only_reads(self):
        for route, body in READ_DOORS.items():
            self.board.scripts[:] = []
            self._post(route, body)
            self.assertTrue(self.board.scripts, "premise: %s never asked the board anything" % route)
            self.assertEqual([s for s in self.board.scripts if "setItem(" in s], [],
                             "%s wrote to the board - it is a read-only door" % route)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "owned_restore writes without confirm again - a hand-typed restore lands in his world unasked",
        "file": "control_app.py",
        "find": "            self._json(200, owned_restore(body.get(\"names\"), confirm=_confirmed(body.get(\"confirm\"))))\n",
        "replace": "            self._json(200, owned_restore(body.get(\"names\"), confirm=True))\n",
        "matches": 1,
    },
    {
        "why": "vault_autosort presses Auto-Sort without confirm again",
        "file": "control_app.py",
        "find": "            self._json(200, vault_autosort(confirm=_confirmed(body.get(\"confirm\"))))\n",
        "replace": "            self._json(200, vault_autosort(confirm=True))\n",
        "matches": 1,
    },
]
