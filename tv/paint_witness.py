#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DID THE WINDOW ACTUALLY PAINT? — a second witness for the rescue, taken from PIXELS.

His words, 2026-09-04, after the console went black on him: *"maybe we can have like a safegaurd
for this connected to the watchdog/heart of the console that sees it rendering or something
regressing it automatically just restarts the console before i even notice it :)"*, and then:
*"and a picture harness pixel harness of some sort like a visual screenshot or something im sure
we can safegaurd it by that too if you cant archicture a bypass :)"*.

⚠⚠ THE EXISTING WITNESS ASKS THE PAGE, AND A BLANK PAGE CAN STILL ANSWER. `_UI_BEAT` is published
BY the document — `blankStrikes`, `elsHigh`, `rafNow` all come from JavaScript running inside the
window whose health is in question. That is not worthless (a wedged renderer stops beating), but
it cannot see the case he actually hit: a document that keeps beating while nothing reaches the
screen. This module never asks the page. It reads the compositor's own bitmap of his window.

⚠⚠ IT IS A WITNESS, NOT A TRIGGER, AND THAT IS DELIBERATE. Nothing here reloads, restarts, clicks
or writes. It answers one question — BLANK / PAINTED / UNKNOWN — and the rescue decides. Its most
valuable answer is the one that REFUSES: a window that is provably painted is a window that must
not be reloaded under him, whatever the beat says. [[heart-first]]

── WHY "MOSTLY DARK" WOULD HAVE BEEN WRONG, MEASURED ON HIS RUNNING CONSOLE ───────────────────
The obvious test is "is it black?". Measured on his live window (pid 11243, 1120x660) while it was
perfectly healthy: **72.7% of sampled pixels sit below luminance 24.** His console is a dark theme.
A darkness test would have called a healthy console blank every single time it ran.

What separates them is UNIFORMITY, not darkness — how much of the window is one single colour:

    surface                              modal share      distinct luminances
    his console, BLANK (caught live)        0.9963                 8-9
    his console, healthy                0.069 / 0.122           156 / 34
    Terminal                                0.6628                 117
    Safari                                  0.4892                 125
    a synthetic all-black buffer            1.0000                   1

⚠⚠ AND THE FIRST ROW IS WHY `distinct` IS NOT PART OF THE VERDICT. This module shipped with a
second bar, `distinct <= 4`, and then found his console **blank white with only the titlebar
drawn** — and called it PAINTED, because the CHROME contributes 8-9 luminances on its own. Every
fixture behind that bar was chrome-free and no real window ever is. **The one case it existed to
catch is the case it would have missed.** Modal share alone has a margin of 0.9963 against 0.6628
for the busiest ordinary window measured. [[visual-regression-detector]]

⚠ AND THE READING IS NOISY. His healthy console measured 156 distinct luminances one moment and 34
seconds later — the content moves. The margin to the bar is enormous (0.122 vs 0.98), but a single
frame is still a sample, so `blank_strikes()` requires CONSECUTIVE agreeing frames before anyone
should act. [[regression-guard]]

    python3 tv/paint_witness.py           # look at his console once, say what was seen
    python3 tv/paint_witness.py --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: a window smaller than this is a helper, not his console. Same rule and same number as
#: window_visibility.MIN_ON_SCREEN_PX — quoted below rather than re-typed, so the two cannot drift.
try:
    from window_visibility import MIN_ON_SCREEN_PX
except Exception:                                  # pragma: no cover - measured at import
    MIN_ON_SCREEN_PX = 40 * 40

#: THE BAR. Measured 2026-09-04 against his live console and three ordinary applications.
BLANK_MODAL_SHARE = 0.98    #: one colour covering ~all of the window
#: ⚠⚠ REPORTED, NOT REQUIRED — AND THE REASON IS A LIVE CATCH ON HIS OWN MACHINE.
#: This started as a second bar, `distinct <= 4`, calibrated against healthy windows and synthetic
#: all-black buffers. Then the harness was pointed at his running console and found it **blank
#: white, only the titlebar drawn** — the exact fault he reported — and called it **PAINTED**,
#: because the window CHROME (traffic lights, "TV DIABLO" title, the 1px rule under it) contributes
#: **9** distinct luminances all by itself. A real blank window is never chrome-free, and every
#: fixture I had built was. The conjunct would have failed on the only case that matters.
#:
#: Modal share alone separates them with room to spare, measured the same minute:
#:     his console, BLANK NOW      0.9963      <- caught
#:     his console, healthy    0.069 / 0.122
#:     Terminal                    0.6628
#:     Safari                      0.4892
#: 98% of a window being ONE colour is blank whether or not a titlebar is drawn on top of it.
BLANK_MAX_DISTINCT = 4      #: kept for the report; NOT part of the verdict — see above

#: how many CONSECUTIVE blank frames before this witness is willing to say so out loud. A single
#: frame can catch a legitimate mid-repaint moment; three cannot.
BLANK_STRIKES = 3

BLANK = "BLANK"
PAINTED = "PAINTED"
UNKNOWN = "UNKNOWN"


def _quartz():
    try:
        import Quartz
        return Quartz
    except Exception:
        return None


def window_for(pid, quartz=None):
    """The window id of the biggest on-screen window owned by `pid`. -> (id|None, why)

    ⚠ None is UNKNOWN, never "he has no console". A pid with no listed window may be starting,
    minimised, or on another Space, and none of those is a black screen.
    """
    Q = quartz if quartz is not None else _quartz()
    if Q is None:
        return None, "Quartz is not importable here - the window server cannot be asked"
    try:
        opts = Q.kCGWindowListOptionOnScreenOnly | Q.kCGWindowListExcludeDesktopElements
        rows = Q.CGWindowListCopyWindowInfo(opts, Q.kCGNullWindowID)
    except Exception as e:
        return None, "the window server refused the list (%s)" % type(e).__name__
    if rows is None:
        return None, "the window server returned nothing at all"
    best, best_area = None, 0.0
    for row in rows:
        try:
            if int(row.get("kCGWindowOwnerPID", -1)) != int(pid):
                continue
            b = row.get("kCGWindowBounds") or {}
            area = float(b.get("Width", 0)) * float(b.get("Height", 0))
        except Exception:
            continue
        if area >= MIN_ON_SCREEN_PX and area > best_area:
            best, best_area = row.get("kCGWindowNumber"), area
    if best is None:
        return None, ("pid %s owns no on-screen window big enough to be his console, which is not "
                      "the same as a blank one" % pid)
    return best, ""


OCCLUDED = "OCCLUDED"


def occluded_by(pid, quartz=None):
    """Is another window sitting ON TOP of his console? -> (list|None, why)

    ⚠ QUOTED, NOT REIMPLEMENTED. `window_visibility` owns every "what is the window server saying"
    question and now owns this one too (REG-594). My first cut walked the z-order here as well —
    a second copy of a safety rule is [[copy-drift]]'s worst case, and this one decides whether a
    healthy console gets reloaded under him.
    """
    try:
        import window_visibility as _wv
        return _wv.covered_by(pid=pid, quartz=quartz)
    except Exception as e:
        return None, "the window witness could not be asked (%s)" % str(e)[:70]


def _grab(window_id, quartz=None):
    """The compositor's bitmap of ONE window. -> (dict|None, why)

    ⚠ READ-ONLY ON HIS SURFACE. CGWindowListCreateImage neither focuses, raises, resizes nor
    activates the window — it copies what is already composited. Nothing here sends an event.
    [[borrowed-surface]]
    """
    Q = quartz if quartz is not None else _quartz()
    if Q is None:
        return None, "Quartz is not importable here"
    try:
        img = Q.CGWindowListCreateImage(
            Q.CGRectNull, Q.kCGWindowListOptionIncludingWindow, window_id,
            Q.kCGWindowImageBoundsIgnoreFraming | Q.kCGWindowImageNominalResolution)
    except Exception as e:
        return None, "the capture raised (%s: %s)" % (type(e).__name__, str(e)[:60])
    if img is None:
        # the usual cause is Screen Recording permission, and saying so beats a bare None
        return None, ("the window server returned no image - the window may have closed, or this "
                      "process may lack Screen Recording permission. Either way NOTHING WAS SEEN")
    try:
        w, h = Q.CGImageGetWidth(img), Q.CGImageGetHeight(img)
        buf = bytes(Q.CGDataProviderCopyData(Q.CGImageGetDataProvider(img)))
        return {"w": w, "h": h, "buf": buf,
                "bpr": Q.CGImageGetBytesPerRow(img),
                "bpp": Q.CGImageGetBitsPerPixel(img) // 8}, ""
    except Exception as e:
        return None, "the image would not yield its pixels (%s)" % type(e).__name__


def measure(shot, samples=60):
    """How uniform is this bitmap? -> dict

    Returns the two numbers the bars are written against, plus the mean luminance — which is NOT
    used to decide anything and is reported because it is the number a reader will reach for
    first, and seeing it high on a blank white window is what stops them re-deriving the bar.
    """
    from collections import Counter
    w, h, buf, bpr, bpp = shot["w"], shot["h"], shot["buf"], shot["bpr"], shot["bpp"]
    lums, total = Counter(), 0
    for yy in range(0, h, max(1, h // samples)):
        for xx in range(0, w, max(1, w // samples)):
            o = yy * bpr + xx * bpp
            if o + 3 > len(buf):
                continue
            b, g, r = buf[o], buf[o + 1], buf[o + 2]
            lums[(r * 299 + g * 587 + b * 114) // 1000] += 1
            total += 1
    if not total:
        return {"samples": 0, "distinct": None, "modalShare": None, "meanLuminance": None,
                "why": "no pixel could be sampled, so nothing was measured"}
    modal, modal_n = lums.most_common(1)[0]
    return {"samples": total, "distinct": len(lums),
            "modalShare": round(modal_n / float(total), 4),
            "modalLuminance": modal,
            "meanLuminance": round(sum(k * v for k, v in lums.items()) / float(total), 1),
            "why": ""}


def verdict(m):
    """BLANK / PAINTED / UNKNOWN for ONE frame. -> (state, why)"""
    if not m or m.get("distinct") is None:
        return UNKNOWN, (m or {}).get("why") or "nothing was measured"
    d, share = m["distinct"], m["modalShare"]
    if share >= BLANK_MODAL_SHARE:
        return BLANK, ("%.1f%% of this window is a SINGLE colour (luminance %s) - nothing is drawn "
                       "on it. %d distinct luminance(s) found, which on a blank window is the "
                       "CHROME: the titlebar and its buttons draw whatever the page does not"
                       % (share * 100.0, m.get("modalLuminance"), d))
    return PAINTED, ("the commonest colour covers %.1f%% of this window across %d distinct "
                     "luminance(s) - it has content on it (blank needs >= %.0f%%)"
                     % (share * 100.0, d, BLANK_MODAL_SHARE * 100.0))


def look(pid, quartz=None, samples=60):
    """One look at one window. -> dict, always the same shape."""
    out = {"pid": pid, "windowId": None, "state": UNKNOWN, "why": "", "measure": None,
           "bars": {"modalShare": BLANK_MODAL_SHARE, "strikes": BLANK_STRIKES,
                    "distinctReportedOnly": BLANK_MAX_DISTINCT}}
    wid, why = window_for(pid, quartz=quartz)
    if wid is None:
        out["why"] = why
        return out
    out["windowId"] = wid
    shot, why = _grab(wid, quartz=quartz)
    if shot is None:
        out["why"] = why
        return out
    m = measure(shot, samples=samples)
    out["measure"] = {k: v for k, v in m.items() if k != "why"}
    out["state"], out["why"] = verdict(m)
    # ⚠⚠ AND A UNIFORM FRAME IS ONLY BLANK IF NOTHING IS COVERING IT. See occluded_by: a window
    # under another app captures as a flat frame, and calling that BLANK accuses a healthy console.
    if out["state"] == BLANK:
        cov, cwhy = occluded_by(pid, quartz=quartz)
        if cov is None:
            out["state"] = UNKNOWN
            out["why"] = ("the frame is uniform, and whether anything is covering the window "
                          "could not be asked (%s) — so BLANK is not sayable" % cwhy)
        elif cov:
            out["state"] = OCCLUDED
            out["why"] = ("NOT blank — %s. The uniform frame is what capturing a covered window "
                          "returns, and the page reporting hidden/not-painting is CORRECT for "
                          "one." % cwhy)
    out["occludedBy"] = None if out["state"] != OCCLUDED else out["why"]
    return out


def blank_strikes(pid, strikes=None, quartz=None, sleep=None):
    """Is this window blank across CONSECUTIVE looks? -> dict

    ⚠⚠ ONE FRAME IS A SAMPLE, NOT A VERDICT. A repaint, a resize or a Space switch can catch a
    window mid-nothing. A window that is genuinely dead stays dead, so this asks again.

    ⚠ AND A SINGLE UNKNOWN ENDS IT. If any look could not be taken, the run is UNKNOWN — not
    "fewer strikes than needed", which would quietly read as healthier than the truth.
    """
    n = int(strikes or BLANK_STRIKES)
    looks, hit = [], 0
    for i in range(n):
        if sleep and i:
            sleep(0.35)
        r = look(pid, quartz=quartz)
        looks.append(r)
        if r["state"] == UNKNOWN:
            return {"state": UNKNOWN, "strikes": i, "needed": n, "looks": looks,
                    "why": "look %d of %d could not be taken (%s), so nothing is established "
                           "about this window" % (i + 1, n, r["why"])}
        if r["state"] == BLANK:
            hit += 1
        else:
            return {"state": PAINTED, "strikes": hit, "needed": n, "looks": looks,
                    "why": "look %d of %d found content on the window, so it is not blank: %s"
                           % (i + 1, n, r["why"])}
    return {"state": BLANK, "strikes": hit, "needed": n, "looks": looks,
            "why": "%d consecutive look(s) found a window with nothing drawn on it" % hit}


def contradicts_a_blank_beat(pid, quartz=None):
    """Do the PIXELS refute the page's own claim to be blank? -> (bool, why)

    THE VALUABLE DIRECTION, and the one his rescue needs most. `_UI_BEAT`'s blank counters come
    from JavaScript inside the window; this is the only check that can say *"the page thinks it is
    empty and I can see that it is not"*. True here should HOLD a rescue.

    ⚠ UNKNOWN IS NOT A CONTRADICTION. A capture that could not be taken returns False with its
    reason, so a missing witness never stops a rescue the beat genuinely called for — silence is
    not evidence. [[feedback-silence-is-not-evidence]]
    """
    r = look(pid, quartz=quartz)
    if r["state"] == PAINTED:
        return True, ("the window server's own bitmap shows content on this window: %s" % r["why"])
    if r["state"] == UNKNOWN:
        return False, ("the pixels could not be read (%s), so they refute nothing - this is an "
                       "absent witness, not a disagreeing one" % r["why"])
    return False, "the pixels agree that nothing is drawn on this window: %s" % r["why"]


def rescue_worked(pid, quartz=None, sleep=None, settle=2.5):
    """After a reload, did PAINTING actually come back? -> dict

    ⚠⚠ MEASURED ON HIS MACHINE, 2026-09-04, AND THIS IS WHY THE FUNCTION EXISTS. The watchdog
    detected the fault correctly and fired correctly — `uiBeat.rescues = 1`, reason *"the page is
    BEATING and DRAWING NOTHING: 20 beats with no frame while the DOM stayed intact (11841
    elements)"* — and **the window was still blank white afterwards**, with `frozenBeats` climbing
    29 → 38 and `painting` still false. The detection works. **The CURE does not cure**, and
    nothing anywhere checked: `rescues: 1` reads exactly like "handled".

    A self-heal that is never verified is a fault that stops being reported — by the machine.
    It goes on being reported by HIM. [[feedback-verify-not-proxy]] [[the-unjoined-end]]

    ⚠ UNKNOWN STAYS UNKNOWN. If the pixels cannot be read the answer is None, never "it worked".
    """
    if sleep:
        sleep(settle)
    r = look(pid, quartz=quartz)
    if r["state"] == UNKNOWN:
        return {"worked": None, "state": UNKNOWN, "why": (
            "whether the reload restored painting is UNKNOWN - the pixels could not be read (%s). "
            "That is not success." % r["why"])}
    if r["state"] == PAINTED:
        return {"worked": True, "state": PAINTED, "why": (
            "the reload restored painting: %s" % r["why"])}
    return {"worked": False, "state": BLANK, "why": (
        "THE RELOAD DID NOT RESTORE PAINTING - the window is still blank after it. Reloading the "
        "document cannot fix a compositor that has stopped presenting frames for this window, and "
        "counting this as a completed rescue is how the fault goes on being reported by him "
        "instead of by the machine. %s" % r["why"])}


def main(argv):
    pid = int(next((a for a in argv if a.isdigit()), os.getpid()))
    r = look(pid)
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nPAINT WITNESS - what the compositor actually shows for pid %d\n" % pid)
    print("  window   %s" % (r["windowId"] if r["windowId"] is not None else "UNKNOWN"))
    print("  state    %s" % r["state"])
    m = r.get("measure") or {}
    if m:
        print("  measured %d sample(s) - %s distinct luminance(s), modal share %s, mean %s"
              % (m.get("samples"), m.get("distinct"), m.get("modalShare"), m.get("meanLuminance")))
    print("  bar      blank needs modalShare >= %.2f, over %d consecutive looks (distinct is "
          "reported, not required - chrome alone draws several)"
          % (BLANK_MODAL_SHARE, BLANK_STRIKES))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
