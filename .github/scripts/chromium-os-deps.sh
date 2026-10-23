#!/usr/bin/env bash
# Chromium's OS packages, best effort and BOUNDED (gbl/ci-speed, 2026-10-23).
#
# MEASURED on 146 "OS deps for Chromium" steps (tv-tests, Routine I, Publish, 2026-10-23): the step either finished
# in under 60 s (126 of them, median 12 s) or sat on a slow Ubuntu mirror until its 5-minute timeout (19 of them) -
# only one landed between (97 s). A hang left the same packages missing that a 90 s cut leaves, so the cut changes no
# verdict and gives back up to 3.5 minutes on the slowest shard, which is the one every run waits for.
#
# 1. Ask Playwright what is missing (--dry-run: no network). Nothing missing -> no apt at all.
# 2. Otherwise install with a 90 s bound. A cut or failed install is a warning, never a red step: if a library is
#    really absent the browser launch fails next and names it, far better than an apt timeout does.
set -u
out=$(timeout 60 npx playwright install-deps --dry-run chromium 2>&1); rc=$?
if [ "$rc" -eq 0 ] && ! printf '%s\n' "$out" | grep -qi 'missing'; then
  echo "chromium OS deps: none missing - apt skipped"
  exit 0
fi
printf '%s\n' "$out"
timeout 90 npx playwright install-deps chromium; rc=$?
if [ "$rc" -eq 124 ]; then
  echo "::warning title=OS deps cut at 90 s::apt did not finish in 90 s (a slow mirror) - continuing; a missing library fails the browser launch next and names itself"
elif [ "$rc" -ne 0 ]; then
  echo "::warning title=OS deps failed::npx playwright install-deps exited $rc - continuing"
fi
exit 0
