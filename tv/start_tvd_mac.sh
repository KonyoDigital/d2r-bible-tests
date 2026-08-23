#!/usr/bin/env bash
# 📺 TV DIABLO — Mac launcher (Desktop app · v1379.1 native pywebview window)
# Real OS app window (not Chrome). Agent stays hidden behind ON/OFF/STOP/RESTART/SIM.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/Library/Python/3.9/bin:$PATH"
# user-site packages (pywebview) for system python3
export PYTHONPATH="${PYTHONPATH:-}"
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true
# v927.2 — arm the local Vision OCR fast lane (v925 LIGHT default ships it off;
# tv/bin/ocr_mac exists and reads a frame in ~10-50ms warm vs ~10s Sonnet-only)
export TV_OCR="${TV_OCR:-1}"
# v928.1 — arm the FILM thread too (same v925-LIGHT cut): without it the SIM/retro
# "visual debugger" gets zero f_*.jpg footage — sessions replay as sparse read-stills
# instead of the 1fps reel (Konyo 2026-07-20: "where are all the SCREENSHOTS?")
export TV_FILM="${TV_FILM:-1}"

# ── TCC SAFEGUARD (2026-07-20 WindowServer-crash lesson) ────────────────────
# Finder/double-click launches capture wallpaper-only: the wrapper .app is
# unsigned, so macOS strips its Screen Recording grant on a crash and silently
# refuses to re-prompt. Terminal holds a durable grant and children inherit it
# at spawn — so a no-TTY launch reroutes itself through Terminal, which hands
# off and closes its own window. Already in a terminal (TTY) → run direct.
if [[ ! -t 0 && -z "${TVD_VIA_TERMINAL:-}" ]]; then
  if /usr/bin/osascript >/dev/null 2>&1 <<OSA
tell application "Terminal"
  set bootTab to do script "export TVD_VIA_TERMINAL=1; nohup bash '$HERE/start_tvd_mac.sh' >/dev/null 2>&1 & disown; exit"
  delay 2
  try
    close (first window whose tabs contains bootTab) saving no
  end try
end tell
OSA
  then
    exit 0
  fi
  # Terminal reroute failed (Automation denied?) — fall through to direct
  # launch so the app still opens, even if capture ends up wallpaper-only.
fi

cd "$REPO"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "TV DIABLO" message "python3 not found. Re-run: curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash" as critical' || true
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  osascript -e 'display alert "TV DIABLO" message "Claude Code not found. Re-run the installer, then log into claude once." as critical' || true
  exit 1
fi

# ensure pywebview (silent if already present)
python3 -c "import webview" 2>/dev/null || \
  python3 -m pip install --user --quiet 'pywebview>=5.0' 2>/dev/null || true

# pull-first (quiet) — v1418 multi-machine FLEET UNITY (parity with start_tvd_win.ps1):
#   • TV_NO_AUTO_PULL=1 → never pull (dev pin)
#   • Untracked junk (?? debug files) must NOT block pull
#   • Modified TRACKED files still block (protect real local work)
#   • fetch + ff-only; if diverged with no tracked edits, reset --hard origin/main
if [[ -d "$REPO/.git" && -z "${TV_NO_AUTO_PULL:-}" ]]; then
  _tracked_dirty=0
  while IFS= read -r _line; do
    [[ -z "$_line" ]] && continue
    case "$_line" in
      \?\?*) ;;  # untracked — ignore
      *) _tracked_dirty=1; break ;;
    esac
  done < <(git -C "$REPO" status --porcelain 2>/dev/null || true)
  if [[ "$_tracked_dirty" -eq 1 ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') skip auto-pull: tracked files modified (local work protected)" \
      >>"$HERE/control_app.log" 2>/dev/null || true
  else
    if git -C "$REPO" fetch origin >/dev/null 2>&1; then
      if git -C "$REPO" merge --ff-only origin/main >/dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') auto-pull: fast-forward ok" \
          >>"$HERE/control_app.log" 2>/dev/null || true
      else
        echo "$(date '+%Y-%m-%d %H:%M:%S') auto-pull: ff failed, reset --hard origin/main (no tracked edits)" \
          >>"$HERE/control_app.log" 2>/dev/null || true
        git -C "$REPO" reset --hard origin/main >/dev/null 2>&1 || true
        echo "$(date '+%Y-%m-%d %H:%M:%S') auto-pull: now on origin/main" \
          >>"$HERE/control_app.log" 2>/dev/null || true
      fi
    else
      echo "$(date '+%Y-%m-%d %H:%M:%S') auto-pull: fetch failed (offline?)" \
        >>"$HERE/control_app.log" 2>/dev/null || true
    fi
  fi
fi

# Foreground: this process IS the app window (must not nohup/disown).
# v1379.1 — before attach, free :17772 so double-click always boots THIS checkout
# (never window-only onto a stale headless that still holds the port).
LOG="$HERE/control_app.log"
VER=$(python3 -c "import re,pathlib; t=pathlib.Path('$HERE/control_app.py').read_text(); m=re.search(r'\"ver\": \"(v[\\d.]+)\"', t); print(m.group(1) if m else 'v?')" 2>/dev/null || echo "v?")
# ── v2012 — DO NOT KILL A CONSOLE THAT IS SECONDS OLD; IT IS THE ONE STARTING UP ────────────
#
# The kill below is right: a double-click must boot THIS checkout and never window-only onto a
# stale headless (v1379.1). But it is UNCONDITIONAL, and two launches close together therefore
# race — launch 2 kills launch 1, launch 3 kills launch 2.
#
# MEASURED on his machine, control_app.log 2026-08-23. He closed the window with ✕, and then:
#     01:30:01  auto-pull: fast-forward ok   → native window up
#     01:30:21  auto-pull: fast-forward ok   → window gone (signal-SIGTERM)
#     01:30:51  auto-pull: fast-forward ok   → window gone (signal-SIGTERM)
# Three launches in fifty seconds, each SIGTERMing the one before it, each stopping ON AIR through
# the exit safeguard. If he had been recording, that is a session killed by a race with itself.
#
# ⚠ AND IT WAS MISREAD ONCE ALREADY. Those three `auto-pull` lines look like a poller reacting to a
# git push; auto-pull runs ONCE PER LAUNCH, right above. Reading them as a timeline of cause pinned
# the blame on a push nine minutes earlier. The lines are a symptom of relaunching, not a cause.
#
# THE RULE: if something is already listening and it is YOUNGER than the grace window, another
# launch is still coming up — stand down rather than take the port from it. An incumbent that is
# genuinely old is stale and still gets replaced, exactly as before.
#
# TV_FORCE_PORT=1 restores the old unconditional behaviour, for the case this guard gets wrong:
# a console crash-looping would hold the port with a forever-young pid and block a manual launch.
_TVD_PORT_GRACE="${TV_PORT_GRACE_S:-25}"     # supervisor cycles at 20s; a console binds in a few

_tvd_age_secs() {   # elapsed seconds for a pid from macOS `ps -o etime=` ([[dd-]hh:]mm:ss); -1 unknown
  local e d h m s
  e=$(ps -o etime= -p "$1" 2>/dev/null | tr -d ' ')
  [ -z "$e" ] && { echo -1; return; }
  d=0; h=0; m=0; s=0
  case "$e" in *-*) d=${e%%-*}; e=${e#*-};; esac
  case "$e" in
    *:*:*) h=${e%%:*}; e=${e#*:}; m=${e%%:*}; s=${e#*:};;
    *:*)   m=${e%%:*}; s=${e#*:};;
    *)     s=$e;;
  esac
  echo $(( 10#$d*86400 + 10#$h*3600 + 10#$m*60 + 10#$s ))
}

if command -v lsof >/dev/null 2>&1 && [ -z "${TV_FORCE_PORT:-}" ]; then
  for pid in $(lsof -tiTCP:17772 -sTCP:LISTEN 2>/dev/null); do
    _age=$(_tvd_age_secs "$pid")
    if [ "$_age" -ge 0 ] && [ "$_age" -lt "$_TVD_PORT_GRACE" ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') port :17772 held by pid $pid, ${_age}s old — STANDING DOWN. Another console is still coming up; taking the port now is the restart storm that killed a session on 2026-08-23. TV_FORCE_PORT=1 to override." \
        >>"$HERE/control_app.log" 2>/dev/null || true
      exit 0
    fi
  done
fi

# soft-kill anything still listening on the control port (not us — we have not bound yet)
if command -v lsof >/dev/null 2>&1; then
  for pid in $(lsof -tiTCP:17772 -sTCP:LISTEN 2>/dev/null); do
    kill "$pid" 2>/dev/null || true
  done
  sleep 0.4
  for pid in $(lsof -tiTCP:17772 -sTCP:LISTEN 2>/dev/null); do
    kill -9 "$pid" 2>/dev/null || true
  done
  sleep 0.2
fi
# brief dock notification so Konyo can SEE the ship stamp on every double-click
osascript -e "display notification \"starting ${VER}\" with title \"TV DIABLO\"" 2>/dev/null || true
exec python3 "$HERE/control_app.py" --open >>"$LOG" 2>&1
