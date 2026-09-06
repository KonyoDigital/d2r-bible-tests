#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHICH PART OF THE WINDOW PAINTED — a witness that can say "this half is drawn and that half is not".

Konyo, 2026-09-06, with a screenshot: *"theres a big empty space here im pretty sure there was
something here"*. The console's Sessions tab had rendered its right-hand rail correctly — relaunch,
eagle, repair, THE FLEET, THE SHELF — while roughly 1080x560 of the MAIN COLUMN was blank.

⚠⚠ THE EXISTING WITNESS COULD NOT HAVE SEEN IT, AND THAT IS MEASURED, NOT ASSUMED.
`paint_witness.blank_strikes(pid)` asks about the WHOLE WINDOW. Its own message is
*"look N of M found content ON THE WINDOW, so it is not blank"*. His rail was painting, so the
window HAD content, so the witness answered PAINTED — correctly, for the question it asks.
`tv/ui_faults.jsonl` proves the gap rather than merely suggesting it: on the day of his sighting it
recorded 21 faults, SIXTEEN of them `console-pixels-blank-nothing-else-saw-it`, and **ZERO within 45
minutes of 20:14**. The instrument was working and blind at the same time.
⇒ A partially blank console was invisible to the only instrument watching for a blank console.
[[gate-blind-to-unexercised-input]] [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]

=== WHY A GRID AND NOT TWO NAMED PANELS ===
The obvious build is "measure the main column and the rail". That hardcodes today's layout into a
health check, and the layout is the thing most likely to change — the rail has already moved twice
this month. A grid asks no layout question at all: it measures N x M cells and reports each one, so
"some of the window is drawn and some is not" is expressible without knowing what lives where.
The named regions below are DERIVED from the grid columns, never measured separately, so the two can
never disagree. [[copy-drift]]

=== WHAT IS REUSED, DELIBERATELY ===
`measure()` and `verdict()` come from paint_witness unchanged. Re-deriving the thresholds here would
create a second opinion about "blank" that nobody reconciles, and they were expensive to get right:
his console is a DARK THEME — 72.7% of pixels below luminance 24 while perfectly healthy — so the
verdict rests on UNIFORMITY (modal share) and an INK tail, never on darkness.

⚠ READ-ONLY ON HIS SURFACE. It reads the compositor's existing bitmap through paint_witness._grab;
nothing here focuses, raises, resizes, clicks or reloads. It is a WITNESS, not a trigger.
[[borrowed-surface]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS NON-ASCII, AND HIS WINDOWS CONSOLE IS cp1255. Without this, a report that
# contains one arrow or emoji raises UnicodeEncodeError WHILE REPORTING — so a perfectly clean tree
# exits non-zero and the failure is about the printing, not the finding. Caught by the pre-push
# gate, which is the only thing that could have: it never fails on this Mac.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

import paint_witness as PW  # noqa: E402

BLANK = PW.BLANK
PAINTED = PW.PAINTED
UNKNOWN = PW.UNKNOWN

#: grid shape. 3 columns x 2 rows: enough to separate a rail from a column and a header from a body,
#: coarse enough that each cell still holds thousands of pixels to sample.
COLS = 3
ROWS = 2

#: a cell smaller than this is not worth a verdict — too few pixels for modal share to mean anything
MIN_CELL_PX = 40

#: named regions, DERIVED from grid columns so they cannot drift from the cells they summarise.
#: The console's rail sits on the right; `main` is everything left of it.
REGIONS = {"main": (0, COLS - 1), "rail": (COLS - 1, COLS)}


def _sub(shot, x0, y0, x1, y1):
    """A view of one rectangle of a shot, in the shape measure() expects. -> dict|None

    ⚠ NO PIXELS ARE COPIED. It re-points the origin and shrinks w/h, keeping the ORIGINAL bytes-per-
    row, so measure()'s `yy * bpr + xx * bpp` still lands on the right pixel. Copying a sub-image out
    of a 1120x660 buffer for every cell would allocate megabytes on a health tick.
    """
    w, h = int(x1 - x0), int(y1 - y0)
    if w < MIN_CELL_PX or h < MIN_CELL_PX:
        return None
    off = int(y0) * shot["bpr"] + int(x0) * shot["bpp"]
    return {"w": w, "h": h, "bpr": shot["bpr"], "bpp": shot["bpp"],
            "buf": shot["buf"][off:], "_x0": int(x0), "_y0": int(y0)}


def cells(pid, quartz=None, samples=40, cols=COLS, rows=ROWS):
    """Every grid cell's verdict for ONE frame. -> dict

    `samples` is per axis PER CELL and sits below paint_witness's 60 on purpose: six cells at 60
    would sample 6x the pixels of one whole-window look on every health tick.

    ⚠ 40, NOT 24, AND THE NUMBER WAS MEASURED. At 24 samples one cell of his live console reported
    BLANK; at 40 the same cell reported PAINTED. The ink test needs BOTH p99 and brightShare under
    their bars, and a sparsely-sampled cell near that boundary flips. A verdict that changes with
    the sample count is not a verdict — which is exactly why nothing here is trusted from ONE frame.
    """
    out = {"ok": False, "cols": cols, "rows": rows, "cells": [], "why": "",
           "painted": None, "blank": None, "unknown": None}
    win, why = PW.window_for(pid, quartz=quartz)
    if not win:
        out["why"] = why or "no window could be found for this process"
        return out
    # ⚠⚠ OCCLUSION FIRST, AND THIS IS THE FALSE POSITIVE THAT WOULD HAVE MADE THE ROW USELESS.
    # CAUGHT ON HIS LIVE MACHINE: at the moment of writing, Safari and Terminal covered 100% of his
    # console, so every cell read blank. A window covered on ONE SIDE — Safari over the left half —
    # would read blank-left / painted-right and fire "the window is PARTLY drawn" as a FAULT, about
    # a console that is perfectly healthy and merely behind another window.
    # An occluded capture is not evidence about painting. UNKNOWN, never a fault, and never OK.
    # [[unknown-stays-unknown]] [[borrowed-surface]]
    # ⚠ occluded_by returns a TUPLE (coverers, why), NOT a dict with a "state" key. My first guard
    # read `occ.get("state")`, matched nothing, and silently let an occluded window through — the
    # guard was present, wired, and doing nothing. Verified against the real return value before
    # trusting it: (['Safari (100.0%)', 'Terminal (51.8%)'], 'Safari ... cover 100.0% ...').
    try:
        _cov, _cwhy = PW.occluded_by(pid, quartz=quartz)
    except Exception:
        _cov, _cwhy = None, ""
    if _cov:
        out["occluded"] = True
        out["coveredBy"] = list(_cov)
        out["why"] = ("the window is COVERED (%s), so its bitmap is not evidence about what it "
                      "painted - UNKNOWN, not a fault" % str(_cwhy or "")[:140])
        return out
    shot, why2 = PW._grab(win.get("id") if isinstance(win, dict) else win, quartz=quartz)
    if not shot:
        # UNKNOWN, never "fine": no Screen Recording permission looks exactly like a healthy window
        # to anything that treats a failed capture as an absence of faults.
        out["why"] = why2 or "the window server returned no image"
        return out
    W, H = shot["w"], shot["h"]
    # skip the OS title bar for the same reason paint_witness does: it is drawn by the window server
    # whether or not the page painted, and it held his blank window three points under the bar.
    top = PW.CHROME_TOP_PX if H > PW.CHROME_TOP_PX * 4 else 0
    cw, ch = W // cols, (H - top) // rows
    n_p = n_b = n_u = 0
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * cw, top + r * ch
            sub = _sub(shot, x0, y0, x0 + cw, y0 + ch)
            if sub is None:
                st, w2, m = UNKNOWN, "the cell is too small to measure (%dx%d)" % (cw, ch), None
            else:
                m = PW.measure(sub, samples=samples)
                st, w2 = PW.verdict(m)
            n_p += (st == PAINTED); n_b += (st == BLANK); n_u += (st == UNKNOWN)
            out["cells"].append({"col": c, "row": r, "state": st, "why": w2,
                                 "rect": [x0, y0, cw, ch],
                                 "modalShare": (m or {}).get("modalShare"),
                                 "brightShare": (m or {}).get("brightShare")})
    out.update({"ok": True, "painted": n_p, "blank": n_b, "unknown": n_u,
                "w": W, "h": H,
                "why": "%d painted, %d blank, %d unknown across %d cell(s)"
                       % (n_p, n_b, n_u, len(out["cells"]))})
    return out


def regions(pid, quartz=None, **kw):
    """The named regions, DERIVED from the grid. -> dict

    A region is BLANK only when EVERY measurable cell in it is blank, and PAINTED when any is
    painted. A region whose cells could not be measured is UNKNOWN — never PAINTED by default.
    """
    g = cells(pid, quartz=quartz, **kw)
    out = {"ok": g.get("ok"), "why": g.get("why"), "regions": {}, "grid": g}
    if not g.get("ok"):
        return out
    for name, (c0, c1) in REGIONS.items():
        mine = [x for x in g["cells"] if c0 <= x["col"] < c1]
        known = [x for x in mine if x["state"] != UNKNOWN]
        if not known:
            st = UNKNOWN
        elif all(x["state"] == BLANK for x in known):
            st = BLANK
        elif any(x["state"] == PAINTED for x in known):
            st = PAINTED
        else:
            st = UNKNOWN
        out["regions"][name] = {"state": st, "cells": len(mine), "measured": len(known)}
    return out


def half_blank(pid, quartz=None, **kw):
    """THE QUESTION HIS SIGHTING ASKED, and the one the whole-window witness cannot answer. -> dict

    True when the window is PARTLY painted: at least one cell drawn and at least one blank. That is
    a window whose beat is healthy, whose DOM is intact, and part of which is not on screen.
    ⚠ It is NOT a fault on its own — a legitimately empty panel (an idle list, a collapsed drawer)
    is blank and fine. It is a READING, and the doctor row decides what to do with it. The
    difference matters: this must not become a trigger that reloads his console under him.
    """
    g = cells(pid, quartz=quartz, **kw)
    if not g.get("ok"):
        return {"ok": False, "half": None, "why": g.get("why")}
    half = bool(g["painted"] and g["blank"])
    where = [c for c in g["cells"] if c["state"] == BLANK]
    return {"ok": True, "half": half, "painted": g["painted"], "blank": g["blank"],
            "unknown": g["unknown"],
            "blankCells": [[c["col"], c["row"]] for c in where],
            "why": ("%d of %d cell(s) are blank while %d are painted - the window is PARTLY drawn"
                    % (g["blank"], len(g["cells"]), g["painted"])) if half
                   else ("nothing is blank" if not g["blank"] else "every measurable cell is blank"),
            "grid": g}


#: consecutive looks before a partly-drawn window is believed. paint_witness uses the same idea for
#: the whole window and states the reason: "ONE FRAME IS A SAMPLE, NOT A VERDICT. A repaint, a
#: resize or a Space switch can catch a window mid-nothing."
HALF_STRIKES = 3


def half_blank_strikes(pid, strikes=None, quartz=None, sleep=None, **kw):
    """Is the window PARTLY drawn across CONSECUTIVE looks? -> dict

    ⚠⚠ THIS, NOT `half_blank`, IS WHAT THE HEART READS. A single frame flips: measured on his live
    console, the same cell read BLANK at 24 samples and PAINTED at 40, because the ink test needs
    both p99 and brightShare under their bars and a cell near that boundary is unstable. A window
    caught mid-repaint is not a fault, and a health row that cries wolf gets ignored within a week —
    a distrusted instrument is a switched-off one.

    ⚠ THE SAME CELLS must be blank every time. A different blank cell on each look is a repainting
    window, not a stuck one, and it is REFUSED here rather than averaged into a fault.
    """
    n = HALF_STRIKES if strikes is None else strikes
    _sleep = sleep if sleep is not None else __import__("time").sleep
    seen = None
    last = None
    for i in range(n):
        if i:
            _sleep(0.6)
        r = half_blank(pid, quartz=quartz, **kw)
        last = r
        if not r.get("ok"):
            return {"ok": False, "half": None, "looks": i + 1,
                    "why": "look %d of %d could not be taken (%s), so NOTHING is known about this "
                           "window" % (i + 1, n, str(r.get("why"))[:100])}
        if not r.get("half"):
            return {"ok": True, "half": False, "looks": i + 1, "grid": r.get("grid"),
                    "why": "look %d of %d found the window fully drawn (or fully blank), so it is "
                           "not partly drawn: %s" % (i + 1, n, str(r.get("why"))[:110])}
        cur = {tuple(c) for c in (r.get("blankCells") or [])}
        seen = cur if seen is None else (seen & cur)
        if not seen:
            return {"ok": True, "half": False, "looks": i + 1, "grid": r.get("grid"),
                    "why": "the blank cells MOVED between looks, so the window is repainting rather "
                           "than stuck - refused as a fault"}
    return {"ok": True, "half": True, "looks": n, "cells": sorted(seen or []),
            "grid": (last or {}).get("grid"),
            "why": "%d cell(s) were blank on ALL %d look(s) while others stayed painted: %s"
                   % (len(seen or []), n, sorted(seen or []))}


def main(argv):
    import json
    pid = int(argv[1]) if len(argv) > 1 else os.getpid()
    r = half_blank(pid)
    print(json.dumps(r.get("grid"), indent=2)[:2000])
    print("half-blank: %s - %s" % (r.get("half"), r.get("why")))
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
