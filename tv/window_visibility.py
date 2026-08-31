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


def contradicts_a_hidden_beat(pid=None, quartz=None):
    """True ONLY when the OS positively says the window is on screen while the page's last word
    was 'hidden'. Unknown stays unknown, and unknown does NOT overrule v2325."""
    seen, why = on_screen(pid=pid, quartz=quartz)
    return (seen is True), why


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
