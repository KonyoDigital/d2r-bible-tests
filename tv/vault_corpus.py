#!/usr/bin/env python3
"""What ownership footage does he ACTUALLY have? — the first artifact of the Vault Manager project.

    python3 tv/vault_corpus.py            # index the reels the sweeps walk
    python3 tv/vault_corpus.py --loose    # index the loose frames in frames/hist too

WHY THIS EXISTS, AND WHY IT IS FIRST. His brief asks the readers to log his inventory, his equipment
and his stash, verify across 3+ sessions that nothing moved, and render it back 1:1. None of that is
buildable until one question is answered with a number: HOW MANY FRAMES OF EACH SURFACE DOES HE
HAVE, AND WHICH TAB IS EACH ONE ON. Every previous attempt at this lane was argued rather than
measured, and REG-185 ("0 of 17 reels declare an ownership surface") was read for months as "there
is no stash footage" when it only ever said "no reel DECLARED one".

MEASURED THE FIRST TIME THIS RAN, 2026-08-21:

    frames/hist ROOT (loose)      883 frames   —  12 stash+inventory,  8 with a readable tab
    the 27 REELS the sweeps walk 1970 frames   — 112 stash+inventory, 151 with a readable tab

    ...and the two sets share ZERO filenames. They are separate archives, and every stash measurement
    before this file — the 68-frame corpus, the gem calibration, stash_grid_truth.json — was taken on
    the LOOSE half, which no sweep has ever walked.

TWO SIGNALS, BOTH STRUCTURAL, NEITHER A MODEL CALL:
  · the INVENTORY title — gold text on stone in a fixed band, scored as a FRACTION so a fire-lit
    screen (0.2355) and a menu (0.0071) fall outside the tight window the real title occupies.
    ⚠ Gold alone is not enough and the window is the whole trick: the lobby, the in-game menu and
    the Chronicle panel all print gold titles, and all six candidates I opened in the 0.002-0.01
    band were one of those three. Only the tight cluster is the panel.
  · the ACTIVE-TAB GEM (v1912) — which stash tab is selected, 12/12 on the labelled corpus.

It reads nothing but pixels, spends no vision, and writes one index file.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

# A GOLD PANEL TITLE, in the band where D2R draws one — measured off his own "both panels open"
# frame (6_1784984233446).
#
# ⚠ v1925 — IT IS NOT THE *INVENTORY* TITLE, and calling it that was a label outliving its referent.
# The test is "gold-on-stone lettering in this band", which is equally true of the CHRONICLE panel:
# spot-checking the frames this admits turned up a Holy Grail page with First Found dates and a 63%
# completion bar, correctly reporting panel=True. `scan()` has always been honest about this — it
# returns `panel` beside `tab`, and `panel` means A TITLED PANEL IS OPEN — but the name above
# invited every reader to take it for an inventory detector.
#
# If you need "is this the inventory", ask `inventory_lattice()`: it requires a 10x4 grid of square
# cells and refuses everything else, including the game-creation lobby menu that this band cannot
# tell from a panel. [[label-outlived-referent]]
TITLE_BAND = (0.56, 0.125, 0.80, 0.165)
# The window the real title occupies. Below it: no panel. Above it: another gold thing.
#
# ⚠ v1925 — THE LOWER BOUND WAS RESOLUTION-DEPENDENT AND ADMITTED NOTHING ON HIS LARGER FRAMES.
# The original 0.0006 was measured on a single 2560x1665 frame, which scores 0.00079 and sits
# comfortably inside it. His reel records at 2940x1912, and there the SAME panel scores 0.00024 —
# because the band is a FRACTION of the frame while D2R draws the title at a near-fixed pixel size,
# so a bigger window means the same lettering covers proportionally less of the band.
#
# Measured across all 153 frames of reel_s_1784984019250_95276, classed by inventory_lattice (an
# independent oracle — it never consults the title):
#
#     shipped  0.00060-0.00120 -> inventory  0/94   non-inventory 0/59   <- ADMITS NOTHING
#     now      0.00008-0.00120 -> inventory 94/94   non-inventory 0/59
#
# The upper bound was always right; only the floor was wrong. The classes separate with a wide gap
# (inventory 0.00013-0.00024 and 0.00079; everything else 0.0-0.00004 or 0.00175-0.00291), so this
# is a window with real margin rather than a constant tuned until the answer came out.
#
# A gate that admits nothing is the same defect as one that admits everything: it has stopped
# carrying information, and nothing said so because nobody compared the two classes.
# [[feedback-blind-fixture-green-gate]] [[feedback-threshold-above-the-ceiling]]
TITLE_MIN, TITLE_MAX = 0.00008, 0.0012
OUT = os.path.join(HERE, "vault_corpus_index.json")


def title_score(path):
    """Fraction of the title band that is D2R's gold-on-stone lettering. None if unreadable."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
    except Exception:
        return None
    w, h = im.size
    if w < 200 or h < 200:
        return None
    c = im.crop((int(w * TITLE_BAND[0]), int(h * TITLE_BAND[1]),
                 int(w * TITLE_BAND[2]), int(h * TITLE_BAND[3])))
    px = c.load()
    W, H = c.size
    n = 0
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if r > 150 and g > 110 and b < 110 and (r - b) > 60 and (r - g) < 90:
                n += 1
    return n / float(W * H or 1)


def scan(paths):
    """-> rows of {frame, reel, title, panel, tab}. Pure; no writes, no model calls."""
    import stash_eye as se
    rows = []
    for reel, p in paths:
        s = title_score(p)
        if s is None:
            continue
        tab, _d = se.tab_from_gem(p)
        panel = bool(TITLE_MIN < s < TITLE_MAX)
        if panel or tab:
            rows.append({"reel": reel, "frame": os.path.basename(p),
                         "title": round(s, 4), "panel": panel, "tab": tab or None})
    return rows


def _paths(hist, loose=False):
    import glob
    out = []
    for d in sorted(glob.glob(os.path.join(hist, "reel_*"))):
        for p in sorted(glob.glob(os.path.join(d, "*.jpg"))):
            out.append((os.path.basename(d), p))
    if loose:
        for p in sorted(glob.glob(os.path.join(hist, "*.jpg"))):
            out.append(("(loose)", p))
    return out


def main(argv=None):
    import collections
    import time
    argv = list(argv if argv is not None else sys.argv[1:])
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    paths = _paths(hist, loose=("--loose" in argv))
    if not paths:
        print("⚠ no frames under %s — nothing to index, which is not the same as nothing to find"
              % hist)
        return 2
    print("scanning %d frame(s) under %s …" % (len(paths), hist))
    t0 = time.time()
    rows = scan(paths)
    by_reel = collections.Counter(r["reel"] for r in rows if r["tab"])
    tabs = collections.Counter(r["tab"] for r in rows if r["tab"])
    panels = sum(1 for r in rows if r["panel"])
    print("\n%d frame(s) carry ownership evidence, in %.0fs" % (len(rows), time.time() - t0))
    print("  stash+inventory template (both panels open): %d" % panels)
    print("  a READABLE stash tab (the active-tab gem):   %d" % sum(tabs.values()))
    print("\n  by tab:  %s" % (dict(tabs) or "none"))
    print("  ⚠ a tab with no frames cannot be verified, simulated or debugged — say so rather than "
          "letting its absence read as 'nothing there'.")
    print("\n  by reel (tab-readable frames):")
    for reel, n in by_reel.most_common(12):
        print("     %-34s %d" % (reel, n))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"hist": hist, "scanned": len(paths), "rows": rows,
                   "totals": {"withEvidence": len(rows), "panels": panels,
                              "tabReadable": sum(tabs.values()), "byTab": dict(tabs)}},
                  fh, indent=1)
    print("\nwrote %s" % os.path.relpath(OUT, os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── THE INVENTORY LATTICE ───────────────────────────────────────────────────────────────────────
# Solved 2026-08-21 after five attempts aimed at the wrong panel. Full record in
# PROJECT_VAULT_MANAGER.md; the short version, because the refusals below only make sense with it:
#
#   * The GEMS tab has NO cell borders. Five attempts hunted vertical dividers in a panel that has
#     none — and it is out of scope by his own words ("gems/runes/materials never move").
#   * The INVENTORY grid does: 10 x 4, pitch 86.75 x 85.75, square cells.
#   * A LATTICE IS REGULAR. Fitting pitch+phase beats picking peaks, because item art has to land on
#     a periodic grid to score and it does not. Every earlier attempt discarded that property.
#   * Borders are found by RIDGE on the per-axis MEDIAN, not brightness: border visibility depends
#     on occupancy (a border around a black empty cell is nearly invisible), so no global threshold
#     exists, and item art is bright at SOME y while a border is bright at EVERY y.
#
# ⚠ THE REFUSALS ARE THE FEATURE. Without them this returned a confident "18 occupied, 9 free" for
# the game-creation LOBBY MENU — a column of checkboxes is periodic, so a lattice fitter finds a
# lattice in it. A periodic grid is a PROXY; the 10x4 square inventory is the thing.
_LAT_LO, _LAT_HI = 70.0, 100.0
INV_CROP = (0.595, 0.495, 0.915, 0.70)   # fractions of the frame
INV_COLS, INV_ROWS = 10, 4               # the D2 inventory is ALWAYS this


def _ridge(v, k=12):
    import numpy as _np
    n = len(v)
    out = _np.zeros(n)
    for i in range(n):
        l = v[max(0, i - k):max(1, i - 2)]
        r = v[min(n - 1, i + 3):min(n, i + k + 1)]
        if len(l) and len(r):
            out[i] = max(0.0, v[i] - max(l.mean(), r.mean()))
    return out


def _fit(v):
    import numpy as _np
    best = None
    n = len(v)
    for pitch in _np.arange(_LAT_LO, _LAT_HI, 0.25):
        for phase in _np.arange(0, pitch, 1.0):
            xs = _np.arange(phase, n, pitch)
            if len(xs) < 4:
                continue
            idx = _np.clip(_np.round(xs).astype(int), 0, n - 1)
            sc = float(v[idx].mean())
            if best is None or sc > best[0]:
                best = (sc, float(pitch), float(phase), idx)
    return best


def inventory_lattice(frame_path):
    """{ok, colPitch, rowPitch, cols, rows} or {ok: False, why} — and it says NO often.

    Each refusal is a real failure seen on his own reel:
      * pitch pinned to a SEARCH BOUND -> the fit found nothing (33 frames)
      * ridge score at the noise floor -> a black loading frame reads exactly like this (7 frames)
      * not exactly 10x4, or cells not square -> the LOBBY MENU (13 frames)
    """
    try:
        import numpy as _np
        from PIL import Image
        im = Image.open(frame_path).convert("L")
    except Exception as e:
        return {"ok": False, "why": "unreadable: %s" % str(e)[:80]}
    W, H = im.size
    if W < 1200 or H < 800:
        return {"ok": False, "why": "frame too small (%dx%d) to hold the panel" % (W, H)}
    g = _np.asarray(im.crop((int(INV_CROP[0] * W), int(INV_CROP[1] * H),
                             int(INV_CROP[2] * W), int(INV_CROP[3] * H))), dtype=_np.float32)
    sc, cp, _cph, cols = _fit(_ridge(_np.median(g, axis=0)))
    sr, rp, _rph, rows = _fit(_ridge(_np.median(g, axis=1)))
    for nm, pitch, score in (("columns", cp, sc), ("rows", rp, sr)):
        if abs(pitch - _LAT_LO) < 0.3 or abs(pitch - (_LAT_HI - 0.25)) < 0.3:
            return {"ok": False, "why": "%s pitch pinned to the search bound (%.2f) — the fit found "
                                        "nothing, which is not a narrow grid" % (nm, pitch)}
        if score < 3.0:
            return {"ok": False, "why": "%s ridge score %.2f is at the noise floor — no lattice "
                                        "here" % (nm, score)}
    nc, nr = len(cols) - 1, len(rows) - 1
    if (nc, nr) != (INV_COLS, INV_ROWS):
        return {"ok": False, "why": "found %dx%d cells; the D2 inventory is ALWAYS %dx%d"
                                    % (nc, nr, INV_COLS, INV_ROWS)}
    if abs(cp - rp) > 4.0:
        return {"ok": False, "why": "cells are not square (%.1f x %.1f) — a menu fits a lattice "
                                    "too, and this is how it is told apart" % (cp, rp)}
    return {"ok": True, "colPitch": cp, "rowPitch": rp,
            "cols": [int(x) for x in cols], "rows": [int(y) for y in rows],
            "cells": nc * nr, "crop": INV_CROP}


def inventory_occupancy(frame_path, lat=None):
    """{ok, occupied, free, grid} — free inventory space, the number the vault manager needs.

    An EMPTY cell is uniformly near-black (mean 4.3, std 0.6-1.0); an occupied one is 31-169 with
    std 20-78. The gap is enormous and three separate threshold pairs return the identical answer,
    which is what a real bimodal signal looks like and what a tuned constant never does.

    ⚠ The obvious feature was WRONG: occupied cells sit on a blue background, but the ITEM ART
    covers it — a grey cube, an orange torch and silver coins all score negative on blue-minus-red.
    Hue found 4 of 22.

    ⚠ ONE FRAME IS A FIXTURE. A tooltip drawn over the panel makes an empty cell read as occupied
    (measured: one frame of 94 said 23/17 instead of 22/18). A per-frame occlusion detector was
    tried and rejected — divider continuity gives 0.477 clean vs 0.452 occluded, a threshold rather
    than a separation. Use `inventory_reading()` over a reel instead; his own 3+-witness rule is the
    occlusion detector.
    """
    try:
        import numpy as _np
        from PIL import Image
        im = Image.open(frame_path).convert("L")
    except Exception as e:
        return {"ok": False, "why": "unreadable: %s" % str(e)[:80]}
    r = lat or inventory_lattice(frame_path)
    if not r.get("ok"):
        return {"ok": False, "why": r.get("why")}
    W, H = im.size
    g = _np.asarray(im.crop((int(INV_CROP[0] * W), int(INV_CROP[1] * H),
                             int(INV_CROP[2] * W), int(INV_CROP[3] * H))), dtype=_np.float32)
    cols, rows = r["cols"], r["rows"]
    grid, occ, free = [], 0, 0
    for i in range(len(rows) - 1):
        line = []
        for j in range(len(cols) - 1):
            cell = g[rows[i] + 12:rows[i + 1] - 12, cols[j] + 12:cols[j + 1] - 12]
            if cell.size == 0:
                line.append(None)
                continue
            taken = bool(cell.mean() > 20 or cell.std() > 15)
            line.append(taken)
            if taken:
                occ += 1
            else:
                free += 1
        grid.append(line)
    return {"ok": True, "occupied": occ, "free": free, "cells": occ + free, "grid": grid}


def inventory_reading(frame_paths):
    """The MODAL reading across many frames, with the count that agreed.

    93 of 94 is evidence. 1 of 1 is a fixture, and this project has already paid for believing one.
    A minority reading is reported rather than dropped, because it is either a contaminated frame or
    the first sign of an edge case, and those look identical until someone opens it.
    """
    from collections import Counter
    seen, refused = [], 0
    for p in (frame_paths or []):
        o = inventory_occupancy(p)
        if o.get("ok"):
            seen.append((o["occupied"], o["free"]))
        else:
            refused += 1
    if not seen:
        return {"ok": None, "read": 0, "refused": refused,
                "say": "no frame held a readable inventory panel — which is not the same as an "
                       "empty inventory"}
    c = Counter(seen).most_common()
    (occ, free), n = c[0]
    out = {"ok": True, "occupied": occ, "free": free, "agreed": n, "read": len(seen),
           "refused": refused, "minority": [{"occupied": a, "free": b, "frames": k}
                                            for (a, b), k in c[1:]]}
    out["say"] = ("%d free of %d, agreed by %d of %d readable frame(s)%s"
                  % (free, occ + free, n, len(seen),
                     "" if len(c) == 1 else "; %d frame(s) disagreed and are listed rather than "
                                            "averaged away" % sum(k for _, k in c[1:])))
    return out
