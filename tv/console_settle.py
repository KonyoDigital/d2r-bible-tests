#!/usr/bin/env python3
"""#42c — BEFORE THE CONSOLE DEMOS, LET HIS CONSOLE FINISH MOVING ONTO THE CODE BEING PUSHED.

Measured 2026-09-30 on v3526's push #1: the fast-forward of main put new code on disk, his console's version-drift lane
re-exec'd onto it at 10:18:15, and the pre-push demos ran 7 s later - j7_shelfStory timed out against a console that was
still booting, and a green tree was REFUSED. Sixteen of sixteen passed once it had settled.

So the hook asks /api/status first and waits, bounded, while the console:
  · runs OLDER code than the file on disk and its relaunch is not held (the re-exec is coming), or
  · relaunched less than MIN_AGE_S ago, or
  · says its engine is not ready.
A held relaunch, a console that does not answer, or the bound running out all go straight on - the demos decide, and the
hook's own freshness warning says what they tested. This never refuses a push by itself.
[[stale-reading]] [[unknown-stays-unknown]]
"""
import argparse
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

#: a console younger than this (seconds since its server module loaded) is still settling
MIN_AGE_S = 30
#: the longest the hook waits - a little over the drift lane's 300 s check, so a coming re-exec is seen
MAX_WAIT_S = 360
POLL_S = 5


def read(port=17772, timeout=5):
    """/api/status of the console on `port`. -> dict | None (it did not answer)"""
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/status" % port, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def verdict(st, now_ms, min_age_s=MIN_AGE_S):
    """Is the console settled enough to demo against? Pure. -> ("go" | "wait", why)"""
    if not isinstance(st, dict):
        return "go", "the console did not answer /api/status - the demos decide"
    f = st.get("moduleFreshness") if isinstance(st.get("moduleFreshness"), dict) else {}
    drift = st.get("drift") if isinstance(st.get("drift"), dict) else {}
    rl = drift.get("relaunch") if isinstance(drift.get("relaunch"), dict) else {}
    if f.get("known") and f.get("stale"):
        if rl.get("may") is False:
            return "go", ("it runs older code than the file on disk and its relaunch is held (%s) - the demos test "
                          "the server as it was" % (rl.get("waiting") or rl.get("blocker") or rl.get("why") or "?"))
        return "wait", "it runs older code than the file on disk - its re-exec onto the pushed code is coming"
    loaded = f.get("loadedAtMs")
    if isinstance(loaded, (int, float)) and not isinstance(loaded, bool):
        age = (now_ms - loaded) / 1000.0
        if age < min_age_s:
            return "wait", "it relaunched %.0f s ago - letting it settle to %d s" % (max(0.0, age), min_age_s)
    if st.get("engineReady") is False:
        return "wait", "its engine is not ready yet"
    return "go", "settled"


# named wait_until_settled, never `wait`: a production `def wait` anywhere flips lane_census's thread target
# `target=wp.wait` (a Popen's) from FOREIGN to UNKNOWN - measured on this very file's first gate run (v3528)
def wait_until_settled(port=17772, max_wait_s=MAX_WAIT_S, min_age_s=MIN_AGE_S, poll_s=POLL_S, fetch=None, clock=None, sleep=None):
    """Poll until the console is settled or the bound runs out. -> (state, why, waited_s); state is "go" | "timeout"."""
    fetch = fetch or (lambda: read(port))
    clock = clock or time.time
    sleep = sleep or time.sleep
    t0 = clock()
    first_why = None
    while True:
        state, why = verdict(fetch(), int(clock() * 1000), min_age_s)
        if state == "go":
            return "go", (why if first_why is None else "%s (waited: %s)" % (why, first_why)), clock() - t0
        first_why = first_why or why
        if clock() - t0 >= max_wait_s:
            return "timeout", "still not settled after %d s: %s" % (int(clock() - t0), why), clock() - t0
        sleep(poll_s)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=17772)
    ap.add_argument("--wait", type=float, default=MAX_WAIT_S)
    ap.add_argument("--min-age", type=float, default=MIN_AGE_S)
    a = ap.parse_args(argv)
    state, why, waited = wait_until_settled(a.port, a.wait, a.min_age)
    print("console settle: %s after %.0f s - %s" % (state, waited, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
