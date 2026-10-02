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

    # ── FREE INVENTORY SPACE, per reel ────────────────────────────────────────────────────────
    # v1928 — THE JOIN. inventory_lattice / inventory_occupancy / inventory_reading were built and
    # guarded and NOTHING CALLED THEM, which is the defect this whole night has been about: a
    # mechanism that reads as protection and carries nothing. This is the tap.
    #
    # Only frames the title scan already called a PANEL are offered, and only a handful per reel:
    # the lattice fit is the expensive part, and inventory_reading needs corroboration rather than
    # volume. It reports how many frames AGREED, because 93 of 94 is evidence and 1 of 1 is a
    # fixture — this project has already paid for believing one frame.
    inv_rows = {}
    by_reel_panels = collections.defaultdict(list)
    for r in rows:
        if r.get("panel"):
            by_reel_panels[r["reel"]].append(os.path.join(hist, r["reel"], r["frame"]))
    if by_reel_panels:
        print("\n  free inventory space (10x4 grid; %d frame(s) sampled per reel):" % INV_SAMPLE)
        for reel in sorted(by_reel_panels):
            fs = [p for p in by_reel_panels[reel][:INV_SAMPLE] if os.path.isfile(p)]
            if not fs:
                continue
            rd = inventory_reading(fs)
            inv_rows[reel] = rd
            if rd.get("ok"):
                print("     %-34s %2d free of %d  (%d of %d frame(s) agreed%s)"
                      % (reel, rd["free"], rd["occupied"] + rd["free"], rd["agreed"], rd["read"],
                         "" if not rd["minority"] else "; %d disagreed"
                         % sum(m["frames"] for m in rd["minority"])))
            else:
                # A REFUSAL IS A RESULT. "no frame held a readable inventory panel" and "his
                # inventory is empty" are opposite facts and must never print the same.
                print("     %-34s %s" % (reel, rd.get("say", "no reading")))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"hist": hist, "scanned": len(paths), "rows": rows,
                   "inventory": inv_rows,
                   "totals": {"withEvidence": len(rows), "panels": panels,
                              "tabReadable": sum(tabs.values()), "byTab": dict(tabs)}},
                  fh, indent=1)
    print("\nwrote %s" % os.path.relpath(OUT, os.path.dirname(HERE)))
    return 0

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

# ⚠⚠ v3539 REG-1648 — EVERY PIXEL CONSTANT IN THIS LATTICE WAS MEASURED AT ONE FRAME HEIGHT, AND HIS
# CAPTURE CHANGED HEIGHT. The crop above is in FRACTIONS of the frame; the pitch search (70-100), the
# ridge window (12), the square tolerance (4) and the occupancy inset (12) are PIXELS, all taken from
# his 2940x1912 Retina reel. From reel_s_1788087297344 (2026-08-31) on, his Mac records 1440x936 and
# 1440x904, where a cell is ~42 px: the rows crop is 192 px tall, no pitch >= 70 fits four rows into
# it, and the fit returned None on EVERY frame - "no grid is visible here" over a plain 10x4 grid.
#     MEASURED 2026-10-01, the panel frames of every reel on his Mac:
#         2940x1912  1 reel    lattice ok 12 of 12 sampled
#         1440x936   7 reels   lattice ok  0 of 64 sampled
#         1440x904   1 reel    lattice ok  0 of 12 sampled
# So the vault's free cross-check had been blind on all new footage for a month: no read frame was
# ever reconciled, no seal could be definitive, and the vault lane re-read two of his reels on every
# relaunch with no possible way to finish them (REG-1647).
# D2R draws its UI in proportion to the frame HEIGHT, not its width - the row pitch measured 85.75
# @1912, 42.0 @936 and 40.5 @904, which is 85.75 x H/1912 each time, while 1440 wide is the same at
# both heights. So every pixel constant scales by H / _CAL_H; at 1912 it is exactly the constant it
# was, and every refusal below is kept: a menu still has to be 10x4 SQUARE cells at the scaled pitch.
# ⚠ Widening the search instead of scaling it is WRONG and was measured: on a 1440 frame an open
# 20-110 search locks onto the 2x column harmonic (84.5 / 81.75) - a lattice of every other border.
# [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
_CAL_H = 1912.0                          # the frame height every pixel constant here was measured at


def _ui_scale(h):
    """Pixels-per-calibration-pixel for a frame of height `h`. -> float (1.0 at his 2940x1912 reel)"""
    return float(h) / _CAL_H

# ── v2016 — WHY THERE IS NO STASH LATTICE, AND WHY WIDENING THE CROP WILL NOT MAKE ONE ─────────
# The obvious next feature is "do the same for the stash" — it holds far more than the inventory, and
# vault_doctor reports 220 occupied cells with zero names on his film. It was attempted 2026-08-23 and
# the attempt is recorded here because the obvious method is GUARANTEED to produce a confident wrong
# answer.
#
# WHAT IS REAL: the stash region genuinely has a grid. Measured on the left side of his own frames,
# _fit(_ridge(median)) returns pitch 86.8 x 87.0 — IDENTICAL to the inventory's 86.8 x 85.8 on the
# same frame, with ridge scores 26-38 against a 3.0 noise floor. That is D2R's cell size and it is
# not a coincidence.
#
# WHAT IS NOT: this fitter cannot find where a grid ENDS. `_fit` does not detect ridges — it
# GENERATES them: `xs = arange(phase, n, pitch)` lays evenly-spaced samples across the WHOLE crop and
# keeps the best-scoring pitch/phase. So the returned positions are evenly spaced by construction,
# and the cell COUNT is simply crop_width / pitch. Measured: the same frame yields 13x12, 11x9 or 9x9
# purely by moving the crop, and a "longest evenly-spaced run" check returns the total every time —
# it measures the instrument, not the panel.
#
# WHY THE INVENTORY WORKS ANYWAY: because 10x4 is KNOWN and ENFORCED. The refusal above —
# `if (nc, nr) != (INV_COLS, INV_ROWS)` — is doing the real work; the fit only has to agree. That is
# also what turns the LOBBY MENU away, and the comment above says so.
#
# SO A STASH LATTICE NEEDS GROUND TRUTH THIS REPO DOES NOT HAVE. RotW is a mod and nothing here
# records its stash dimensions. Until the panel's own BORDER is detected (a real edge, not a fitted
# pitch), or he states the grid size, any stash occupancy would be a guess dressed as a measurement —
# and it would feed the glimpse and the over-read detector, which exist to catch exactly that.
# [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
INV_SAMPLE = 8                           # frames per reel: corroboration, not volume


def _ridge(v, k=12, a=2, b=3):
    import numpy as _np
    n = len(v)
    out = _np.zeros(n)
    for i in range(n):
        l = v[max(0, i - k):max(1, i - a)]
        r = v[min(n - 1, i + b):min(n, i + k + 1)]
        if len(l) and len(r):
            out[i] = max(0.0, v[i] - max(l.mean(), r.mean()))
    return out


def _fit(v, lo=_LAT_LO, hi=_LAT_HI, phase_step=1.0):
    import numpy as _np
    best = None
    n = len(v)
    for pitch in _np.arange(lo, hi, 0.25):
        for phase in _np.arange(0, pitch, phase_step):
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
    # ⚠⚠ v2799 — `_fit` CAN RETURN None AND BOTH OF THESE UNPACKED IT BLIND.
    # Its only exit is `return best`, and `best` stays None when no candidate pitch clears the
    # scoring. Measured on his live eye.jpg 2026-09-08:
    #     TypeError: cannot unpack non-iterable NoneType object   (vault_corpus.py:300, 0.4s)
    # Every other refusal in this function returns {"ok": False, "why": …} — that is the whole
    # contract of the docstring above ("it says NO often… each refusal is a real failure seen on
    # his own reel"). This one path threw instead, so MINI AUTO's caller reported the generic
    # "reading the frame raised TypeError" and the actual fact — the ridge fit found no grid —
    # never reached him. An exception is not a reason. [[unknown-stays-unknown]]
    # REG-1648 — the pitch search, the ridge window and the phase step in THIS frame's pixels
    _s = _ui_scale(H)
    _lo, _hi = _LAT_LO * _s, _LAT_HI * _s
    _k, _a, _b = max(4, int(round(12 * _s))), max(1, int(round(2 * _s))), max(1, int(round(3 * _s)))
    _ph = 1.0 if _s >= 0.75 else 0.5
    _cands = _np.arange(_lo, _hi, 0.25)
    _rcol, _rrow = _ridge(_np.median(g, axis=0), _k, _a, _b), _ridge(_np.median(g, axis=1), _k, _a, _b)
    _cfit = _fit(_rcol, _lo, _hi, _ph)
    _rfit = _fit(_rrow, _lo, _hi, _ph)
    for _nm, _got in (("columns", _cfit), ("rows", _rfit)):
        if _got is None:
            return {"ok": False,
                    "why": "the %s ridge fit found no candidate pitch at all on this frame — that "
                           "is 'no grid is visible here', not 'the panel is empty'. The usual "
                           "cause is that the container is not open, or the frame caught a "
                           "transition." % _nm}
    sc, cp, _cph, cols = _cfit
    sr, rp, _rph, rows = _rfit
    for nm, pitch, score in (("columns", cp, sc), ("rows", rp, sr)):
        if abs(pitch - _cands[0]) < 0.3 or abs(pitch - _cands[-1]) < 0.3:
            return {"ok": False, "why": "%s pitch pinned to the search bound (%.2f) — the fit found "
                                        "nothing, which is not a narrow grid" % (nm, pitch)}
        if score < 3.0:
            return {"ok": False, "why": "%s ridge score %.2f is at the noise floor — no lattice "
                                        "here" % (nm, score)}
    nc, nr = len(cols) - 1, len(rows) - 1
    if (nc, nr) != (INV_COLS, INV_ROWS) or abs(cp - rp) > 4.0 * _s:
        # REG-1712 — the fit SAW a grid and miscounted it; the calibrated box knows where the grid is
        _cal = _calibrated_lattice(W, H, cp, rp, _s, nc, nr, fit=(cols, rows, _rcol, _rrow))
        if _cal is not None:
            return _cal
    if (nc, nr) != (INV_COLS, INV_ROWS):
        return {"ok": False, "why": "found %dx%d cells; the D2 inventory is ALWAYS %dx%d"
                                    % (nc, nr, INV_COLS, INV_ROWS)}
    if abs(cp - rp) > 4.0 * _s:
        return {"ok": False, "why": "cells are not square (%.1f x %.1f) — a menu fits a lattice "
                                    "too, and this is how it is told apart" % (cp, rp)}
    return {"ok": True, "colPitch": cp, "rowPitch": rp,
            "cols": [int(x) for x in cols], "rows": [int(y) for y in rows],
            "cells": nc * nr, "crop": INV_CROP, "scale": round(_s, 4)}


#: REG-1712 — how much of the fit's own evidence must sit ON the calibrated seams before the calibrated grid is taken.
#: MEASURED 2026-10-02 over 158 frames the loose first cut admitted, each looked at. His 55 real inventories MEASURED:
#: row lines on the calibrated rows >=0.75 (54 of 55), column lines >=0.30, the ridge at the calibrated seams below
#: the ridge half a cell over by <= -0.49 sd (columns) and <= -0.15 sd (rows). The THRESHOLDS below sit inside that
#: range with a margin (0.75 / 0.25 / -0.4 / -0.1), and the result was measured WITH THESE THRESHOLDS: 54 of 55 real
#: accepted, 0 of the 103 others (a webcam, fire, lightning, the Join Game screen, a tooltip, his own console) - their
#: best pitch matched only because the pitch search is a narrow band around this very cell size. (REG-1721: the first
#: wording quoted the measured range as if it were the thresholds - the #231 code seat.)
_CAL_ROW_ALIGN, _CAL_COL_ALIGN, _CAL_COL_SEAM, _CAL_ROW_SEAM = 0.75, 0.25, -0.4, -0.1


def _seams_on_the_grid(cols, rows, rcol, rrow, gc, gr, pc, pr):
    """REG-1712 — do the PIXELS put seams where the calibrated grid says? -> (bool, why)

    Two readings of this frame's own ridges, neither of them the pitch: where the fit's lines fall (phase - the share
    within 0.15 of a cell of a calibrated line) and how the ridge stands at the calibrated seams against half a cell
    over, in units of its own spread."""
    import numpy as _np

    def _align(found, cal, pitch):
        found = [float(x) for x in found]
        return (sum(1 for x in found if min(abs(x - c) for c in cal) <= 0.15 * pitch) / float(len(found))) if found else 0.0

    def _seam(r, cal, pitch):
        r = _np.asarray(r, dtype=float)
        on = [r[int(round(c))] for c in cal if 0 <= int(round(c)) < len(r)]
        off = [r[int(round(c + pitch / 2.0))] for c in cal[:-1] if 0 <= int(round(c + pitch / 2.0)) < len(r)]
        if not on or not off:
            return None
        return (float(_np.mean(on)) - float(_np.mean(off))) / (float(_np.std(r)) + 1e-6)

    ac, ar = _align(cols, gc, pc), _align(rows, gr, pr)
    kc, kr = _seam(rcol, gc, pc), _seam(rrow, gr, pr)
    ok = (ar >= _CAL_ROW_ALIGN and ac >= _CAL_COL_ALIGN and kc is not None and kr is not None
          and kc <= _CAL_COL_SEAM and kr <= _CAL_ROW_SEAM)
    return ok, ("lines on the calibrated grid: rows %.2f, columns %.2f; seam ridge %s / %s sd"
                % (ar, ac, "?" if kc is None else "%.2f" % kc, "?" if kr is None else "%.2f" % kr))


def _calibrated_lattice(W, H, cp, rp, s, nc, nr, fit=None):
    """REG-1712 — THE LINE FIT SAW A GRID AND MISCOUNTED IT; THE CALIBRATED BOX KNOWS WHERE IT IS. -> lattice | None

    MEASURED 2026-10-02 on his full inventory (reel_s_1790869575044_77535, 39 frames, 0 accepted): a 2x2 cube and
    1x3 grand charms cover the seams the ridge fit counts, so it found 9x4 (25 frames) or 11x4 and refused "the D2
    inventory is ALWAYS 10x4" - every cross-check of a FULL inventory refused, the vault seal was never definitive,
    and the reel was retired at PRINTER for good. The grid is not unknown: slot_identity.panel_box_for measured it
    and REG-1712 put it in this frame's pixels (height-scaled, centred - drawn over these frames, on every seam).

    Taken ONLY when the fit itself measured THIS panel's cell size on at least one axis (within the fit's own 4 px
    squareness bar) AND the frame's own ridges put their seams on the calibrated grid (_seams_on_the_grid). A fit that
    found nothing, a noise-floor ridge, a frame of no measured aspect, a grid of some other size, or a frame whose
    seams are not where the inventory's are still refuses."""
    try:
        import slot_identity as _si
        box, _why = _si.panel_box_for(W, H, container="inventory")
    except Exception:
        return None
    if not box:
        return None
    bx, by, bw, bh = box
    pc, pr = bw / float(INV_COLS), bh / float(INV_ROWS)
    tol = 4.0 * s
    if not (abs(cp - pc) <= tol or abs(rp - pr) <= tol):
        return None
    x0, y0 = int(INV_CROP[0] * W), int(INV_CROP[1] * H)
    cw, ch = int(INV_CROP[2] * W) - x0, int(INV_CROP[3] * H) - y0
    cols = [int(round(bx - x0 + i * pc)) for i in range(INV_COLS + 1)]
    rows = [int(round(by - y0 + j * pr)) for j in range(INV_ROWS + 1)]
    if cols[0] < 0 or rows[0] < 0 or cols[-1] > cw or rows[-1] > ch:
        return None
    # ⚠ THE PITCH IS NO EVIDENCE BY ITSELF: the search band sits around this cell size, so ANY frame's best pitch lands
    # near it (the first cut admitted a webcam, a fire and the Join Game screen as full inventories). The pixels must put
    # their seams on this grid - a fit with no evidence to give is refused, never waved through.
    if not fit:
        return None
    _ok, _seen = _seams_on_the_grid(fit[0], fit[1], fit[2], fit[3], cols, rows, pc, pr)
    if not _ok:
        return None
    return {"ok": True, "colPitch": pc, "rowPitch": pr, "cols": cols, "rows": rows, "seams": _seen,
            "cells": INV_COLS * INV_ROWS, "crop": INV_CROP, "scale": round(s, 4), "source": "calibrated",
            "why": ("the line fit counted %dx%d (pitch %.1f x %.1f) - items cover the seams it counts; its pitch "
                    "matches the calibrated inventory's %.1f px cells, so the grid is the calibrated one"
                    % (nc, nr, cp, rp, pc))}


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
    _in = max(3, int(round(12 * _ui_scale(H))))   # REG-1648 — the cell inset in this frame's pixels
    grid, occ, free = [], 0, 0
    for i in range(len(rows) - 1):
        line = []
        for j in range(len(cols) - 1):
            cell = g[rows[i] + _in:rows[i + 1] - _in, cols[j] + _in:cols[j + 1] - _in]
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

# ══════════════════════════════════════════════════════════════════════════════════════════════
# v1995 — THE MAP BEFORE THE NAMES.  Konyo: "like a IROBOT cleaning my house it maps out my house
# and it doesnt necesarily know whats there yet.. so same here i want it to like sort of understand
# the reverse of it and see where we have room."
#
# Everything above answers "what is in this panel". These answer "what SHAPE is this panel", which
# is a different and cheaper question, and it survives having no names at all.
#
# THE THREE KINDS OF CELL, and the distinction is his:
#   FIXED    occupied in essentially every frame — the Horadric Cube, tomes, charms. His words:
#            "the space that isnt locked for the items like hordaic cube and my other tombs and
#            charms.. which again should render this and lock it accordingly like the equipment."
#            Furniture, not loot. Nothing should ever suggest moving it.
#   OPEN     free in essentially every frame — "the grey area that left is space to loot and play
#            with for farming".
#   CHURN    changes between frames — where loot actually flows. This is the interesting set and it
#            is where a stash-from-inventory shows up.
#
# NOTHING HERE NAMES AN ITEM, EVER. It is arithmetic on a boolean grid. That is the point: it works
# on exactly the frames the paid reader has to give up on, and it cannot fabricate.
# ══════════════════════════════════════════════════════════════════════════════════════════════

_MAP_MIN_FRAMES = 3          # 1 frame is a fixture; 2 is a coincidence. His own witness rule.
_STABLE_AT = 0.90            # occupied (or free) in >=90% of readable frames = not churn


def _grids(frame_paths):
    """Occupancy grids that agree on GEOMETRY. A lattice that fit differently describes a different
    panel, and comparing cell (2,3) across two geometries compares two different squares."""
    grids, refused, shapes = [], [], {}
    for p in (frame_paths or []):
        o = inventory_occupancy(p)
        if not o.get("ok") or not o.get("grid"):
            refused.append({"frame": p, "why": o.get("why") or "no grid"})
            continue
        g = o["grid"]
        shape = (len(g), len(g[0]) if g else 0)
        shapes[shape] = shapes.get(shape, 0) + 1
        grids.append((p, g, shape))
    if not grids:
        return [], refused, None
    # the modal geometry wins; the rest are refused rather than reshaped
    best = sorted(shapes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    keep = [(p, g) for (p, g, sh) in grids if sh == best]
    for (p, g, sh) in grids:
        if sh != best:
            refused.append({"frame": p, "why": "grid %sx%s, the run agreed on %sx%s" % (sh[0], sh[1], best[0], best[1])})
    return keep, refused, best


def space_map(frame_paths):
    """The iRobot map of one panel: which squares are furniture, which are open floor, which churn.

    Returns {ok, rows, cols, fixed, open, churn, frames, refused, mask} where `mask` is a grid of
    'fixed' | 'open' | 'churn' | None, so a renderer can draw the room without knowing a single item
    name.
    """
    keep, refused, shape = _grids(frame_paths)
    if len(keep) < _MAP_MIN_FRAMES:
        return {"ok": None, "frames": len(keep), "refused": refused,
                "say": "%d readable frame(s) — need %d before calling any square fixed. One frame "
                       "is a fixture." % (len(keep), _MAP_MIN_FRAMES)}
    rows, cols = shape
    n = len(keep)
    fixed = open_ = churn = 0
    mask = []
    for i in range(rows):
        line = []
        for j in range(cols):
            vals = [g[i][j] for (_p, g) in keep if g[i][j] is not None]
            if not vals:
                line.append(None)
                continue
            share = sum(1 for v in vals if v) / float(len(vals))
            if share >= _STABLE_AT:
                line.append("fixed"); fixed += 1
            elif share <= (1.0 - _STABLE_AT):
                line.append("open"); open_ += 1
            else:
                line.append("churn"); churn += 1
        mask.append(line)
    return {"ok": True, "rows": rows, "cols": cols, "frames": n, "refused": refused,
            "fixed": fixed, "open": open_, "churn": churn, "mask": mask,
            "say": "%d square(s) never move (cube / tomes / charms — treat them like equipment), "
                   "%d are open floor, %d churn (that is where loot lands)" % (fixed, open_, churn)}


def motion_between(before_paths, after_paths):
    """Did things LEAVE this panel, or arrive in it? Counts only — never which item.

    Cell-level, so it is far stronger than comparing two totals: a frame where one item left and
    another arrived has an unchanged total and a very obvious cell delta.
    """
    a, ra, sa = _grids(before_paths)
    b, rb, sb = _grids(after_paths)
    if not a or not b:
        return {"ok": None, "say": "one side had no readable panel — that is not 'nothing moved'",
                "refused": ra + rb}
    if sa != sb:
        return {"ok": None, "say": "the two sides fit different grids (%s vs %s) — refusing to "
                                   "compare square to square" % (sa, sb), "refused": ra + rb}
    rows, cols = sa

    def _stable(grids):
        """A square is only credited when the frames on that side AGREE about it."""
        out = []
        for i in range(rows):
            line = []
            for j in range(cols):
                vals = [g[i][j] for (_p, g) in grids if g[i][j] is not None]
                if not vals:
                    line.append(None); continue
                share = sum(1 for v in vals if v) / float(len(vals))
                line.append(True if share >= _STABLE_AT else False if share <= 1 - _STABLE_AT else None)
            out.append(line)
        return out

    A, B = _stable(a), _stable(b)
    left = arrived = unchanged = unsure = 0
    for i in range(rows):
        for j in range(cols):
            x, y = A[i][j], B[i][j]
            if x is None or y is None:
                unsure += 1
            elif x and not y:
                left += 1
            elif y and not x:
                arrived += 1
            else:
                unchanged += 1
    return {"ok": True, "left": left, "arrived": arrived, "unchanged": unchanged, "unsure": unsure,
            "framesBefore": len(a), "framesAfter": len(b), "refused": ra + rb,
            "say": "%d square(s) emptied, %d filled, %d unchanged, %d could not be called"
                   % (left, arrived, unchanged, unsure)}


def infer_transfer(inv_before, inv_after, stash_before, stash_after):
    """THE CROSS-REFERENCE HE ASKED FOR — "if two reels or a couple show this logic it should be
    able to also as an extra layer of measurement and accuracy to cross reference between those
    reels and understand alone that it moved from my inventory to my stash".

    Two panels, two moments, and CONSERVATION is the check: if the inventory lost k squares and the
    stash gained k, that is a stash-in and the two independent measurements agree. If they do not
    balance, that is the finding — items also enter from the floor and leave to a vendor — and it
    says so instead of picking the flattering reading. [[feedback-contradiction-is-the-finding]]
    """
    mi = motion_between(inv_before, inv_after)
    ms = motion_between(stash_before, stash_after)
    if not mi.get("ok") or not ms.get("ok"):
        return {"ok": None, "inventory": mi, "stash": ms,
                "say": "one panel could not be read on both sides — no transfer can be claimed"}
    out_i, in_s = mi["left"], ms["arrived"]
    moved = min(out_i, in_s)
    balanced = (out_i == in_s) and moved > 0
    if moved == 0:
        verdict, say = "no-transfer", "nothing left the inventory and landed in the stash"
    elif balanced:
        verdict = "stashed"
        say = ("%d item(s) moved INVENTORY -> STASH. Two independent panels agree exactly "
               "(%d out, %d in), and no name was needed to know it." % (moved, out_i, in_s))
    else:
        verdict = "partial"
        say = ("%d square(s) emptied in the inventory and %d filled in the stash — they do NOT "
               "balance, so at least one item came from or went somewhere else (floor, vendor, "
               "cube). Reported, not reconciled away." % (out_i, in_s))
    return {"ok": True, "verdict": verdict, "moved": moved, "leftInventory": out_i,
            "arrivedStash": in_s, "balanced": balanced, "inventory": mi, "stash": ms, "say": say}


if __name__ == "__main__":
    sys.exit(main())
