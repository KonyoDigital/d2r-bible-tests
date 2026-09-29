# -*- coding: utf-8 -*-
"""REG-1459 — THE SHELF'S LIST IS WARMED AT BOOT, SO HIS FIRST CLICK DOES NOT LOOK LIKE A DEAD BUTTON.

His report 2026-09-29: *"the SHELF when clicked its not opening the section for me"*. MEASURED on his Mac
right after a relaunch: /api/sessions (448 sessions, 453 KB) took 11.2 s cold, 2.7 s warm; the console
demo that opens the shelf gives it 15 s including the render, and it timed out against the freshly
started server while passing 16/16 once warm.

DRIVEN with a real loopback server on an ephemeral port (never :17772): the prewarm asks exactly
/api/sessions on the port it is given and records what happened; a refused port is recorded, never
raised; the rescue loop asks once at SHELF_PREWARM_TICK; status publishes the outcome. RED_PROOF below.
"""
import inspect
import os
import socket
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import control_app as ca  # noqa: E402


class _Rec(BaseHTTPRequestHandler):
    seen = []

    def do_GET(self):
        _Rec.seen.append(self.path)
        body = b'{"sessions": []}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TheShelfIsWarmedAtBoot(unittest.TestCase):

    def setUp(self):
        self.saved = dict(ca._SHELF_PREWARM)

    def tearDown(self):
        ca._SHELF_PREWARM.clear()
        ca._SHELF_PREWARM.update(self.saved)

    def test_it_asks_the_real_handler_on_its_own_port(self):
        _Rec.seen = []
        srv = HTTPServer(("127.0.0.1", 0), _Rec)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            ca._prewarm_shelf(port=srv.server_address[1], _thread=lambda fn: fn())
        finally:
            srv.shutdown()
            srv.server_close()
        self.assertEqual(_Rec.seen, ["/api/sessions"],
                         "the prewarm did not ask this console's own /api/sessions: %r" % _Rec.seen)
        self.assertIs(ca._SHELF_PREWARM["done"], True)
        self.assertIsInstance(ca._SHELF_PREWARM["ms"], int)

    def test_a_refused_port_is_recorded_never_raised(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        ca._prewarm_shelf(port=port, _thread=lambda fn: fn())
        self.assertIs(ca._SHELF_PREWARM["done"], False)
        self.assertIn("could not ask", ca._SHELF_PREWARM["why"])

    def test_the_rescue_loop_asks_once_and_status_says_so(self):
        loop = inspect.getsource(ca._console_rescue_loop)
        self.assertIn("_prewarm_shelf()", loop, "nothing warms the shelf - his first click pays 11 s")
        self.assertIn('== SHELF_PREWARM_TICK', loop, "the prewarm is not a one-shot at boot")
        self.assertIn('"shelfPrewarm": dict(_SHELF_PREWARM)', inspect.getsource(ca),
                      "the prewarm's outcome is invisible")


RED_PROOF = [
    {
        "why": "2026-09-29 - nothing warms the shelf at boot; his first SHELF click pays the 11 s cold build",
        "file": "tv/control_app.py",
        "find": "                _prewarm_shelf()            # REG-1459 — his first SHELF click is served warm\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the prewarm asks a different route, so the cache his click reads stays cold",
        "file": "tv/control_app.py",
        "find": "(_urlopen or _ur.urlopen)(\"http://127.0.0.1:%d/api/sessions\" % int(port or CONTROL_PORT),",
        "replace": "(_urlopen or _ur.urlopen)(\"http://127.0.0.1:%d/api/status\" % int(port or CONTROL_PORT),",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
