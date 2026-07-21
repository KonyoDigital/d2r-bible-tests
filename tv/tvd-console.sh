#!/bin/bash
# 🛡️ Give the immortal always-up console back (clears the scan pause-flag). Konyo 2026-07-22.
# The supervisor will bring :17772 back up headless within ~20s (or instantly if you like).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -f "$HERE/.tvd_supervisor_pause"
echo "🛡️ pause-flag cleared — the supervisor will restore the always-up console on :17772 within ~20s."
