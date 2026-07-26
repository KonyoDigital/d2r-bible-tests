#  TV DIABLO - one-shot Windows installer (Windows only  -  v1404)
#
#     irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
#
# One paste: Git + Python + pywebview + Claude Code + Grok CLI (optional SuperGrok
# vision lane), clones the bible repo, drops Desktop "TV DIABLO" -> real native app
# window (pywebview / Edge WebView2, NOT Chrome). Windows control UI (pywebview / WebView2):
# ON/OFF/STOP/RESTART/SIM  -  hidden agent. Grok stays OFF until you authorize once.
#
# Served as text/plain so `irm | iex` always gets a string.
$ErrorActionPreference = 'Stop'

# v1404 WINDOWS ONLY - never run Mac scripts on this PC; never claim Mac parity here.
if ($env:OS -ne 'Windows_NT') {
  Write-Host 'TV DIABLO installer: Windows only. Use the Mac installer on macOS.' -ForegroundColor Red
  return
}
$env:TV_PLATFORM = 'windows'
$env:TV_OS = 'windows'

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
  Say "installing $label..."
  $wingetArgs = @('install', '-e', '--id', $id, '--silent',
                  '--accept-package-agreements', '--accept-source-agreements',
                  '--disable-interactivity')
  & winget @wingetArgs | Out-Null
  Refresh-Path
  Start-Sleep -Seconds 1
  Refresh-Path
}

Say "installer (Windows only  -  v1404) - one shot, then Desktop TV DIABLO = the control app"

if (-not (Have 'winget')) {
  Warn "winget not found - install 'App Installer' from the Microsoft Store, then re-run this line."
  return
}

Refresh-Path
if (-not (Have 'git')) {
  Winget-Install 'Git.Git' 'Git'
}
if (Have 'git') { Ok "git $((git --version) -replace 'git version ','')" } else {
  Warn "git still missing - close this window, open a NEW PowerShell, re-run the install line."
  return
}

$py = Real-Python
if (-not $py) {
  Winget-Install 'Python.Python.3.12' 'Python 3.12'
  $py = Real-Python
}
if ($py) { Ok "python ($py)" } else {
  Warn "python still missing (or only the Windows Store stub is installed)."
  Warn "turn OFF 'App execution aliases' for python.exe in Settings -> Apps -> Advanced, then re-run."
  return
}

# -- pywebview (real native window via Edge WebView2 - not Chrome) ------------
Say "installing pywebview (native app window)..."
try {
  & $py -m pip install --user --quiet 'pywebview>=5.0' | Out-Null
  # v770 - pywebview on Windows NEEDS the Edge WebView2 Runtime; locked-down PCs lack it and
  # the app silently falls to a browser. Bootstrap it loudly if missing.
  $wv2 = Test-Path "$env:ProgramFiles (x86)\Microsoft\EdgeWebView\Application" -PathType Container
  if (-not $wv2) { $wv2 = Test-Path "${env:ProgramFiles(x86)}\Microsoft\EdgeWebView\Application" }
  if (-not $wv2) {
    Say "installing Edge WebView2 Runtime (the native window engine)..."
    winget install -e --id Microsoft.EdgeWebView2Runtime --silent --accept-package-agreements --accept-source-agreements | Out-Null
  }
  Ok "pywebview (native window  -  WebView2)"
} catch {
  Warn "pywebview pip install failed - app will retry on first launch / browser fallback"
}

# -- bible repo FIRST (so Desktop shortcut always lands even if Claude install flakes) --
if (Test-Path (Join-Path $repoDir '.git')) {
  Say "updating the bible repo..."
  try {
    git -C $repoDir pull --ff-only 2>&1 | Out-Null
  } catch {
    Warn "git pull failed - using whatever is already at $repoDir"
  }
} else {
  Say "cloning the bible repo..."
  git clone --depth 1 $repoUrl $repoDir | Out-Null
}

# v761+ twin requires the control app surface
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
    Warn "clone incomplete - missing $rel at $repoDir"
    Warn "git pull main (need v761+). Re-run this install line after the repo updates."
    return
  }
}
Ok "repo at $repoDir (control app present)"

# v1404 - pin Windows ship identity (no Mac mesh)
$shipPath = Join-Path $repoDir 'tv\WINDOWS_SHIP.json'
if (-not (Test-Path -LiteralPath $shipPath)) {
  Warn "WINDOWS_SHIP.json missing after clone - repo may be incomplete. Re-run after git pull."
} else {
  try {
    $ship = Get-Content -LiteralPath $shipPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($ship.platform -ne 'windows') {
      Warn "WINDOWS_SHIP.platform is '$($ship.platform)' - expected windows. Do not use Mac installers on this PC."
    } else {
      Ok "Windows ship $($ship.ver)  -  platform=windows  -  $($ship.name)"
    }
    $stampObj = [ordered]@{
      platform   = 'windows'
      shipVer    = [string]$ship.ver
      installedAt = (Get-Date).ToString('o')
      computer   = $env:COMPUTERNAME
      user       = $env:USERNAME
      repo       = $repoDir
      launcher   = 'tv\start_tvd_win.ps1'
      capture    = 'tv\capture_win.ps1'
      installer  = 'tv\install-tvd.ps1'
    }
    $stampPath = Join-Path $repoDir 'tv\.windows_install.json'
    ($stampObj | ConvertTo-Json) | Set-Content -LiteralPath $stampPath -Encoding UTF8
    Ok "install stamp: $stampPath"
  } catch {
    Warn "could not read WINDOWS_SHIP.json: $($_.Exception.Message)"
  }
}


# -- Claude Code (needed for vision ON AIR) -----------------------------------
# v784.1 - Windows PowerShell 5.1 often returns .Content as Byte[] for install.ps1;
#          Invoke-Expression then dies with "Cannot convert System.Byte[] to String".
#          Decode to UTF-8 string; fall backs: irm|iex, winget. NEVER abort before Desktop.
function Install-ClaudeCode {
  if (Have 'claude') { return $true }
  Say "installing Claude Code (Anthropic's official installer)..."

  # Path A - robust download + decode (fixes Byte[] crash on PS 5.1)
  try {
    $resp = Invoke-WebRequest -Uri 'https://claude.ai/install.ps1' -UseBasicParsing
    $scriptText = $null
    if ($null -eq $resp.Content) {
      throw "empty install.ps1 body"
    } elseif ($resp.Content -is [byte[]]) {
      $scriptText = [System.Text.Encoding]::UTF8.GetString($resp.Content)
    } else {
      $scriptText = [string]$resp.Content
    }
    if (-not $scriptText -or $scriptText.Length -lt 20) {
      throw "install.ps1 body too short"
    }
    Invoke-Expression $scriptText
  } catch {
    Warn "official install.ps1 path failed ($($_.Exception.Message))"
    # Path B - irm | iex (PowerShell may coerce bytes differently)
    try {
      Invoke-Expression (Invoke-RestMethod -Uri 'https://claude.ai/install.ps1')
    } catch {
      Warn "irm/iex path failed ($($_.Exception.Message))"
      # Path C - winget (when published)
      try {
        if (Have 'winget') {
          Say "trying winget Anthropic.ClaudeCode..."
          winget install -e --id Anthropic.ClaudeCode --silent --accept-package-agreements --accept-source-agreements 2>$null | Out-Null
        }
      } catch {}
    }
  }

  Refresh-Path
  Start-Sleep -Seconds 2
  Refresh-Path
  # common install locations not yet on PATH in this shell
  foreach ($p in @(
    (Join-Path $env:USERPROFILE '.local\bin'),
    (Join-Path $env:LocalAppData 'Programs\claude'),
    (Join-Path $env:LocalAppData 'claude'),
    (Join-Path $env:APPDATA 'npm')
  )) {
    if ((Test-Path -LiteralPath $p) -and ($env:Path -notlike "*$p*")) {
      $env:Path = "$p;$env:Path"
    }
  }
  return (Have 'claude')
}

Refresh-Path
$claudeOk = Install-ClaudeCode
if ($claudeOk) {
  Ok "claude code"
} else {
  Warn "claude still missing - vision ON AIR needs it."
  Warn "install manually: https://docs.anthropic.com/en/docs/claude-code"
  Warn "or in a NEW PowerShell:  irm https://claude.ai/install.ps1 | iex"
  Warn "Desktop app will still be created - log into Claude before ON."
}

# -- Grok Build CLI (optional SuperGrok vision lane  -  G5  -  never required) ----
# Official xAI installer (same spirit as Claude Code). Cousin can leave Grok OFF.
# Authorize once later: console  Authorize Grok, or:  grok login
function Install-GrokCli {
  if (Have 'grok') { return $true }
  Say "installing Grok CLI (xAI SuperGrok  -  optional vision lane)..."
  try {
    $resp = Invoke-WebRequest -Uri 'https://x.ai/cli/install.ps1' -UseBasicParsing
    $scriptText = $null
    if ($null -eq $resp.Content) {
      throw "empty install.ps1 body"
    } elseif ($resp.Content -is [byte[]]) {
      $scriptText = [System.Text.Encoding]::UTF8.GetString($resp.Content)
    } else {
      $scriptText = [string]$resp.Content
    }
    if (-not $scriptText -or $scriptText.Length -lt 20) {
      throw "install.ps1 body too short"
    }
    Invoke-Expression $scriptText
  } catch {
    Warn "official Grok install.ps1 path failed ($($_.Exception.Message))"
    try {
      Invoke-Expression (Invoke-RestMethod -Uri 'https://x.ai/cli/install.ps1')
    } catch {
      Warn "Grok irm/iex path failed ($($_.Exception.Message))"
    }
  }
  Refresh-Path
  Start-Sleep -Seconds 2
  Refresh-Path
  foreach ($p in @(
    (Join-Path $env:USERPROFILE '.grok\bin'),
    (Join-Path $env:USERPROFILE '.local\bin'),
    (Join-Path $env:LocalAppData 'Programs\grok'),
    (Join-Path $env:LocalAppData 'grok')
  )) {
    if ((Test-Path -LiteralPath $p) -and ($env:Path -notlike "*$p*")) {
      $env:Path = "$p;$env:Path"
    }
  }
  return (Have 'grok')
}

Refresh-Path
$grokOk = Install-GrokCli
if ($grokOk) {
  Ok "grok cli (optional - authorize later in console or: grok login)"
} else {
  Warn "grok CLI not installed - optional. Grok Eyes stays OFF until you install SuperGrok CLI."
  Warn "manual:  irm https://x.ai/cli/install.ps1 | iex   then:  grok login"
}

# Desktop shortcut -> start_tvd_win.ps1 -> pythonw + pywebview native window
$ws  = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
# OneDrive Desktop redirect (common on Windows 11)
$deskCandidates = @(
  $desktop,
  (Join-Path $env:USERPROFILE 'Desktop'),
  (Join-Path $env:USERPROFILE 'OneDrive\Desktop'),
  (Join-Path $env:USERPROFILE 'OneDrive - Personal\Desktop')
) | Select-Object -Unique
$lnkPath = $null
foreach ($d in $deskCandidates) {
  if ($d -and (Test-Path -LiteralPath $d)) {
    $lnkPath = Join-Path $d 'TV DIABLO.lnk'
    break
  }
}
if (-not $lnkPath) {
  $lnkPath = Join-Path $desktop 'TV DIABLO.lnk'
}
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath       = 'powershell.exe'
# Hidden host shell only - the app window is pywebview (pythonw), not this console
$lnk.Arguments        = "-NoLogo -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$repoDir\tv\start_tvd_win.ps1`""
$lnk.WorkingDirectory = $repoDir
$ico = Join-Path $repoDir 'tv\appicon.ico'
if (Test-Path -LiteralPath $ico) {
  $lnk.IconLocation = $ico
} else {
  $lnk.IconLocation = 'powershell.exe,0'
}
$lnk.Description      = 'TV DIABLO Windows - native WebView2 control (NOT Mac  -  hidden scanner  -  Claude)'
$lnk.Save()
Ok "Desktop shortcut: $lnkPath"

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

Say "DONE. Double-click TV DIABLO on your Desktop (or Start Menu)."
Say "Native app window (not Chrome)  -  ON / OFF / STOP / RESTART / SIM  -  one window."
if (-not $claudeOk) {
  Warn "finish Claude Code install, then re-open TV DIABLO and press ON AIR."
}
$credFile = Join-Path $HOME '.claude\.credentials.json'
if (-not (Test-Path $credFile)) {
  Warn "first run may walk you through logging into your own Claude account (once)."
}
if ($grokOk) {
  $gAuth = Join-Path $HOME '.grok\auth.json'
  if (-not (Test-Path $gAuth)) {
    Warn "Grok CLI ready - open TV DIABLO ->  advanced ->  Authorize Grok (browser once), or: grok login"
  } else {
    Ok "Grok already authorized on this PC (no re-login needed)"
  }
}
echo ""
echo "   Windows only:  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex"
echo "   Ship:         tv\WINDOWS_SHIP.json  (platform=windows)"
