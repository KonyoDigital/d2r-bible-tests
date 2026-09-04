#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE ONE MEASUREMENT MINI AUTO ALREADY HAS AND THROWS AWAY.

⚠⚠ WHY THIS EXISTS, AND IT IS THE ROOT OF A CHAIN SIX STATIONS LONG. Traced 2026-09-04, from his
question *"no reel can reach the pruning zone at all"*:

    out decides nothing for all 40 reels
      <- the FRAME door has never once said YES
      <- no seal has ever carried `extracted` with the contract's facts
         (measured: 22 of 30 vault seals carry `extracted: []`, 8 predate the field, ZERO satisfy it)
      <- the contract is ('name', 'location', 'provenance') and `name` is documented as
         "the item's name, WHICH ONLY EVER APPEARS IN A HOVER TOOLTIP"
      <- MINI AUTO is the only thing that films hover tooltips
      <- and `slot_identity.anchor_from_tooltip_rect` REFUSES, because no tooltip->cell offset
         has ever been calibrated (REG-601: the lock that read OPEN over a broken feature)

**So mini auto being uncalibrated is why the river cannot reach the prune.** His padlock catch and
his pruning wall are the same defect two stations apart.

⚠⚠ AND THE CALIBRATION DATA IS NOT MISSING — IT IS DISCARDED. `anchor_from_tooltip_rect`'s own
refusal says the offset "has to be measured once against a real frame whose true cell is known",
and asks for "his 20-item vault test". Measured: **nothing anywhere records a known cell for a
hovered item** — grep for trueCell/knownCell/cellTruth returns nothing, and `stash_grid_truth.json`
is about PANEL classification, not tooltips.

But `hover_mode._step(i, target, screen_xy)` receives `target` — the point in FRAME space that
`slot_identity` planned — and **that IS the true cell, by construction, because mini auto CHOSE
it**. It updates a status dict and drops it. The actuator knows the answer at the moment of
hovering and nothing writes it down. [[the-unjoined-end]] [[plumbing-with-no-tap]]

So this records the pairing when he runs mini auto, and derives the offset afterwards from footage
he already has. **Nothing here drives his pointer** — `hover_drive` does that, only when he asks,
and this is a passive witness of it. [[borrowed-surface]]

⚠ IT REFUSES RATHER THAN DEFAULTING. With no steps recorded, `calibrate()` returns None and says
so. A plausible constant here would place every item in the wrong cell with total confidence, which
is the exact failure `anchor_from_tooltip_rect` refuses in order to avoid.
[[unknown-stays-unknown]]
"""
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))

#: where the pairings land. One line per hovered cell, appended as it happens, so a sweep that is
#: stopped half way still leaves everything it did establish.
JOURNAL = os.path.join(HERE, "hover_calibration.jsonl")

#: how many agreeing steps before an offset may be called measured. One pair is an anecdote and
#: two cannot outvote a bad one; the offset is a property of the game's layout, so a real reading
#: repeats exactly and a spread means something else moved.
MIN_STEPS = 5

#: what share of readings may sit outside AGREE_PX before the sample is judged to be measuring
#: more than one thing. Deliberately small: this is a layout constant, not a noisy signal.
OUTLIER_MAX = 0.2

#: how far two step-offsets may differ and still count as the same reading, in pixels. The tooltip
#: rect comes from a pixel diff, so a pixel or two of edge is expected; a whole cell is not.
AGREE_PX = 6.0


def record_step(i, target, screen_xy=None, container="stash", frame_size=None, path=None):
    """Write down that mini auto hovered `target` (frame space) just now. -> dict (the row)

    Called from `hover_mode`'s step callback, where the true cell is known because it was chosen.
    Never raises into the sweep: a calibration note that strands his pointer would be a far worse
    bug than the one it is here to fix.
    """
    row = {"ts": int(time.time() * 1000), "i": int(i),
           "target": [float(target[0]), float(target[1])] if target else None,
           "screen": [float(screen_xy[0]), float(screen_xy[1])] if screen_xy else None,
           "container": str(container or ""),
           "frameSize": list(frame_size) if frame_size else None}
    try:
        with io.open(path or JOURNAL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return row


def steps(path=None):
    """Every recorded hover, oldest first. -> (list, why). why non-empty means NOTHING was read."""
    p = path or JOURNAL
    if not os.path.exists(p):
        return [], ("no hover has ever been recorded — mini auto has not run since this journal "
                    "existed, so there is nothing to calibrate FROM. That is not a failed "
                    "calibration; it is an unattempted one")
    out = []
    try:
        for ln in io.open(p, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except Exception as exc:
        return [], "the hover journal would not read (%s)" % type(exc).__name__
    return out, ""


def _frames_by_ts(reel_dir):
    """The reel's frames as (epoch_ms, path), oldest first. Frame names carry their own clock."""
    out = []
    try:
        for nm in os.listdir(reel_dir):
            if not nm.lower().endswith(".jpg"):
                continue
            stem = os.path.splitext(nm)[0]
            digits = "".join(ch for ch in stem if ch.isdigit())
            if len(digits) < 13:
                continue
            try:
                out.append((int(digits[-13:]), os.path.join(reel_dir, nm)))
            except ValueError:
                continue
    except Exception:
        return []
    out.sort()
    return out


def _offset_for(step, frames, corner):
    """The tooltip->cell offset this ONE step demonstrates. -> (offset|None, why)"""
    ts = int(step.get("ts") or 0)
    tgt = step.get("target")
    if not tgt:
        return None, "the step recorded no target, so its true cell is unknown"
    # the frame captured AFTER the dwell, and the one before it to diff against
    after = [f for f in frames if f[0] >= ts]
    before = [f for f in frames if f[0] < ts]
    if not after or not before:
        return None, ("no frame pair straddles this hover (%d frames before, %d after) — the reel "
                      "does not cover the moment the tip was drawn" % (len(before), len(after)))
    try:
        import tooltip_crop as TC
    except Exception as exc:
        return None, "tooltip_crop would not import (%s)" % type(exc).__name__
    rect, why = TC.changed_rect(before[-1][1], after[0][1])
    if not rect:
        return None, "the two frames show no difference (%s), so no tooltip was drawn" % (why or "")
    l, t, r, b = [float(v) for v in rect]
    corners = {"topleft": (l, t), "topright": (r, t), "bottomleft": (l, b), "bottomright": (r, b)}
    if corner not in corners:
        return None, "unknown corner %r" % (corner,)
    cx, cy = corners[corner]
    return (float(tgt[0]) - cx, float(tgt[1]) - cy), ""


def calibrate(reel_dir, corner="topleft", path=None):
    """The measured tooltip->cell offset for this reel. -> (offset|None, report)

    ⚠⚠ IT RETURNS None RATHER THAN A PLAUSIBLE PAIR, and that is the whole design. A guessed offset
    places every item in the wrong cell WITH TOTAL CONFIDENCE — `anchor_from_tooltip_rect` refuses
    the zero offset for exactly this reason, and a calibrator that defaults would hand it the
    guess it is refusing to make for itself.
    """
    rows, why = steps(path=path)
    rep = {"steps": len(rows), "used": 0, "offsets": [], "corner": corner, "why": ""}
    if not rows:
        rep["why"] = why
        return None, rep
    frames = _frames_by_ts(reel_dir)
    if not frames:
        rep["why"] = ("no timestamped frames under %s, so no hover can be paired with the picture "
                      "it produced" % os.path.basename(reel_dir))
        return None, rep
    got, refused = [], {}
    for st in rows:
        off, owhy = _offset_for(st, frames, corner)
        if off is None:
            refused[owhy[:90]] = refused.get(owhy[:90], 0) + 1
            continue
        got.append(off)
    rep["used"] = len(got)
    rep["offsets"] = [[round(x, 1), round(y, 1)] for x, y in got[:12]]
    rep["refused"] = refused
    if len(got) < MIN_STEPS:
        rep["why"] = ("only %d hover(s) could be paired with a tooltip, and %d are needed before "
                      "an offset is a measurement rather than an anecdote. Refusing rather than "
                      "averaging what is here." % (len(got), MIN_STEPS))
        return None, rep
    xs = sorted(o[0] for o in got)
    ys = sorted(o[1] for o in got)
    mx, my = xs[len(xs) // 2], ys[len(ys) // 2]
    # ⚠ THE SPREAD IS THE CHECK, NOT THE COUNT. The offset is a property of the game's layout at a
    # given resolution, so honest readings repeat almost exactly. A wide spread means the steps are
    # not measuring one thing — a resolution change mid-sweep, or tips drawn on the other side near
    # a screen edge — and averaging them would produce a number no single frame supports.
    far = [o for o in got if abs(o[0] - mx) > AGREE_PX or abs(o[1] - my) > AGREE_PX]
    # ⚠⚠ A BARE MAJORITY IS NOWHERE NEAR ENOUGH, AND MY FIRST CUT ACCEPTED ONE. It refused only
    # when MORE THAN HALF disagreed, so three readings 800px from the other five still yielded an
    # offset — its own test caught it. This is a physical constant of the game's layout at a given
    # resolution: honest readings do not merely out-vote the others, they nearly all agree. A
    # third of the sample landing a cell away means these hovers are not measuring one thing, and
    # the median of two populations is a number no frame supports.
    if len(far) > max(1, int(len(got) * OUTLIER_MAX)):
        rep["why"] = ("%d of %d readings disagree with the median by more than %.0fpx, so these "
                      "hovers are not measuring one offset. A tip drawn on the other side of the "
                      "cursor near a screen edge does exactly this — calibrate away from the edges."
                      % (len(far), len(got), AGREE_PX))
        return None, rep
    rep["why"] = ("%d of %d hovers agree within %.0fpx" % (len(got) - len(far), len(got), AGREE_PX))
    rep["outliers"] = len(far)
    return (round(mx, 1), round(my, 1)), rep


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else ""
    off, rep = calibrate(d) if d else (None, {"why": "usage: hover_calibration.py <reel_dir>"})
    print(json.dumps({"offset": off, "report": rep}, indent=2, ensure_ascii=False))
