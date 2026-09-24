# -*- coding: utf-8 -*-
"""#223 — A WINDOW TITLE THAT MENTIONS THE GAME IS NOT THE GAME.

MEASURED 2026-09-24: with no game open, the eye's picker scored a FINDER window titled
"tv-diablo-mailbox" at 1602 — pinnable as the game, because `"diablo" in title` was the whole
qualification — and a stub console filmed his desktop with it (the render gate then flaked on
whichever window happened to be in front). Finder "d2r notes" and Preview "diablo map.png" scored
the same. DRIVEN on the pure scorer: an ordinary app is never the game on its title alone; the game
binary, a wine/CrossOver host, and an owner he named in TV_WINDOW_MATCH still are. RED_PROOF below.
"""
import os
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


class ATitleIsNotAnOwner(unittest.TestCase):

    def setUp(self):
        self._m = os.environ.pop("TV_WINDOW_MATCH", None)

    def tearDown(self):
        if self._m is not None:
            os.environ["TV_WINDOW_MATCH"] = self._m
        else:
            os.environ.pop("TV_WINDOW_MATCH", None)

    def test_an_ordinary_app_is_never_the_game_on_its_title(self):
        for owner, title in (("Finder", "tv-diablo-mailbox"), ("Finder", "d2r notes"),
                             ("Preview", "diablo map.png"), ("TextEdit", "Diablo II: Resurrected notes")):
            self.assertIsNone(tv.score_d2r_window_candidate(owner, title, 1400, 900),
                              "%s %r was pinnable as the game" % (owner, title))

    def test_the_game_is_still_the_game(self):
        self.assertIsNotNone(tv.score_d2r_window_candidate("D2R.exe", "Diablo II: Resurrected", 1470, 956))
        self.assertIsNotNone(tv.score_d2r_window_candidate("CrossOver", "Diablo II: Resurrected", 1470, 956))
        self.assertIsNotNone(tv.score_d2r_window_candidate("wine64-preloader", "Diablo II: Resurrected", 1470, 956))

    def test_an_owner_he_named_is_honoured(self):
        self.assertIsNone(tv.score_d2r_window_candidate("Whisky", "Diablo II: Resurrected", 1470, 956),
                          "premise: an unnamed wrapper is not trusted on its title")
        os.environ["TV_WINDOW_MATCH"] = "whisky"
        self.assertIsNotNone(tv.score_d2r_window_candidate("Whisky", "Diablo II: Resurrected", 1470, 956))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#223 - a Finder/Preview window whose title mentions diablo is pinned as the game again, and the eye films his desktop",
        "file": "tv_diablo.py",
        "find": "    if not owner_ok:\n        return None\n",
        "replace": "    pass\n",
        "matches": 1,
    },
]
