#!/usr/bin/env bash
# 📺 TV DIABLO — one-shot Mac installer (mirrors the Windows cousin move)
#
#     curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash
#
# One paste: ensures git + python3 + pywebview + Claude Code, clones the repo,
# installs `tvd`, drops TV DIABLO.app on Desktop. Double-click → real native
# app window (pywebview, not Chrome). Same product as Windows.
set -euo pipefail

REPO_URL="${TVD_REPO_URL:-https://github.com/KonyoDigital/d2r-bible-tests.git}"
REPO_DIR="${TVD_REPO:-$HOME/d2r_bible_tests}"
BIN_DIR="${HOME}/.local/bin"

Say()  { printf '\033[36m📺 %s\033[0m\n' "$*"; }
Ok()   { printf '\033[32m   ✓ %s\033[0m\n' "$*"; }
Warn() { printf '\033[33m   ⚠ %s\033[0m\n' "$*"; }

export PATH="/opt/homebrew/bin:/usr/local/bin:${BIN_DIR}:$PATH"

Say "TV DIABLO installer (Mac) — one shot, then the Desktop app does the rest"

# ── Xcode CLT / git ──────────────────────────────────────────────────────────
if ! command -v git >/dev/null 2>&1; then
  Say "installing Apple Command Line Tools (includes git)…"
  xcode-select --install 2>/dev/null || true
  Warn "if a dialog appeared, finish installing Command Line Tools, then re-run this line."
  exit 1
fi
Ok "git $(git --version | sed 's/git version //')"

# ── Python 3 ─────────────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    Say "installing Python via Homebrew…"
    brew install python@3.12 || brew install python3
  else
    Warn "python3 not found. Install from https://www.python.org/downloads/ or: brew install python3"
    exit 1
  fi
fi
Ok "python3 $(python3 --version 2>&1 | head -1)"

# ── pywebview (real native app window — not Chrome) ──────────────────────────
Say "installing pywebview (native app window)…"
if python3 -m pip install --user --quiet 'pywebview>=5.0' 2>/dev/null \
   || python3 -m pip install --user --quiet --break-system-packages 'pywebview>=5.0' 2>/dev/null; then
  Ok "pywebview (native window)"
else
  Warn "pywebview pip install failed — app will try again on first launch / browser fallback"
fi

# ── Claude Code (vision brain — YOUR subscription) ───────────────────────────
if ! command -v claude >/dev/null 2>&1; then
  Say "installing Claude Code (Anthropic's official installer)…"
  if ! curl -fsSL https://claude.ai/install.sh | bash; then
    Warn "native installer failed."
    Warn "install manually: https://docs.anthropic.com/en/docs/claude-code — then re-run this line."
    exit 1
  fi
  export PATH="/opt/homebrew/bin:/usr/local/bin:${BIN_DIR}:${HOME}/.local/bin:$PATH"
fi
if command -v claude >/dev/null 2>&1; then
  Ok "claude code"
else
  Warn "claude still missing — open a NEW Terminal tab and re-run this line."
  exit 1
fi

# ── Grok Build CLI (optional SuperGrok vision · G5 · never required) ─────────
export PATH="${HOME}/.grok/bin:${HOME}/.local/bin:${PATH}"
if ! command -v grok >/dev/null 2>&1; then
  Say "installing Grok CLI (xAI SuperGrok · optional vision lane)…"
  if curl -fsSL https://x.ai/cli/install.sh | bash; then
    export PATH="${HOME}/.grok/bin:${HOME}/.local/bin:${PATH}"
  else
    Warn "Grok CLI install failed — optional. Leave Grok Eyes OFF or install later:"
    Warn "  curl -fsSL https://x.ai/cli/install.sh | bash   then:  grok login"
  fi
fi
if command -v grok >/dev/null 2>&1; then
  Ok "grok cli (optional — authorize later in console ⚡ or: grok login)"
  if [[ ! -f "${HOME}/.grok/auth.json" ]]; then
    Warn "Grok not authorized yet — TV DIABLO → ⚙ advanced → ⚡ Authorize Grok (browser once)"
  else
    Ok "Grok already authorized on this Mac"
  fi
else
  Warn "grok still missing — optional; console works without it"
fi

# ── bible repo ───────────────────────────────────────────────────────────────
if [[ -d "$REPO_DIR/.git" ]]; then
  Say "updating the bible repo…"
  git -C "$REPO_DIR" pull --ff-only 2>/dev/null || Warn "git pull failed — using what's already at $REPO_DIR"
else
  Say "cloning the bible repo…"
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi
if [[ ! -f "$REPO_DIR/tv/start_tvd_mac.sh" ]]; then
  Warn "clone incomplete — missing tv/start_tvd_mac.sh at $REPO_DIR"
  Warn "(if you are the developer with a dirty tree, ensure start_tvd_mac.sh is committed + pulled)"
  exit 1
fi
chmod +x "$REPO_DIR/tv/start_tvd_mac.sh" \
         "$REPO_DIR/tv/install-tvd.sh" \
         "$REPO_DIR/tv/tvd" 2>/dev/null || true
Ok "repo at $REPO_DIR"

# ── tvd one-word CLI ─────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
cp "$REPO_DIR/tv/tvd" "$BIN_DIR/tvd"
chmod +x "$BIN_DIR/tvd"
for rc in "$HOME/.zshrc" "$HOME/.zprofile"; do
  touch "$rc"
  if ! grep -q '\$HOME/\.local/bin\|\$HOME/.local/bin' "$rc" 2>/dev/null; then
    {
      echo ''
      echo '# TV DIABLO — tvd on PATH'
      echo 'export PATH="$HOME/.local/bin:$PATH"'
    } >> "$rc"
  fi
done
Ok "command: tvd  ($BIN_DIR/tvd)"

# ── Desktop + ~/Applications app (Windows .lnk equivalent) ───────────────────
make_app() {
  local dest="$1"
  local macexe="$dest/Contents/MacOS/launcher"
  local plist="$dest/Contents/Info.plist"
  local script_path="$REPO_DIR/tv/start_tvd_mac.sh"

  rm -rf "$dest"
  mkdir -p "$dest/Contents/MacOS" "$dest/Contents/Resources"
  # v762 — the real icon (extracted Diablo on a grimoire CRT tile), not a white box
  [[ -f "$REPO_DIR/tv/appicon.icns" ]] && cp "$REPO_DIR/tv/appicon.icns" "$dest/Contents/Resources/AppIcon.icns"

  # launcher: NO Terminal — start_tvd_mac.sh opens the HD control window (v757)
  cat > "$macexe" <<APP
#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:${HOME}/.local/bin:${HOME}/Library/Python/3.9/bin:${HOME}/Library/Python/3.12/bin:/usr/bin:/bin:\$PATH"
SCRIPT="$script_path"
if [[ ! -f "\$SCRIPT" ]]; then
  /usr/bin/osascript -e 'display alert "TV DIABLO" message "Missing launcher script. Re-run: curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash" as critical'
  exit 1
fi
exec bash "\$SCRIPT"
APP
  chmod +x "$macexe"

  # 2026-07-31 — the bundle version was a FIFTH surface nobody checked. This file hardcoded 787 while
# the installed bundles said 1379.3, so re-running the installer would have REGRESSED the app's
# advertised version. v1489 gave the repo one place to bump; the bundle now reads from it too.
TVD_VER="$(grep -oE 'VERSION = "v[0-9.]+"' "$(dirname "$0")/tv_diablo.py" 2>/dev/null | grep -oE '[0-9.]+' | head -1)"
[ -n "$TVD_VER" ] || TVD_VER="0"

cat > "$plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>launcher</string>
  <key>CFBundleIdentifier</key>
  <string>com.konyo.tvdiablo</string>
  <key>CFBundleName</key>
  <string>TV DIABLO</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleDisplayName</key>
  <string>TV DIABLO</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleVersion</key>
  <string>${TVD_VER}</string>
  <key>CFBundleShortVersionString</key>
  <string>${TVD_VER}</string>
  <key>LSUIElement</key>
  <false/>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

  xattr -dr com.apple.quarantine "$dest" 2>/dev/null || true
}

DESKTOP_APP="${HOME}/Desktop/TV DIABLO.app"
mkdir -p "${HOME}/Applications"
make_app "$DESKTOP_APP"
make_app "${HOME}/Applications/TV DIABLO.app"
Ok "Desktop app: TV DIABLO"
Ok "Applications: ~/Applications/TV DIABLO.app"

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -f "$DESKTOP_APP" 2>/dev/null || true

Say "DONE. Double-click TV DIABLO on your Desktop."
CRED_HIT=0
for c in \
  "${HOME}/.claude/.credentials.json" \
  "${HOME}/.config/claude/.credentials.json" \
  "${HOME}/.claude.json"
do
  [[ -f "$c" ]] && CRED_HIT=1 && break
done
if [[ "$CRED_HIT" -eq 0 ]]; then
  Warn "first run may ask you to log into your own Claude account (once)."
fi
Say "then double-click TV DIABLO -> press ON AIR. Farm."
echo ""
echo "   Mac:      curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash"
echo "   Windows:  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
