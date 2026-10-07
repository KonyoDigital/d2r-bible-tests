# -*- coding: utf-8 -*-
"""THE ONE LAUNCHER DECISION, Mac and Windows: bring the running console forward, leave it, or replace it
(REG-1514, REG-1758, REG-1940).

The second eye on v3523's bg-service merge (4e22a57a, #231): start_tvd_mac.sh asked a console forward only when
its window was in the BACKGROUND, and anything else - including a window that was simply UP - fell through to the
soft-kill of :17772. So a Desktop double-click on a console that was running fine, maybe filming his session, killed
it and booted a fresh one. Until REG-1758 the Windows launcher only ever brought a running console forward, so an old
process kept serving :17772 after the disk had moved. Both launchers now ask this function. The kill exists for one
reason (v1379.1): a double-click must never window-only onto a STALE console still running older code. The console
answers that itself (/api/freshness, /api/status moduleFreshness, v3288), so the rule is now:

  · it answers, its window is up (front, fullscreen) or backgrounded, and it does not say it is older -> ask it
    forward; if it comes, this launch ends there (FORWARD, exit 0);
  · it SAYS it is older than the disk, it SAYS it has no window (headless, a window-only view), or nothing is
    serving the port at all -> replace it (REPLACE, exit 3);
  · anything this file cannot tell - a timeout, an unreadable or ok:false answer, a window mode it does not know,
    a front request that times out or is refused, the decision's own time running out, the decision raising ->
    leave it running (LEAVE, exit 2). UNKNOWN IS NOT CONSENT (REG-1940): from REG-1758 (v3571) every one of these
    exited 1, and the Windows launcher read 1 as consent and Stop-Process -Force'd the console on :17772 - a Desktop click
    while he played, a 5 s timeout under the game, and his console was gone. Exit 1 is not used at all: an
    uncaught exception exits 1, so 1 can never mean "replace".
  · a freshness check that TIMES OUT is not an answer. The window was already read. Ask that console forward.
    Measured on the ALT: /api/status took 10.5s under the game, the icon waits 5s, and the timeout was read as
    "cannot say", which replaced a healthy console. The small route is /api/freshness. An old console without
    it (HTTP 404) is asked /api/status once. A timeout is not asked twice.

Driven by tv/test_the_launcher_brings_a_running_console_forward.py against a fake console on an ephemeral port.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

FROM = "mac-launcher"

# REG-1940 - THREE ANSWERS, NOT TWO. Measured against a fake console before this fix: a current console that is
# FULLSCREEN (v3579 added that mode - the Windows default - and this file only knew front/background), a slow
# /api/window, a slow front request and an ok:false front reply all came back "replace".
FORWARD = "forward"   # it came forward - this launch ends
LEAVE = "leave"       # could not tell - it is left running, never stopped on a guess
REPLACE = "replace"   # it said it is older than the disk or has no window, or nothing serves the port
#: exit codes. 1 is deliberately NOT one of them: an uncaught exception exits 1, so 1 must never mean "replace".
EXIT = {FORWARD: 0, LEAVE: 2, REPLACE: 3}
#: window modes that are a window this launch can bring forward (control_app.window_mode_payload)
WINDOW_UP = ("front", "fullscreen", "background")
#: window modes the console says have no window to show - a double-click needs one, so they are replaced
NO_WINDOW = ("headless", "window-only")
#: the whole decision gets this long, so three slow calls cannot hold the Desktop icon for 15-20 s (v1445/v1463).
#: Running out is "could not tell", which never replaces anything.
BUDGET_S = 9.0


def _get(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def _post(url, body, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def _refused(e):
    """True only when nothing is listening on the port (connection refused). A timeout, a reset or an HTTP
    error means something IS there and did not answer in time - that is not a reason to kill it."""
    if isinstance(e, urllib.error.HTTPError):
        return False
    if isinstance(e, ConnectionRefusedError):
        return True
    return isinstance(e, urllib.error.URLError) and isinstance(getattr(e, "reason", None), ConnectionRefusedError)


def _freshness(base, left):
    """-> (fresh, answered). `left()` is the time the decision has left, in seconds.

    fresh is True (this process is the file on disk), False (it is older), or None (it cannot say).
    answered is False when no freshness body came back: the wait ran out, the socket never
    answered, the route returned an HTTP error other than 404, or the body could not be read.
    A 404 means this console has no /api/freshness yet, so /api/status is asked once. Any other
    failure is not asked twice. Only a body that says the code is older replaces (REG-1940).
    """
    body = None
    t = left()
    if t <= 0:
        return None, False
    try:
        body = _get(base + "/api/freshness", t) or {}
    except urllib.error.HTTPError as e:
        if getattr(e, "code", None) != 404:
            return None, False
    except Exception:
        return None, False
    if not isinstance(body, dict) or "known" not in body:
        t = left()
        if t <= 0:
            return None, False
        try:
            body = (_get(base + "/api/status", t) or {}).get("moduleFreshness") or {}
        except Exception:
            return None, False
    if isinstance(body, dict) and body.get("known"):
        return (not bool(body.get("stale"))), True
    return None, True


def decide(port, who=FROM, timeout=5.0, budget=BUDGET_S, clock=time.monotonic):
    """-> (verdict, why). verdict is FORWARD, LEAVE or REPLACE; main() turns it into EXIT[verdict]."""
    base = "http://127.0.0.1:%d" % int(port)
    end = clock() + float(budget)

    def left():
        return min(float(timeout), end - clock())

    try:
        win = _get(base + "/api/window", left())
    except Exception as e:
        if _refused(e):
            return REPLACE, "nothing is serving :%d (%s) - the launcher boots one" % (int(port), type(e).__name__)
        return LEAVE, ("the console did not answer /api/window in time (%s) - it is left running, "
                       "never replaced on a timeout (REG-1940)" % type(e).__name__)
    mode = str((win.get("mode") if isinstance(win, dict) else "") or "")
    if mode in NO_WINDOW:
        return REPLACE, "its window is %r - a double-click needs a window, so it is replaced" % mode
    if mode not in WINDOW_UP:
        return LEAVE, ("its window answer was %r - this launcher cannot tell what that is, so the console is left "
                       "running, never replaced on a guess (REG-1940)" % (mode or "no mode"))
    fresh, answered = _freshness(base, left)
    if fresh is False:
        return REPLACE, "it runs code OLDER than the file on disk - replaced so this checkout boots (v1379.1)"
    t = left()
    if t <= 0:
        return LEAVE, ("the icon's %.0fs ran out before the console could be asked forward - it is left running "
                       "(REG-1940)" % float(budget))
    try:
        rec = _post(base + "/api/window", {"do": "front", "from": who}, t) or {}
    except Exception as e:
        return LEAVE, ("it did not answer the front request (%s) - it is left running and focused from outside, "
                       "never replaced on a timeout (REG-1940)" % type(e).__name__)
    if not (isinstance(rec, dict) and rec.get("ok")):
        _why = str(rec.get("why") or "")[:120] if isinstance(rec, dict) else ""
        return LEAVE, ("it answered but did not come forward%s - it is left running and focused from outside, "
                       "never replaced on a refusal (REG-1940)" % ((" (%s)" % _why) if _why else ""))
    if fresh is True:
        return FORWARD, ("the running console (window %s, current code) was brought to the front instead of "
                         "replaced" % mode)
    if not answered:
        return FORWARD, ("the running console (window %s) did not answer the freshness check in time - "
                         "asked forward instead of replaced" % mode)
    return FORWARD, ("the running console (window %s) could not say whether it is current - "
                     "asked forward instead of replaced" % mode)


def main(argv):
    port = 17772
    who = FROM
    try:
        if "--port" in argv:
            port = int(argv[argv.index("--port") + 1])
        if "--from" in argv:
            who = argv[argv.index("--from") + 1]
        verdict, why = decide(port, who)
    except Exception as e:
        verdict, why = LEAVE, "the decision itself raised %s - nothing is replaced on a guess (REG-1940)" % (
            type(e).__name__)
    print(why)
    return EXIT.get(verdict, EXIT[LEAVE])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
