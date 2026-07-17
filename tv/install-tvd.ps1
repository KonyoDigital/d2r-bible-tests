# 📺 TV DIABLO — one-shot Windows installer (the cousin move)
#
#     irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
#
# One paste does everything: installs Git + Python + Claude Code if missing (winget /
# Anthropic's official installer), clones or updates the bible repo, and drops a
# "TV DIABLO" shortcut on the Desktop. The ONE human step left is the first-run
# Claude login — your own subscription, in your own browser; the shortcut walks you
# through it. Zero API keys, read-only by construction (screen capture only).
$ErrorActionPreference = 'Stop'
$repoUrl  = 'https://github.com/KonyoDigital/d2r-bible-tests.git'
$repoDir  = Join-Path $HOME 'd2r_bible_tests'

function Say($m)  { Write-Host "📺 $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "   ✓ $m" -ForegroundColor Green }
function Warn($m) { Write-Host "   ⚠ $m" -ForegroundColor Yellow }

function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path','User')
}

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Say "TV DIABLO installer — one shot, then the Desktop shortcut does the rest"

# ── winget is the package backbone (ships with Windows 10/11) ─────────────────
if (-not (Have 'winget')) {
  Warn "winget not found — install 'App Installer' from the Microsoft Store, then re-run this line."
  return
}

# ── Git ──────────────────────────────────────────────────────────────────────
if (-not (Have 'git')) {
  Say "installing Git…"
  winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements | Out-Null
  Refresh-Path
}
if (Have 'git') { Ok "git $((git --version) -replace 'git version ','')" } else { Warn "git still missing — re-open PowerShell and re-run."; return }

# ── Python ───────────────────────────────────────────────────────────────────
$py = $null
foreach ($c in @('python','py')) { if (Have $c) { $py = $c; break } }
if (-not $py) {
  Say "installing Python…"
  winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements | Out-Null
  Refresh-Path
  foreach ($c in @('python','py')) { if (Have $c) { $py = $c; break } }
}
if ($py) { Ok "python ($py)" } else { Warn "python still missing — re-open PowerShell and re-run."; return }

# ── Claude Code (the vision brain — runs on YOUR subscription) ───────────────
if (-not (Have 'claude')) {
  Say "installing Claude Code (Anthropic's official installer)…"
  try {
    irm https://claude.ai/install.ps1 | iex
  } catch {
    Warn "native installer failed ($_)."
    Warn "install manually: https://docs.anthropic.com/en/docs/claude-code — then re-run this line."
    return
  }
  Refresh-Path
}
if (Have 'claude') { Ok "claude code" } else { Warn "claude still missing after install — re-open PowerShell and re-run."; return }

# ── The bible repo (public) — clone once, pull forever ───────────────────────
if (Test-Path (Join-Path $repoDir '.git')) {
  Say "updating the bible repo…"
  git -C $repoDir pull --ff-only | Out-Null
} else {
  Say "cloning the bible repo…"
  git clone --depth 1 $repoUrl $repoDir | Out-Null
}
Ok "repo at $repoDir"

# ── Desktop shortcut → the launcher (capture + reader in one) ────────────────
$ws  = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'TV DIABLO.lnk'))
$lnk.TargetPath   = 'powershell.exe'
$lnk.Arguments    = "-ExecutionPolicy Bypass -File `"$repoDir\tv\start_tvd_win.ps1`""
$lnk.WorkingDirectory = $repoDir
$lnk.IconLocation = 'shell32.dll,238'
$lnk.Description  = 'TV DIABLO — read-only loot scanner on your own Claude subscription'
$lnk.Save()
Ok "Desktop shortcut: TV DIABLO"

Say "DONE. Double-click the TV DIABLO shortcut on your Desktop."
$credFile = Join-Path $HOME '.claude\.credentials.json'
if (-not (Test-Path $credFile)) {
  Warn "first run will walk you through the ONE human step: logging into your own Claude account."
}
Say "then open the bible → 📺 TV·D tab → flip the switch. Farm."
