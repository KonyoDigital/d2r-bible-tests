#!/bin/bash
# 🛡️ Give the immortal always-up console back (clears the scan pause-flag). Konyo 2026-07-22.
# The supervisor will bring :17772 back up headless within ~20s (or instantly if you like).
#
# ⛔ v1608 — REFUSES BY DEFAULT. The console this restores is HEADLESS, and a headless
# launch does NOT hold the macOS Screen Recording grant: ON AIR refuses, nothing records,
# Theatre plays black. On 2026-08-03 that cost a night of farming footage. This script was
# the thing that caused it and it said nothing, so now it says it and makes you opt in.
#
#   bash tv/tvd-console.sh              → warns and EXITS 2, pause-flag untouched
#   bash tv/tvd-console.sh --force      → proceeds (also: --yes, -y)
#   TVD_NO_RECORD_OK=1 bash tv/tvd-console.sh   → proceeds
#
# No tty is not consent: a supervisor, cron or wrapper with no flag takes the refusing path,
# so nothing can silently hand back a console that cannot record.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"

# ── opt-in gate ───────────────────────────────────────────────────────────────
CONFIRMED=0
[ "${TVD_NO_RECORD_OK:-}" = "1" ] && CONFIRMED=1
if [ "$#" -gt 0 ]; then
  for _arg in "$@"; do
    case "$_arg" in
      --force|--yes|-y) CONFIRMED=1 ;;
    esac
  done
fi

if [ "$CONFIRMED" -ne 1 ]; then
  echo ""
  echo "⛔ STOP — this would take RECORDING away from you."
  echo ""
  echo "   Right now :17772 is (or should be) the real TV DIABLO.app, launched through"
  echo "   Terminal, and THAT process is the one macOS gave Screen Recording to."
  echo ""
  echo "   Clearing the pause-flag lets the supervisor put the HEADLESS console back on"
  echo "   :17772 within ~20s. A headless launch does NOT inherit the Screen Recording"
  echo "   grant. The moment it does:"
  echo "     · ON AIR / 🔴 record will REFUSE"
  echo "     · nothing is captured — no frames, no reel"
  echo "     · Theatre plays a BLACK screen, and it looks like the app is broken"
  echo ""
  echo "   Only run this when you are DONE recording for now."
  echo ""
  echo "   To get a recording-capable console back:   bash tv/tvd-scan.sh"
  echo "   To check the grant any time:               doctor → 'screen_recording' check"
  echo ""
  echo "   If you really want the headless console anyway, re-run with:"
  echo "     bash '$HERE/tvd-console.sh' --force        (or --yes / -y)"
  echo "     TVD_NO_RECORD_OK=1 bash '$HERE/tvd-console.sh'"
  echo ""
  exit 2
fi

rm -f "$HERE/.tvd_supervisor_pause"
echo "🛡️ pause-flag cleared — the supervisor will restore the always-up console on :17772 within ~20s."
