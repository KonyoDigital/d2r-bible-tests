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
# Announcing-only WAS the resting state, and this sentence outlived it — v2153 armed auto-relaunch
# ON BY DEFAULT, and the line 17 rows below already says so. Kept, corrected rather than deleted,
# because the reasoning above it is still the reason the guard is careful:
#   auto-relaunch is ON unless something turns it off. TV_AUTO_RELAUNCH=0 turns it off;
#   TV_AUTO_RELAUNCH=1 is only needed to force it back on OVER a saved OFF.
# v2153 — ARMED. Konyo, twice: "it can definitely relaunch to other new builds", and then
# "its still not auto relaunching for the newer updates. we said it should relaunch by itself
# based on updates we do. automatically."
#
# It was armed at v2145 and I DISARMED it at v2146, because the world guard it leans on could not
# yet tell two different CLAIMED stores apart — so a relaunch that came back as a new WebKit store
# would have read as the same world and his vault could have been stranded silently. That was the
# right call then. v2147 rebuilt the guard on d2r_lsrRoute's install id, and drift_may_relaunch()
# now REFUSES on drift. The reason for the 0 is gone, so the 0 goes.
#
# What still stops it, every one of them checked before any execv:
#   * the board's world has drifted           -> refuse (v2147)
#   * a chronicle sweep is reading            -> refuse
#   * a vault sweep is reading                -> refuse
#   * a mini is recording                     -> refuse
#   * the agent is alive, i.e. HE IS FILMING  -> refuse (killing it orphans that reel's frames)
# Set TV_AUTO_RELAUNCH=0 by hand to go back to announce-only.
# ⚠ v2181 — NO BLANKET EXPORT. This forced TV_AUTO_RELAUNCH=1 on every console the supervisor
# started, and the env var outranks the saved setting — so a switch HE turned off would have been
# overridden by whichever launcher happened to start the app. The arming default is ON in
# control_app now (v2180), so this export bought nothing and cost him the ability to say no.
# A value already in the environment is still passed through, because that is a human choosing.
[ -n "${TV_AUTO_RELAUNCH:-}" ] && export TV_AUTO_RELAUNCH

# ⚠ v2181 — THE PAUSE MUST **NOT** EXPIRE. I SHIPPED AN EXPIRY AND IT WAS WRONG.
# v2180 found $PAUSE_FLAG dated Aug 3 on his machine, called it a forgotten leftover from a
# tvd-scan run, and made it self-clear after six hours. Then I read tvd-console.sh — the script
# whose whole job is clearing this flag — and it REFUSES BY DEFAULT, in its own words:
#
#     "the console this restores is HEADLESS, and a headless launch does NOT hold the macOS
#      Screen Recording grant: ON AIR refuses, nothing records, Theatre plays black.
#      On 2026-08-03 that cost a night of farming footage."
#
# That is the date on the flag. It is not forgotten — it is DELIBERATE, and it is the only thing
# standing between the supervisor and putting a console on :17772 that cannot record. An expiry
# would have re-caused the exact incident it was set for, unattended, six hours after any scan.
# tvd-console.sh already refuses without --force and says "no tty is not consent"; a timer is a
# worse version of the consent this system deliberately requires.
#
# What survives from v2180 is the half that was actually missing: the supervisor SAYS it has
# stood down, and how old the flag is. A supervisor that is not supervising and does not say so
# is indistinguishable from one that is — but saying so is the fix, not acting on its own.
# [[feedback-silence-is-not-evidence]] [[crossover-is-the-diablo-install]] — ask what a thing
# DOES before removing it.
_paused_said=0
while true; do
  if [ -f "$PAUSE_FLAG" ]; then
    _age_min=$(( ( $(date +%s) - $(stat -f %m "$PAUSE_FLAG" 2>/dev/null || date +%s) ) / 60 ))
    if [ "$_paused_said" = "0" ]; then
      echo "$(date '+%F %T') supervisor: STOOD DOWN — $PAUSE_FLAG is present (${_age_min}m old). This is deliberate: clearing it lets a HEADLESS console take :17772, which does NOT hold Screen Recording. Restore only with: bash tv/tvd-console.sh --force"
      _paused_said=1
    fi
  else
    _paused_said=0
  fi
  if [ ! -f "$PAUSE_FLAG" ]; then
    # port not answering? bring up the headless console.
    if ! curl -s -o /dev/null -m 3 "http://127.0.0.1:$PORT/api/status" 2>/dev/null; then
      # make sure no half-dead headless lingers, then relaunch headless
      # ── v2160 — KILL BY PORT, NEVER BY NAME PATTERN. `pkill -f "control_app.py --no-open"`
      # matches ANY process whose command line merely CONTAINS that string — a grep, an editor, a
      # shell that scrolled it, a sibling harness. It is his standing rule for exactly this
      # reason, and it has already cost real processes: a session of mine killed its own two
      # shells with a name pattern, and his live console has been taken down twice the same way.
      #
      # The question this code actually has is "something half-dead is holding :$PORT" — so ask
      # the PORT who holds it and kill THAT pid. When nothing holds it there is nothing to kill,
      # which is the common case and used to be a blind volley into the process table.
      _holder="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1)"
      if [ -n "$_holder" ]; then
        kill "$_holder" 2>/dev/null
        sleep 1
        kill -0 "$_holder" 2>/dev/null && kill -9 "$_holder" 2>/dev/null
      fi
      nohup python3 "$HERE/control_app.py" --no-open >> "$LOG" 2>&1 &
      disown 2>/dev/null || true
    fi
  fi
  sleep 20
done
