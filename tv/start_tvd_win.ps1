# 📺 TV DIABLO — Windows launcher (what the Desktop shortcut runs)
# Starts BOTH halves: the .NET screen-capture loop (minimized window) and the
# reader agent (this window). First run walks through the one-time Claude login.
# Read-only by construction · your own Claude subscription · zero API keys.
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path   # …\d2r_bible_tests\tv
$repo = Split-Path -Parent $here

function Say($m) { Write-Host "📺 $m" -ForegroundColor Cyan }

# subscription contract: never let a shell API key outrank the login (the v720 lesson)
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Say "claude not found — re-run the installer: irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
  Read-Host "press Enter to close"; return
}

# ── the ONE human step: your own Claude login, once ──────────────────────────
$credFile = Join-Path $HOME '.claude\.credentials.json'
if (-not (Test-Path $credFile)) {
  Say "FIRST RUN — log into YOUR Claude account (your subscription pays for vision, no API keys)."
  Say "a Claude window opens now: complete the login it offers, then type /exit to come back here."
  Start-Process -Wait powershell -ArgumentList '-NoLogo','-Command','claude'
  if (-not (Test-Path $credFile)) {
    Say "login not detected — run the shortcut again after logging in."
    Read-Host "press Enter to close"; return
  }
  Say "login detected ✓"
}

# pull-first doctrine (Mac ships, Windows follows)
try { git -C $repo pull --ff-only 2>$null | Out-Null } catch {}

# ── capture loop, minimized ──────────────────────────────────────────────────
$cap = Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$here\capture_win.ps1`"" `
        -WindowStyle Minimized -PassThru
Say "capture loop running (minimized window, pid $($cap.Id))"

# ── the reader (this window) ─────────────────────────────────────────────────
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
Say "reader starting — open the bible → 📺 TV·D tab → flip the switch. Ctrl-C here stops (farewell read included)."
try {
  & $py "$here\tv_diablo.py" --watch
} finally {
  try { Stop-Process -Id $cap.Id -Force -ErrorAction SilentlyContinue } catch {}
  Say "stopped — capture loop closed too."
}
