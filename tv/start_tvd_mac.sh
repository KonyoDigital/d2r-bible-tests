#!/usr/bin/env bash
# 📺 TV DIABLO — Mac launcher (what the Desktop "TV DIABLO" app runs)
# Same product surface as Windows start_tvd_win.ps1: strip API keys, first-run
# Claude login, pull latest, open the board, start the live scanner.
# Capture is macOS screencapture (built into the agent) — no second process.
# Read-only by construction · your Claude subscription · zero API keys.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PORT="${TV_PORT:-17771}"
PY="${TVD_PYTHON:-python3}"

Say() { printf '\033[36m📺 %s\033[0m\n' "$*"; }
Warn() { printf '\033[33m   !!  %s\033[0m\n' "$*"; }

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
# subscription contract: never let a shell API key outrank the login
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true

cd "$REPO"

if ! command -v claude >/dev/null 2>&1; then
  Say "claude not found — re-run the installer:"
  echo "   curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash"
  read -r -p "press Enter to close…" _
  exit 1
fi

# ── the ONE human step: your own Claude login, once ──────────────────────────
# Claude Code stores auth in a few places across versions; any one is enough.
CRED_OK=0
for c in \
  "${HOME}/.claude/.credentials.json" \
  "${HOME}/.config/claude/.credentials.json" \
  "${HOME}/.claude.json"
do
  [[ -f "$c" ]] && CRED_OK=1 && break
done
if [[ "$CRED_OK" -eq 0 ]]; then
  Say "FIRST RUN — log into YOUR Claude account (your subscription pays for vision, no API keys)."
  Say "a Claude session opens now: complete the login it offers, then type /exit to come back here."
  claude || true
  CRED_OK=0
  for c in \
    "${HOME}/.claude/.credentials.json" \
    "${HOME}/.config/claude/.credentials.json" \
    "${HOME}/.claude.json"
  do
    [[ -f "$c" ]] && CRED_OK=1 && break
  done
  if [[ "$CRED_OK" -eq 0 ]]; then
    Warn "no credentials file seen yet — continuing anyway (many installs keep auth in Keychain)."
    Warn "if vision fails, run:  claude   then /login, then re-open TV DIABLO."
  else
    Say "login detected ✓"
  fi
fi

# pull-first doctrine (Mac ships, Windows follows — both sides stay current)
if [[ -d "$REPO/.git" ]]; then
  git -C "$REPO" pull --ff-only 2>/dev/null || true
fi

# ── open the same board Windows sees (TV·D tab) ──────────────────────────────
# Prefer local bible.html (full offline board, polls localhost:17771). Live site as fallback.
BOARD_LOCAL="$REPO/bible.html"
if [[ -f "$BOARD_LOCAL" ]]; then
  # hash #tvd lands on the TV·D tab (honored when TV was on / on explicit deep link)
  open "$BOARD_LOCAL"
  # second open with hash — some macOS versions drop hash on file://; best-effort
  open "file://${BOARD_LOCAL}#tvd" 2>/dev/null || true
else
  open "https://bull-4-u.com/d2r/#tvd" 2>/dev/null || true
fi

Say "board opening — click 📺 TV·D → flip the switch ON (green LIVE when the bridge answers)."
Say "scanner starting on http://127.0.0.1:${PORT}/state"
Say "Screen Recording: if macOS asks, Allow for Terminal (or iTerm) — read-only screenshots only."
echo "   stop with Ctrl-C  ·  or another terminal: tvd stop"
echo ""

# already live?
if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  Say "already LIVE on :$PORT — leaving it running. Flip the TV·D switch."
  read -r -p "press Enter to close this window…" _
  exit 0
fi

exec env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN \
  TV_MODEL="${TV_MODEL:-sonnet}" \
  "$PY" "$HERE/tv_diablo.py"
