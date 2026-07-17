# 📺 TV DIABLO — one-shot Windows installer (the cousin move)
#
#     irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
#
# One paste does everything: installs Git + Python + Claude Code if missing (winget /
# Anthropic's official installer), clones or updates the bible repo, and drops a
# "TV DIABLO" shortcut on the Desktop. The ONE human step left is the first-run
# Claude login — your own subscription, in your own browser; the shortcut walks you
# through it. Zero API keys, read-only by construction (screen capture only).
#
# Served as text/plain (not octet-stream) so Windows PowerShell's `irm | iex` always
# gets a string. (The BOM lives in start_tvd_win.ps1 — the file PS 5.1 runs via -File.)
$ErrorActionPreference = 'Stop'
$repoUrl  = 'https://github.com/KonyoDigital/d2r-bible-tests.git'
$repoDir  = Join-Path $HOME 'd2r_bible_tests'

function Say($m)  { Write-Host "TV DIABLO  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "   OK  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "   !!  $m" -ForegroundColor Yellow }

# Older Windows PowerShell defaults can block TLS1.2 against GitHub / Claude / CF.
try {
  [Net.ServicePointManager]::SecurityProtocol = `
    [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {}

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = @($machine, $user) -join ';'
  # winget often finishes before the new PATH is visible in this shell — seed the usual homes
  $extras = @(
    (Join-Path $env:ProgramFiles 'Git\cmd'),
    (Join-Path $env:ProgramFiles 'Git\bin'),
    (Join-Path ${env:ProgramFiles(x86)} 'Git\cmd'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python312'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python312\Scripts'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python313'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python313\Scripts'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python311'),
    (Join-Path $env:LocalAppData 'Programs\Python\Python311\Scripts'),
    (Join-Path $env:LocalAppData 'Microsoft\WinGet\Links'),
    (Join-Path $env:USERPROFILE '.local\bin'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Microsoft\WinGet\Packages')
  )
  foreach ($p in $extras) {
    if ($p -and (Test-Path -LiteralPath $p) -and ($env:Path -notlike ("*{0}*" -f $p))) {
      $env:Path = "$p;$env:Path"
    }
  }
}

function Have($cmd) {
  return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

# Windows Store "python" App Execution Alias is a stub that opens the Store — not a real interpreter.
function Real-Python {
  foreach ($c in @('python', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    $src = [string]$cmd.Source
    if ($src -match 'WindowsApps\\(?:python|python3)\.exe$') { continue }
    if ($c -eq 'py') {
      try {
        $v = & $c -3 -c "import sys; print(sys.version)" 2>$null
        if ($LASTEXITCODE -ne 0 -and -not $v) { continue }
      } catch { continue }
    } else {
      try {
        $v = & $c -c "import sys; print(sys.version)" 2>$null
        if (-not $v) { continue }
      } catch { continue }
    }
    return $c
  }
  return $null
}

function Winget-Install($id, $label) {
  Say "installing $label…"
  $wingetArgs = @('install', '-e', '--id', $id, '--silent',
                  '--accept-package-agreements', '--accept-source-agreements',
                  '--disable-interactivity')
  & winget @wingetArgs | Out-Null
  Refresh-Path
  Start-Sleep -Seconds 1
  Refresh-Path
}

Say "installer — one shot, then the Desktop shortcut does the rest"

# ── winget is the package backbone (ships with Windows 10/11) ─────────────────
if (-not (Have 'winget')) {
  Warn "winget not found — install 'App Installer' from the Microsoft Store, then re-run this line."
  return
}

# ── Git ──────────────────────────────────────────────────────────────────────
Refresh-Path
if (-not (Have 'git')) {
  Winget-Install 'Git.Git' 'Git'
}
if (Have 'git') { Ok "git $((git --version) -replace 'git version ','')" } else {
  Warn "git still missing — close this window, open a NEW PowerShell, re-run the install line."
  return
}

# ── Python ───────────────────────────────────────────────────────────────────
$py = Real-Python
if (-not $py) {
  Winget-Install 'Python.Python.3.12' 'Python 3.12'
  $py = Real-Python
}
if ($py) { Ok "python ($py)" } else {
  Warn "python still missing (or only the Windows Store stub is installed)."
  Warn "turn OFF 'App execution aliases' for python.exe in Settings → Apps → Advanced, then re-run."
  return
}

# ── Claude Code (the vision brain — runs on YOUR subscription) ───────────────
Refresh-Path
if (-not (Have 'claude')) {
  Say "installing Claude Code (Anthropic's official installer)…"
  try {
    # iwr -UseBasicParsing is more reliable than irm on older PS when content-type is odd
    $install = (Invoke-WebRequest -Uri 'https://claude.ai/install.ps1' -UseBasicParsing).Content
    Invoke-Expression $install
  } catch {
    Warn "native installer failed ($_)."
    Warn "install manually: https://docs.anthropic.com/en/docs/claude-code — then re-run this line."
    return
  }
  Refresh-Path
  Start-Sleep -Seconds 1
  Refresh-Path
}
if (Have 'claude') { Ok "claude code" } else {
  Warn "claude still missing after install — close this window, open a NEW PowerShell, re-run."
  return
}

# ── The bible repo (public) — clone once, pull forever ───────────────────────
if (Test-Path (Join-Path $repoDir '.git')) {
  Say "updating the bible repo…"
  try {
    git -C $repoDir pull --ff-only 2>&1 | Out-Null
  } catch {
    Warn "git pull failed — using whatever is already at $repoDir"
  }
} else {
  Say "cloning the bible repo…"
  git clone --depth 1 $repoUrl $repoDir | Out-Null
}
if (-not (Test-Path (Join-Path $repoDir 'tv\start_tvd_win.ps1'))) {
  Warn "clone looks incomplete — missing tv\start_tvd_win.ps1 at $repoDir"
  return
}
Ok "repo at $repoDir"

# ── Desktop shortcut → the launcher (capture + reader in one) ────────────────
$ws  = New-Object -ComObject WScript.Shell
$lnkPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'TV DIABLO.lnk'
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath       = 'powershell.exe'
$lnk.Arguments        = "-NoLogo -ExecutionPolicy Bypass -File `"$repoDir\tv\start_tvd_win.ps1`""
$lnk.WorkingDirectory = $repoDir
$lnk.IconLocation     = 'shell32.dll,238'
$lnk.Description      = 'TV DIABLO — read-only loot scanner on your own Claude subscription'
$lnk.Save()
Ok "Desktop shortcut: TV DIABLO"

Say "DONE. Double-click the TV DIABLO shortcut on your Desktop."
$credFile = Join-Path $HOME '.claude\.credentials.json'
if (-not (Test-Path $credFile)) {
  Warn "first run will walk you through the ONE human step: logging into your own Claude account."
}
Say "then open the bible → TV·D tab → flip the switch. Farm."
