#!/bin/bash
# 🎥 Hand :17772 to the real TCC-granted TV DIABLO.app for LIVE SCANNING (Konyo 2026-07-22).
# Pauses the console supervisor, frees the port, and launches the app the TCC-correct way.
# When you're done scanning, run tvd-console.sh to give the immortal headless console back.
#
# v1251 — find the app on Desktop / Applications / next to this script (old path only
# looked at tv/TV DIABLO.app which is often missing → silent open fail).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
touch "$HERE/.tvd_supervisor_pause"          # tell the supervisor to stand down
# v2160 — free :17772 by asking the PORT who holds it, never by name pattern. `pkill -f` matches
# any command line containing the string, which is how a name-volley takes down a shell, an editor
# or his live console. Kill the listener, or kill nothing.
_h="$(lsof -nP -iTCP:17772 -sTCP:LISTEN -t 2>/dev/null | head -1)"
[ -n "$_h" ] && { kill "$_h" 2>/dev/null; sleep 1; kill -0 "$_h" 2>/dev/null && kill -9 "$_h" 2>/dev/null; }
# also free a stuck primary if nothing is answering (best-effort, never kill user tools)
sleep 1

APP=""
for cand in \
  "$HERE/TV DIABLO.app" \
  "$HOME/Desktop/TV DIABLO.app" \
  "$HOME/Applications/TV DIABLO.app" \
  "/Applications/TV DIABLO.app"
do
  if [ -d "$cand" ]; then
    APP="$cand"
    break
  fi
done

if [ -z "$APP" ]; then
  # Fall back to the TCC Terminal-chain launcher script directly
  if [ -f "$HERE/start_tvd_mac.sh" ]; then
    echo "🎥 supervisor paused · launching via start_tvd_mac.sh (no .app found)"
    exec bash "$HERE/start_tvd_mac.sh"
  fi
  echo "⛔ TV DIABLO.app not found. Expected on Desktop or Applications."
  exit 1
fi

open "$APP"                    # TCC-correct launch (Terminal reroute → grant inherited)
echo "🎥 supervisor paused · launched: $APP"
echo "   when done scanning, run:  bash '$HERE/tvd-console.sh'  (restores the always-up console)"
