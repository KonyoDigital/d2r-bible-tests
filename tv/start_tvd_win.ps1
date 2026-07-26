# 📺 TV DIABLO — Windows launcher (Desktop · v784 native pywebview window)
# Real OS app window via Edge WebView2 (NOT Chrome). Agent + capture stay hidden.
# Same one-window product as Mac: ON/OFF/STOP/RESTART/SIM · board same-origin · no dual launch.
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $here

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

# PATH seed
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

Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

# v1380.4 — PATH seed for Claude (Desktop shortcut shells often miss ~/.local/bin + npm)
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
  # one more pass: direct file probe (shutil-equivalent)
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
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
      "Claude Code not found — ON AIR cannot read the game without it.`n`n" +
      "In PowerShell run:`n  irm https://claude.ai/install.ps1 | iex`n`n" +
      "Then open a NEW PowerShell, type:  claude`n(finish login once), close it, and open TV DIABLO again.`n`n" +
      "Or re-run the full installer:`n  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex",
      "TV DIABLO", 'OK', 'Error') | Out-Null
    return
  }
}

$py = Real-Python
if (-not $py) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show(
    "No real Python found. Re-run the installer.",
    "TV DIABLO", 'OK', 'Error') | Out-Null
  return
}

# Ensure pywebview (Edge WebView2 backend on Windows)
$probe = if ($py.Cmd -eq 'py') { @('py','-3','-c','import webview') }
         elseif ($py.Cmd -eq 'pythonw') { @('python','-c','import webview') }
         else { @($py.Cmd,'-c','import webview') }
$ok = $false
try {
  & $probe[0] $probe[1..($probe.Length-1)] 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { $ok = $true }
} catch {}
if (-not $ok) {
  $pip = if ($py.Cmd -eq 'py') { @('py','-3','-m','pip','install','--user','--quiet','pywebview>=5.0') }
         elseif ($py.Cmd -eq 'pythonw') { @('python','-m','pip','install','--user','--quiet','pywebview>=5.0') }
         else { @($py.Cmd,'-m','pip','install','--user','--quiet','pywebview>=5.0') }
  try { & $pip[0] $pip[1..($pip.Length-1)] 2>$null | Out-Null } catch {}
}

# Soft first-run Claude login
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

try { git -C $repo pull --ff-only 2>$null | Out-Null } catch {}

$control = Join-Path $here 'control_app.py'
$ui = Join-Path $here 'control_ui.html'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath $ui)) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show(
    "Control app files missing. Re-run installer (need v761+).",
    "TV DIABLO", 'OK', 'Error') | Out-Null
  return
}

# Foreground app process: pythonw shows the native window (no console)
$args = @()
$args += $py.Prefix
$args += $control
$args += '--open'

if ($py.Cmd -eq 'pythonw') {
  # Wait so this host script doesn't exit before the window is up
  Start-Process -FilePath 'pythonw' -ArgumentList $args -WorkingDirectory $repo -Wait
} elseif ($py.Cmd -eq 'py') {
  Start-Process -FilePath 'py' -ArgumentList (@('-3', $control, '--open')) -WorkingDirectory $repo -Wait -WindowStyle Normal
} else {
  Start-Process -FilePath $py.Cmd -ArgumentList @($control, '--open') -WorkingDirectory $repo -Wait -WindowStyle Normal
}
