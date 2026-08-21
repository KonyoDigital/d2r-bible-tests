#!/usr/bin/env python3
"""THE GAME PRINTS ITS OWN ANSWER, AND NOTHING HAS EVER READ IT.

    python3 tv/chronicle_calibrate.py <reel>        # what the game says, vs what the board says

Konyo, 2026-08-21: "and sets.. are you sure its 118/135 how is it 87%? ingame im 85% somewthing isnt
calliberated properly to the ingame with the console.." — and then the harder question:
"the AI READERS needs to be doing this automatically... like where is the AI intelligence and AI
coder that routes and funnels and watchdog even for a safegaurd of this?"

He is right that it was missing. Every Chronicle page in the game carries a completion bar and a
printed percentage in the bottom-left of the category column. The readers have been photographing
that panel for months and NOTHING has ever compared it to the board's own tally. Two numbers about
the same collection, computed by different routes, and no one put them side by side — which is the
one arrangement that turns a silent drift into a finding. [[feedback-contradiction-is-the-finding]]

WHAT THIS MEASURES, AND HOW HONESTLY
  · the BAR's gold fill as a fraction of its track — structural, no OCR, no model call.
  · ⚠ CALIBRATED TO ABOUT ±1.5 POINTS, NOT BETTER. On his 2026-08-21 sets reel the fill reads
    0.8395 on four separate frames (stable, so the READING is repeatable) while the page's own
    printed digits say 85%. The soft right edge of the fill and the track's end-cap are worth about
    a point. So this is a WATCHDOG, not a counter: it is built to catch a 3-point disagreement,
    and it must never be quoted as the exact figure. [[unknown-stays-unknown]]

WHAT SETTLED THE ARITHMETIC ON 2026-08-21, and it was HIS two sentences, not this file:
    "this is exactly 19 i still have missing"  +  "meaning i have 116/135"
    116 + 19 = 135  ✓  and 116/135 = 85.9%, which the game truncates to the 85% on the page.
So the DENOMINATOR is right and the board's 118 was two too many. A watchdog that had been running
would have said so the first time the gap opened.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

# The completion bar's band, measured off his own Chronicle frames (2940x1912).
BAR_BAND = (0.10, 0.63, 0.40, 0.74)
TOLERANCE = 0.03          # 3 points. Below the gap that matters, above this reader's own error.


def bar_fill(path):
    """The game's own completion, as a fraction. None when no bar is on the frame.

    Refuses rather than guesses: too little gold is not a bar, and a bar with no dark track to its
    right has no measurable end.
    """
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
    except Exception:
        return None
    w, h = im.size
    if w < 200 or h < 200:
        return None
    c = im.crop((int(w * BAR_BAND[0]), int(h * BAR_BAND[1]),
                 int(w * BAR_BAND[2]), int(h * BAR_BAND[3])))
    W, H = c.size
    px = c.load()

    def is_gold(p):
        r, g, b = p
        return r > 120 and g > 105 and b < 130 and (r - b) > 35

    best_y, best_n = None, 0
    for y in range(H):
        n = sum(1 for x in range(W) if is_gold(px[x, y]))
        if n > best_n:
            best_y, best_n = y, n
    if best_y is None or best_n < 20:
        return None
    gold = [x for x in range(W) if is_gold(px[x, best_y])]
    x0, xg = gold[0], gold[-1]
    x1 = xg
    while x1 + 1 < W:
        r, g, b = px[x1 + 1, best_y]
        if r < 90 and g < 90 and b < 90:
            x1 += 1
        else:
            break
    if x1 <= x0:
        return None
    return (xg - x0 + 1) / float(x1 - x0 + 1)


def read_reel(reel_dir, sample=6):
    """-> the median fill across a sample of a reel's frames, and how many frames carried a bar."""
    import statistics
    idx = os.path.join(reel_dir, "index.json")
    try:
        with open(idx, encoding="utf-8") as fh:
            frames = [f.get("f") for f in (json.load(fh).get("frames") or []) if f.get("f")]
    except Exception:
        frames = sorted(f for f in os.listdir(reel_dir) if f.endswith(".jpg"))
    if not frames:
        return None, 0
    step = max(1, len(frames) // max(1, sample))
    fills = []
    for f in frames[::step]:
        v = bar_fill(os.path.join(reel_dir, f))
        if v is not None:
            fills.append(v)
    if not fills:
        return None, 0
    return statistics.median(fills), len(fills)


def verdict(game_fill, board_found, board_total):
    """The whole point: put the two numbers side by side and say when they disagree."""
    if game_fill is None:
        return {"ok": None, "say": "no completion bar on any sampled frame — the game said nothing, "
                                   "which is not the same as agreeing"}
    if not board_total:
        return {"ok": None, "say": "the board reported no total — nothing to compare against"}
    board = board_found / float(board_total)
    gap = board - game_fill
    out = {"gameFill": round(game_fill, 4), "boardPct": round(board, 4), "gap": round(gap, 4),
           "impliedFound": int(round(game_fill * board_total))}
    if abs(gap) <= TOLERANCE:
        out["ok"] = True
        out["say"] = ("the board and the game agree within %.0f points (board %.1f%%, game ~%.1f%%)"
                      % (TOLERANCE * 100, board * 100, game_fill * 100))
    else:
        out["ok"] = False
        out["say"] = ("⚠ THE BOARD AND THE GAME DISAGREE: the board says %d/%d = %.1f%%, the game's "
                      "own bar reads about %.1f%%. At the board's own total that is roughly %d "
                      "found, %d fewer than the board counts. One of the two is wrong and the game "
                      "is the one holding the items."
                      % (board_found, board_total, board * 100, game_fill * 100,
                         out["impliedFound"], board_found - out["impliedFound"]))
    return out


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    if argv and not argv[0].startswith("-"):
        reels = [argv[0] if os.path.isdir(argv[0]) else os.path.join(hist, argv[0])]
    else:
        import glob
        reels = sorted(glob.glob(os.path.join(hist, "reel_*")),
                       key=lambda p: os.path.getmtime(p), reverse=True)[:1]
    if not reels or not os.path.isdir(reels[0]):
        print("⚠ no reel to read — say which one: python3 tv/chronicle_calibrate.py <reel>")
        return 2
    d = reels[0]
    fill, n = read_reel(d)
    print("reel: %s" % os.path.basename(d))
    if fill is None:
        print("  no completion bar found on any sampled frame.")
        print("  ⚠ That is NOT 'the board is fine' — it is 'the game was not asked'.")
        return 0
    print("  the game's own completion bar reads about %.1f%%   (median of %d frame(s))"
          % (fill * 100, n))
    print("  ⚠ this reader is good to about ±1.5 points — a watchdog, never a counter")
    print()
    print("  to compare, pass the board's numbers:  --board FOUND TOTAL")
    if "--board" in argv:
        i = argv.index("--board")
        try:
            found, total = int(argv[i + 1]), int(argv[i + 2])
        except Exception:
            print("  --board needs two integers")
            return 2
        v = verdict(fill, found, total)
        print()
        print("  %s" % v["say"])
        return 0 if v.get("ok") is not False else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
