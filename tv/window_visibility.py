"""Is his console window ACTUALLY on his screen? — asked of the OS, not of the page.

WHY THIS MODULE EXISTS. The console's self-heal reads `document.visibilityState` out of the
page's own heartbeat. That is circular, and the circle latched shut on 2026-08-31:

    uiBeat:  n: 436   hidden: True   ageS: 128.6   silenceBoundS: 60.0   rescues: 0

WebKit throttles - and can suspend outright - the timers of a window it considers hidden. The
heartbeat IS a timer (`setInterval(_beat, 5000)`). So the only thing that could ever clear the
`hidden` flag is a beat, and a hidden window is precisely the thing that stops beating. From the
first hidden beat onward the rescue is disarmed FOR EVER, and Konyo watched a black window on
his own screen while the server explained that he could not see it.

v2325 was right that silence from a window he is not looking at proves nothing, and this module
does not undo that. It supplies the missing half: a witness that does not live inside the thing
being judged. Only a POSITIVE, independent "it is on screen right now" may overrule the flag.

WHY CGWindowList AND NOT A SCREENSHOT. Window *listing* needs no Screen Recording grant; only
capturing pixels does. That distinction is load-bearing on this Mac - a capture-based probe
would answer "cannot tell" for a denied app and we would be back to guessing.
[[unknown-stays-unknown]] [[chrome-cdp-mac]]

THREE ANSWERS, NEVER TWO. True = the OS lists an on-screen window for this pid. False = it lists
this pid's windows and none are on screen. None = COULD NOT ESTABLISH - no Quartz, an exception,
or no window of ours known at all. None must never be read as False: "nobody looked" and "it is
not there" are opposite facts, and collapsing them is how the first version of this bug shipped.
"""

import os

MIN_ON_SCREEN_PX = 40 * 40   # a 1x1 helper window is not "his console is on screen"
#: how much of his window another app must cover before he genuinely cannot see it. Measured on the
#: case that produced REG-594: Citrix Viewer covered the console 100.0%. A partial overlap still
#: leaves him something to look at, so this is deliberately near-total rather than "any overlap".
COVERED_PCT = 95.0


def _quartz():
    try:
        import Quartz
        return Quartz
    except Exception:
        return None


def on_screen(pid=None, quartz=None):
    """Return (True|False|None, why). None means NOT ESTABLISHED - never 'no'."""
    pid = os.getpid() if pid is None else int(pid)
    Q = quartz if quartz is not None else _quartz()
    if Q is None:
        return None, "Quartz is not importable here - cannot ask the window server"
    try:
        opts = Q.kCGWindowListOptionOnScreenOnly | Q.kCGWindowListExcludeDesktopElements
        rows = Q.CGWindowListCopyWindowInfo(opts, Q.kCGNullWindowID)
    except Exception as exc:
        return None, "the window server refused the list (%s)" % type(exc).__name__
    if rows is None:
        return None, "the window server returned nothing at all"

    mine = 0
    for row in rows:
        try:
            if int(row.get("kCGWindowOwnerPID", -1)) != pid:
                continue
        except Exception:
            continue
        mine += 1
        bounds = row.get("kCGWindowBounds") or {}
        try:
            area = float(bounds.get("Width", 0)) * float(bounds.get("Height", 0))
        except (TypeError, ValueError):
            area = 0.0
        if area >= MIN_ON_SCREEN_PX:
            return True, "the window server lists a %dx%d window for pid %d on screen" % (
                int(float(bounds.get("Width", 0))), int(float(bounds.get("Height", 0))), pid)
    if mine:
        return False, "pid %d owns %d on-screen entr(ies), all too small to be his console" % (pid, mine)
    return False, "the window server lists no on-screen window for pid %d" % pid


def _union_area(rects):
    """Area covered by a set of rectangles, counting overlap ONCE. -> float

    ⚠⚠ REG-595 — SUMMING PERCENTAGES IS THE WRONG ARITHMETIC AND IT FAILS BOTH WAYS. Adding each
    window's own share reports three windows stacked on the SAME half of his console as 96%
    covered while he is looking at the other half; asking each one separately (what v2615 did)
    misses two windows that tile it completely and reports "nothing is covering it". The union is
    the only measure that answers the question actually being asked: **how much of his window can
    he not see.**

    Coordinate compression rather than a raster: the window count here is a handful, and a grid
    would make the answer depend on a resolution nobody chose.
    """
    rects = [r for r in rects if r[2] > r[0] and r[3] > r[1]]
    if not rects:
        return 0.0
    xs = sorted(set([r[0] for r in rects] + [r[2] for r in rects]))
    ys = sorted(set([r[1] for r in rects] + [r[3] for r in rects]))
    total = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        for j in range(len(ys) - 1):
            y0, y1 = ys[j], ys[j + 1]
            for (a0, b0, a1, b1) in rects:
                if a0 <= x0 and a1 >= x1 and b0 <= y0 and b1 >= y1:
                    total += (x1 - x0) * (y1 - y0)
                    break
    return total


def covered_by(pid=None, quartz=None):
    """What is sitting ON TOP of his window? -> (list-of-descriptions | None, why)

    ⚠⚠ REG-594 — "LISTED ON SCREEN" IS NOT "HE CAN SEE IT", AND THE GAP COST A WHOLE DAY.
    `on_screen()` answers whether the window server lists the window, and a window covered 100% by
    another app IS listed. `contradicts_a_hidden_beat()` treated that as proof the page was lying
    about being hidden, so the rescue kept reloading a console that was simply behind something.
    MEASURED 2026-09-04: **Citrix Viewer, 1289x752 at (108,78), covering the console's 1120x660 at
    (175,148) by 100.0%**, and frontmost — while the console reported `hidden: true`,
    `painting: false`, and had been RELOADED SEVEN TIMES.

    The page was right every time. WebKit suspends painting on an occluded view by design, so
    `hidden` and `not painting` are the CORRECT readings of a healthy console behind a window.
    v2325's rule already said it — *"a window he cannot see is not a window that is stuck"* — and
    the check written to enforce it asked the wrong question.

    The z-order was always available: `CGWindowListCopyWindowInfo` returns windows FRONT TO BACK,
    so anything listed before his is above it. [[feedback-verify-not-proxy]]
    """
    pid = os.getpid() if pid is None else int(pid)
    Q = quartz if quartz is not None else _quartz()
    if Q is None:
        return None, "Quartz is not importable here - occlusion cannot be asked"
    try:
        opts = Q.kCGWindowListOptionOnScreenOnly | Q.kCGWindowListExcludeDesktopElements
        rows = Q.CGWindowListCopyWindowInfo(opts, Q.kCGNullWindowID)
    except Exception as exc:
        return None, "the window server refused the list (%s)" % type(exc).__name__
    if rows is None:
        return None, "the window server returned nothing at all"
    mine, mine_layer, above = None, None, []
    for row in rows:                                  # FRONT to BACK
        b = row.get("kCGWindowBounds") or {}
        try:
            rect = (float(b.get("X", 0)), float(b.get("Y", 0)),
                    float(b.get("Width", 0)), float(b.get("Height", 0)))
        except (TypeError, ValueError):
            continue
        if rect[2] * rect[3] < MIN_ON_SCREEN_PX:
            continue
        try:
            same = int(row.get("kCGWindowOwnerPID", -1)) == pid
        except Exception:
            same = False
        try:
            layer = int(row.get("kCGWindowLayer") or 0)
        except (TypeError, ValueError):
            layer = 0
        if same:
            mine, mine_layer = rect, layer
            break
        above.append((str(row.get("kCGWindowOwnerName") or "?"), rect, layer))
    if mine is None:
        return None, "no window of his was listed to compare against"
    mx, my, mw, mh = mine
    # ⚠⚠ SYSTEM CHROME IS NOT AN OCCLUDER, AND THE FIRST CUT OF THIS SAID IT WAS. Measured: the
    # Dock's backing window is 1470x956 at (0,0) on LAYER 20 and the menu bar is layer 24 — both
    # span the whole screen and hide nothing. Counting them made his console read "covered" always,
    # which would have DISABLED the rescue outright: an over-correction strictly worse than the
    # false alarms it was fixing. Only windows on the SAME layer as his own are real occluders —
    # Citrix Viewer is layer 0, exactly like the console.
    #
    # ⚠ COMPARED TO HIS WINDOW'S OWN LAYER, never hardcoded to 0. A layer filter has cost this repo
    # once already: his D2R game window sits on layer 26 and a `layer == 0` test dropped it
    # entirely. [[d2r-game-window-layer-26]]
    #
    # ⚠⚠ REG-595 — ASK WHAT HE CANNOT SEE, NOT WHETHER ANY SINGLE WINDOW HIDES IT. v2615 compared
    # each covering window against the bar on its own, so Citrix on one half of the screen and a
    # browser on the other — together hiding the console completely — came back as an EMPTY list
    # and the reason said "nothing is covering it". He has said Citrix Viewer is work, unrelated
    # to this console, so it lives beside other windows rather than always over everything: the
    # tiled case is his ordinary desk, not a corner. The clipped rectangles are unioned instead.
    clipped, parts = [], []
    for name, (x, y, w, h), layer in above:
        if mine_layer is not None and layer != mine_layer:
            continue
        x0, y0 = max(x, mx), max(y, my)
        x1, y1 = min(x + w, mx + mw), min(y + h, my + mh)
        if x1 <= x0 or y1 <= y0:
            continue
        clipped.append((x0, y0, x1, y1))
        parts.append((name, 100.0 * (x1 - x0) * (y1 - y0) / float(mw * mh or 1)))
    if not clipped:
        return [], ""
    pct = 100.0 * _union_area(clipped) / float(mw * mh or 1)
    if pct < COVERED_PCT:
        return [], ""
    out = ["%s (%.1f%%)" % (name, p) for name, p in parts]
    if len(out) == 1:
        return out, "%s is on top of it, so he cannot see it" % out[0]
    return out, ("%s cover %.1f%% of it between them, so he cannot see it"
                 % (", ".join(out), pct))


def contradicts_a_hidden_beat(pid=None, quartz=None):
    """True ONLY when the OS positively says the window is on screen AND NOTHING IS COVERING IT,
    while the page's last word was 'hidden'. Unknown stays unknown, and unknown does NOT overrule
    v2325.

    ⚠⚠ REG-594 — this used to return True for a window listed on screen and covered 100% by
    another app, which is how a healthy console got reloaded seven times in one day. A covered
    window CONFIRMS a hidden beat; it does not contradict it. See covered_by().
    """
    seen, why = on_screen(pid=pid, quartz=quartz)
    if seen is not True:
        return False, why
    cov, cwhy = covered_by(pid=pid, quartz=quartz)
    if cov is None:
        # ⚠ UNKNOWN IS NOT PERMISSION. If occlusion could not be asked, the old answer is not
        # safe to keep - it is the answer that caused the false alarms.
        return False, ("%s, but whether anything is covering it could not be asked (%s) - so this "
                       "does not contradict a hidden beat" % (why, cwhy))
    if cov:
        return False, ("%s - and %s. A covered window CONFIRMS a hidden beat rather than "
                       "contradicting it" % (why, cwhy))
    return True, "%s, and nothing is covering it" % why


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import sys
    target = int(sys.argv[1]) if len(sys.argv) > 1 else os.getpid()
    seen, why = on_screen(target)
    print("on_screen(%d) = %s" % (target, seen))
    print("  %s" % why)
