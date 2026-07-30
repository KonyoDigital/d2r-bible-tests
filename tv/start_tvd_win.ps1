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

function Focus-TvdWindow([bool]$unhide = $true) {
  # v1446 - pure C# EnumWindows (PS scriptblock EnumWindows hangs under D2R load).
  # v1460 - HIDDEN windows count too. The old callback bailed on !IsWindowVisible and only
  # ever handled IsIconic, so an SW_HIDE-ed 'TV DIABLO' window was unreachable: control kept
  # answering /api/status, the launcher took its 'already up - focus and leave' branch, focus
  # silently found nothing, and every Desktop double-click did nothing at all. Now we collect
  # visible AND hidden matches, prefer visible, and SW_SHOW a hidden one before raising it.
  # Also report whether the raise actually took (Law 9) instead of always logging success.
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
  const int SW_SHOW = 5;
  const int SW_RESTORE = 9;
  static IntPtr vis = IntPtr.Zero;
  static IntPtr hid = IntPtr.Zero;
  public static bool WasHidden = false;
  public static bool Raised = false;
  public static bool NowVisible = false;
  static bool Cb(IntPtr h, IntPtr l) {
    var sb = new StringBuilder(256);
    GetWindowText(h, sb, 256);
    string t = sb.ToString() ?? "";
    if (t == "TV DIABLO" || t.StartsWith("TV DIABLO ")) {
      if (IsWindowVisible(h)) { vis = h; return false; }   // visible is the best case - stop
      if (hid == IntPtr.Zero) hid = h;                     // remember first hidden, keep looking
    }
    return true;
  }
  // Returns TRUE only when the window is ACTUALLY visible afterwards. A cross-process
  // ShowWindow does not reliably un-hide a WinForms window that was born SW_HIDE (measured
  // on this machine), so we must verify rather than assume - otherwise the launcher logs
  // 'focused' for a window the human still cannot see. That lie is what hid this bug.
  //
  // unhide=false during a fresh boot: WinForms creates the form hidden and shows it itself a
  // moment later, so forcing SW_SHOW in that gap would paint a black frame before WebView2's
  // first paint - the very "black screen window" the user reported. Only force it as a
  // deliberate recovery (warm re-click, or after the boot grace period has expired).
  public static bool Focus(bool unhide) {
    vis = IntPtr.Zero; hid = IntPtr.Zero; WasHidden = false; Raised = false; NowVisible = false;
    EnumWindows(Cb, IntPtr.Zero);
    IntPtr found = (vis != IntPtr.Zero) ? vis : hid;
    if (found == IntPtr.Zero) return false;
    WasHidden = (vis == IntPtr.Zero);
    if (WasHidden) {
      if (!unhide) return false;   // let the app show its own window; not a success yet
      ShowWindow(found, SW_SHOW);
    }
    if (IsIconic(found)) ShowWindow(found, SW_RESTORE);
    Raised = SetForegroundWindow(found);
    NowVisible = IsWindowVisible(found);
    return NowVisible;
  }
}
"@
    }
    if ([TvdFocusFast]::Focus($unhide)) {
      $how = 'visible'
      if ([TvdFocusFast]::WasHidden) { $how = 'un-hid' }
      Write-TvdLaunchLog ("focused existing TV DIABLO window [{0} raised={1}]" -f $how, [TvdFocusFast]::Raised)
      return $true
    }
    if ([TvdFocusFast]::WasHidden -and $unhide) {
      # Found it, but SW_SHOW did not stick - the window is unrecoverable from out here.
      Write-TvdLaunchLog 'found a HIDDEN TV DIABLO window but SW_SHOW did not stick - stale process; STOP+reopen'
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
        # v1460 - Stop-Job has NO -Force parameter on Windows PowerShell 5.1. The old call
        # threw a ParameterBindingException straight past -ErrorAction into the outer catch,
        # so the job was NEVER stopped: it kept running and its merge --ff-only / reset --hard
        # rewrote control_app.py + control_ui.html ~0.6s AFTER python had already started.
        # The app then served swapped UI files from stale code and the window never came up.
        # Stop it for real, and WAIT for it to die before any spawn so the working tree is
        # never rewritten under a booting app. (ASCII only here - see REG-046.)
        Stop-Job -Job $fetchJob -ErrorAction SilentlyContinue
        $null = Wait-Job $fetchJob -Timeout 5
        Write-TvdLaunchLog ("auto-pull: timed out (12s) - stopped job state={0}; launching with local tree" -f $fetchJob.State)
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

# v1460 - the working tree must be QUIET before we spawn python. Stop-Job kills the job's
# runspace but a git.exe it already launched can outlive it and finish its merge/reset a
# moment later - which is exactly how control_app.py + control_ui.html got rewritten 0.6s
# after python started. Bounded wait; never blocks the icon for long.
function Wait-TvdGitQuiet([int]$maxMs = 6000) {
  $waited = 0
  while ($waited -lt $maxMs) {
    $g = @(Get-Process git -ErrorAction SilentlyContinue)
    if ($g.Count -eq 0) {
      if ($waited -gt 0) { Write-TvdLaunchLog ("git quiet after {0}ms" -f $waited) }
      return $true
    }
    Start-Sleep -Milliseconds 250
    $waited += 250
  }
  Write-TvdLaunchLog ("git still running after {0}ms - spawning anyway (tree may shift)" -f $maxMs)
  return $false
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

# v1460 - never spawn while git may still be rewriting the tree (see Wait-TvdGitQuiet).
[void](Wait-TvdGitQuiet)
$controlStamp = $null
try { $controlStamp = (Get-Item -LiteralPath $control).LastWriteTime } catch {}

Write-TvdLaunchLog ("launch FileName={0} Args={1} WD={2}" -f $exePath, $argLine, $repo)

try {
  # pythonw = no console flash (pythonw.exe is a GUI-subsystem binary - it has NO console).
  #
  # v1460 ROOT CAUSE of the dead Desktop icon: v1444 added -WindowStyle Hidden here. That
  # sets STARTUPINFO.wShowWindow = SW_HIDE on the child, and .NET WinForms applies the
  # startup show-command to the process's FIRST top-level window - which is pywebview's
  # WebView2 host window. So the app window was created correctly (right title, 1120x737,
  # on-screen) and then never shown: control answered :17772, /api/status said ready, the
  # launcher logged 'launch complete', and the user saw nothing but two PowerShell consoles
  # blink. Proven A/B on this machine: same script spawned Hidden -> IsWindowVisible False,
  # spawned default -> True. The flag was never needed (pythonw has no console to hide).
  $proc = Start-Process -FilePath $exePath -ArgumentList $argLine -WorkingDirectory $repo -PassThru
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
  # v1460 Law 9 - a /api/status answer is NOT proof of a window. v1448 traded the slow
  # doctor probe for this fast one and started logging 'launch complete' for a process that
  # served :17772 with no window at all, which is how the dead-icon state stayed invisible
  # in the log for days. Give WebView2 a bounded chance to paint, then log what is TRUE.
  $win = $false
  for ($w = 0; $w -lt 12; $w++) {
    # First ~2.4s = boot grace: WinForms creates the form hidden and shows it itself, so do
    # NOT force SW_SHOW yet (that would flash a black frame before WebView2's first paint).
    # Still hidden after the grace period = a real fault, so force it then.
    if (Focus-TvdWindow ($w -ge 6)) { $win = $true; break }
    Start-Sleep -Milliseconds 400
  }
  if ($controlStamp) {
    try {
      $now = (Get-Item -LiteralPath $control).LastWriteTime
      if ($now -ne $controlStamp) {
        Write-TvdLaunchLog ("WARN control_app.py was rewritten during boot ({0} -> {1}) - app is running stale code; relaunch" -f $controlStamp, $now)
      }
    } catch {}
  }
  if ($win) {
    Write-TvdLaunchLog 'launch complete (window up)'
  } else {
    Write-TvdLaunchLog 'WARN control up but NO TV DIABLO window after ~4.8s - headless/hidden; STOP+reopen if the icon stays dead'
  }
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
