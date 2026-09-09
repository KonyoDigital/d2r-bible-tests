#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎞➖ WHAT HE SEES IS WHAT THE NUMBER COUNTS.

Konyo, 2026-09-10, on the 8 reels the test suite opens by name: *"what do i need to see them for??
hide them.. make them for AI information and data base.. but visually no need for this for me.. i
want it clean without it. surgically remove them visaully leave them backend obivosuly so nothing
regresses"* — and, on the count: *"just do -8... its a hidden minus 8 .. no need to even mention
those 8 anywhere visually on the console."*

⚠⚠ HIDING ROWS IS THE EASY HALF. The dangerous half is a total that still counts them: 27 rows on
screen under the word "35" is a number that has stopped describing what he is looking at — the same
defect as a `0` with no denominator, wearing different clothes. So the subtraction is ONE filter,
applied ONCE, and every figure moves with it.

MEASURED on his shelf the day it shipped:

    backend   onDisk 35 · releasable 16 · frames 4037 · panels 2181 · useful 54.0%
    console   onDisk 27 · releasable  8 · frames 2895 · panels 2071 · useful 71.5%

The useful% RISING is honest, not flattery: the fixture reels are mostly empty film, and taking
them out of the denominator is what makes the remaining figure describe his real footage.

⚠ NOTHING IS DELETED AND NOTHING REGRESSES. `reel_story` and `reel_retention` are untouched, the
reels stay on disk, retention still holds them under `test-fixture`, and the 14 test files that
open them by name still find them.

[[zero-needs-a-denominator]] [[label-outlived-referent]] [[the-unjoined-end]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints 🎞 ➖ ⚠ ★
console_safe.enable()

import control_app as C  # noqa: E402


RED_PROOF = [
    {
        "why": "hiding the rows while the counts still include them — 27 reels on screen under the "
               "word 35, which is the exact class of lying number this whole arc has been about",
        "file": "control_app.py",
        "find": '    out["onDisk"] = len(keep)',
        "replace": '    pass',
        "matches": 1,
    },
    {
        "why": "un-hiding the fixtures entirely: his console goes back to showing 8 reels he has no "
               "reason to look at, which is the thing he asked to be surgically removed",
        "file": "control_app.py",
        "find": 'SHELF_HIDDEN_TAGS = ("test-fixture",)',
        "replace": 'SHELF_HIDDEN_TAGS = ()',
        "matches": 1,
    },
    {
        "why": "leaving the STAGE tallies unsubtracted: the lane counts describe 35 reels while the "
               "list under them shows 27, so two figures on one screen disagree about one shelf",
        "file": "control_app.py",
        "find": '        out["stages"] = st',
        "replace": '        pass',
        "matches": 1,
    },
]


def _story(rows, stages=None, y=None):
    """A shelf, built here. Never his. [[feedback-fixtures-never-touch-live-data]]"""
    st = stages or {"filmed": 0, "triaged": 0, "swept": 0, "banked": 0,
                    "vault-done": 0, "releasable": 0}
    for r in rows:
        if r.get("stage") in st:
            st[r["stage"]] += 1
    fr = sum(int(r.get("frames") or 0) for r in rows)
    pa = sum(int(r.get("panels") or 0) for r in rows)
    return {"ok": True, "onDisk": len(rows), "reels": list(rows), "stages": st,
            "yield": y or {"frames": fr, "panels": pa,
                           "usefulPct": round(100.0 * pa / fr, 1) if fr else None,
                           "emptyPct": round(100.0 - 100.0 * pa / fr, 1) if fr else None,
                           "reelsMeasured": len(rows), "storeOk": True}}


def _row(name, tag, stage, frames=100, panels=50):
    return {"reel": name, "tag": tag, "stage": stage, "frames": frames, "panels": panels,
            "mb": 1.0, "pages": 0, "why": "fixture"}


class TheShelfSubtractsTheFixtures(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_count_equals_what_he_can_SEE(self):
        """★★ The whole point. Rows and onDisk are one number or the number is a lie."""
        rows = [_row("reel_a", "test-fixture", "releasable"),
                _row("reel_b", "test-fixture", "releasable"),
                _row("reel_c", "recent", "releasable"),
                _row("reel_d", "panels-never-banked", "banked")]
        v = C._shelf_visible(_story(rows))
        self.assertEqual(len(v["reels"]), v["onDisk"],
                         "the shelf shows %d row(s) under the number %d — a total that counts reels "
                         "he cannot see" % (len(v["reels"]), v["onDisk"]))
        self.assertEqual(2, v["onDisk"], "expected the 2 non-fixture reels, got %d" % v["onDisk"])

    def test_no_hidden_tag_survives_into_the_rows(self):
        """★★ The subtraction itself."""
        rows = [_row("reel_a", "test-fixture", "releasable"), _row("reel_c", "recent", "banked")]
        v = C._shelf_visible(_story(rows))
        left = [r["reel"] for r in v["reels"] if r.get("tag") in C.SHELF_HIDDEN_TAGS]
        self.assertEqual([], left, "hidden-tag reels are still rendered: %r" % left)

    def test_the_STAGE_tallies_move_with_the_rows(self):
        """★★ The half that silently lies. Lane counts describing 35 while the list shows 27 is
        two figures on one screen disagreeing about one shelf."""
        rows = [_row("reel_a", "test-fixture", "releasable"),
                _row("reel_b", "test-fixture", "releasable"),
                _row("reel_c", "recent", "releasable"),
                _row("reel_d", "panels-never-banked", "banked")]
        v = C._shelf_visible(_story(rows))
        self.assertEqual(1, v["stages"]["releasable"],
                         "releasable still counts the hidden fixtures: %r" % v["stages"])
        self.assertEqual(sum(v["stages"].values()), v["onDisk"],
                         "the stage tallies sum to %d and the shelf says %d"
                         % (sum(v["stages"].values()), v["onDisk"]))

    def test_the_YIELD_is_recomputed_over_what_survives(self):
        """★★ A percentage whose denominator includes invisible reels is not about his footage."""
        rows = [_row("reel_a", "test-fixture", "releasable", frames=1000, panels=10),
                _row("reel_c", "recent", "banked", frames=100, panels=80)]
        v = C._shelf_visible(_story(rows))
        self.assertEqual(100, v["yield"]["frames"], "yield frames still counts hidden film")
        self.assertEqual(80, v["yield"]["panels"], "yield panels still counts hidden panels")
        self.assertEqual(80.0, v["yield"]["usefulPct"],
                         "usefulPct is %r — computed over a denominator he cannot see"
                         % v["yield"]["usefulPct"])

    def test_a_shelf_with_NO_frames_says_UNKNOWN_not_zero_percent(self):
        """★ 0 of 0 is not 0%. [[zero-needs-a-denominator]]"""
        rows = [_row("reel_a", "test-fixture", "releasable", frames=5, panels=1),
                _row("reel_c", "recent", "banked", frames=0, panels=0)]
        v = C._shelf_visible(_story(rows))
        self.assertIsNone(v["yield"]["usefulPct"],
                          "a shelf with zero visible frames reported %r%% useful"
                          % v["yield"]["usefulPct"])

    # ── nothing regresses ───────────────────────────────────────────────────────────────────
    def test_it_does_NOT_touch_a_shelf_with_nothing_to_hide(self):
        """★ The identity case: no fixtures, no change, same object back."""
        rows = [_row("reel_c", "recent", "banked"), _row("reel_d", "panels-never-banked", "banked")]
        s = _story(rows)
        v = C._shelf_visible(s)
        self.assertIs(s, v, "the story was rebuilt when there was nothing to subtract")

    def test_the_BACKEND_still_sees_every_reel(self):
        """★★ His condition: 'leave them backend obivosuly so nothing regresses'. The filter must
        return a NEW story and leave the caller's rows alone."""
        rows = [_row("reel_a", "test-fixture", "releasable"), _row("reel_c", "recent", "banked")]
        s = _story(rows)
        before = len(s["reels"])
        v = C._shelf_visible(s)
        self.assertEqual(before, len(s["reels"]),
                         "the filter mutated the caller's story — retention and the test files that "
                         "open those reels by name read the same object")
        self.assertLess(len(v["reels"]), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
