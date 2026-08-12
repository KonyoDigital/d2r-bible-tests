#!/usr/bin/env python3
"""v1710 — the TZ relay must reach a live payload, and say so honestly.

The console card's fallback copy is 'the tracker relay could not reach the live
site'. That string fired when the live Pages function WAS reachable and returned
{current:'', next:'', history:[...]} — d2runewizard briefly empty, KV still
full. The UI treated an empty current as DOWN and blamed the network.

Same class as a 401 on /d2r/api/tz: the app lives under /d2r/, the public
function lives at /api/tz, and a relative fetch (or a 'fixed' upstream) hits
the gate. Middleware only ungated the exact pathname /api/tz.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

os.environ.setdefault("TV_CONTROL_PORT", "17972")
os.environ.setdefault("TV_PORT", "17971")
import control_app as ca  # noqa: E402


class TestMiddlewareLeavesBothTzPathsOpen(unittest.TestCase):
    def test_d2r_api_tz_is_ungated(self):
        mw = open(os.path.join(REPO, "functions", "_middleware.js"), encoding="utf-8").read()
        self.assertIn("/d2r/api/tz", mw)
        self.assertRegex(
            mw,
            r"pathname === '/api/tz'|pathname === '/d2r/api/tz'|/api/tz' && |/d2r/api/tz",
        )

    def test_d2r_path_has_a_function(self):
        p = os.path.join(REPO, "functions", "d2r", "api", "tz.js")
        self.assertTrue(os.path.isfile(p), " /d2r/api/tz has no Pages function — "
                        "ungating it would 404")
        src = open(p, encoding="utf-8").read()
        self.assertTrue(
            "onRequestGet" in src,
            "the /d2r/api/tz function must export the same GET handler",
        )


class TestTzProxyPrefersALivePayload(unittest.TestCase):
    def setUp(self):
        ca._TZ_CACHE.update(ts=0.0, code=0, body=None)

    def tearDown(self):
        ca._TZ_CACHE.update(ts=0.0, code=0, body=None)

    def test_empty_current_with_history_is_success_not_down(self):
        payload = {
            "current": "",
            "next": "",
            "ts": 1,
            "history": [{"slot": 1, "zone": "The Pit"}],
        }

        class _R:
            status = 200
            def read(self):
                return json.dumps(payload).encode()
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        with mock.patch("urllib.request.urlopen", return_value=_R()):
            code, body = ca._tz_proxy()
        self.assertEqual(code, 200)
        self.assertEqual(body.get("history")[0]["zone"], "The Pit")
        self.assertFalse(body.get("error"), body)

    def test_gated_d2r_path_falls_through_to_public(self):
        public = {
            "current": "Travincal",
            "next": "The Pit",
            "ts": 1,
            "history": [],
        }
        calls = []

        def _open(req, timeout=12, context=None):
            url = req.full_url if hasattr(req, "full_url") else req
            calls.append(str(url))
            if "/d2r/" in str(url):
                raise OSError("HTTP Error 401: Unauthorized")

            class _R:
                status = 200
                def read(self):
                    return json.dumps(public).encode()
                def __enter__(self):
                    return self
                def __exit__(self, *a):
                    return False
            return _R()

        with mock.patch.object(ca, "_TZ_UPSTREAMS",
                               ["https://bull-4-u.com/d2r/api/tz",
                                "https://bull-4-u.com/api/tz"]):
            with mock.patch("urllib.request.urlopen", side_effect=_open):
                code, body = ca._tz_proxy()
        self.assertEqual(code, 200, body)
        self.assertEqual(body.get("current"), "Travincal")
        self.assertTrue(any("/api/tz" in c and "/d2r/" not in c for c in calls),
                        calls)

    def test_paint_uses_history_before_blaming_the_network(self):
        ui = open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                  errors="ignore").read()
        # the fallback string may still exist for a TRUE network miss
        self.assertIn("the tracker relay could not reach the live site", ui)
        # but a history-only payload must be painted, not blamed on the network
        self.assertRegex(
            ui,
            r"history\[0\]|d\.history",
            " _tzPaint still treats an empty current as unreachable even when "
            "the relay returned history",
        )


class TestBoardFetchTriesTheGatedCousin(unittest.TestCase):
    def test_refresh_tries_d2r_path(self):
        board = open(os.path.join(REPO, "bible.html"), encoding="utf-8",
                     errors="ignore").read()
        # file:// still short-circuits
        self.assertIn("location.protocol === 'file:'", board)
        self.assertIn("/d2r/api/tz", board)
        self.assertIn("/api/tz", board)


if __name__ == "__main__":
    unittest.main()
