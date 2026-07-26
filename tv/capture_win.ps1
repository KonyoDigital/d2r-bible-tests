# TV DIABLO - Windows capture loop (v1416 true D2R pixels)
# Zero installs: .NET System.Drawing. Read-only screenshots only.
#
#   TV_CAPTURE=auto|full|window   (default AUTO - pin D2R.exe when present, else full)
#   TV_WINDOW_MATCH=extra,tokens
#   TV_CAPTURE_MS=200
#
# Writes:
#   frames/live.bmp, live.png, eye.jpg, cap_target.json
#   frames/win_pin_debug.json  - last pin candidates (cousin debug)
#
# v1416: PrintWindow first. NEVER trust GetDC+BitBlt for D2R (returns desktop
#         z-order = chat/IDE while label says D2R). CopyFromScreen / primary
#         monitor ONLY when D2R is foreground. Else wait for focus.
# v1413: PROCESS-FIRST pin. Pure ASCII + BOM for Hebrew PS 5.1.

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class TvdWin {
  public struct RECT { public int Left, Top, Right, Bottom; }
  public struct POINT { public int X, Y; }
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
  [DllImport("gdi32.dll")] public static extern bool BitBlt(IntPtr hdcDest, int nXDest, int nYDest, int nWidth, int nHeight, IntPtr hdcSrc, int nXSrc, int nYSrc, int dwRop);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hwnd, int dwAttribute, out int pvAttribute, int cbAttribute);
  public const int SRCCOPY = 0x00CC0020;
}
"@

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $here 'frames'
New-Item -ItemType Directory -Force -Path $frames | Out-Null

$mode = if ($env:TV_CAPTURE) { $env:TV_CAPTURE.ToLower().Trim() } else { 'auto' }
$pollMs = 200
if ($env:TV_CAPTURE_MS) {
  try { $pollMs = [Math]::Max(80, [int]$env:TV_CAPTURE_MS) } catch { $pollMs = 200 }
}
$extra = @()
if ($env:TV_WINDOW_MATCH) {
  $extra = $env:TV_WINDOW_MATCH.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
}

# ProcessName without .exe (Get-Process -Name)
$procExact = @('D2R', 'DiabloIIResurrected', 'DiabloII')
# Blocklist: never pin these even if title says Diablo
$ownerBlock = @(
  'chrome', 'msedge', 'firefox', 'brave', 'opera', 'vivaldi', 'iexplore',
  'code', 'cursor', 'devenv', 'notepad', 'windowsterminal', 'powershell', 'pwsh',
  'slack', 'discord', 'outlook', 'winword', 'excel', 'applicationframehost',
  'searchhost', 'shellexperiencehost', 'textinputhost',
  'battle.net', 'agent', 'blizzard browser', 'blizzardupdateagent', 'blizzarderror'
)
$titleBlock = @(
  'farming bible', 'd2r bible', 'tv diablo', 'localhost', '127.0.0.1',
  'bull-4-u', 'github', 'visual studio', 'notepad', 'battle.net'
)
$titleHints = @(
  'diablo ii', 'diablo 2', 'diablo ii: resurrected', 'diablo ii resurrected',
  'd2r', 'resurrected', 'diabloii'
) + $extra

function Get-WindowTitle([IntPtr]$hwnd) {
  try {
    $len = [TvdWin]::GetWindowTextLength($hwnd)
    if ($len -le 0) { return '' }
    $sb = New-Object System.Text.StringBuilder ($len + 1)
    [void][TvdWin]::GetWindowText($hwnd, $sb, $sb.Capacity)
    return $sb.ToString()
  } catch { return '' }
}

function Test-OwnerBlocked([string]$procName) {
  $ol = ($procName | ForEach-Object { $_.ToLower() })
  foreach ($b in $ownerBlock) {
    if ($ol -and $ol -like "*$b*") { return $true }
  }
  return $false
}

function Test-TitleBlocked([string]$title) {
  $tl = ($title | ForEach-Object { $_.ToLower() })
  foreach ($b in $titleBlock) {
    if ($tl -and $tl -like "*$b*") { return $true }
  }
  return $false
}

function Test-IsCloaked([IntPtr]$hwnd) {
  # DWMWA_CLOAKED = 14
  try {
    $cloak = 0
    $hr = [TvdWin]::DwmGetWindowAttribute($hwnd, 14, [ref]$cloak, 4)
    if ($hr -eq 0 -and $cloak -ne 0) { return $true }
  } catch {}
  return $false
}

function Get-WindowGeom([IntPtr]$hwnd) {
  $wr = New-Object TvdWin+RECT
  if (-not [TvdWin]::GetWindowRect($hwnd, [ref]$wr)) { return $null }
  $w = $wr.Right - $wr.Left
  $h = $wr.Bottom - $wr.Top
  # Prefer client rect for games (no border chrome); fall back to window rect
  $cr = New-Object TvdWin+RECT
  $left = $wr.Left; $top = $wr.Top
  if ([TvdWin]::GetClientRect($hwnd, [ref]$cr)) {
    $cw = $cr.Right - $cr.Left
    $ch = $cr.Bottom - $cr.Top
    if ($cw -ge 320 -and $ch -ge 240) {
      $pt = New-Object TvdWin+POINT
      $pt.X = 0; $pt.Y = 0
      if ([TvdWin]::ClientToScreen($hwnd, [ref]$pt)) {
        $left = $pt.X; $top = $pt.Y
        $w = $cw; $h = $ch
      }
    }
  }
  if ($w -lt 320 -or $h -lt 240) { return $null }
  return @{ Left = $left; Top = $top; W = $w; H = $h }
}

function New-Candidate([IntPtr]$hwnd, [string]$procName, [string]$title, [int]$score, [hashtable]$geom) {
  $label = if ($title) { "$procName - $title" } else { "$procName (no title)" }
  return @{
    Hwnd = $hwnd; Score = $score; W = $geom.W; H = $geom.H
    Left = $geom.Left; Top = $geom.Top; Label = $label
    Proc = $procName; Title = $title
  }
}

function Score-Candidate([string]$procName, [string]$title, [int]$w, [int]$h, [bool]$isFg) {
  $ol = $procName.ToLower()
  $tl = $title.ToLower()
  $score = 0
  if ($ol -eq 'd2r') { $score += 8000 }
  elseif ($ol -like 'd2r*') { $score += 6000 }
  elseif ($ol -like '*diablo*') { $score += 3000 }
  if ($tl -like '*diablo ii*' -or $tl -like '*diablo 2*' -or $tl -like '*resurrected*') { $score += 1500 }
  elseif ($tl -like '*d2r*' -or $tl -like '*diablo*') { $score += 800 }
  if ($isFg) { $score += 500 }
  # Prefer large game-sized windows
  $score += [Math]::Min([int](($w * $h) / 50000), 80)
  return $score
}

function Find-D2RByProcess {
  # PROCESS-FIRST. v1416: NEVER Get-Process / MainWindowHandle (both hang under D2R here).
  # Get PID via GetProcessesByName, then EnumWindows for that PID only.
  $cands = @()
  $wantPids = @{}
  $pidToName = @{}
  foreach ($n in $procExact) {
    try {
      foreach ($p in [System.Diagnostics.Process]::GetProcessesByName($n)) {
        if (-not $p) { continue }
        $wantPids[[int]$p.Id] = $true
        $pidToName[[int]$p.Id] = $p.ProcessName
      }
    } catch {}
  }
  if ($wantPids.Count -eq 0) { return @() }

  $script:pidCands = @()
  $script:wantPids = $wantPids
  $script:pidToName = $pidToName
  $script:fgHwnd = [TvdWin]::GetForegroundWindow()
  $script:enumPidOnly = {
    param([IntPtr]$h, [IntPtr]$lp)
    try {
      if ([TvdWin]::IsIconic($h)) { return $true }
      # NEVER name a var $pid — PowerShell automatic $PID is read-only (crashes EnumWindows)
      $winPid = 0
      [void][TvdWin]::GetWindowThreadProcessId($h, [ref]$winPid)
      if (-not $script:wantPids.ContainsKey([int]$winPid)) { return $true }
      $geom = Get-WindowGeom $h
      if (-not $geom -or $geom.W -lt 480 -or $geom.H -lt 360) { return $true }
      $title = Get-WindowTitle $h
      if (Test-TitleBlocked $title) { return $true }
      $procName = [string]$script:pidToName[[int]$winPid]
      if (-not $procName) { $procName = 'D2R' }
      $isFg = ($h -eq $script:fgHwnd)
      $score = Score-Candidate $procName $title $geom.W $geom.H $isFg
      $score += 2000
      $script:pidCands += ,(New-Candidate $h $procName $title $score $geom)
    } catch {}
    return $true
  }
  try { [void][TvdWin]::EnumWindows($script:enumPidOnly, [IntPtr]::Zero) } catch {}
  return $script:pidCands
}

function Find-D2RByEnum {
  $script:cands = @()
  $fg = [TvdWin]::GetForegroundWindow()
  $script:enumCb = {
    param([IntPtr]$hwnd, [IntPtr]$lp)
    if ([TvdWin]::IsIconic($hwnd)) { return $true }
    if (Test-IsCloaked $hwnd) { return $true }
    $title = Get-WindowTitle $hwnd
    $procId = 0
    [void][TvdWin]::GetWindowThreadProcessId($hwnd, [ref]$procId)
    $procName = ''
    # v1416: no Get-Process -Id (can hang under D2R)
    try {
      $pp = [System.Diagnostics.Process]::GetProcessById([int]$procId)
      if ($pp) { $procName = $pp.ProcessName }
    } catch {}
    if (Test-OwnerBlocked $procName) { return $true }
    if (Test-TitleBlocked $title) { return $true }
    $ol = $procName.ToLower()
    $tl = $title.ToLower()
    $blob = "$ol $tl"
    $hit = $false
    if ($ol -eq 'd2r' -or $ol -like 'd2r*' -or $ol -like '*diablo*ii*' -or $ol -like '*diabloii*') { $hit = $true }
    if (-not $hit) {
      foreach ($t in $script:titleHints) {
        if ($blob -like "*$t*") { $hit = $true; break }
      }
    }
    if (-not $hit) { return $true }
    # Title-only hits (no D2R process) still require visible window
    $isProc = ($ol -eq 'd2r' -or $ol -like 'd2r*')
    if (-not $isProc -and -not [TvdWin]::IsWindowVisible($hwnd)) { return $true }
    $geom = Get-WindowGeom $hwnd
    if (-not $geom) { return $true }
    if ($geom.W -lt 480 -or $geom.H -lt 360) { return $true }
    $isFg = ($hwnd -eq $script:fg)
    $score = Score-Candidate $procName $title $geom.W $geom.H $isFg
    $script:cands += ,(New-Candidate $hwnd $procName $title $score $geom)
    return $true
  }
  $script:titleHints = $titleHints
  $script:fg = $fg
  $script:cands = @()
  try { [void][TvdWin]::EnumWindows($script:enumCb, [IntPtr]::Zero) } catch {}
  return $script:cands
}

function Find-D2RWindow {
  $all = @()
  try { $all += Find-D2RByProcess } catch { Write-Host "  proc-scan: $_" }
  # Only fall back to full title enum when process pin found nothing (enum calls GetProcessById per window — slow/risky)
  if (-not $all -or $all.Count -eq 0) {
    try { $all += Find-D2RByEnum } catch { Write-Host "  enum-scan: $_" }
  }
  # de-dupe by hwnd
  $best = $null
  $seenH = @{}
  $debug = @()
  foreach ($c in $all) {
    if (-not $c) { continue }
    $key = [int64]$c.Hwnd
    if ($seenH.ContainsKey($key)) { continue }
    $seenH[$key] = $true
    $debug += @{
      proc = $c.Proc; title = $c.Title; score = $c.Score
      w = $c.W; h = $c.H; left = $c.Left; top = $c.Top
    }
    if (-not $best -or $c.Score -gt $best.Score) { $best = $c }
  }
  # debug dump for cousin troubleshooting
  try {
    $dbgPath = Join-Path $frames 'win_pin_debug.json'
    # v1416: no Get-Process here (hangs under D2R on some PCs)
    $d2rAlive = $false
    try {
      $pp = [System.Diagnostics.Process]::GetProcessesByName('D2R')
      if ($pp -and $pp.Length -gt 0) { $d2rAlive = $true }
    } catch {}
    $obj = @{
      ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      d2rProcessAlive = $d2rAlive
      candidateCount = $debug.Count
      best = if ($best) { $best.Label } else { $null }
      candidates = $debug
    }
    ($obj | ConvertTo-Json -Depth 4 -Compress) | Set-Content -Path $dbgPath -Encoding UTF8
  } catch {}
  return $best
}

function Test-D2RProcessAlive {
  # v1415: do NOT call Get-Process (hangs under D2R). Prefer last pin label / tool-less check.
  try {
    $p = Join-Path $frames 'cap_target.json'
    if (Test-Path -LiteralPath $p) {
      $j = Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($j.d2rProcess -eq $true) { return $true }
      $lab = [string]$j.label
      if ($lab -match 'D2R|Diablo') { return $true }
    }
  } catch {}
  # light process check via .NET (faster than tasklist; still may lag — keep last)
  try {
    $procs = [System.Diagnostics.Process]::GetProcessesByName('D2R')
    if ($procs -and $procs.Length -gt 0) { return $true }
  } catch {}
  return $false
}

function Test-BitmapMostlyBlack([System.Drawing.Bitmap]$bmp) {
  # Multi-point sample: single center pixel fooled us when BitBlt returned desktop chrome.
  if (-not $bmp -or $bmp.Width -lt 4 -or $bmp.Height -lt 4) { return $true }
  $pts = @(
    @([int]($bmp.Width / 2), [int]($bmp.Height / 2)),
    @([int]($bmp.Width / 4), [int]($bmp.Height / 4)),
    @([int](3 * $bmp.Width / 4), [int]($bmp.Height / 4)),
    @([int]($bmp.Width / 4), [int](3 * $bmp.Height / 4)),
    @([int](3 * $bmp.Width / 4), [int](3 * $bmp.Height / 4))
  )
  $dark = 0
  foreach ($p in $pts) {
    $c = $bmp.GetPixel($p[0], $p[1])
    if ($c.R -lt 12 -and $c.G -lt 12 -and $c.B -lt 12) { $dark++ }
  }
  return ($dark -ge 4)
}

function Capture-WindowBitmap($target) {
  # v1416 CRITICAL: D2R is DirectX. GetDC+BitBlt often returns DESKTOP z-order
  # (chat/IDE sitting on the D2R rect) while still non-black — label said D2R,
  # film was Grok. Never treat BitBlt as trusted game pixels.
  # Trust order:
  #   1) PrintWindow (true hwnd buffer when the game allows it)
  #   2) CopyFromScreen ONLY if D2R is foreground
  #   3) else return black/null so caller waits for focus (no chat overlay)
  $bmp = $null
  $g = $null
  $hwnd = [IntPtr]$target.Hwnd
  if ($hwnd -eq [IntPtr]::Zero -or -not [TvdWin]::IsWindow($hwnd)) {
    return $null
  }
  $fg = [TvdWin]::GetForegroundWindow()
  $isFg = ($fg -eq $hwnd)

  # 1) PrintWindow (PW_RENDERFULLCONTENT = 2) — real window content when supported
  try {
    $bmp = New-Object System.Drawing.Bitmap $target.W, $target.H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    try {
      $ok = [TvdWin]::PrintWindow($hwnd, $hdc, 2)
      if (-not $ok) { [void][TvdWin]::PrintWindow($hwnd, $hdc, 0) }
    } finally {
      $g.ReleaseHdc($hdc)
    }
    if (-not (Test-BitmapMostlyBlack $bmp)) {
      return @{ Bmp = $bmp; G = $g; How = 'PrintWindow' }
    }
  } catch {
    if ($g) { try { $g.Dispose() } catch {} }
    if ($bmp) { try { $bmp.Dispose() } catch {} }
    $bmp = $null; $g = $null
  }

  # 2) CopyFromScreen ONLY if D2R is foreground (only safe screen grab)
  if ($isFg) {
    try {
      if ($bmp) { try { $g.Dispose() } catch {}; try { $bmp.Dispose() } catch {} }
      $bmp = New-Object System.Drawing.Bitmap $target.W, $target.H
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      $g.CopyFromScreen($target.Left, $target.Top, 0, 0, $bmp.Size)
      if (-not (Test-BitmapMostlyBlack $bmp)) {
        return @{ Bmp = $bmp; G = $g; How = 'CopyFromScreen-fg' }
      }
    } catch {
      if ($g) { try { $g.Dispose() } catch {} }
      if ($bmp) { try { $bmp.Dispose() } catch {} }
      $bmp = $null; $g = $null
    }
  } else {
    Write-Host '  D2R not foreground - refusing screen grab (BitBlt/CopyFromScreen would film chat/IDE)'
  }

  # v1416: BitBlt deliberately NOT used — for DX games it returns desktop composite.
  if ($bmp) {
    return @{ Bmp = $bmp; G = $g; How = 'PrintWindow-black' }
  }
  return $null
}

function Capture-PrimaryMonitor {
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
  return @{ Bmp = $bmp; G = $g; How = 'PrimaryMonitor'; W = $b.Width; H = $b.Height }
}

function Save-EyeJpeg([System.Drawing.Bitmap]$src, [string]$path) {
  $maxPx = 900
  $nw = $src.Width; $nh = $src.Height
  if ($nw -gt $maxPx -or $nh -gt $maxPx) {
    $scale = [Math]::Min($maxPx / [double]$nw, $maxPx / [double]$nh)
    $nw = [Math]::Max(1, [int]($src.Width * $scale))
    $nh = [Math]::Max(1, [int]($src.Height * $scale))
  }
  $eye = New-Object System.Drawing.Bitmap $nw, $nh
  $eg = [System.Drawing.Graphics]::FromImage($eye)
  $eg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $eg.DrawImage($src, 0, 0, $nw, $nh)
  $tmp = $path + '.part'
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $ep = New-Object System.Drawing.Imaging.EncoderParameters 1
  $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality, [long]55)
  if ($codec) {
    $eye.Save($tmp, $codec, $ep)
  } else {
    $eye.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Jpeg)
  }
  if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue }
  Move-Item -Force -LiteralPath $tmp -Destination $path -ErrorAction SilentlyContinue
  $eg.Dispose(); $eye.Dispose()
}

function Write-CapTarget([string]$mode, [string]$label) {
  $p = Join-Path $frames 'cap_target.json'
  $obj = @{
    mode = $mode
    label = $label
    ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    d2rProcess = (Test-D2RProcessAlive)
  }
  ($obj | ConvertTo-Json -Compress) | Set-Content -Path $p -Encoding UTF8
  # also plain text for quick eyes
  try {
    Set-Content -Path (Join-Path $frames 'cap_target.txt') -Value "$mode|$label" -Encoding UTF8
  } catch {}
}

Write-Host "TV DIABLO capture (Windows) mode=$mode poll=${pollMs}ms v1416 PrintWindow-or-focus (never BitBlt desktop lie)"
$lastLabel = ''
$lastGood = $null
$loopN = 0
while ($true) {
  $bmp = $null
  $g = $null
  $loopN++
  try {
    # heartbeat so we can see if pin/capture is stuck (no Get-Process)
    try {
      Set-Content -Path (Join-Path $frames 'capture_heartbeat.txt') -Value ("n={0} t={1}" -f $loopN, [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -Encoding UTF8
    } catch {}
    $target = $null
    $capMode = 'full'
    $capLabel = 'full screen'
    $d2rAlive = Test-D2RProcessAlive

    if ($mode -eq 'window' -or $mode -eq 'auto' -or $mode -eq 'win' -or $mode -eq 'game') {
      $target = Find-D2RWindow
      # sticky last pin
      if (-not $target -and $lastGood -and $lastGood.Hwnd -and [TvdWin]::IsWindow([IntPtr]$lastGood.Hwnd) -and -not [TvdWin]::IsIconic([IntPtr]$lastGood.Hwnd)) {
        $geom = Get-WindowGeom ([IntPtr]$lastGood.Hwnd)
        if ($geom -and $geom.W -ge 480 -and $geom.H -ge 360) {
          $target = @{
            Hwnd = $lastGood.Hwnd; Score = $lastGood.Score
            W = $geom.W; H = $geom.H; Left = $geom.Left; Top = $geom.Top
            Label = $lastGood.Label; Proc = $lastGood.Proc; Title = $lastGood.Title
          }
        }
      }
    }

    $got = $null
    if ($target -and $mode -ne 'full') {
      if ($target.Label -ne $lastLabel) {
        Write-Host ("  eye pinned: {0} ({1}x{2})" -f $target.Label, $target.W, $target.H)
        $lastLabel = $target.Label
      }
      $got = Capture-WindowBitmap $target
      if ($got -and $got.How -ne 'PrintWindow-black') {
        $bmp = $got.Bmp; $g = $got.G
        $capMode = 'window'
        $capLabel = $target.Label + ' via ' + $got.How
        $lastGood = $target
      } elseif ($got) {
        # black pin — free and fall through
        try { $got.G.Dispose() } catch {}
        try { $got.Bmp.Dispose() } catch {}
        Write-Host ("  pin black ({0}) — trying primary monitor (D2R exclusive fullscreen?)" -f $target.Label)
      } else {
        Write-Host ("  pin grab failed: {0}" -f $target.Label)
      }
    }

    # Primary-monitor fallback ONLY when D2R is the FOREGROUND window (exclusive FS).
    # If chat/IDE is on top, primary CopyFromScreen films the wrong app (v1415 bug).
    if (-not $bmp -and $d2rAlive -and $mode -ne 'full') {
      $fg = [TvdWin]::GetForegroundWindow()
      $d2rIsFg = $false
      if ($target -and $target.Hwnd) {
        $d2rIsFg = ([IntPtr]$target.Hwnd -eq $fg)
      }
      if ($d2rIsFg) {
        try {
          $pm = Capture-PrimaryMonitor
          $bmp = $pm.Bmp; $g = $pm.G
          $capMode = 'window'
          $capLabel = 'D2R foreground - primary monitor (' + $pm.How + ')'
          if ($lastLabel -ne $capLabel) {
            Write-Host ("  {0}" -f $capLabel)
            $lastLabel = $capLabel
          }
        } catch {
          Write-Host "  primary monitor fail: $_"
        }
      } else {
        if ($lastLabel -ne '__need_focus__') {
          Write-Host '  D2R running but NOT focused - click the GAME window (not this chat). Pin refuses desktop composite.'
          $lastLabel = '__need_focus__'
        }
        Write-CapTarget 'waiting' 'D2R running - click Diablo window to focus (will not film chat/IDE on top)'
        Start-Sleep -Milliseconds 400
        continue
      }
    }

    if (-not $bmp) {
      if ($mode -eq 'window' -or $mode -eq 'win' -or $mode -eq 'game') {
        if ($lastLabel -ne '__waiting__') {
          Write-Host '  waiting for D2R.exe (open the GAME, not only Battle.net)...'
          $lastLabel = '__waiting__'
        }
        $msg = if ($d2rAlive) {
          'D2R.exe running but no capturable window - try borderless windowed'
        } else {
          'D2R.exe not found - open Diablo II Resurrected in-game (not only Battle.net)'
        }
        Write-CapTarget 'waiting' $msg
        Start-Sleep -Milliseconds 500
        continue
      }
      # auto + no game: full virtual screen so capture process stays healthy
      if ($lastLabel -ne '__full__') {
        Write-Host '  full virtual screen (no D2R.exe - open the game in-game)'
        $lastLabel = '__full__'
      }
      $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
      $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
      $capMode = if ($d2rAlive) { 'window' } else { 'waiting' }
      $capLabel = if ($d2rAlive) {
        'D2R alive - full virtual screen fallback'
      } else {
        'full screen (no D2R.exe - open game in-game)'
      }
    }

    $tmp = Join-Path $frames 'live.tmp.bmp'
    $out = Join-Path $frames 'live.bmp'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Bmp)
    Move-Item -Force $tmp $out
    $png = Join-Path $frames 'live.png'
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $eye = Join-Path $frames 'eye.jpg'
    try { Save-EyeJpeg $bmp $eye } catch { Write-Host "  eye.jpg: $_" }
    Write-CapTarget $capMode $capLabel
    $g.Dispose(); $bmp.Dispose()
  } catch {
    Write-Host "  capture error: $_"
    try { if ($g) { $g.Dispose() } } catch {}
    try { if ($bmp) { $bmp.Dispose() } } catch {}
  }
  Start-Sleep -Milliseconds $pollMs
}
