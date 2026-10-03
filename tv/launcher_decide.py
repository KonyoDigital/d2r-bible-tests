# -*- coding: utf-8 -*-
"""THE ONE LAUNCHER DECISION, Mac and Windows: bring the running console forward, or replace it (REG-1514, REG-1758).

The second eye on v3523's bg-service merge (4e22a57a, #231): start_tvd_mac.sh asked a console forward only when
its window was in the BACKGROUND, and anything else - including a window that was simply UP - fell through to the
soft-kill of :17772. So a Desktop double-click on a console that was running fine, maybe filming his session, killed
it and booted a fresh one. Until REG-1758 the Windows launcher only ever brought a running console forward, so an old process kept serving :17772 after the disk had moved. Both launchers now ask this function. The kill exists for one reason (v1379.1):
a double-click must never window-only onto a STALE console still running older code. The console answers that
itself (/api/status moduleFreshness, v3288), so the rule is now:

  · it answers, its window is up or backgrounded, and it says it IS the code on disk -> ask it forward; if it comes,
    this launch ends there (exit 0);
  · it is stale, headless, a window-only view, cannot say whether it is current, or does not come forward ->
    replace it, exactly as before (exit 1) - v1460's trap is a Desktop icon that does nothing.
  · a console whose window is BACKGROUNDED and cannot say whether it is current is still asked forward - that is
    what bg-service shipped, and replacing it would stop the reel it is filming.

Driven by tv/test_the_launcher_brings_a_running_console_forward.py against a fake console on an ephemeral port.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

FROM = "mac-launcher"


def _get(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def _post(url, body, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


def decide(port, who=FROM, timeout=5.0):
    """-> (bring_forward_done: bool, why: str)"""
    base = "http://127.0.0.1:%d" % int(port)
    try:
        mode = str((_get(base + "/api/window", timeout) or {}).get("mode") or "")
    except Exception as e:
        return False, "the console did not answer /api/window (%s) - replacing it" % type(e).__name__
    if mode not in ("front", "background"):
        return False, "its window is %r - a double-click needs a window, so it is replaced" % (mode or "unknown")
    fresh = None
    try:
        f = (_get(base + "/api/status", timeout) or {}).get("moduleFreshness") or {}
        if f.get("known"):
            fresh = not f.get("stale")
    except Exception:
        fresh = None
    if fresh is False:
        return False, "it runs code OLDER than the file on disk - replaced so this checkout boots (v1379.1)"
    if fresh is None and mode == "front":
        return False, "its window is up but it cannot say whether it runs the current code - replaced (v1379.1)"
    try:
        ok = bool((_post(base + "/api/window", {"do": "front", "from": who}, timeout) or {}).get("ok"))
    except Exception as e:
        return False, "it would not come forward (%s) - replaced so the icon never does nothing (v1460)" % type(e).__name__
    if not ok:
        return False, "it answered but did not come forward - replaced so the icon never does nothing (v1460)"
    return True, "the running console (window %s, current code) was brought to the front instead of replaced" % mode


def main(argv):
    port = 17772
    who = FROM
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])
    if "--from" in argv:
        who = argv[argv.index("--from") + 1]
    done, why = decide(port, who)
    print(why)
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
