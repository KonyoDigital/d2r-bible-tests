#!/usr/bin/env bash
# 📺 TV DIABLO — Mac launcher (Desktop app · v761 native pywebview window)
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

# pull-first (quiet)
if [[ -d "$REPO/.git" ]]; then
  git -C "$REPO" pull --ff-only >/dev/null 2>&1 || true
fi

# Foreground: this process IS the app window (must not nohup/disown)
# If control server already up, --open still attaches a second window then exits when closed.
LOG="$HERE/control_app.log"
exec python3 "$HERE/control_app.py" --open >>"$LOG" 2>&1
