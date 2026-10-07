# -*- coding: utf-8 -*-
"""REG-1993 - THE RENDER GATE'S BOUND MOVES WITH THE MACHINE'S LOAD, ALL THREE NUMBERS TOGETHER.

His question, 2026-10-07, after the v3603 push starved at the render (353 s, load 8 while he played ON AIR over
GeForceNOW): "raise the limit why not?". A FIXED higher ceiling is an absent hang detector at every quiet minute, so the
bound is scaled by the load the push measures when the render starts: at or under BASE_LOAD (the daytime load the
317 / 333 / 353 numbers were measured at, 2026-09-27) nothing changes; above it the hook's kill, render_check's clean-run
cost and its report-by deadline all grow by load / BASE_LOAD, capped at CAP. A render that hangs is still killed, at a
bound proportional to how busy the machine was.

    python3 tv/render_bound.py        -> "<scale> <1-min load>"   (the hook reads it; "1.00 unknown" when unreadable)
"""
import os
import sys

#: the 1-min load the render numbers were measured at (render_check._CLEAN_RUN_COST's note: "296s and 317s at load ~5")
BASE_LOAD = 5.0
#: past this the reading says more about the machine than about the page; the gate still judges it
CAP = 2.5


def scale(load):
    """The factor the render's three numbers grow by at this 1-min load. -> float in [1, CAP]; 1 when unreadable."""
    try:
        v = float(load)
    except (TypeError, ValueError):
        return 1.0
    if v != v or v <= BASE_LOAD:
        return 1.0
    return min(CAP, v / BASE_LOAD)


def from_env(env=None):
    """The factor the hook measured and handed down (TV_RENDER_SCALE). -> float in [1, CAP]; 1 when absent or unreadable."""
    raw = (os.environ if env is None else env).get("TV_RENDER_SCALE")
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return 1.0
    if v != v:
        return 1.0
    return max(1.0, min(CAP, v))


def main():
    try:
        l1 = os.getloadavg()[0]
    except (OSError, AttributeError):
        l1 = None
    print("%.2f %s" % (scale(l1), ("%.2f" % l1) if l1 is not None else "unknown"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
