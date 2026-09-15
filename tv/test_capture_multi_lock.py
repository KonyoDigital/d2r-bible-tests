#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-lock capture: default stays single-D2; Chrome/GFN extra is opt-in.

The D2 pin already spent years learning not to grab Chrome (v779.1, v852). This
suite holds that law AND the new extra-pin allowlist so guest GFN testing cannot
quietly become "pin Battle.net / the bible tab / TV DIABLO".
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

os.environ.setdefault("TV_PORT", "17973")  # never collide with a live agent

import capture_lock as CL  # noqa: E402
import tv_diablo as tv  # noqa: E402


def _env(**kw):
    """Isolated environ: only the capture keys we name, so a host TV_CAPTURE cannot leak in."""
    base = {k: v for k, v in os.environ.items()
            if k not in ("TV_CAPTURE", "TV_CAPTURE_EXTRA")}
    base.update(kw)
    return base


class TestCaptureLockPlan(unittest.TestCase):
    def test_default_is_single_d2_auto(self):
        plan = CL.capture_lock_plan(_env())
        self.assertEqual(plan["primary_mode"], "auto")
        self.assertEqual(plan["extra_kinds"], ())
        self.assertEqual(plan["lock"], "single")
        self.assertFalse(CL.extras_armed(_env()))

    def test_auto_explicit_stays_single(self):
        plan = CL.capture_lock_plan(_env(TV_CAPTURE="auto"))
        self.assertEqual(plan["lock"], "single")
        self.assertEqual(plan["extra_kinds"], ())

    def test_window_and_full_stay_single_without_extra(self):
        for mode in ("window", "win", "game", "full"):
            plan = CL.capture_lock_plan(_env(TV_CAPTURE=mode))
            self.assertEqual(plan["lock"], "single", mode)
            self.assertEqual(plan["primary_mode"], mode)
            self.assertEqual(plan["extra_kinds"], ())

    def test_multi_alias_arms_chrome_extra_on_auto_primary(self):
        plan = CL.capture_lock_plan(_env(TV_CAPTURE="multi"))
        self.assertEqual(plan["primary_mode"], "auto")
        self.assertEqual(plan["extra_kinds"], ("chrome",))
        self.assertEqual(plan["lock"], "multi")

    def test_capture_extra_gfn(self):
        plan = CL.capture_lock_plan(_env(TV_CAPTURE="auto", TV_CAPTURE_EXTRA="gfn"))
        self.assertEqual(plan["primary_mode"], "auto")
        self.assertEqual(plan["extra_kinds"], ("gfn",))
        self.assertEqual(plan["lock"], "multi")

    def test_capture_extra_pipe_or_comma(self):
        a = CL.capture_lock_plan(_env(TV_CAPTURE_EXTRA="chrome|gfn"))
        b = CL.capture_lock_plan(_env(TV_CAPTURE_EXTRA="chrome,gfn"))
        # gfn is the stricter subset — one extra pin, prefer gfn
        self.assertEqual(a["extra_kinds"], ("gfn",))
        self.assertEqual(b["extra_kinds"], ("gfn",))

    def test_unknown_extra_token_does_not_arm_multi(self):
        plan = CL.capture_lock_plan(_env(TV_CAPTURE="auto", TV_CAPTURE_EXTRA="safari,firefox"))
        self.assertEqual(plan["lock"], "single")
        self.assertEqual(plan["extra_kinds"], ())

    def test_full_plus_extra_keeps_full_primary(self):
        plan = CL.capture_lock_plan(_env(TV_CAPTURE="full", TV_CAPTURE_EXTRA="chrome"))
        self.assertEqual(plan["primary_mode"], "full")
        self.assertEqual(plan["lock"], "multi")
        self.assertEqual(plan["extra_kinds"], ("chrome",))

    def test_host_tv_capture_cannot_leak_into_empty_plan(self):
        with mock.patch.dict(os.environ, {"TV_CAPTURE": "multi", "TV_CAPTURE_EXTRA": "gfn"}):
            plan = CL.capture_lock_plan({})
            # empty mapping is the caller's env — not os.environ
            self.assertEqual(plan["lock"], "single")
            self.assertEqual(plan["primary_mode"], "auto")


class TestChromeGfnAllowlist(unittest.TestCase):
    def test_gfn_chrome_is_accepted(self):
        sc = CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "GeForce NOW", 1920, 1080, True, kind="gfn")
        self.assertIsNotNone(sc)
        self.assertGreater(sc, 5000)

    def test_gfn_kind_rejects_unrelated_chrome_tab(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "Inbox — Gmail", 1400, 900, True, kind="gfn"))

    def test_chrome_kind_accepts_plain_chrome_and_prefers_gfn(self):
        plain = CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "New Tab", 1400, 900, True, kind="chrome")
        gfn = CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "GeForce NOW - D2R", 1920, 1080, True, kind="chrome")
        self.assertIsNotNone(plain)
        self.assertIsNotNone(gfn)
        self.assertGreater(gfn, plain)

    def test_battle_net_lobby_never_extra(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Battle.net.exe", "Battle.net", 1470, 805, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "Battle.net", 1400, 900, True, kind="chrome"))

    def test_crossover_home_never_extra(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "CrossOver", "CrossOver", 1150, 700, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "CrossOver", "Home", 1150, 700, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "CrossOver", 1400, 900, True, kind="chrome"))

    def test_tv_diablo_and_bible_tab_never_extra(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "Konyo's D2R Farming Bible", 1400, 900, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "TV DIABLO", 1280, 800, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "localhost:17772", 1280, 800, True, kind="chrome"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "python", "TV DIABLO", 1280, 800, True, kind="chrome"))

    def test_d2r_window_is_not_an_extra_pin(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "D2R.exe", "Diablo II: Resurrected", 1470, 956, True, kind="chrome"))

    def test_safari_is_not_the_gfn_path(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Safari", "GeForce NOW", 1920, 1080, True, kind="gfn"))

    def test_chrome_helper_and_random_owner_rejected(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome Helper", "GeForce NOW", 1920, 1080, True, kind="gfn"))
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Not Chrome", "GeForce NOW", 1920, 1080, True, kind="gfn"))

    def test_tiny_chrome_bar_rejected(self):
        self.assertIsNone(CL.score_chrome_gfn_window_candidate(
            "Google Chrome", "GeForce NOW", 1470, 33, True, kind="gfn"))


class TestD2ScorerStillRejectsBrowsers(unittest.TestCase):
    """Auto-single mode: Chrome must still lose the PRIMARY pin even with a game title."""

    def test_chrome_bible_tab_dead_for_d2(self):
        self.assertIsNone(tv.score_d2r_window_candidate(
            "Google Chrome", "Konyo's D2R Farming Bible", 1470, 900, True))

    def test_chrome_with_game_title_still_dead_for_d2(self):
        self.assertIsNone(tv.score_d2r_window_candidate(
            "Google Chrome", "Diablo II: Resurrected build guide", 1470, 900, True))
        self.assertIsNone(tv.score_d2r_window_candidate(
            "Google Chrome", "GeForce NOW", 1920, 1080, True))

    def test_d2_exe_still_wins_primary(self):
        game = tv.score_d2r_window_candidate(
            "D2R.exe", "Diablo II: Resurrected", 1470, 956, True)
        self.assertIsNotNone(game)
        self.assertGreater(game, 10000)


class TestPickExtraFromWindowList(unittest.TestCase):
    def setUp(self):
        self.windows = [
            {"owner": "CrossOver", "title": "Home", "width": 1150, "height": 700,
             "wid": 11, "onscreen": True},
            {"owner": "Battle.net.exe", "title": "Battle.net", "width": 1470, "height": 805,
             "wid": 12, "onscreen": True},
            {"owner": "Google Chrome", "title": "Konyo's D2R Farming Bible", "width": 1400,
             "height": 900, "wid": 13, "onscreen": True},
            {"owner": "D2R.exe", "title": "Diablo II: Resurrected", "width": 1470,
             "height": 956, "wid": 14, "onscreen": True},
            {"owner": "Google Chrome", "title": "GeForce NOW", "width": 1920,
             "height": 1080, "wid": 99, "onscreen": True},
            {"owner": "Google Chrome", "title": "New Tab", "width": 1280,
             "height": 800, "wid": 15, "onscreen": True},
        ]

    def test_gfn_kind_picks_geforce_not_bible_or_d2(self):
        hit = CL.pick_extra_window(self.windows, kind="gfn")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["wid"], 99)
        self.assertEqual(hit["kind"], "gfn")
        self.assertEqual(hit["mode"], "window")
        self.assertEqual(hit["file"], "eye.gfn.jpg")

    def test_chrome_kind_prefers_gfn_over_plain_tab(self):
        hit = CL.pick_extra_window(self.windows, kind="chrome")
        self.assertEqual(hit["wid"], 99)
        self.assertEqual(hit["kind"], "gfn")

    def test_no_match_returns_none(self):
        blocked = [w for w in self.windows if w["wid"] not in (99, 15)]
        self.assertIsNone(CL.pick_extra_window(blocked, kind="gfn"))


class TestStatusShapeBackwardCompatible(unittest.TestCase):
    def test_single_waiting_keeps_classic_keys(self):
        primary = {"mode": "waiting", "label": "eye arming…", "wid": None}
        st = CL.build_capture_status(primary, extras=None, env=_env())
        self.assertEqual(st["captureLock"], "single")
        self.assertEqual(st["captureTarget"]["mode"], "waiting")
        self.assertEqual(st["captureTarget"]["label"], "eye arming…")
        self.assertIsNone(st["captureTarget"]["wid"])
        self.assertIn("kind", st["captureTarget"])
        self.assertEqual(st["captureTarget"]["kind"], "d2")
        self.assertEqual(len(st["captureTargets"]), 1)
        self.assertEqual(st["captureTargets"][0]["mode"], "waiting")
        # classic clients that only read captureTarget still work
        for k in ("mode", "label", "wid"):
            self.assertIn(k, st["captureTarget"])

    def test_full_mode_unchanged_when_single(self):
        primary = {"mode": "full", "label": "full screen", "wid": None}
        st = CL.build_capture_status(primary, extras=None, env=_env(TV_CAPTURE="full"))
        self.assertEqual(st["captureLock"], "single")
        self.assertEqual(st["captureTarget"]["mode"], "full")
        self.assertEqual(len(st["captureTargets"]), 1)

    def test_window_mode_unchanged_when_single(self):
        primary = {"mode": "window", "label": "D2R.exe · Diablo II: Resurrected", "wid": 42}
        st = CL.build_capture_status(primary, extras=None, env=_env(TV_CAPTURE="auto"))
        self.assertEqual(st["captureTarget"]["mode"], "window")
        self.assertEqual(st["captureTarget"]["wid"], 42)
        self.assertEqual(st["captureLock"], "single")
        self.assertEqual(len(st["captureTargets"]), 1)

    def test_multi_status_keeps_primary_and_lists_extra(self):
        primary = {"mode": "window", "label": "D2R.exe · Diablo II: Resurrected", "wid": 42}
        extra = {"kind": "gfn", "mode": "window", "label": "Google Chrome · GeForce NOW",
                 "wid": 99, "file": "eye.gfn.jpg"}
        st = CL.build_capture_status(primary, extras=[extra],
                                     env=_env(TV_CAPTURE_EXTRA="gfn"))
        self.assertEqual(st["captureLock"], "multi")
        self.assertEqual(st["captureTarget"]["mode"], "window")
        self.assertEqual(st["captureTarget"]["wid"], 42)
        self.assertEqual(st["captureTarget"]["kind"], "d2")
        self.assertEqual(len(st["captureTargets"]), 2)
        self.assertEqual(st["captureTargets"][0]["kind"], "d2")
        self.assertEqual(st["captureTargets"][1]["kind"], "gfn")
        self.assertEqual(st["captureTargets"][1]["file"], "eye.gfn.jpg")
        # primary dict in the list is the same pin the classic field names
        self.assertEqual(st["captureTargets"][0]["wid"], st["captureTarget"]["wid"])

    def test_multi_armed_with_no_window_still_reports_waiting_extra(self):
        primary = {"mode": "waiting", "label": "D2R window not listed — eye held", "wid": None}
        st = CL.build_capture_status(primary, extras=None,
                                     env=_env(TV_CAPTURE="multi"))
        self.assertEqual(st["captureLock"], "multi")
        self.assertEqual(st["captureTarget"]["mode"], "waiting")
        self.assertEqual(len(st["captureTargets"]), 2)
        self.assertEqual(st["captureTargets"][1]["mode"], "waiting")
        self.assertIsNone(st["captureTargets"][1]["wid"])

    def test_json_roundtrip_keeps_classic_client_shape(self):
        st = CL.build_capture_status(
            {"mode": "window", "label": "D2R.exe · Diablo II: Resurrected", "wid": 7},
            extras=[{"kind": "chrome", "mode": "window", "label": "Google Chrome · GeForce NOW",
                     "wid": 8}],
            env=_env(TV_CAPTURE="multi"))
        blob = json.loads(json.dumps(st))
        self.assertIsInstance(blob["captureTarget"], dict)
        self.assertIsInstance(blob["captureTargets"], list)
        self.assertEqual(blob["captureTarget"]["mode"], "window")
        self.assertEqual(blob["captureLock"], "multi")

    def test_disk_payload_does_not_smuggle_list_into_captureTarget(self):
        payload = {
            "mode": "window",
            "label": "D2R.exe · Diablo II: Resurrected",
            "wid": 1,
            "captureTargets": [
                {"kind": "d2", "mode": "window", "wid": 1},
                {"kind": "gfn", "mode": "window", "label": "GeForce NOW", "wid": 2},
            ],
        }
        primary = CL.primary_from_disk_payload(payload)
        self.assertNotIn("captureTargets", primary)
        self.assertEqual(primary["mode"], "window")
        extras = CL.extras_from_disk_payload(payload)
        self.assertEqual(len(extras), 1)
        self.assertEqual(extras[0]["kind"], "gfn")


class TestFrameLaneTagging(unittest.TestCase):
    def test_primary_eye_name_unchanged(self):
        self.assertEqual(CL.eye_filename("d2"), "eye.jpg")
        self.assertEqual(CL.eye_filename("game"), "eye.jpg")
        self.assertEqual(CL.live_filename("d2"), "live.jpg")

    def test_extra_eye_is_tagged(self):
        self.assertEqual(CL.eye_filename("gfn"), "eye.gfn.jpg")
        self.assertEqual(CL.eye_filename("chrome"), "eye.chrome.jpg")
        self.assertEqual(CL.live_filename("gfn"), "live.gfn.jpg")

    def test_extra_archive_does_not_use_f_prefix(self):
        name = CL.extra_archive_name("gfn", 1780000000000)
        self.assertTrue(name.startswith("x_gfn_"))
        self.assertTrue(name.endswith(".jpg"))
        self.assertFalse(name.startswith("f_"))
        self.assertEqual(CL.extra_archive_name("d2", 5), "f_5.jpg")

    def test_intelligence_skips_extra_lanes_not_live_bmp(self):
        self.assertTrue(CL.is_intelligence_skip_name("eye.jpg"))
        self.assertTrue(CL.is_intelligence_skip_name("eye.gfn.jpg"))
        self.assertTrue(CL.is_intelligence_skip_name("live.gfn.jpg"))
        self.assertTrue(CL.is_intelligence_skip_name("x_gfn_1.jpg"))
        self.assertFalse(CL.is_intelligence_skip_name("live.bmp"))
        self.assertFalse(CL.is_intelligence_skip_name("live.jpg"))
        self.assertFalse(CL.is_intelligence_skip_name("live.png"))


class TestTvDiabloStatusJoin(unittest.TestCase):
    """The agent must actually publish captureTargets — a helper nobody calls is the unjoined end."""

    def test_helper_exists_and_uses_live_globals(self):
        self.assertTrue(callable(tv.capture_status_fields))
        old_t, old_e = tv._CAP_TARGET, list(getattr(tv, "_CAP_EXTRAS", []) or [])
        try:
            tv._CAP_TARGET = {"mode": "waiting", "label": "eye arming…", "wid": None}
            tv._CAP_EXTRAS = []
            with mock.patch.dict(os.environ, {"TV_CAPTURE": "auto"}, clear=False):
                # strip extra if the host exported one
                os.environ.pop("TV_CAPTURE_EXTRA", None)
                st = tv.capture_status_fields()
            self.assertEqual(st["captureLock"], "single")
            self.assertEqual(st["captureTarget"]["mode"], "waiting")
            self.assertEqual(len(st["captureTargets"]), 1)
        finally:
            tv._CAP_TARGET = old_t
            tv._CAP_EXTRAS = old_e

    def test_newest_watched_frame_skips_extra_eye(self):
        d = tempfile.mkdtemp()
        old = tv.FRAMES
        try:
            tv.FRAMES = d
            with open(os.path.join(d, "eye.gfn.jpg"), "wb") as fh:
                fh.write(b"gfn" + b"x" * 100)
            with open(os.path.join(d, "live.bmp"), "wb") as fh:
                fh.write(b"BM" + b"y" * 200)
            hit = tv.newest_watched_frame()
            self.assertTrue(hit and hit.endswith("live.bmp"), hit)
        finally:
            tv.FRAMES = old
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_cap_target_shape_still_has_mode_and_label(self):
        self.assertIn("mode", tv._CAP_TARGET)
        self.assertIn("label", tv._CAP_TARGET)


class TestSyncExtrasRespectsPlan(unittest.TestCase):
    def test_sync_clears_extras_when_single(self):
        old = list(getattr(tv, "_CAP_EXTRAS", []) or [])
        try:
            tv._CAP_EXTRAS = [{"kind": "gfn", "mode": "window", "wid": 9, "label": "x"}]
            with mock.patch.dict(os.environ, {"TV_CAPTURE": "auto", "TV_CAPTURE_EXTRA": ""},
                                 clear=False):
                os.environ.pop("TV_CAPTURE_EXTRA", None)
                tv._sync_cap_extras(windows=[
                    {"owner": "Google Chrome", "title": "GeForce NOW",
                     "width": 1920, "height": 1080, "wid": 99, "onscreen": True},
                ])
            self.assertEqual(tv._CAP_EXTRAS, [])
        finally:
            tv._CAP_EXTRAS = old

    def test_sync_accepts_gfn_when_multi(self):
        old = list(getattr(tv, "_CAP_EXTRAS", []) or [])
        try:
            tv._CAP_EXTRAS = []
            wins = [
                {"owner": "Google Chrome", "title": "GeForce NOW",
                 "width": 1920, "height": 1080, "wid": 99, "onscreen": True},
                {"owner": "Google Chrome", "title": "TV DIABLO",
                 "width": 1280, "height": 800, "wid": 3, "onscreen": True},
            ]
            with mock.patch.dict(os.environ, {"TV_CAPTURE": "multi"}, clear=False):
                os.environ.pop("TV_CAPTURE_EXTRA", None)
                tv._sync_cap_extras(windows=wins)
            self.assertEqual(len(tv._CAP_EXTRAS), 1)
            self.assertEqual(tv._CAP_EXTRAS[0]["wid"], 99)
            self.assertNotEqual(tv._CAP_EXTRAS[0]["wid"], 3)
        finally:
            tv._CAP_EXTRAS = old


if __name__ == "__main__":
    unittest.main()
