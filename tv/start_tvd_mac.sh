#!/usr/bin/env bash
# 📺 TV DIABLO — Mac launcher (Desktop app entry · v757)
# Opens the HD control window (no Terminal UI). Agent runs hidden behind the scenes.
# Buttons: ON / OFF / STOP / RESTART / SIM · board auto-connects on ON.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true

cd "$REPO"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "TV DIABLO" message "python3 not found. Re-run: curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash" as critical' || true
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  osascript -e 'display alert "TV DIABLO" message "Claude Code not found. Re-run the installer, then log into claude once." as critical' || true
  exit 1
fi

# pull-first (quiet)
if [[ -d "$REPO/.git" ]]; then
  git -C "$REPO" pull --ff-only >/dev/null 2>&1 || true
fi

open_control_window() {
  local url="http://127.0.0.1:17772/"
  open -na "Google Chrome" --args --app="$url" --new-window 2>/dev/null && return 0
  open -na "Microsoft Edge" --args --app="$url" --new-window 2>/dev/null && return 0
  open -na "Brave Browser" --args --app="$url" --new-window 2>/dev/null && return 0
  open -na "Arc" --args --app="$url" --new-window 2>/dev/null && return 0
  open "$url" 2>/dev/null || true
}

# If control server already up, just re-open the window
if lsof -tiTCP:17772 -sTCP:LISTEN >/dev/null 2>&1; then
  open_control_window
  exit 0
fi

# Detached control server + app window (no Terminal)
LOG="$HERE/control_app.log"
nohup python3 "$HERE/control_app.py" --open >>"$LOG" 2>&1 &
disown 2>/dev/null || true
exit 0
