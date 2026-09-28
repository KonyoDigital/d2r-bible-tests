# -*- coding: utf-8 -*-
"""2026-09-27 — ON WINDOWS THE SHADOW READER COULD NEVER ROLL, AND BOOSTEROID'S OWN APP COULD NEVER PIN.

HIS ASK: "on the windows alt console the shadow reader thats defaulted on. make sure its working there
properly ... the game is on there and has been on."

MEASURED over SSH on his ALT, read-only apart from switching shadow on:
  · shadow on, "armed", and tv/shadow_watch.json rewritten every 20 s with "Diablo is not on screen" while
    the game ran through Boosteroid. capture_preflight asked find_d2r_window_mac(), which opens with a
    Quartz import - on Windows that fails, returns None, and None read as "no game". No Windows PC could
    ever start a shadow reel, whatever was on its screen.
  · the reel's own capture half had seen the same window on 2026-09-25 and held its eye
    (frames/cap_target.json on that PC): "a cloud window is open but its title does not name the game:
    Boosteroid 'Boosteroid'; Boosteroid 'QTrayIconMessageWindow'". Boosteroid's own app titles its window
    with the service's name and nothing else, so the rule "the title must name the game" (#232) could never
    pass it. #232's own note said the first real session would teach us the title; this is that session.

  · DRIVEN: find_d2r_window_win over a fake Win32 walk shaped like the ALT's real one - the Boosteroid window
    pins (its hwnd, labelled Boosteroid); its tray window does not; a CHROME tab titled "Boosteroid" (their
    website) never pins and is named as a near-miss; a local D2R.exe pins over a stream.
  · DRIVEN: control_app.capture_preflight on a Windows console asks the Windows finder, and its reason
    reaches the shadow watcher when nothing pins.
  · SOURCE: capture_win.ps1's C# twin carries the same measured bare title, native app only.
RED_PROOF below.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import tv_diablo as tv  # noqa: E402
import window_visibility as WV  # noqa: E402


def _row(hwnd, pid, title, w, h, iconic=False):
    """Built by the SHIPPED Win32 row rule, plus the hwnd the walk now carries."""
    r = WV._win_row(pid, title, (0, 0, w, h), 0, iconic, 0)
    r["hwnd"] = hwnd
    return r


class _Walk(object):
    def __init__(self, rows):
        self._rows = rows

    def rows(self):
        return list(self._rows)


# the ALT's screen as measured: its own console on top of nothing, Boosteroid streaming, its tray window
PROCS = {10: "pythonw.exe", 20: "Boosteroid.exe", 30: "chrome.exe", 40: "D2R.exe", 50: "explorer.exe"}
ALT = [_row(1001, 10, "TV DIABLO", 1280, 720),
       _row(2002, 20, "Boosteroid", 1920, 1040),
       _row(2003, 20, "QTrayIconMessageWindow", 0, 0),
       _row(5005, 50, "Program Manager", 1920, 1080)]


class TheWindowsFinderSeesWhatTheALTShows(unittest.TestCase):

    def test_boosteroids_own_window_pins(self):
        hit = tv.find_d2r_window_win(win=_Walk(ALT), procs=PROCS)
        self.assertIsNotNone(hit, "the Boosteroid window streaming D2R on his ALT was not pinned: %s" % tv._PICK_WHY)
        self.assertEqual(hit[0], 2002, "pinned the wrong window: %r" % (hit,))
        self.assertTrue(hit[1].startswith("Boosteroid"), "the route is not on the label: %r" % (hit,))

    def test_their_website_in_a_browser_never_pins_and_is_named(self):
        rows = [_row(3003, 30, "Boosteroid", 1920, 1040), _row(1001, 10, "TV DIABLO", 1280, 720)]
        self.assertIsNone(tv.find_d2r_window_win(win=_Walk(rows), procs=PROCS),
                          "a Chrome tab titled 'Boosteroid' (their website) pinned as the game")
        self.assertIn("boosteroid", tv._PICK_WHY, "the near-miss was not named: %r" % tv._PICK_WHY)

    def test_a_local_game_beats_a_stream(self):
        rows = ALT + [_row(4004, 40, "Diablo II: Resurrected", 1920, 1080)]
        hit = tv.find_d2r_window_win(win=_Walk(rows), procs=PROCS)
        self.assertEqual((hit or (None,))[0], 4004, "a running D2R.exe lost to a stream: %r" % (hit,))

    def test_nothing_on_screen_says_so_with_its_count(self):
        rows = [_row(1001, 10, "TV DIABLO", 1280, 720), _row(5005, 50, "Program Manager", 1920, 1080)]
        self.assertIsNone(tv.find_d2r_window_win(win=_Walk(rows), procs=PROCS))
        self.assertIn("among 2 listed", tv._PICK_WHY, "the why lost its denominator: %r" % tv._PICK_WHY)

    def test_an_unreadable_walk_is_not_no_game(self):
        class _Boom(object):
            def rows(self):
                raise OSError("EnumWindows refused")
        self.assertIsNone(tv.find_d2r_window_win(win=_Boom(), procs=PROCS))
        self.assertIn("win32-walk", tv._PICK_WHY)

    def test_a_walk_that_lists_nothing_is_blind_not_empty(self):
        """MEASURED on the ALT: run from SSH the walk lists 0 windows and the snapshot 213 processes."""
        self.assertIsNone(tv.find_d2r_window_win(win=_Walk([]), procs=PROCS))
        self.assertTrue(tv._PICK_UNKNOWN, "a walk that saw no desktop read as 'no game'")
        self.assertIn("UNKNOWN", tv._PICK_WHY)
        tv.find_d2r_window_win(win=_Walk(ALT), procs=PROCS)
        self.assertFalse(tv._PICK_UNKNOWN, "a real look left the UNKNOWN flag standing")

    def test_the_rule_itself(self):
        self.assertEqual(tv.game_route("Boosteroid", "Boosteroid"), "boosteroid")
        self.assertEqual(tv.game_route("chrome", "Boosteroid"), "near:boosteroid")
        self.assertEqual(tv.game_route("Boosteroid", "Boosteroid Launcher"), "near:boosteroid",
                         "an UNMEASURED bare title pinned - only the measured one may")
        self.assertIsNotNone(tv.score_d2r_window_candidate("Boosteroid", "Boosteroid", 1920, 1040))
        self.assertIsNone(tv.score_d2r_window_candidate("Boosteroid", "QTrayIconMessageWindow", 1920, 1040))


class TheWindowsDoorAsksTheWindowsFinder(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        self.ca = ca
        self._saved = (ca.IS_WIN, tv.find_d2r_window_win, tv.find_d2r_window_mac, tv._PICK_WHY,
                       tv._PICK_UNKNOWN, os.environ.get("TV_CAPTURE"))
        self.asked = []
        ca.IS_WIN = True
        os.environ["TV_CAPTURE"] = "auto"
        tv.find_d2r_window_mac = lambda *a, **k: self.asked.append("mac") or None

    def tearDown(self):
        ca = self.ca
        ca.IS_WIN, tv.find_d2r_window_win, tv.find_d2r_window_mac, tv._PICK_WHY, tv._PICK_UNKNOWN, env = self._saved
        if env is None:
            os.environ.pop("TV_CAPTURE", None)
        else:
            os.environ["TV_CAPTURE"] = env

    def test_a_windows_console_sees_the_stream(self):
        tv.find_d2r_window_win = lambda *a, **k: self.asked.append("win") or (2002, "Boosteroid · Boosteroid")
        pre = self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertEqual(self.asked, ["win"], "a Windows console asked %r for the game window" % self.asked)
        self.assertIs(pre.get("windowSeen"), True, "the Boosteroid window did not reach the door: %r" % pre)

    def test_the_finders_reason_reaches_the_door(self):
        def _none(*a, **k):
            tv._PICK_WHY = "no game window among 7 listed; a cloud window ... Boosteroid 'Boosteroid Launcher'"
            return None
        tv.find_d2r_window_win = _none
        tv._PICK_UNKNOWN = False
        pre = self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertIs(pre.get("windowSeen"), False)
        self.assertIn("Boosteroid Launcher", pre.get("windowWhy") or "",
                      "the door said 'not on screen' and dropped which window it passed on: %r" % pre)

    def test_a_blind_finder_is_unknown_at_the_door(self):
        def _blind(*a, **k):
            tv._PICK_UNKNOWN = True
            tv._PICK_WHY = "the window walk listed NO windows at all - UNKNOWN"
            return None
        tv.find_d2r_window_win = _blind
        pre = self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertIsNone(pre.get("windowSeen"), "a finder that could not look told the door 'no game': %r" % pre)
        self.assertIn("could not look", pre.get("windowWhy") or "")

    def test_premise_a_mac_console_still_asks_quartz(self):
        self.ca.IS_WIN = False
        tv.find_d2r_window_win = lambda *a, **k: self.asked.append("win") or None
        self.ca.capture_preflight("shadow", look_for_window=True)
        self.assertEqual(self.asked, ["mac"])


class TheLaneHealthHonoursUnknown(unittest.TestCase):
    """The second eye on v3519 (reproduced): lane_health's shadow-watch 'owed' read a finder that could not LOOK as
    'nothing owed'. Three states, driven through owed_counts() with the finder stubbed."""

    def setUp(self):
        import control_app as ca
        import lane_health as LH
        self.ca, self.LH = ca, LH
        self._saved = (ca._shadow_state, ca._chron_owed_count, ca._vault_owed_reels, tv.find_d2r_window_win,
                       tv._PICK_UNKNOWN, LH.sys.platform)
        ca._shadow_state = lambda: {"on": True, "recording": False}
        ca._chron_owed_count = lambda: 0
        ca._vault_owed_reels = lambda: []
        LH.sys.platform = "win32"

    def tearDown(self):
        (self.ca._shadow_state, self.ca._chron_owed_count, self.ca._vault_owed_reels, tv.find_d2r_window_win,
         tv._PICK_UNKNOWN, self.LH.sys.platform) = self._saved

    def _owed(self, finder):
        tv.find_d2r_window_win = finder
        return self.LH.owed_counts().get("shadow-watch")

    def test_three_states(self):
        def blind():
            tv._PICK_UNKNOWN = True
            return None

        def looked():
            tv._PICK_UNKNOWN = False
            return None
        self.assertIsNone(self._owed(blind), "a finder that could not look reported 'nothing owed'")
        self.assertEqual(self._owed(looked), 0)
        self.assertEqual(self._owed(lambda: (5, "Boosteroid")), 1, "the game on screen with nothing rolling owes a reel")


class TheMacFinderSaysWhenItCannotLook(unittest.TestCase):
    """The second eye on v3520: the Mac finder returned None on a Quartz failure without raising _PICK_UNKNOWN, so
    'could not look' read as 'no game' on his Mac too. Driven with Quartz made unimportable."""

    def test_a_quartz_failure_is_unknown_and_a_real_look_clears_it(self):
        saved = ("Quartz" in sys.modules, sys.modules.get("Quartz"), tv._PICK_CACHE, tv.sys.platform, tv._PICK_UNKNOWN)
        try:
            sys.modules["Quartz"] = None            # import Quartz now raises ImportError
            tv._PICK_CACHE = None
            tv.sys.platform = "darwin"
            tv._PICK_UNKNOWN = False
            self.assertIsNone(tv.find_d2r_window_mac())
            self.assertTrue(tv._PICK_UNKNOWN, "a Quartz import failure read as 'no game' - it could not look")
        finally:
            had, q, cache, plat, unk = saved
            if had:
                sys.modules["Quartz"] = q
            else:
                sys.modules.pop("Quartz", None)
            tv._PICK_CACHE, tv.sys.platform, tv._PICK_UNKNOWN = cache, plat, unk


class TheCaptureHalfCarriesTheSameTitle(unittest.TestCase):

    def test_the_csharp_twin_pins_the_measured_title_native_only(self):
        with io.open(os.path.join(HERE, "capture_win.ps1"), encoding="utf-8-sig") as fh:
            src = fh.read()
        code = "\n".join(l.split("//", 1)[0] for l in src.split("\n"))
        self.assertIn('BoosteroidBareTitles = new string[] { "boosteroid" }', code)
        i = code.find("public static string CloudRoute(")
        j = code.find("if (!HasGame(tl)) return \"\";", i)
        self.assertGreater(i, -1)
        self.assertIn('if (!browser && pl.Contains("boosteroid") && Array.IndexOf(BoosteroidBareTitles, tl) >= 0) '
                      'return "boosteroid";', code[i:j],
                      "the capture half still holds its eye on Boosteroid's own window (or pins a browser tab)")
        self.assertEqual(tuple(tv._NATIVE_BARE_TITLES.get("boosteroid") or ()), ("boosteroid",),
                         "the Python and C# bare titles drifted apart")


RED_PROOF = [
    {
        "why": "the second eye on v3520 - a Quartz failure on the Mac reads as 'no game' again",
        "file": "tv_diablo.py",
        "find": "        _PICK_UNKNOWN = True                    # could not LOOK - never \"no game\" (second eye on v3520)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the second eye on v3519 - lane health reads a blind Windows finder as 'nothing owed' again",
        "file": "lane_health.py",
        "find": "            if win == \"RAISED\" or (win is None and getattr(_tv, \"_PICK_UNKNOWN\", False)):\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a window walk that saw no desktop (0 windows, as over SSH on the ALT) reads as 'no game'",
        "file": "tv_diablo.py",
        "find": "    if not listed:\n        _PICK_WHY = (\"the window walk listed NO windows at all",
        "replace": "    if False:\n        _PICK_WHY = (\"the window walk listed NO windows at all",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the door ignores the finder's UNKNOWN and tells shadow the game is off",
        "file": "control_app.py",
        "find": "            if not win and getattr(_tv, \"_PICK_UNKNOWN\", False):   # either OS (the second eye on v3520)\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a Windows console asks the Quartz finder again: the shadow reader never rolls on Windows",
        "file": "control_app.py",
        "find": "            win = _tv.find_d2r_window_win() if IS_WIN else _tv.find_d2r_window_mac()\n",
        "replace": "            win = _tv.find_d2r_window_mac()\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the door drops the finder's reason: a held shadow says only 'not on screen'",
        "file": "control_app.py",
        "find": "                facts[\"windowWhy\"] = \"Diablo is not on screen\" + ((\" (%s)\" % _pw[:300]) if _pw else \"\")\n",
        "replace": "                facts[\"windowWhy\"] = \"Diablo is not on screen\"\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - Boosteroid's own window (titled only 'Boosteroid') is a near-miss again",
        "file": "tv_diablo.py",
        "find": "            bare = native and not browser and tl in _NATIVE_BARE_TITLES.get(route, ())\n",
        "replace": "            bare = False\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - a browser tab titled 'Boosteroid' (their website) pins as the game",
        "file": "tv_diablo.py",
        "find": "            bare = native and not browser and tl in _NATIVE_BARE_TITLES.get(route, ())\n",
        "replace": "            bare = (native or tab) and tl in _NATIVE_BARE_TITLES.get(route, ())\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the scorer refuses a routed stream whose title names only the service",
        "file": "tv_diablo.py",
        "find": "    if not is_game and not title_game and not _cloud:\n",
        "replace": "    if not is_game and not title_game:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the capture half holds its eye on Boosteroid's own window again",
        "file": "capture_win.ps1",
        "find": "    if (!browser && pl.Contains(\"boosteroid\") && Array.IndexOf(BoosteroidBareTitles, tl) >= 0) return \"boosteroid\";\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-27 - the Windows finder names every window's owner from the title, so no process is ever the game",
        "file": "tv_diablo.py",
        "find": "            rows.append({\"owner\": _win_owner((procs or {}).get(int(r.get(\"kCGWindowOwnerPID\", -1)), \"\")),\n",
        "replace": "            rows.append({\"owner\": r.get(\"kCGWindowOwnerName\") or \"\",\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
