# TV DIABLO - Windows launcher (Desktop - native pywebview / WebView2, NOT Chrome)
# Agent + capture stay hidden. Same product as Mac: ON/OFF/STOP/RESTART/SIM.
# Encoding: ASCII-only strings so Windows PowerShell 5.1 never mis-parses UTF-8.
$ErrorActionPreference = 'Continue'
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

try { git -C $repo pull --ff-only 2>$null | Out-Null } catch {}

$control = Join-Path $here 'control_app.py'
$ui = Join-Path $here 'control_ui.html'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath $ui)) {
  Write-TvdLaunchLog 'control_app.py or control_ui.html missing'
  Show-TvdError "Control app files missing. Re-run installer (need v761+).`n`nLog: $launchLog"
  return
}

# ---------------------------------------------------------------------------
# v1401 CRITICAL: USERPROFILE with spaces (e.g. Hebrew names)
#   BAD:  Start-Process -ArgumentList @($control, '--open')
#         PowerShell does not quote array elements -> python sees only
#         C:\Users\<first-token> and dies: can't open file ... [Errno 2]
#   Symptom: Desktop TV DIABLO flash-closes; /api/doctor never answers.
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
  # No long -Wait: control_app can stay headless after window close.
  $proc = Start-Process -FilePath $exePath -ArgumentList $argLine -WorkingDirectory $repo -PassThru
  Write-TvdLaunchLog ("started pid={0}" -f $proc.Id)
} catch {
  Write-TvdLaunchLog ("Start-Process FAILED: {0}" -f $_)
  Show-TvdError "TV DIABLO failed to start Python.`n`n$_`n`nLog: $launchLog"
  return
}

$doctorOk = $false
$doctorBody = ''
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Milliseconds 400
  if ($proc.HasExited) {
    Write-TvdLaunchLog ("python exited early code={0}" -f $proc.ExitCode)
    break
  }
  try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:17772/api/doctor' -UseBasicParsing -TimeoutSec 1
    $doctorBody = [string]$resp.Content
    if ($doctorBody -match '"ok"\s*:\s*true') { $doctorOk = $true; break }
  } catch {}
}

if (-not $doctorOk) {
  $hint = if ($proc.HasExited) {
    "Python exited immediately (exit $($proc.ExitCode)). Often a path/space launch bug or missing pywebview."
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
