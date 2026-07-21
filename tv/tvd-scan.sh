#!/bin/bash
# 🎥 Hand :17772 to the real TCC-granted TV DIABLO.app for LIVE SCANNING (Konyo 2026-07-22).
# Pauses the console supervisor, frees the port, and launches the app the TCC-correct way.
# When you're done scanning, run tvd-console.sh to give the immortal headless console back.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
touch "$HERE/.tvd_supervisor_pause"          # tell the supervisor to stand down
pkill -f "control_app.py --no-open" 2>/dev/null   # free :17772 (headless only)
sleep 1
open "$HERE/TV DIABLO.app"                    # TCC-correct launch (Terminal reroute → grant inherited)
echo "🎥 supervisor paused · launched TV DIABLO.app for scanning."
echo "   when done scanning, run:  bash '$HERE/tvd-console.sh'  (restores the always-up console)"
