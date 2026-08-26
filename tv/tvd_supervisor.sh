#!/bin/bash
# 🛡️ TV DIABLO console supervisor — keeps :17772 bulletproof always-up (Konyo 2026-07-22).
# Runs under launchd (com.konyo.tvd-console) with KeepAlive. Every ~20s it ensures the
# control console answers on :17772 — bringing up a HEADLESS instance if nothing owns it.
#
# POLITE: if the pause-flag exists (a real TCC scanning app wants the port), the supervisor
# stays out of the way and does NOT hold :17772 — so `tvd-scan.sh` can hand the port to
# TV DIABLO.app for live screen-capture. `tvd-console.sh` clears the flag; console resumes.
#
# NOTE: a launchd/shell-launched headless server has NO Screen-Recording TCC grant, so it
# serves the console/API/retro but cannot itself capture the game. Live scanning = the .app.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PAUSE_FLAG="$HERE/.tvd_supervisor_pause"
LOG="$HERE/control_app.log"
PORT=17772
# v2145 — the headless console the supervisor revives follows the shipped build too, under the same
# guards as the window (refuses while a sweep reads or while he is filming). TV_AUTO_RELAUNCH=0
# returns it to announce-only.
# ⚠ v2146 — DISARMED AGAIN, DELIBERATELY, ONE VERSION AFTER ARMING IT. He said yes to auto-relaunch
# ON A CONDITION: "just make sure the other profile locking of the chronicles and everything is
# connected to the profile and pc related to it.. so nothing ever gets deleted or regressed." A
# cross-family review of the v2145 guard showed that condition is NOT met, and the gap is not small:
#
#   · THE GUARD CANNOT SEE THE CASE IT WAS WRITTEN FOR. Identity is only {owner, pfx}, and a CLAIMED
#     board publishes pfx:'' — so a brand-new claimed store is byte-identical to the old one and
#     board_identity_drift() answers "ok" over an empty vault. The install id and profile that WOULD
#     tell them apart already sit on d2r_lsrRoute and this reader ignores them.
#   · AUTO-RELAUNCH NEVER ASKS IT. drift_may_relaunch() checks the env flag and nothing_in_flight();
#     it never calls board_identity_drift(), so an already-drifted world does not block the execv.
#   · AND THE FALLBACK PATH RUNS EPHEMERAL STORAGE. If webview.start() takes its TypeError fallback,
#     the board comes back WITHOUT private_mode=False — v2043 exactly — and auto-relaunch would then
#     repeat that every _DRIFT_EVERY_S (300s) instead of once.
#
# Announcing-only is the honest resting state until the guard detects a new claimed world AND
# drift_may_relaunch consults it. Set TV_AUTO_RELAUNCH=1 by hand to override.
export TV_AUTO_RELAUNCH="${TV_AUTO_RELAUNCH:-0}"

while true; do
  if [ ! -f "$PAUSE_FLAG" ]; then
    # port not answering? bring up the headless console.
    if ! curl -s -o /dev/null -m 3 "http://127.0.0.1:$PORT/api/status" 2>/dev/null; then
      # make sure no half-dead headless lingers, then relaunch headless
      pkill -f "control_app.py --no-open" 2>/dev/null
      sleep 1
      nohup python3 "$HERE/control_app.py" --no-open >> "$LOG" 2>&1 &
      disown 2>/dev/null || true
    fi
  fi
  sleep 20
done
