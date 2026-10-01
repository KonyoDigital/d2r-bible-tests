# -*- coding: utf-8 -*-
"""#147 — ONE ROUTE TABLE ON EVERY PC: THE SAME WINDOW IS THE SAME ROUTE ON THE MAC, THE ALT AND DEAN'S PC.

His words, 2026-10-01: "it should be universal though like i said... nvidea play also if it opens it can be dual on
macbook and on windows alt and also on deans" - then "also the native route the local... so 4". The four routes are
local (D2R.exe), crossover (D2R hosted by CrossOver on the Mac), boosteroid and geforce-now, each in its own app or a
browser tab.

MEASURED the same evening: he installed Boosteroid on the Mac and the Mac finder pinned it ("Boosteroid · Boosteroid ·
Boosteroid") - the judge is already one (game_route / _pick_game_window), the finders only LIST differently. But the
bare-title rule was Boosteroid's alone: GeForce NOW's own app titled with nothing but its name was a near-miss on every
PC, so it would record no reel and no prover would stand aside for it; and the "a bare window must show the D2R HUD"
check asked label_is_bare_boosteroid by name.

This law drives ONE table through BOTH finders - the Mac's judge over Quartz-shaped rows (owner as macOS names the app)
and find_d2r_window_win over Win32-shaped rows with a process snapshot (owner as an exe) - and requires every row to name
the same route on both, the bare service windows to be bare on both, and the near-misses (a service's website tab) to
pin on neither. RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import tv_diablo as T  # noqa: E402

W, H = 1470, 923

#: (case, mac owner, windows exe, title, route expected, bare expected) - None for a platform the route does not exist on
TABLE = [
    ("native D2R", "D2R.exe", "D2R.exe", "Diablo II: Resurrected", "local", False),
    ("CrossOver on the Mac", "CrossOver", None, "Diablo II: Resurrected", "crossover", False),
    ("Boosteroid app, bare", "Boosteroid", "Boosteroid.exe", "Boosteroid", "boosteroid", True),
    ("GeForce NOW app, bare", "GeForce NOW", "GeForceNOW.exe", "GeForce NOW", "geforce-now", True),
    ("GeForce NOW app, names the game", "GeForce NOW", "GeForceNOW.exe",
     "Diablo® II: Resurrected™ on GeForce NOW", "geforce-now", False),
    ("GeForce NOW in a browser tab", "Google Chrome", "chrome.exe",
     "Diablo II: Resurrected – Infernal Edition on GeForce NOW", "geforce-now", False),
    ("Boosteroid in a browser tab", "Google Chrome", "chrome.exe", "Diablo II: Resurrected - Boosteroid", "boosteroid",
     False),
]
#: windows that must pin on NEITHER platform: a service's own website, and a page that only mentions the game
NEVER = [
    ("Boosteroid's website", "Google Chrome", "chrome.exe", "Boosteroid"),
    ("GeForce NOW's website", "Google Chrome", "chrome.exe", "GeForce NOW"),
    ("a build guide tab", "Google Chrome", "chrome.exe", "Diablo II: Resurrected build guide"),
]


def _mac_pick(owner, title):
    """the Mac finder's judge over one Quartz-shaped row (find_d2r_window_mac builds exactly these)"""
    best, _near = T._pick_game_window([{"owner": owner, "title": title, "w": W, "h": H, "onscreen": True, "wid": 7}])
    return best[3] if best else None


class _Win32:
    def __init__(self, title):
        self._rows = [{"kCGWindowBounds": {"Width": W, "Height": H}, "kCGWindowOwnerName": title,
                       "kCGWindowOwnerPID": 4242, "iconic": False, "hwnd": 9}]

    def rows(self):
        return self._rows


def _win_pick(exe, title):
    """the Windows finder end to end, through its own seams (window walk + process snapshot)"""
    got = T.find_d2r_window_win(win=_Win32(title), procs={4242: exe})
    return got[1] if got else None


def _route_of(label, owner, title):
    return T.game_route(owner, title) if label else None


class TheSameWindowIsTheSameRouteEverywhere(unittest.TestCase):

    def test_every_route_pins_on_every_pc_that_can_run_it(self):
        for case, mac_owner, exe, title, route, _bare in TABLE:
            with self.subTest(case=case, pc="Mac"):
                lab = _mac_pick(mac_owner, title)
                self.assertIsNotNone(lab, "%s is not the game on the Mac: %s" % (case, T._PICK_WHY))
                self.assertEqual(T.game_route(mac_owner, title), route, case)
            if exe is None:
                continue
            with self.subTest(case=case, pc="Windows (the ALT, Dean's)"):
                lab = _win_pick(exe, title)
                self.assertIsNotNone(lab, "%s is not the game on Windows: %s" % (case, T._PICK_WHY))
                self.assertEqual(T.game_route(T._win_owner(exe), title), route, case)

    def test_a_bare_service_window_is_bare_on_every_pc(self):
        for case, mac_owner, exe, title, _route, bare in TABLE:
            labels = [("Mac", _mac_pick(mac_owner, title))]
            if exe is not None:
                labels.append(("Windows", _win_pick(exe, title)))
            for pc, lab in labels:
                with self.subTest(case=case, pc=pc):
                    self.assertEqual(T.label_is_bare_cloud(lab or ""), bare,
                                     "%s on %s: label %r - a bare service window must show the D2R HUD before it "
                                     "counts, and a titled one must not be held to it" % (case, pc, lab))

    def test_a_website_or_a_guide_pins_nowhere(self):
        for case, mac_owner, exe, title in NEVER:
            with self.subTest(case=case):
                self.assertIsNone(_mac_pick(mac_owner, title), "%s pinned as the game on the Mac" % case)
                self.assertIsNone(_win_pick(exe, title), "%s pinned as the game on Windows" % case)


class TheConsoleAsksTheOneRule(unittest.TestCase):

    def test_the_hud_check_and_the_bare_test_ask_label_is_bare_cloud(self):
        import control_app as CA
        for fn in (CA._bare_hud_verdict, CA.tv_label_is_bare):
            names = set(fn.__code__.co_names)
            self.assertIn("label_is_bare_cloud", names, "%s still asks a one-service rule" % fn.__name__)
            self.assertNotIn("label_is_bare_boosteroid", names, fn.__name__)

    def test_a_bare_geforce_now_window_is_held_to_the_hud(self):
        import control_app as CA
        pre = {"windowLabel": "GeForce NOW · GeForce NOW · GeForce NOW"}
        self.assertTrue(CA.tv_label_is_bare(pre), "a bare GeForce NOW window skipped the HUD check")
        self.assertFalse(CA.tv_label_is_bare({"windowLabel": "GeForce NOW · Diablo II: Resurrected on GeForce NOW"}))


RED_PROOF = [
    {"why": "#147 - GeForce NOW's own app with a bare title is a near-miss again (no reels, no stand-aside)",
     "file": "tv_diablo.py",
     "find": "                       \"geforce-now\": (\"geforce now\", \"geforcenow\", \"nvidia geforce now\")}\n",
     "replace": "                       }\n",
     "matches": 1},
    {"why": "#147 - the bare test knows one service again",
     "file": "tv_diablo.py",
     "find": "    for route, names in _NATIVE_BARE_TITLES.items():\n        if all(s in names or s == route for s in segs):\n",
     "replace": "    for route, names in list(_NATIVE_BARE_TITLES.items())[:1]:\n        if all(s in names or s == route for s in segs):\n",
     "matches": 1},
    {"why": "#147 - the console's bare test asks Boosteroid by name again",
     "file": "control_app.py",
     "find": "    return bool(isinstance(pre, dict) and _tv.label_is_bare_cloud(pre.get(\"windowLabel\") or \"\"))\n",
     "replace": "    return bool(isinstance(pre, dict) and _tv.label_is_bare_boosteroid(pre.get(\"windowLabel\") or \"\"))\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
