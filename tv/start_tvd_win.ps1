# TV DIABLO - Windows launcher ONLY (Desktop - native pywebview / WebView2, NOT Chrome)
# NOT for Mac. Mac uses start_tvd_mac.sh / install-tvd.sh on a different machine.
# Agent + capture stay hidden. Controls: ON/OFF/STOP/RESTART/SIM.
# Encoding: ASCII-only strings so Windows PowerShell 5.1 never mis-parses UTF-8.
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

function Real-Python {
  # Prefer pythonw for GUI-only (no console flash)
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

function Show-TvdError([string]$text) {
  try {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($text, 'TV DIABLO', 'OK', 'Error') | Out-Null
  } catch {
    Write-Host $text
  }
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

Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

# PATH seed for Claude (Desktop shortcut shells often miss ~/.local/bin + npm)
foreach ($p in @(
  (Join-Path $env:USERPROFILE '.local\bin'),
  (Join-Path $env:LocalAppData 'Programs\claude'),
  (Join-Path $env:LocalAppData 'claude'),
  (Join-Path $env:APPDATA 'npm'),
  (Join-Path $env:LocalAppData 'Microsoft\WinGet\Links')
)) {
  if ((Test-Path -LiteralPath $p) -and ($env:Path -notlike "*$p*")) {
    $env:Path = "$p;$env:Path"
  }
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  $claudeHit = $null
  foreach ($c in @(
    (Join-Path $env:USERPROFILE '.local\bin\claude.exe'),
    (Join-Path $env:USERPROFILE '.local\bin\claude.cmd'),
    (Join-Path $env:APPDATA 'npm\claude.cmd'),
    (Join-Path $env:LocalAppData 'Programs\claude\claude.exe')
  )) {
    if (Test-Path -LiteralPath $c) { $claudeHit = $c; break }
  }
  if ($claudeHit) {
    $env:TV_CLAUDE_BIN = $claudeHit
    $env:Path = "$(Split-Path -Parent $claudeHit);$env:Path"
  } else {
    Write-TvdLaunchLog 'Claude Code not found'
    Show-TvdError (
      "Claude Code not found - ON AIR cannot read the game without it.`n`n" +
      "In PowerShell run:`n  irm https://claude.ai/install.ps1 | iex`n`n" +
      "Then open a NEW PowerShell, type:  claude`n(finish login once), close it, and open TV DIABLO again.`n`n" +
      "Or re-run the full installer:`n  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex`n`n" +
      "Log: $launchLog"
    )
    return
  }
}

$py = Real-Python
if (-not $py) {
  Write-TvdLaunchLog 'No real Python found'
  Show-TvdError "No real Python found. Re-run the installer.`n`nLog: $launchLog"
  return
}

# Ensure pywebview (Edge WebView2 backend on Windows)
$probe = if ($py.Cmd -eq 'py') { @('py', '-3', '-c', 'import webview') }
         elseif ($py.Cmd -eq 'pythonw') { @('python', '-c', 'import webview') }
         else { @($py.Cmd, '-c', 'import webview') }
$ok = $false
try {
  & $probe[0] $probe[1..($probe.Length - 1)] 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { $ok = $true }
} catch {}
if (-not $ok) {
  $pip = if ($py.Cmd -eq 'py') { @('py', '-3', '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
         elseif ($py.Cmd -eq 'pythonw') { @('python', '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
         else { @($py.Cmd, '-m', 'pip', 'install', '--user', '--quiet', 'pywebview>=5.0') }
  try { & $pip[0] $pip[1..($pip.Length - 1)] 2>$null | Out-Null } catch {}
}

# Soft first-run Claude login (skip if any known cred file exists)
$credHit = $false
foreach ($c in @(
  (Join-Path $HOME '.claude\.credentials.json'),
  (Join-Path $HOME '.config\claude\.credentials.json'),
  (Join-Path $HOME '.claude.json')
)) {
  if (Test-Path -LiteralPath $c) { $credHit = $true; break }
}
if (-not $credHit) {
  Write-TvdLaunchLog 'No Claude creds yet - opening claude login shell (wait)'
  Start-Process -Wait powershell -ArgumentList '-NoLogo', '-Command', 'claude' -ErrorAction SilentlyContinue
}

# v1404 multi-machine: auto-pull only when clean (dirty = local work protected).
# TV_NO_AUTO_PULL=1 skips entirely. Cousin clean install still always tracks origin.
if (-not $env:TV_NO_AUTO_PULL) {
  $dirty = $null
  try { $dirty = git -C $repo status --porcelain 2>$null } catch {}
  if (-not $dirty) {
    try { git -C $repo pull --ff-only 2>$null | Out-Null } catch {}
  } else {
    Write-TvdLaunchLog 'skip auto-pull: dirty working tree (local work protected)'
  }
} else {
  Write-TvdLaunchLog 'skip auto-pull: TV_NO_AUTO_PULL set'
}

$control = Join-Path $here 'control_app.py'
$ui = Join-Path $here 'control_ui.html'
$capture = Join-Path $here 'capture_win.ps1'
$shipPath = Join-Path $here 'WINDOWS_SHIP.json'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath $ui)) {
  Write-TvdLaunchLog 'control_app.py or control_ui.html missing'
  Show-TvdError "Control app files missing. Re-run WINDOWS installer.`n  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex`n`nLog: $launchLog"
  return
}
if (-not (Test-Path -LiteralPath $capture)) {
  Write-TvdLaunchLog 'capture_win.ps1 missing'
  Show-TvdError "Windows capture missing (capture_win.ps1). Re-run WINDOWS installer (not Mac).`n`nLog: $launchLog"
  return
}
# v1404 - pin Windows ship identity; refuse Mac-confused trees
$shipVer = '?'
if (Test-Path -LiteralPath $shipPath) {
  try {
    $ship = Get-Content -LiteralPath $shipPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($ship.platform -ne 'windows') {
      Show-TvdError "WINDOWS_SHIP.platform=$($ship.platform) - this launcher is Windows only.`nRe-install with the Windows IRM line."
      return
    }
    $shipVer = [string]$ship.ver
    Write-TvdLaunchLog ("Windows ship ver={0} name={1}" -f $shipVer, $ship.name)
    $stampPath = Join-Path $here '.windows_install.json'
    if (-not (Test-Path -LiteralPath $stampPath)) {
      $stampObj = [ordered]@{
        platform    = 'windows'
        shipVer     = $shipVer
        launchedAt  = (Get-Date).ToString('o')
        computer    = $env:COMPUTERNAME
        repo        = $repo
        launcher    = 'start_tvd_win.ps1'
      }
      ($stampObj | ConvertTo-Json) | Set-Content -LiteralPath $stampPath -Encoding UTF8
    }
  } catch {
    Write-TvdLaunchLog ("WINDOWS_SHIP.json read failed: {0}" -f $_)
  }
} else {
  Write-TvdLaunchLog 'WINDOWS_SHIP.json missing - pull latest Windows repo'
}

# ---------------------------------------------------------------------------
# v1406 SINGLE INSTANCE (screenshot 2026-07-26: one console open + second
# launch error dialog "Python exited immediately (exit 1)").
# Desktop double-click / dual shortcut / race used to start TWO --open processes.
# Mutex + "already up => exit quiet" = one window only, no false error toast.
# ---------------------------------------------------------------------------
$mutex = $null
try {
  $created = $false
  $mutex = New-Object System.Threading.Mutex($true, 'Local\TV_DIABLO_WIN_LAUNCHER_v1', [ref]$created)
  if (-not $created) {
    Write-TvdLaunchLog 'launcher mutex busy - another start_tvd_win in flight; exit quiet'
    try { $mutex.Dispose() } catch {}
    $mutex = $null
    return
  }
} catch {
  Write-TvdLaunchLog ("mutex note: {0}" -f $_)
  $mutex = $null
}

function Test-TvdDoctorOk {
  try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:17772/api/doctor' -UseBasicParsing -TimeoutSec 1
    $body = [string]$resp.Content
    if ($body -match '"ok"\s*:\s*true') { return $true }
  } catch {}
  return $false
}

# Already running with a healthy control server => do NOT spawn a second --open
if (Test-TvdDoctorOk) {
  Write-TvdLaunchLog 'doctor already ok - TV DIABLO is open; not starting a second window'
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  return
}

# ---------------------------------------------------------------------------
# v1401 CRITICAL: USERPROFILE with spaces (e.g. Hebrew names)
#   BAD:  Start-Process -ArgumentList @($control, '--open')
#   GOOD: one ArgumentList string with quoted script path.
# ---------------------------------------------------------------------------
$exeCmd = Get-Command $py.Cmd -ErrorAction SilentlyContinue
$exePath = if ($exeCmd) { [string]$exeCmd.Source } else { $py.Cmd }

if ($py.Cmd -eq 'py') {
  $argLine = '-3 "' + $control + '" --open'
} else {
  $argLine = '"' + $control + '" --open'
}

Write-TvdLaunchLog ("launch FileName={0} Args={1} WD={2}" -f $exePath, $argLine, $repo)

try {
  $proc = Start-Process -FilePath $exePath -ArgumentList $argLine -WorkingDirectory $repo -PassThru
  Write-TvdLaunchLog ("started pid={0}" -f $proc.Id)
} catch {
  Write-TvdLaunchLog ("Start-Process FAILED: {0}" -f $_)
  if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }
  Show-TvdError "TV DIABLO failed to start Python.`n`n$_`n`nLog: $launchLog"
  return
}

$doctorOk = $false
$doctorBody = ''
for ($i = 0; $i -lt 25; $i++) {
  Start-Sleep -Milliseconds 400
  # Another instance won the port and is healthy - our child may exit 0/1; that is OK
  if (Test-TvdDoctorOk) {
    $doctorOk = $true
    try {
      $doctorBody = [string](Invoke-WebRequest -Uri 'http://127.0.0.1:17772/api/doctor' -UseBasicParsing -TimeoutSec 1).Content
    } catch {}
    Write-TvdLaunchLog ("doctor OK (single instance) pid_self={0} exited={1}" -f $proc.Id, $proc.HasExited)
    break
  }
  if ($proc.HasExited -and $i -gt 5) {
    # Give a peer a moment; if still no doctor, real failure
    Start-Sleep -Milliseconds 600
    if (Test-TvdDoctorOk) { $doctorOk = $true; break }
    Write-TvdLaunchLog ("python exited early code={0}" -f $proc.ExitCode)
    break
  }
}

if ($mutex) { try { $mutex.ReleaseMutex() | Out-Null } catch {}; $mutex.Dispose() }

if (-not $doctorOk) {
  # Last chance: peer may still be binding
  if (Test-TvdDoctorOk) {
    Write-TvdLaunchLog 'doctor OK on final check'
    return
  }
  $hint = if ($proc.HasExited) {
    "Python exited (exit $($proc.ExitCode)) and doctor is down. Path/space, missing pywebview, or crash."
  } else {
    "Control process is running but /api/doctor did not return ok:true yet."
  }
  Write-TvdLaunchLog ("doctor FAIL: $hint body=$doctorBody")
  Show-TvdError (
    "TV DIABLO did not come up cleanly.`n`n$hint`n`n" +
    "Doctor: http://127.0.0.1:17772/api/doctor`nLog: $launchLog`n`n" +
    "Try in a NEW PowerShell:`n  powershell -File `"$PSCommandPath`""
  )
  return
}

Write-TvdLaunchLog ("doctor OK: $doctorBody")
