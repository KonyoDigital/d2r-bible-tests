#!/bin/bash
# check_divergence.sh — run BEFORE any bible.html edit session (CC 2026-06-11).
# Exit 0 = safe to edit. Exit 1 = STOP: uncommitted divergence from another
# writer (probably Claude Desktop) — snapshot exists, coordinate via Konyo.
set -u
cd /Users/konyo/d2r_bible_tests || exit 1

dirty=$(git diff --name-only -- bible.html)
lock=""
[ -f bible.html.EDIT_LOCK ] && lock=$(head -1 bible.html.EDIT_LOCK)

if [ -n "$dirty" ] && [ -z "$lock" ]; then
  ./autosnap.sh   # make sure the foreign WIP is captured before anything else
  echo "DIVERGENCE: bible.html differs from HEAD with NO edit lock claimed."
  echo "Another writer (Desktop?) has uncommitted work. Snapshot taken:"
  git log refs/snapshots/bible --oneline -1
  echo "DO NOT WRITE — merge or coordinate via Konyo first."
  exit 1
fi
if [ -n "$lock" ]; then
  echo "LOCKED: $lock"
  echo "If that owner is not you, DO NOT WRITE."
  exit 1
fi
echo "CLEAN: bible.html matches HEAD, no lock claimed. Claim the lock and edit."
exit 0
