#!/usr/bin/env python3
"""FIND THE D2R TOOLTIP IN ONE FRAME, BY WHERE THE TEXT IS.

★ Konyo needs the hover pass automated, and everything downstream — the cursor->cell offset, the
slot identity of each item, MINI(AUTOMATIC) driving the hovers itself — is blocked on one thing:
locating the tooltip in a frame. This is that.

⚠ WHY THE EXISTING METHOD CANNOT DO IT, MEASURED ON HIS OWN FILM. tooltip_crop.changed_rect()
differences two consecutive frames and takes the bounding box of what moved. Run against
reel_s_1788103468647_77044, 39 consecutive pairs produced 38 rectangles and EVERY ONE was
(0, 0, 2940, 1908) — the whole screen — because the D2R world never stops animating behind the
panels. vault_retro then discards anything over 60 KB as mis-derived, so in production every crop
was derived, judged wrong and thrown away silently. That one mechanism explains tooltip_crops
empty on all 16 reels and grounded = 0.

⚠ AND TWO OBVIOUS ALTERNATIVES ALSO FAIL, both killed by looking at the actual pixels:
   · DARKNESS — 48.7% of his frame is near-black. D2R is a dark game; the tooltip does not stand out.
   · A GOLD BORDER / FLAT PANEL — the D2R tooltip is SEMI-TRANSPARENT. The stash grid shows
     THROUGH it and its edges are soft. There is no hard border to find and the region is not flat.
     I only learned this by rendering the frame and looking at it. [[visual-regression-detector]]

WHAT IS ACTUALLY TRUE OF A TOOLTIP: it is the one place on screen with DENSE HORIZONTAL TEXT. So
tile the frame, OCR each tile, and the tooltip is where the text clusters. The OCR worker returns
lines but no coordinates, and tiling is how you get coordinates out of a reader that has none.

Measured on 2_1788104655412.jpg (2560x1665, the Crescent Moon frame): a 4x4 sweep took 0.2s for
16 calls and put 9 of the 22 text lines in a single tile.
"""
import os

DEFAULT_COLS = 6
DEFAULT_ROWS = 6
_MIN_LINE_CHARS = 3
_MIN_AREA_FRAC = 0.08   # far below his real 33%, far above the 2.8% HUD impostor


def _ocr():
    try:
        import tv_diablo as _tv
        return _tv._OCR
    except Exception:
        return None


def density(frame_path, cols=DEFAULT_COLS, rows=DEFAULT_ROWS, tmp_dir=None, reader=None):
    """Text-line count per tile. -> (grid, why)

    `reader` takes a path and returns {"lines": [...]}; it defaults to the local OCR worker so
    callers do not have to know about it, and can be injected so this is testable without one.
    """
    try:
        from PIL import Image
    except Exception as e:
        return None, "PIL is unavailable: %s" % str(e)[:60]
    if not frame_path or not os.path.isfile(frame_path):
        return None, "no frame at %r" % (frame_path,)
    rd = reader or (lambda p: (_ocr().read(p, timeout=4.0) or {}) if _ocr() else {})
    tmp = os.path.join(tmp_dir or os.path.dirname(os.path.abspath(frame_path)),
                       ".tooltip_tile.jpg")
    try:
        im = Image.open(frame_path).convert("RGB")
    except Exception as e:
        return None, "the frame could not be opened: %s" % str(e)[:60]
    W, H = im.size
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            box = (c * W // cols, r * H // rows, (c + 1) * W // cols, (r + 1) * H // rows)
            try:
                im.crop(box).save(tmp, "JPEG", quality=80)
                j = rd(tmp) or {}
                n = len([l for l in (j.get("lines") or [])
                         if len(str(l).strip()) >= _MIN_LINE_CHARS])
            except Exception:
                n = 0
            row.append(n)
        grid.append(row)
    try:
        os.remove(tmp)
    except Exception:
        pass
    return {"grid": grid, "size": (W, H), "cols": cols, "rows": rows}, None


def locate(frame_path, cols=DEFAULT_COLS, rows=DEFAULT_ROWS, tmp_dir=None, reader=None,
           min_lines=6):
    """Where is the tooltip in this frame? -> (rect|None, why)

    `rect` is (left, top, width, height) in FRAME pixels — the same shape tooltip_crop.crop_to
    already takes, so this drops into the existing crop path.

    THE RULE: start at the densest tile and GROW while neighbours still carry text. A tooltip is
    taller than one tile and the growth is what makes the rectangle fit it rather than a corner
    of it.

    ⚠ IT REFUSES RATHER THAN GUESSING. Below `min_lines` of text in the whole frame there is no
    tooltip to find — he was not hovering — and returning a rectangle anyway would hand the crop
    path a picture of the floor. An empty frame and an unhovered one are the same honest answer.
    """
    d, why = density(frame_path, cols=cols, rows=rows, tmp_dir=tmp_dir, reader=reader)
    if not d:
        return None, why
    grid, (W, H) = d["grid"], d["size"]
    total = sum(sum(r) for r in grid)
    if total < min_lines:
        return None, ("only %d text line(s) in the whole frame — below the %d needed to call this a "
                      "tooltip, so nothing is claimed" % (total, min_lines))
    best = max(((grid[r][c], r, c) for r in range(rows) for c in range(cols)))
    if best[0] <= 0:
        return None, "no tile carried any text"
    _, br, bc = best
    keep = {(br, bc)}
    changed = True
    while changed:
        changed = False
        for (r, c) in list(keep):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (r + dr, c + dc)
                if n in keep:
                    continue
                if 0 <= n[0] < rows and 0 <= n[1] < cols and grid[n[0]][n[1]] > 0:
                    keep.add(n)
                    changed = True
    rs = [r for r, _ in keep]
    cs = [c for _, c in keep]
    x0 = min(cs) * W // cols
    x1 = (max(cs) + 1) * W // cols
    y0 = min(rs) * H // rows
    y1 = (max(rs) + 1) * H // rows
    rect = (x0, y0, x1 - x0, y1 - y0)

    # ⚠ AN AREA FLOOR, BECAUSE TEXT DENSITY ALONE FINDS THE HUD. Measured across his reels: on a
    # reel that registered NOTHING, this returned (2450, 0, 490, 318) on FIVE consecutive frames —
    # the same small box in the top-right corner every time. That is persistent game chrome, not a
    # tooltip, and a finder that confidently returns it would hand the crop path a picture of the
    # UI on every unhovered frame.
    #
    # The separation is SIZE and it is not close. On the same reels:
    #     real tooltip (Crescent Moon)   1280 x 1110  =  33.4% of the frame
    #     the HUD false positive          490 x  318  =   2.8% of the frame
    # A tooltip carries a name, a base, and six to twelve stat lines; it cannot be small. So the
    # floor sits far below the real one and far above the impostor, and anything between them is
    # refused rather than guessed. [[feedback-threshold-above-the-ceiling]] — the inverse: a
    # threshold nothing can fall between is the one worth having.
    frac = float(rect[2] * rect[3]) / float(max(1, W * H))
    if frac < _MIN_AREA_FRAC:
        return None, ("the densest text is only %.1f%% of the frame (floor %.0f%%) — that is game "
                      "chrome, not a tooltip. Measured: his real tooltip covers 33%%, the top-right "
                      "HUD box covers 2.8%%." % (frac * 100, _MIN_AREA_FRAC * 100))
    return rect, None


LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tooltip_find.json")


def _load():
    import json
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d):
    import json
    try:
        tmp = LEDGER + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1, sort_keys=True)
        os.replace(tmp, LEDGER)
    except Exception:
        pass


def bank(found, named=None, why=None):
    """Record one attempt. -> None

    k = a located tooltip that then produced a NAME.
    n = tooltips located.
    So the score answers "when this says it found a tooltip, was it really one" — which is the only
    question worth asking of a finder, and the one the HUD false positive would have failed.

    ⚠ `named=None` means nobody has told us yet whether the crop yielded a name. It is banked as
    PENDING and counts in neither side, because "not yet read" and "read and empty" are opposite
    facts. [[unknown-stays-unknown]]
    """
    import time
    d = _load()
    d["attempts"] = int(d.get("attempts") or 0) + 1
    if not found:
        d["refused"] = int(d.get("refused") or 0) + 1
    else:
        d["located"] = int(d.get("located") or 0) + 1
        if named is True:
            d["named"] = int(d.get("named") or 0) + 1
        elif named is False:
            d["blank"] = int(d.get("blank") or 0) + 1
        else:
            d["pending"] = int(d.get("pending") or 0) + 1
    d["lastAt"] = int(time.time() * 1000)
    if why:
        d["lastWhy"] = str(why)[:160]
    _save(d)


def report():
    """Wilson on "a located tooltip really was one". -> dict

    Uses the SAME tv/confidence.wilson_lower every other lane here uses — the capture doors, the
    per-tab readers, the chronicle and vault sweeps, prune_shadow — rather than a seventh
    hand-rolled ratio.
    """
    try:
        from confidence import wilson_lower
    except Exception:
        try:
            from tv.confidence import wilson_lower
        except Exception:
            wilson_lower = None
    d = _load()
    k = int(d.get("named") or 0)
    bad = int(d.get("blank") or 0)
    n = k + bad
    w = None
    if wilson_lower is not None and n > 0:
        try:
            w = round(float(wilson_lower(k, n)), 3)
        except Exception:
            w = None
    return {
        "attempts": int(d.get("attempts") or 0),
        "located": int(d.get("located") or 0),
        "refused": int(d.get("refused") or 0),
        "named": k, "blank": bad, "pending": int(d.get("pending") or 0),
        "judged": n, "wilson": w,
        "areaFloor": _MIN_AREA_FRAC,
        "say": ("no located tooltip has been judged yet — nothing is proved either way"
                if n == 0 else
                "%d of %d located tooltips yielded a name · Wilson floor %.3f" % (k, n, w or 0.0)),
        "lastWhy": d.get("lastWhy") or "",
    }


def main(argv=None):
    import sys
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: tooltip_find.py <frame.jpg>")
        return 2
    rect, why = locate(argv[0])
    print("── TOOLTIP ──")
    print("  frame : %s" % argv[0])
    if rect:
        print("  rect  : %s" % (rect,))
    else:
        print("  none  : %s" % why)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
