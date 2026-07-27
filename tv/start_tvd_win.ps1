# TV DIABLO - Windows launcher ONLY (Desktop - native pywebview / WebView2, NOT Chrome)
# NOT for Mac. Mac uses start_tvd_mac.sh / install-tvd.sh on a different machine.
# Agent + capture stay hidden. Controls: ON/OFF/STOP/RESTART/SIM.
# Encoding: ASCII-only strings so Windows PowerShell 5.1 never mis-parses UTF-8.
#
# v1444-v1448 UX launch smooth:
#   - ready probe = /api/status (NOT full doctor ok:true which is false under ON AIR + SLOW)
#   - if already up: focus + exit BEFORE git/pip (no lag, no second window)
#   - auto-pull time-boxed; never blocks a warm relaunch
#   - C# focus (no PS EnumWindows hang under D2R)
#   - short ready wait; no error dialog while python still starting
$ErrorActionPreference = 'Continue'
if ($env:OS -ne 'Windows_NT') {
  Write-Host 'TV DIABLO start_tvd_win.ps1 is Windows only.' -ForegroundColor Red
  return
}
$env:TV_PLATFORM = 'windows'
$env:TV_OS = 'windows'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $here
$launchLog = Join-Path $here 'start_tvd_win.log'

function Write-TvdLaunchLog([string]$msg) {
  $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
  try { Add-Content -LiteralPath $launchLog -Value $line -Encoding UTF8 } catch {}
}

function Test-TvdControlUp {
  # v1444 — control is UP when /api/status answers with a ver field.
  # NEVER require doctor.ok=true: that is false while LIVE with frame faults and takes seconds.
  try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:17772/api/status' -UseBasicParsing -TimeoutSec 0.35
    $body = [string]$resp.Content
    if ($body -match '"ver"\s*:\s*"v') { return $true }
  } catch {}
  return $false
}

function Focus-TvdWindow {
  # v1446 — pure C# EnumWindows (PS scriptblock EnumWindows hangs under D2R load).
  try {
    if (-not ('TvdFocusFast' -as [type])) {
      Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class TvdFocusFast {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  static IntPtr found = IntPtr.Zero;
  static bool Cb(IntPtr h, IntPtr l) {
    if (!IsWindowVisible(h)) return true;
    var sb = new StringBuilder(256);
    GetWindowText(h, sb, 256);
    string t = sb.ToString() ?? "";
    if (t == "TV DIABLO" || t.StartsWith("TV DIABLO ")) { found = h; return false; }
    return true;
  }
  public static bool Focus() {
    found = IntPtr.Zero;
    EnumWindows(Cb, IntPtr.Zero);
    if (found == IntPtr.Zero) return false;
    if (IsIconic(found)) ShowWindow(found, 9);
    SetForegroundWindow(found);
    return true;
  }
}
"@
    }
    if ([TvdFocusFast]::Focus()) {
      Write-TvdLaunchLog 'focused existing TV DIABLO window'
      return $true
    }
  } catch {
    Write-TvdLaunchLog ("focus note: {0}" -f $_)
  }
  return $false
}

function Show-TvdError([string]$text) {
  try {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($text, 'TV DIABLO', 'OK', 'Error') | Out-Null
  } catch {
    Write-Host $text
  }
}

# ---------------------------------------------------------------------------
# v1417/v1448 SINGLE INSTANCE FIRST — before git/pip/python probes.
# ---------------------------------------------------------------------------
$mutex = $null
try {
  $created = $false
  $mutex = New-Object System.Threading.Mutex($true, 'Local\TV_DIABLO_WIN_LAUNCHER_v2', [ref]$created)
  if (-not $created) {
    Write-TvdLaunchLog 'launcher mutex busy - focus existing / exit quiet'
    [void](Focus-TvdWindow)
    try { $mutex.Dispose() } catch {}
    $mutex = $null
    return
  }
} catch {
  Write-TvdLaunchLog ("mutex note: {0}" -f $_)
  $mutex = $null
}

# v1444/v1445 — ALREADY UP: focus and leave. Do not git-pull, pip, or spawn python.
if (Test-TvdControlUp) {
  Write-TvdLaunchLog 'control already up - focusing; skip pull/spawn'
  [void](Focus-TvdWindow)
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  return
}

# PATH seed
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path', 'User')
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
        return @{ Cmd = 'py'; Prefix = @('-3') }
      } catch { continue }
    }
    if ($c -eq 'pythonw') {
      $py = Get-Command python -ErrorAction SilentlyContinue
      if ($py -and ([string]$py.Source) -notmatch 'WindowsApps\\') {
        return @{ Cmd = 'pythonw'; Prefix = @() }
      }
      continue
    }
    try {
      $v = & $c -c "import sys; print(sys.version)" 2>$null
      if (-not $v) { continue }
      return @{ Cmd = $c; Prefix = @() }
    } catch { continue }
  }
  return $null
}

$py = Real-Python
if (-not $py) {
  Write-TvdLaunchLog 'No real Python found'
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  Show-TvdError "No real Python found. Re-run the installer.`n`nLog: $launchLog"
  return
}

# v1447 — webview probe once; cache result so warm launches skip pip
$wvCache = Join-Path $here '.webview_ok'
$needWv = -not (Test-Path -LiteralPath $wvCache)
if ($needWv) {
  $probe = if ($py.Cmd -eq 'py') { @('py', '-3', '-c', 'import webview') }
           elseif ($py.Cmd -eq 'pythonw') { @('python', '-c', 'import webview') }
           else { @($py.Cmd, '-c', 'import webview') }
  $ok = $false
  try {
    & $probe[0] $probe[1..($probe.Length - 1)] 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true }
  } catch {}
  if (-not $ok) {
    Write-TvdLaunchLog 'installing pywebview (first run)'
    $pip = if ($py.Cmd -eq 'py') { @('py', '-3', '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
           elseif ($py.Cmd -eq 'pythonw') { @('python', '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
           else { @($py.Cmd, '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
    try { & $pip[0] $pip[1..($pip.Length - 1)] 2>$null | Out-Null } catch {}
  } else {
    try { Set-Content -LiteralPath $wvCache -Value '1' -Encoding ASCII } catch {}
  }
}

# v1447 — NEVER open a blocking claude login shell on Desktop double-click (extra window lag).
# Doctor/ON AIR will surface Claude missing if needed.

# v1445 — time-boxed auto-pull AFTER we know we must spawn (not on warm re-open).
# Cap wall time so a hung git never freezes the Desktop icon for 30s+.
if (-not $env:TV_NO_AUTO_PULL) {
  $trackedDirty = $false
  try {
    $porc = @(git -C $repo status --porcelain 2>$null)
    foreach ($line in $porc) {
      if ($line -and ($line -notmatch '^\?\?')) { $trackedDirty = $true; break }
    }
  } catch {}
  if ($trackedDirty) {
    Write-TvdLaunchLog 'skip auto-pull: tracked files modified'
  } else {
    try {
      $env:GIT_TERMINAL_PROMPT = '0'
      # shallow-ish: fetch with 10s kill via job
      $fetchJob = Start-Job -ScriptBlock {
        param($r)
        git -C $r fetch origin --quiet 2>$null
        git -C $r merge --ff-only origin/main 2>$null
        if ($LASTEXITCODE -ne 0) {
          git -C $r reset --hard origin/main 2>$null
        }
      } -ArgumentList $repo
      $null = Wait-Job $fetchJob -Timeout 12
      if ($fetchJob.State -eq 'Running') {
        Stop-Job $fetchJob -Force -ErrorAction SilentlyContinue
        Write-TvdLaunchLog 'auto-pull: timed out (12s) — launching with local tree'
      } else {
        Write-TvdLaunchLog 'auto-pull: done'
      }
      Remove-Job $fetchJob -Force -ErrorAction SilentlyContinue
    } catch {
      Write-TvdLaunchLog ("auto-pull error: {0}" -f $_)
    }
  }
} else {
  Write-TvdLaunchLog 'skip auto-pull: TV_NO_AUTO_PULL set'
}

# Re-check after pull: another click may have won
if (Test-TvdControlUp) {
  Write-TvdLaunchLog 'control came up during pull - focus only'
  [void](Focus-TvdWindow)
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  return
}

$control = Join-Path $here 'control_app.py'
$ui = Join-Path $here 'control_ui.html'
$capture = Join-Path $here 'capture_win.ps1'
$shipPath = Join-Path $here 'WINDOWS_SHIP.json'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath $ui)) {
  Write-TvdLaunchLog 'control_app.py or control_ui.html missing'
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  Show-TvdError "Control app files missing. Re-run WINDOWS installer.`nLog: $launchLog"
  return
}
if (-not (Test-Path -LiteralPath $capture)) {
  Write-TvdLaunchLog 'capture_win.ps1 missing'
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  Show-TvdError "Windows capture missing (capture_win.ps1).`nLog: $launchLog"
  return
}

$shipVer = '?'
if (Test-Path -LiteralPath $shipPath) {
  try {
    $ship = Get-Content -LiteralPath $shipPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($ship.platform -ne 'windows') {
      if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
      Show-TvdError "WINDOWS_SHIP.platform=$($ship.platform) - this launcher is Windows only."
      return
    }
    $shipVer = [string]$ship.ver
    Write-TvdLaunchLog ("Windows ship ver={0}" -f $shipVer)
  } catch {
    Write-TvdLaunchLog ("WINDOWS_SHIP.json read failed: {0}" -f $_)
  }
}

$exeCmd = Get-Command $py.Cmd -ErrorAction SilentlyContinue
$exePath = if ($exeCmd) { [string]$exeCmd.Source } else { $py.Cmd }
if ($py.Cmd -eq 'py') {
  $argLine = '-3 "' + $control + '" --open'
} else {
  $argLine = '"' + $control + '" --open'
}

Write-TvdLaunchLog ("launch FileName={0} Args={1} WD={2}" -f $exePath, $argLine, $repo)

try {
  # pythonw = no console flash
  $proc = Start-Process -FilePath $exePath -ArgumentList $argLine -WorkingDirectory $repo -PassThru -WindowStyle Hidden
  Write-TvdLaunchLog ("started pid={0}" -f $proc.Id)
} catch {
  Write-TvdLaunchLog ("Start-Process FAILED: {0}" -f $_)
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  Show-TvdError "TV DIABLO failed to start Python.`n`n$_`n`nLog: $launchLog"
  return
}

# v1448 — ready wait uses FAST status probe (max ~8s), not 45s doctor ok:true
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Milliseconds 400
  if (Test-TvdControlUp) {
    $ready = $true
    Write-TvdLaunchLog ("ready status OK i={0} pid={1}" -f $i, $proc.Id)
    break
  }
  if ($proc.HasExited -and $i -gt 3) {
    Start-Sleep -Milliseconds 400
    if (Test-TvdControlUp) { $ready = $true; break }
    Write-TvdLaunchLog ("python exited early code={0}" -f $proc.ExitCode)
    break
  }
}

# Release launcher mutex ASAP so a second click only FOCUSES (does not queue another full launch)
if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose(); $mutex = $null }

if ($ready) {
  [void](Focus-TvdWindow)
  Write-TvdLaunchLog 'launch complete'
  return
}

# Soft: process still alive — window may paint under WebView2 cold start; no scary dialog
if (-not $proc.HasExited) {
  Write-TvdLaunchLog 'status slow but process alive - exit quiet (window coming)'
  [void](Focus-TvdWindow)
  return
}

Write-TvdLaunchLog 'launch FAIL: process dead and status down'
Show-TvdError (
  "TV DIABLO did not come up.`n`nPython exited and control is down.`n" +
  "Log: $launchLog`n`nTry: powershell -File `"$PSCommandPath`""
)
