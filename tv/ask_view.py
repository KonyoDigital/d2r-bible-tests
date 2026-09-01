"""ASK FOR A LOOK — name the pane the console should show, so a human eye can photograph it.

Konyo, 2026-09-01: *"you make it open instead of the sessions tab.. the place you want it to
screenshot live.. that way it opens exactly where you want then it screenshots it back to you."*

THE PROBLEM THIS SOLVES. The visual harness has eyes and no hands. Synthetic pointer events need
macOS Accessibility permission; without it `CGEventPost` succeeds and moves nothing, so the eye
can look and cannot click. But almost nothing that is actually owed needs a pointer — it needs the
RIGHT PANE to be in front of the camera. This writes that request; the console honors it once,
stamps the screen so the returned photograph is attributable, and puts his tab back.

    python3 tv/ask_view.py vault --brief HE-2 --why "read the item count on screen"
    python3 tv/ask_view.py --clear
    python3 tv/ask_view.py --show

⚠ IT IS A REQUEST, NOT A COMMAND. The most it can do is change which tab is in front. It cannot
open the game, cannot arm the prune, cannot apply anything, and it is refused outright while a
capture is live because routing the shell mid-reel throws the reel away.

⚠ AND IT IS ONE SHOT. The console honors an `id` exactly once, so a file left on disk never
becomes a console that keeps yanking itself back to a tab he keeps leaving.
"""

import argparse
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PATH = os.environ.get("TV_VIEW_REQUEST") or os.path.join(HERE, ".view_request.json")

#: kept in step with control_app.VIEW_REQUEST_PANES — imported rather than retyped, because two
#: copies of one list is exactly the drift that makes a request silently unroutable. [[copy-drift]]
try:
    from control_app import VIEW_REQUEST_PANES as PANES
except Exception:
    PANES = ()


def ask(view, brief=None, why=None, ttl_s=600, path=None):
    """Place the request. -> the row written."""
    ts = int(time.time() * 1000)
    row = {"view": str(view).strip().lower(),
           "brief": (str(brief).strip() if brief else None),
           "why": (str(why).strip()[:160] if why else None),
           "ttlS": int(ttl_s),
           "ts": ts,
           "id": "%s@%d" % (str(view).strip().lower(), ts)}
    p = path or PATH
    # ⚠ WRITE VIA A TEMP AND RENAME. The console polls this file about once a second, so a plain
    # open(...,"w") gives it a real chance to read a half-written file — and `open(p,"w")` also
    # EMPTIES the target before the payload exists. [[open-for-write-truncates-first]]
    tmp = p + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(row, indent=2))
    os.replace(tmp, p)
    return row


def clear(path=None):
    p = path or PATH
    try:
        os.remove(p)
        return True
    except OSError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="ask the console to show a pane")
    ap.add_argument("view", nargs="?", help="pane to show, e.g. vault")
    ap.add_argument("--brief", help="which human-eyes brief this look serves, e.g. HE-2")
    ap.add_argument("--why", help="one line: what question the picture should settle")
    ap.add_argument("--ttl", type=int, default=600, help="seconds before his tab is put back")
    ap.add_argument("--clear", action="store_true", help="withdraw any standing request")
    ap.add_argument("--show", action="store_true", help="print the standing request")
    a = ap.parse_args(argv)

    if a.clear:
        print("withdrawn" if clear() else "there was no standing request")
        return 0
    if a.show or not a.view:
        try:
            print(io.open(PATH, encoding="utf-8").read())
        except OSError:
            # ⚠ ABSENT IS NOT EMPTY. "nobody has asked" is a real state and says so in words.
            print("no standing request — nobody has asked for a look")
        return 0
    v = a.view.strip().lower()
    if PANES and v not in PANES:
        # ⚠ REFUSE AN UNROUTABLE PANE AT THE DOOR. `switchTab` no-ops SILENTLY on a name it does
        # not know (the v2120 scar), so the console would sit on whatever was already showing and
        # the eye would photograph it believing it was the requested pane. A wrong picture
        # confidently labelled is worse than no picture. [[the-unjoined-end]]
        print("%r is not a pane this console routes to.\nknown: %s" % (v, ", ".join(sorted(PANES))))
        return 2
    row = ask(v, a.brief, a.why, a.ttl)
    print("asked for %s%s — the console honors it ONCE and puts his tab back in %ds"
          % (row["view"], (" (%s)" % row["brief"]) if row["brief"] else "", row["ttlS"]))
    print("  %s" % PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
