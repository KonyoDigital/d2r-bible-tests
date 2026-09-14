# -*- coding: utf-8 -*-
"""THE RENDER FIXTURE MUST BE ABLE TO REACH THE BRANCH THE TARGET PHOTOGRAPHS.

⚠⚠ THIS LAW EXISTS BECAUSE A GREEN PRODUCT AND A RED GATE DISAGREED, AND THE GATE WAS WRONG.
`shelf-cards` refused for six versions with *"never matched a painted element in 20s — either the
surface is genuinely absent, or this machine was too loaded to build it"*. It was neither. The
sandbox was booted and asked directly:

    /api/sessions -> 357 rows
    footageState  -> {'unknown': 357}          every single one
    footageN      -> {'reeln=0': 357}          every single one
    would render a card -> 0 of 357

Since v3092 the shelf's card builder routes a film-less run OUT of the grid and into the history
chips, which is precisely what Konyo asked for — *"make sure those no footage end up tombstoned and
then deleted also visually and ends up HISTORY"*. `control_app._reeln` counts `f_*.jpg` under
`<TV_HIST>/reel_<sessionId>/`, and `_serve_console` points TV_HIST at a deliberately EMPTY frames
dir because `tv/frames/hist` is 5.6 GB and copying it is an ENOSPC incident this repo has already
paid for. So the two correct decisions met and produced a world in which the card branch is
UNREACHABLE — and the target read that as a defect in the product. A cross-family LOOK at his live
console the same night (#180, 2026-09-14) counted 17 cards / 12 visible, so the pixels were fine
the whole time.

[[gate-blind-to-unexercised-input]] — "a gate is blind to what his data never exercises". This is
its mirror image and it is worse: a fixture that can no longer exercise the branch does not go
quietly green, it goes LOUDLY RED at the product, and someone eventually blesses over it. I refused
to do that; this law is what replaces the refusal with a check.

⚠ WHAT IT PINS, AND WHY EACH HALF IS HERE
  1. the seed actually writes film in the shape control_app COUNTS — not "a file exists somewhere"
  2. it seeds the NEWEST runs, because the grid is newest-first and a card nobody scrolls to is a
     card the fold defect cannot be measured against
  3. the still is real JPEG bytes, not an empty file that would make `_reeln` count a broken image
  4. the JOIN is pinned from the OTHER side: control_app's own counting predicate is parsed, so
     renaming `f_` or `reel_` fails HERE instead of silently emptying the grid again
     [[the-unjoined-end]] [[source-reading-guard]]
  5. the blessed floor stays arithmetically reachable — at least 2 nodes per seeded run, because
     `.shc-hero` and `.shc-sess` are unconditional in the builder while `.shc-area` is not

⚠ AND IT MAY NEVER TOUCH HIS TREE. The seed is asserted to write only inside the directories it is
handed. [[feedback-fixtures-never-touch-live-data]]
"""
import ast
import base64
import io
import json
import os
import shutil
import tempfile
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)
import render_check as rc                                          # noqa: E402


def _world(n_sessions=40):
    """A throwaway sandbox with `n_sessions` distinct runs, newest last."""
    sand = tempfile.mkdtemp(prefix="seedfilm-")
    hist = os.path.join(sand, "frames", "hist")
    os.makedirs(hist, exist_ok=True)
    with io.open(os.path.join(sand, "sessions.jsonl"), "w", encoding="utf-8") as fh:
        for i in range(n_sessions):
            fh.write(json.dumps({"sessionId": "s_fixture_%03d" % i, "ts": 1700000000000 + i,
                                 "scene": "gameplay"}) + "\n")
            # a second row for the same run — the seed must DE-DUPE, not seed it twice
            fh.write(json.dumps({"sessionId": "s_fixture_%03d" % i, "ts": 1700000000001 + i,
                                 "scene": "gameplay"}) + "\n")
    return sand, hist


class TestTheRenderFixtureCanReachTheCardBranch(unittest.TestCase):

    def setUp(self):
        self.sand, self.hist = _world()
        self.addCleanup(shutil.rmtree, self.sand, True)

    # ── 1. the seed writes film in the shape control_app counts ────────────────────────────────
    def test_the_seed_writes_film_the_console_will_count(self):
        filmed, total = rc._seed_film(self.sand, self.hist)
        self.assertEqual(total, 40,
                         "the seed must DE-DUPE by sessionId — 80 rows, 40 runs; it saw %r" % total)
        self.assertEqual(filmed, rc.FILM_RUNS,
                         "seeded %d of a requested %d" % (filmed, rc.FILM_RUNS))
        reels = sorted(d for d in os.listdir(self.hist) if d.startswith("reel_"))
        self.assertEqual(len(reels), rc.FILM_RUNS,
                         "%d reel dir(s) on disk, expected %d" % (len(reels), rc.FILM_RUNS))
        # ⚠ THE PREDICATE, NOT "a file exists". control_app counts `f_*.jpg` and NOTHING else —
        # v947.3 narrowed it on purpose because tab-crop helpers were inflating the shelf by one.
        for d in reels:
            got = [f for f in os.listdir(os.path.join(self.hist, d))
                   if f.startswith("f_") and f.endswith(".jpg")]
            self.assertEqual(len(got), rc.FILM_FRAMES,
                             "%s holds %d counted still(s), expected %d (all files: %r)"
                             % (d, len(got), rc.FILM_FRAMES,
                                sorted(os.listdir(os.path.join(self.hist, d)))))

    # ── 2. the NEWEST runs, because the grid is newest-first ───────────────────────────────────
    def test_it_seeds_the_newest_runs_not_the_oldest(self):
        rc._seed_film(self.sand, self.hist)
        seeded = sorted(d[len("reel_"):] for d in os.listdir(self.hist) if d.startswith("reel_"))
        want = sorted("s_fixture_%03d" % i for i in range(40 - rc.FILM_RUNS, 40))
        self.assertEqual(seeded, want,
                         "seeded the wrong slice — a card at the bottom of a 4,120px scroller is "
                         "not the card the fold defect is measured against")

    # ── 3. real JPEG bytes, not an empty file ──────────────────────────────────────────────────
    def test_the_still_is_real_jpeg_bytes(self):
        raw = base64.b64decode(rc._FILM_STILL_B64)
        self.assertGreater(len(raw), 100, "the embedded still is %d bytes" % len(raw))
        self.assertEqual(raw[:2], b"\xff\xd8", "no JPEG SOI marker — %r" % raw[:8])
        self.assertEqual(raw[-2:], b"\xff\xd9", "no JPEG EOI marker — %r" % raw[-8:])
        rc._seed_film(self.sand, self.hist)
        d = next(x for x in os.listdir(self.hist) if x.startswith("reel_"))
        f = next(x for x in os.listdir(os.path.join(self.hist, d)) if x.startswith("f_"))
        self.assertEqual(os.path.getsize(os.path.join(self.hist, d, f)), len(raw))

    # ── 4. the join, pinned from control_app's side, by PARSE ──────────────────────────────────
    def test_control_app_still_counts_this_shape(self):
        """The ONE region that computes `_reeln` must still join reel_<sid> and count f_*.jpg.

        ⚠ A FIRST CUT OF THIS COUNTED BOTH SHAPES ANYWHERE IN THE FILE and printed
        `join 14 site(s) · predicate 11 site(s)`. An `assertGreaterEqual(.., 1)` over fourteen
        sites cannot fail for the thing it is about — rename the one site that feeds `_reeln` and
        thirteen unrelated ones keep it green. [[sabotage-is-usually-the-wrong-one]]
        So it is anchored to the SMALLEST subtree that computes `_reeln` at all.
        """
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        def _assigns_reeln(n):
            for x in ast.walk(n):
                if (isinstance(x, ast.Assign) and len(x.targets) == 1
                        and isinstance(x.targets[0], ast.Name) and x.targets[0].id == "_reeln"
                        and isinstance(x.value, ast.Call)
                        and isinstance(x.value.func, ast.Name) and x.value.func.id == "len"):
                    return True
            return False

        def _joins_reel(n):
            for x in ast.walk(n):
                if (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                        and x.func.attr == "join"):
                    for a2 in x.args:
                        if (isinstance(a2, ast.BinOp) and isinstance(a2.op, ast.Add)
                                and isinstance(a2.left, ast.Constant) and a2.left.value == "reel_"):
                            return True
            return False

        def _counts_stills(n):
            for x in ast.walk(n):
                if isinstance(x, ast.BoolOp) and isinstance(x.op, ast.And):
                    seen = set()
                    for v in x.values:
                        if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                                and len(v.args) == 1 and isinstance(v.args[0], ast.Constant)):
                            seen.add((v.func.attr, v.args[0].value))
                    if ("startswith", "f_") in seen and ("endswith", ".jpg") in seen:
                        return True
            return False

        regions = [n for n in ast.walk(tree)
                   if getattr(n, "lineno", None) and getattr(n, "end_lineno", None)
                   and _assigns_reeln(n)]
        self.assertTrue(regions, "nothing in control_app.py computes `_reeln` from a len() any "
                                 "more — the shelf no longer counts film, and this seed feeds "
                                 "nothing")
        whole = [n for n in regions if _joins_reel(n) and _counts_stills(n)]
        # ⚠ PRINT THE MATCH COUNTS — a green sabotage is meaningless without them, and "11
        # regions assign _reeln" is 11 NESTED ancestors of one assignment, not 11 places.
        print("   _reeln assigned inside %d nested region(s); %d of them also join reel_<sid> AND "
              "count f_*.jpg%s"
              % (len(regions), len(whole),
                 (" — tightest control_app.py:%d-%d"
                  % (min(whole, key=lambda n: n.end_lineno - n.lineno).lineno,
                     min(whole, key=lambda n: n.end_lineno - n.lineno).end_lineno)) if whole else ""))
        self.assertTrue(
            whole,
            "no region of control_app.py computes `_reeln` while ALSO joining reel_<sessionId> "
            "and counting f_*.jpg — the three halves of the lookup this seed feeds have come "
            "apart, so the seed writes film nothing will count")
        tightest = min(whole, key=lambda n: n.end_lineno - n.lineno)
        self.assertLess(tightest.end_lineno - tightest.lineno, 120,
                        "the tightest region holding all three spans %d lines, which is too loose "
                        "to be about this lookup — the anchor has drifted"
                        % (tightest.end_lineno - tightest.lineno))

    # ── 5. the seed stays inside the dirs it was handed ────────────────────────────────────────
    def test_the_seed_writes_nowhere_else(self):
        before = os.path.getmtime(os.path.join(self.sand, "sessions.jsonl"))
        sz = os.path.getsize(os.path.join(self.sand, "sessions.jsonl"))
        live = os.path.join(HERE, "frames", "hist")
        live_before = sorted(os.listdir(live)) if os.path.isdir(live) else None
        rc._seed_film(self.sand, self.hist)
        self.assertEqual(os.path.getmtime(os.path.join(self.sand, "sessions.jsonl")), before)
        self.assertEqual(os.path.getsize(os.path.join(self.sand, "sessions.jsonl")), sz)
        top = sorted(os.listdir(self.sand))
        self.assertEqual(top, ["frames", "sessions.jsonl"],
                         "the seed created something beside the two it was handed: %r" % top)
        if live_before is not None:
            self.assertEqual(sorted(os.listdir(live)), live_before,
                             "the seed reached HIS frames dir")

    # ── 6. the blessed floor stays arithmetically reachable ────────────────────────────────────
    def test_the_blessed_floor_matches_what_this_world_can_paint(self):
        with io.open(os.path.join(HERE, "render_coverage.json"), encoding="utf-8") as fh:
            floor = (json.load(fh) or {}).get("floor") or {}
        shelf = floor.get("shelf-cards") or {}
        self.assertTrue(shelf, "shelf-cards has no floor at all, so a drop to zero reads as clean")
        # `.shc-hero` and `.shc-sess` are unconditional per card in the builder; `.shc-area` is
        # guarded by `(sm.areas || []).length`. So 2 x cards is the part that is STRUCTURAL.
        low = 2 * rc.FILM_RUNS
        for width, n in sorted(shelf.items()):
            print("   floor shelf-cards %-10s = %-4d (structural minimum %d)" % (width, n, low))
            self.assertGreaterEqual(
                n, low,
                "%s floor is %d, below the %d nodes %d seeded run(s) always paint — a floor under "
                "the structural minimum cannot notice the grid emptying" % (width, n, low, rc.FILM_RUNS))
            self.assertLessEqual(
                n, 3 * rc.FILM_RUNS + 4,
                "%s floor is %d, above the %d nodes %d seeded run(s) can paint even with every "
                "optional line present — it can never be met, which is a permanently red gate"
                % (width, n, 3 * rc.FILM_RUNS + 4, rc.FILM_RUNS))


RED_PROOF = [
    {
        "why": "the seed creates the reel directories but writes no stills, so `_reeln` counts 0, "
               "every run stays film-less, and the shelf grid is empty again while the target "
               "reports the PRODUCT as broken",
        "file": "render_check.py",
        "find": '                with open(os.path.join(rd, "f_%04d.jpg" % k), "wb") as fh2:\n'
                '                    fh2.write(still)',
        "replace": '                with open(os.path.join(rd, "f_%04d.jpg" % k), "wb") as fh2:\n'
                   '                    pass',
        "matches": 1,
    },
    {
        "why": "the seed films the OLDEST runs instead of the newest, so every seeded card sits at "
               "the bottom of a 4,000px scroller and the fold defect this target exists to catch "
               "is measured against cards nobody would ever reach",
        "file": "render_check.py",
        "find": "    for s in sids[-runs:] if runs else []:",
        "replace": "    for s in sids[:runs] if runs else []:",
        "matches": 1,
    },
    {
        "why": "the still becomes an empty file — the directory and the filename are both right, "
               "so every existence check still passes while the console counts a broken image",
        "file": "render_check.py",
        "find": '    still = base64.b64decode(_FILM_STILL_B64)',
        "replace": '    still = b""',
        "matches": 1,
    },
    {
        "why": "the blessed floor is put back above what this world can paint, which is the "
               "permanently-red gate that started all of this",
        "file": "render_coverage.json",
        "find": '  "shelf-cards": {\n   "1120x628": 48,',
        "replace": '  "shelf-cards": {\n   "1120x628": 441,',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
