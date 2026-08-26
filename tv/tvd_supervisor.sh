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
export TV_AUTO_RELAUNCH="${TV_AUTO_RELAUNCH:-1}"

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
