# 📺 TV DIABLO — one-shot Windows installer (the cousin move · v760 twin)
#
#     irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
#
# One paste: Git + Python + pywebview + Claude Code, clones the bible repo,
# drops Desktop "TV DIABLO" → real native app window (pywebview / Edge WebView2,
# NOT Chrome). Same control UI as Mac: ON/OFF/STOP/RESTART/SIM · hidden agent.
#
# Served as text/plain so `irm | iex` always gets a string.
$ErrorActionPreference = 'Stop'
$repoUrl  = 'https://github.com/KonyoDigital/d2r-bible-tests.git'
$repoDir  = Join-Path $HOME 'd2r_bible_tests'

function Say($m)  { Write-Host "TV DIABLO  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "   OK  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "   !!  $m" -ForegroundColor Yellow }

try {
  [Net.ServicePointManager]::SecurityProtocol = `
    [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {}

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = @($machine, $user) -join ';'
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

Say "installer (Windows twin) — one shot, then Desktop TV DIABLO = the control app"

if (-not (Have 'winget')) {
  Warn "winget not found — install 'App Installer' from the Microsoft Store, then re-run this line."
  return
}

Refresh-Path
if (-not (Have 'git')) {
  Winget-Install 'Git.Git' 'Git'
}
if (Have 'git') { Ok "git $((git --version) -replace 'git version ','')" } else {
  Warn "git still missing — close this window, open a NEW PowerShell, re-run the install line."
  return
}

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

# ── pywebview (real native window via Edge WebView2 — not Chrome) ────────────
Say "installing pywebview (native app window)…"
try {
  & $py -m pip install --user --quiet 'pywebview>=5.0' | Out-Null
  Ok "pywebview (native window · WebView2)"
} catch {
  Warn "pywebview pip install failed — app will retry on first launch / browser fallback"
}

Refresh-Path
if (-not (Have 'claude')) {
  Say "installing Claude Code (Anthropic's official installer)…"
  try {
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

# v761 twin requires the control app surface
$need = @(
  'tv\start_tvd_win.ps1',
  'tv\control_app.py',
  'tv\control_ui.html',
  'tv\capture_win.ps1',
  'tv\tv_diablo.py',
  'bible.html'
)
foreach ($rel in $need) {
  if (-not (Test-Path (Join-Path $repoDir $rel))) {
    Warn "clone incomplete — missing $rel at $repoDir"
    Warn "git pull main (need v761+). Re-run this install line after the repo updates."
    return
  }
}
Ok "repo at $repoDir (control app present)"

# Desktop shortcut → start_tvd_win.ps1 → pythonw + pywebview native window
$ws  = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop 'TV DIABLO.lnk'
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath       = 'powershell.exe'
# Hidden host shell only — the app window is pywebview (pythonw), not this console
$lnk.Arguments        = "-NoLogo -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$repoDir\tv\start_tvd_win.ps1`""
$lnk.WorkingDirectory = $repoDir
$lnk.IconLocation     = 'shell32.dll,238'
$lnk.Description      = 'TV DIABLO — native control app (pywebview · hidden scanner · your Claude)'
$lnk.Save()
Ok "Desktop shortcut: TV DIABLO"

# Also Start Menu for discoverability
try {
  $startDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
  if (Test-Path $startDir) {
    $sl = $ws.CreateShortcut((Join-Path $startDir 'TV DIABLO.lnk'))
    $sl.TargetPath       = $lnk.TargetPath
    $sl.Arguments        = $lnk.Arguments
    $sl.WorkingDirectory = $lnk.WorkingDirectory
    $sl.IconLocation     = $lnk.IconLocation
    $sl.Description      = $lnk.Description
    $sl.Save()
    Ok "Start Menu: TV DIABLO"
  }
} catch {}

Say "DONE. Double-click TV DIABLO on your Desktop."
Say "Native app window (not Chrome) · ON / OFF / STOP / RESTART / SIM · board auto-connects."
$credFile = Join-Path $HOME '.claude\.credentials.json'
if (-not (Test-Path $credFile)) {
  Warn "first run may walk you through logging into your own Claude account (once)."
}
echo ""
echo "   Windows:  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
echo "   Mac:      curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash"
