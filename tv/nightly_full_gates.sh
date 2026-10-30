#!/bin/bash
# v3847 FAST GATE - the NIGHTLY FULL RUN. A push runs the fast set (tv/fast_gates.py); every night every gate runs
# on origin/main in its own worktree, so a gate the fast set did not pick is never more than a day from running.
# It records into the shared ledger (git common dir) and writes one verdict line; it posts nothing anywhere.
# Refuses when another gate run holds the machine (one Chrome at a time) - the next night runs it.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TREE="${TV_NIGHTLY_TREE:-/private/tmp/tv-nightly}"
LOG_DIR="${TV_NIGHTLY_LOGS:-$HOME/Library/Logs/tv-nightly}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/full-$(date +%Y%m%d-%H%M).log"
# v3847 eye: one nightly at a time from the first git step (pgrep alone leaves the setup window open), and a skip
# exits 75 (EX_TEMPFAIL) so a skipped night is never read as a green one.
LOCK="$LOG_DIR/.nightly.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date '+%F %T') SKIPPED - another nightly holds $LOCK" >> "$LOG_DIR/verdicts.log"; exit 75
fi
trap 'rmdir "$LOCK"' EXIT
if pgrep -f "tv/run_gates.py" >/dev/null; then
  echo "$(date '+%F %T') SKIPPED - another gate run is going (one Chrome at a time)" >> "$LOG_DIR/verdicts.log"; exit 75
fi
git -C "$REPO" fetch -q origin main || { echo "$(date '+%F %T') NO RUN - fetch failed" >> "$LOG_DIR/verdicts.log"; exit 1; }
if [ -d "$TREE" ]; then git -C "$TREE" checkout -q --detach origin/main && git -C "$TREE" reset -q --hard origin/main
else git -C "$REPO" worktree add -q --detach "$TREE" origin/main; fi \
  || { echo "$(date '+%F %T') NO RUN - the nightly tree could not be set to origin/main" >> "$LOG_DIR/verdicts.log"; exit 1; }
SHA="$(git -C "$TREE" rev-parse --short HEAD)"
[ "$(git -C "$TREE" rev-parse HEAD)" = "$(git -C "$REPO" rev-parse origin/main)" ] \
  || { echo "$(date '+%F %T') NO RUN - the nightly tree is not origin/main" >> "$LOG_DIR/verdicts.log"; exit 1; }
T0=$SECONDS
( cd "$TREE" && caffeinate -i python3 tv/run_gates.py --full ) > "$LOG" 2>&1
RC=$?
echo "$(date '+%F %T') $SHA rc=$RC $(( (SECONDS-T0)/60 ))m $(grep -aE '^(✅|❌) [0-9]+ gate' "$LOG" | tail -1) log=$LOG" >> "$LOG_DIR/verdicts.log"
exit $RC
