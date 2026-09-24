# -*- coding: utf-8 -*-
"""#232 — THE EYE FINDS DIABLO II: RESURRECTED HOWEVER HE RUNS IT, AND ONLY THE GAME.

HIS ORDER, 2026-09-24: "needs to target diablo ii resurrected in macbook like it is crossover or
nvideaplay chrome or boosteroid so windows also regularly for those options + the usual route on
windows locally. and linux cant open those they lock automatically".

MEASURED before this: on the Mac every browser was blocked wholesale, so a GeForce NOW session in a
Chrome tab could never pin; on Windows capture_win.ps1 only enumerated D2R-process windows, so a
streamed session fell through to FULL SCREEN and filmed the desktop. And a store-style title,
"Diablo® II: Resurrected™", never matched "diablo ii" because of the ®.

DRIVEN on the pure picker (game_route + score_d2r_window_candidate) and, for Windows, on the
C# source the script compiles (its routes are asserted by text here and COMPILED on the Windows box
over SSH; a Mac cannot run Add-Type). ⚠ The real cloud window titles are UNMEASURED: the cases below
use the shape the services are expected to show, and a service window whose title does NOT name the
game is a near-miss the picker reports rather than pins. RED_PROOF below.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import tv_diablo as tv  # noqa: E402

W, H = 1470, 956


class TheMacFindsEveryRoute(unittest.TestCase):

    def test_local_and_crossover_still_pin(self):
        self.assertEqual(tv.game_route("D2R.exe", "Diablo II: Resurrected"), "local")
        self.assertEqual(tv.game_route("CrossOver", "Diablo II: Resurrected"), "crossover")
        self.assertIsNotNone(tv.score_d2r_window_candidate("D2R.exe", "Diablo II: Resurrected", W, H))

    def test_geforce_now_in_its_app_or_a_browser_tab_pins(self):
        for owner, title in (("GeForceNOW", "Diablo® II: Resurrected™"),
                             ("Google Chrome", "Diablo® II: Resurrected™ on GeForce NOW"),
                             ("Microsoft Edge", "GeForce NOW - Diablo II: Resurrected"),
                             # MEASURED on his screen 2026-09-24 — the first real streamed title
                             ("Google Chrome", "Diablo II: Resurrected \u2013 Infernal Edition on GeForce NOW")):
            self.assertEqual(tv.game_route(owner, title), "geforce-now", "%s %r" % (owner, title))
            self.assertIsNotNone(tv.score_d2r_window_candidate(owner, title, W, H),
                                 "a streamed D2R window (%s %r) could not pin" % (owner, title))

    def test_boosteroid_in_its_app_or_a_browser_tab_pins(self):
        for owner, title in (("Boosteroid", "Diablo II: Resurrected"),
                             ("Google Chrome", "Boosteroid - Diablo II: Resurrected")):
            self.assertEqual(tv.game_route(owner, title), "boosteroid", "%s %r" % (owner, title))
            self.assertIsNotNone(tv.score_d2r_window_candidate(owner, title, W, H))

    def test_a_browser_needs_BOTH_the_service_and_the_game(self):
        for owner, title in (("Google Chrome", "Diablo II: Resurrected build guide"),   # no service
                             ("Google Chrome", "GeForce NOW"),                          # no game
                             ("Safari", "Boosteroid Cloud Gaming")):                    # no game
            self.assertIsNone(tv.score_d2r_window_candidate(owner, title, W, H),
                              "%s %r pinned as the game" % (owner, title))

    def test_a_service_window_without_the_game_is_a_named_near_miss(self):
        self.assertEqual(tv.game_route("Google Chrome", "GeForce NOW"), "near:geforce-now")
        self.assertEqual(tv.game_route("Boosteroid", "Boosteroid"), "near:boosteroid")

    def test_the_marks_a_store_puts_in_the_name_do_not_hide_it(self):
        self.assertEqual(tv._norm_title("Diablo®  II: Resurrected™"), "diablo ii: resurrected")


class TheMacPickerOnAFakeScreen(unittest.TestCase):
    """find_d2r_window_mac() itself, over a stubbed Quartz window list (never his real screen)."""

    def _screen(self, wins):
        import types
        q = types.ModuleType("Quartz")
        q.kCGWindowListOptionAll, q.kCGNullWindowID = 0, 0
        q.CGWindowListCopyWindowInfo = lambda *a: [
            {"kCGWindowLayer": 0, "kCGWindowOwnerName": o, "kCGWindowName": t,
             "kCGWindowBounds": {"Width": W, "Height": H}, "kCGWindowIsOnscreen": True,
             "kCGWindowNumber": 100 + i} for i, (o, t) in enumerate(wins)]
        self._saved = (sys.modules.get("Quartz"), tv._PICK_CACHE, tv.sys.platform)
        sys.modules["Quartz"] = q
        tv._PICK_CACHE = None
        tv.sys.platform = "darwin"

    def tearDown(self):
        q, cache, plat = getattr(self, "_saved", (None, None, sys.platform))
        if q is None:
            sys.modules.pop("Quartz", None)
        else:
            sys.modules["Quartz"] = q
        tv._PICK_CACHE, tv.sys.platform = None, plat

    def test_a_streamed_window_pins_with_its_route_on_the_label(self):
        self._screen([("Finder", "tv-diablo-mailbox"), ("GeForceNOW", "Diablo\u00ae II: Resurrected\u2122")])
        hit = tv.find_d2r_window_mac()
        self.assertIsNotNone(hit, "the GeForce NOW window streaming D2R was not pinned")
        self.assertTrue(hit[1].startswith("GeForce NOW"), "the route is not on the label: %r" % (hit,))

    def test_a_service_window_without_the_game_is_reported_not_pinned(self):
        self._screen([("Google Chrome", "GeForce NOW"), ("Finder", "d2r notes")])
        self.assertIsNone(tv.find_d2r_window_mac())
        self.assertIn("geforce-now", tv._PICK_WHY, "the near-miss was not named: %r" % tv._PICK_WHY)

    def test_linux_pins_nothing_and_says_why(self):
        self._screen([("GeForceNOW", "Diablo II: Resurrected")])
        tv.sys.platform = "linux"
        self.assertIsNone(tv.find_d2r_window_mac())
        self.assertIn("Linux", tv._PICK_WHY)


class WindowsFindsEveryRoute(unittest.TestCase):
    """capture_win.ps1's C# finder — asserted on its source here, compiled on the Windows box."""

    def setUp(self):
        self.src = io.open(os.path.join(HERE, "capture_win.ps1"), encoding="utf-8-sig").read()

    def test_the_cloud_apps_and_browsers_are_candidates(self):
        self.assertRegex(self.src, r'CloudApps = new string\[\] \{ "GeForceNOW", "Boosteroid" \}')
        self.assertIn('"chrome", "msedge"', self.src)
        self.assertIn("public static string CloudRoute(string proc, string title, bool browser)", self.src)

    def test_a_service_window_that_does_not_name_the_game_is_skipped(self):
        code = "\n".join(l.split("//", 1)[0] for l in self.src.split("\n"))
        self.assertIn('if (route == "") return true;', code,
                      "a browser or cloud-app window that does not name the game became a candidate")

    def test_windows_powershell_can_still_read_it(self):
        """Windows PowerShell reads a file with no BOM as ANSI, so non-ASCII there is mangled. The
        file carries em-dashes in comments and a UTF-8 BOM; it must keep one of the two properties."""
        raw = io.open(os.path.join(HERE, "capture_win.ps1"), "rb").read()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf") or all(b < 128 for b in raw),
                        "capture_win.ps1 has non-ASCII and no BOM: Windows PowerShell reads it as ANSI")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#232 - Linux reaches for Quartz again instead of saying there is nothing to pin there",
        "file": "tv_diablo.py",
        "find": "    if sys.platform.startswith(\"linux\"):\n        _PICK_WHY = (\"Linux: D2R and its cloud routes",
        "replace": "    if False:\n        _PICK_WHY = (\"Linux: D2R and its cloud routes",
        "matches": 1,
    },
    {
        "why": "#232 - every browser is blocked again: a GeForce NOW / Boosteroid tab streaming D2R can never pin",
        "file": "tv_diablo.py",
        "find": "        if not (_title_is_game or _cloud):\n",
        "replace": "        if not _title_is_game:\n",
        "matches": 1,
    },
    {
        "why": "#232 - a browser tab qualifies on the service alone: the GeForce NOW library page pins as the game",
        "file": "tv_diablo.py",
        "find": "        if (native or tab) and has_game:\n",
        "replace": "        if native or tab:\n",
        "matches": 1,
    },
    {
        "why": "#232 - the Windows finder takes any browser/cloud window, named game or not",
        "file": "capture_win.ps1",
        "find": "          if (route == \"\") return true;            // a service window that does not name the game\n",
        "replace": "",
        "matches": 1,
    },
]
