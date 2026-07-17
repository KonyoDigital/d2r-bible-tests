# 📺 TV DIABLO — Windows launcher (Desktop shortcut · v760)
# Opens the SAME HD control window as Mac (no PowerShell agent dump).
# Agent + capture run HIDDEN behind ON/OFF/STOP/RESTART/SIM.
# Read-only · your Claude subscription · zero API keys.
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path   # …\d2r_bible_tests\tv
$repo = Split-Path -Parent $here

function Real-Python {
  foreach ($c in @('pythonw', 'python', 'py')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    $src = [string]$cmd.Source
    if ($src -match 'WindowsApps\\(?:python|python3|pythonw)\.exe$') { continue }
    if ($c -eq 'py') {
      try {
        $v = & $c -3 -c "import sys; print(sys.version)" 2>$null
        if (-not $v) { continue }
        return @{ Cmd = 'py'; ArgsPrefix = @('-3') }
      } catch { continue }
    }
    if ($c -eq 'pythonw' -or $c -eq 'python') {
      try {
        # pythonw has no stdout — probe with python if needed
        if ($c -eq 'pythonw') {
          $py = Get-Command python -ErrorAction SilentlyContinue
          if ($py -and ([string]$py.Source) -notmatch 'WindowsApps\\') {
            return @{ Cmd = 'pythonw'; ArgsPrefix = @() }
          }
          # fall through to python
          continue
        }
        $v = & $c -c "import sys; print(sys.version)" 2>$null
        if (-not $v) { continue }
        return @{ Cmd = $c; ArgsPrefix = @() }
      } catch { continue }
    }
  }
  return $null
}

function Control-Listening {
  try {
    $c = Get-NetTCPConnection -LocalPort 17772 -State Listen -ErrorAction SilentlyContinue
    return [bool]$c
  } catch {
    $net = netstat -ano -p tcp 2>$null | Select-String ':17772' | Select-String 'LISTENING'
    return [bool]$net
  }
}

function Open-ControlWindow {
  $url = 'http://127.0.0.1:17772/'
  $browsers = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:LocalAppData\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LocalAppData\BraveSoftware\Brave-Browser\Application\brave.exe"
  )
  foreach ($b in $browsers) {
    if (Test-Path -LiteralPath $b) {
      Start-Process -FilePath $b -ArgumentList @("--app=$url", "--window-size=1100,780") -WindowStyle Normal | Out-Null
      return
    }
  }
  Start-Process $url | Out-Null
}

# ── PATH seed (same homes as the installer) ──────────────────────────────────
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path','User')
foreach ($p in @(
  "$env:LocalAppData\Programs\Python\Python312",
  "$env:LocalAppData\Programs\Python\Python312\Scripts",
  "$env:LocalAppData\Programs\Python\Python313",
  "$env:LocalAppData\Programs\Python\Python313\Scripts",
  "$env:LocalAppData\Microsoft\WinGet\Links",
  "$env:ProgramFiles\Git\cmd",
  "$env:USERPROFILE\.local\bin"
)) {
  if ((Test-Path -LiteralPath $p) -and ($env:Path -notlike "*$p*")) {
    $env:Path = "$p;$env:Path"
  }
}

# subscription contract
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show(
    "Claude Code not found.`nRe-run:`nirm https://bull-4-u.com/d2r/install-tvd.ps1 | iex",
    "TV DIABLO", 'OK', 'Error') | Out-Null
  return
}

# Soft first-run login (credentials file OR Keychain-style later — just open claude once)
$credHit = $false
foreach ($c in @(
  (Join-Path $HOME '.claude\.credentials.json'),
  (Join-Path $HOME '.config\claude\.credentials.json'),
  (Join-Path $HOME '.claude.json')
)) {
  if (Test-Path -LiteralPath $c) { $credHit = $true; break }
}
if (-not $credHit) {
  Start-Process -Wait powershell -ArgumentList '-NoLogo','-Command','claude' -ErrorAction SilentlyContinue
}

# pull-first
try { git -C $repo pull --ff-only 2>$null | Out-Null } catch {}

$control = Join-Path $here 'control_app.py'
$ui = Join-Path $here 'control_ui.html'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath $ui)) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show(
    "Control app files missing. Re-run the installer so git pull gets v760+.",
    "TV DIABLO", 'OK', 'Error') | Out-Null
  return
}

# Already live → just re-open the window (same as Mac)
if (Control-Listening) {
  Open-ControlWindow
  return
}

$py = Real-Python
if (-not $py) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show(
    "No real Python found (Windows Store stub?). Re-run the installer.",
    "TV DIABLO", 'OK', 'Error') | Out-Null
  return
}

# Prefer pythonw (no console). Fall back to python -WindowStyle Hidden via Start-Process.
$exe = $py.Cmd
$prefix = $py.ArgsPrefix
$argList = @()
$argList += $prefix
$argList += $control
$argList += '--open'

# pythonw = no console (preferred). Do not Redirect* on pythonw (it has no stdio).
if ($exe -eq 'pythonw') {
  Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $repo -WindowStyle Hidden | Out-Null
} elseif ($exe -eq 'py') {
  Start-Process -FilePath 'py' -ArgumentList (@('-3', $control, '--open')) -WorkingDirectory $repo `
    -WindowStyle Hidden | Out-Null
} else {
  Start-Process -FilePath $exe -ArgumentList @($control, '--open') -WorkingDirectory $repo `
    -WindowStyle Hidden | Out-Null
}

# Give the server a beat, then ensure the app window is up (control also --open's)
Start-Sleep -Milliseconds 500
if (Control-Listening) {
  # control_app --open already tried; open again is fine if first missed
} else {
  Start-Sleep -Seconds 1
  if (-not (Control-Listening)) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "Control server did not start on :17772.`nSee tv\control_app.log",
      "TV DIABLO", 'OK', 'Error') | Out-Null
  }
}
