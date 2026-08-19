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


class TestTzCacheDoesNotOutliveItsSlot(unittest.TestCase):
    """v1813 — a cached rotation must not be served across the turn it describes.

    Konyo, 2026-08-19, screenshot stamped 20:00:32: the console read "Burial Grounds, Crypt, and
    Mausoleum" as LIVE NOW. That was the 19:30 slot; the turn had happened 32 seconds earlier.

    The console's own polling was not at fault — v1586/v1587 already fetch six seconds after the
    boundary and drop to a 60s cadence while NEXT is unpublished. The relay underneath was serving
    a 90-second cache that had been filled BEFORE the turn, so the careful 20:00:06 fetch got the
    pre-turn answer and the next look was a further minute away.

    A time-to-live is the wrong instrument for a value that changes on a schedule rather than by
    age: 90 seconds is a fine age for this payload everywhere except across the one instant that
    makes it wrong.
    """

    def setUp(self):
        ca._TZ_CACHE.update(ts=0.0, code=0, body=None)

    def tearDown(self):
        ca._TZ_CACHE.update(ts=0.0, code=0, body=None)

    @staticmethod
    def _upstream(zone):
        payload = {"current": zone, "next": "", "ts": 1,
                   "history": [{"slot": 1787158800000, "zone": zone}]}

        class _R:
            status = 200
            def read(self):
                return json.dumps(payload).encode()
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        return _R

    def test_cache_is_dropped_at_the_slot_boundary(self):
        # a slot starts at an exact 30-minute boundary; sit 40s BEFORE one and fill the cache
        boundary = 1787158800.0                      # 20:00:00 Asia/Jerusalem, from the live feed
        before, after = boundary - 40, boundary + 6  # the console's own post-turn fetch is at +6s

        with mock.patch("time.time", return_value=before):
            with mock.patch("urllib.request.urlopen",
                            return_value=self._upstream("Burial Grounds")()):
                code, body = ca._tz_proxy()
        self.assertEqual(body.get("current"), "Burial Grounds")

        # 46 seconds later — still inside the 90s TTL, but the rotation has TURNED
        with mock.patch("time.time", return_value=after):
            with mock.patch("urllib.request.urlopen",
                            return_value=self._upstream("Flayer Jungle")()) as up:
                code, body = ca._tz_proxy()
                asked = up.call_count
        self.assertEqual(
            body.get("current"), "Flayer Jungle",
            "the relay served a pre-turn rotation after the turn — this is exactly what put "
            "the 19:30 zone on his screen at 20:00:32",
        )
        self.assertGreater(asked, 0, "it must actually re-ask upstream, not just relabel")

    def test_cache_still_holds_inside_one_slot(self):
        # the guard must not become "never cache" — that would hammer upstream every poll
        boundary = 1787158800.0
        t0, t1 = boundary + 5, boundary + 50     # both inside the SAME slot, 45s apart

        with mock.patch("time.time", return_value=t0):
            with mock.patch("urllib.request.urlopen",
                            return_value=self._upstream("Flayer Jungle")()):
                ca._tz_proxy()

        with mock.patch("time.time", return_value=t1):
            with mock.patch("urllib.request.urlopen",
                            return_value=self._upstream("SHOULD NOT BE ASKED")()) as up:
                code, body = ca._tz_proxy()
        self.assertEqual(body.get("current"), "Flayer Jungle")
        self.assertEqual(up.call_count, 0,
                         "inside one slot the cache must still absorb the polls")


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
