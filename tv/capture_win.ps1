# TV DIABLO - Windows capture loop (v1412 pin + recovery)
# Zero installs: .NET System.Drawing. Read-only screenshots only.
#
#   TV_CAPTURE=auto|full|window   (default AUTO - pin D2R.exe when present, else full)
#   TV_WINDOW_MATCH=extra,tokens
#   TV_CAPTURE_MS=200             poll interval (default 200ms)
#
# Writes:
#   frames/live.bmp   - intelligence settle path (agent --watch)
#   frames/live.png   - vision transport fallback
#   frames/eye.jpg    - console film (/frame)
#   frames/cap_target.json - mode/label for control status row
#
# Product: native D2R.exe on Windows. Browsers / TV chrome never pin.
# NOTE: Pure ASCII only. Windows PowerShell 5.1 under non-UTF8 code pages
# (e.g. Hebrew cp1255) mis-parses UTF-8 emoji/emdash files without BOM.
# v1412: PrintWindow fallback (exclusive fullscreen), sticky last pin, wider process match.

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class TvdWin {
  public struct RECT { public int Left, Top, Right, Bottom; }
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
  [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
  [DllImport("gdi32.dll")] public static extern bool BitBlt(IntPtr hdcDest, int nXDest, int nYDest, int nWidth, int nHeight, IntPtr hdcSrc, int nXSrc, int nYSrc, int dwRop);
}
"@

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $here 'frames'
New-Item -ItemType Directory -Force -Path $frames | Out-Null

# v784 AUTO matches Mac agent default (pin game when live)
$mode = if ($env:TV_CAPTURE) { $env:TV_CAPTURE.ToLower().Trim() } else { 'auto' }
$pollMs = 200
if ($env:TV_CAPTURE_MS) {
  try { $pollMs = [Math]::Max(80, [int]$env:TV_CAPTURE_MS) } catch { $pollMs = 200 }
}
$extra = @()
if ($env:TV_WINDOW_MATCH) {
  $extra = $env:TV_WINDOW_MATCH.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
}

# Native Windows D2R process names (ProcessName without .exe)
# Battle.net installs usually: D2R. Store / other wrappers may vary.
$procNames = @(
  'D2R',
  'Diablo II Resurrected',
  'DiabloII',
  'Diablo II',
  'DiabloIIResurrected',
  'Diablo II Resurrected Launcher'
)
$titleHints = @(
  'diablo ii', 'diablo 2', 'diablo ii: resurrected', 'diablo ii resurrected',
  'd2r', 'resurrected', 'diabloii'
) + $extra
# never pin browsers / editors (bible tab titles contain "D2R")
$ownerBlock = @(
  'chrome', 'msedge', 'firefox', 'brave', 'opera', 'vivaldi', 'iexplore',
  'Code', 'Cursor', 'devenv', 'notepad', 'WindowsTerminal', 'powershell', 'pwsh',
  'Slack', 'Discord', 'OUTLOOK', 'WINWORD', 'EXCEL', 'ApplicationFrameHost',
  'SearchHost', 'ShellExperienceHost', 'TextInputHost'
)
$titleBlock = @(
  'farming bible', 'd2r bible', 'tv diablo', 'localhost', '127.0.0.1',
  'bull-4-u', 'github', 'visual studio', 'notepad'
)

function Get-WindowTitle([IntPtr]$hwnd) {
  $len = [TvdWin]::GetWindowTextLength($hwnd)
  if ($len -le 0) { return '' }
  $sb = New-Object System.Text.StringBuilder ($len + 1)
  [void][TvdWin]::GetWindowText($hwnd, $sb, $sb.Capacity)
  return $sb.ToString()
}

function Find-D2RWindow {
  $script:best = $null
  $script:enumCb = {
    param([IntPtr]$hwnd, [IntPtr]$lp)
    if (-not [TvdWin]::IsWindowVisible($hwnd)) { return $true }
    if ([TvdWin]::IsIconic($hwnd)) { return $true }
    $title = Get-WindowTitle $hwnd
    $procId = 0
    [void][TvdWin]::GetWindowThreadProcessId($hwnd, [ref]$procId)
    $procName = ''
    try { $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName } catch {}
    $tl = ($title | ForEach-Object { $_.ToLower() })
    $ol = ($procName | ForEach-Object { $_.ToLower() })
    foreach ($b in $script:ownerBlock) {
      if ($ol -and $ol -like "*$($b.ToLower())*") { return $true }
    }
    foreach ($b in $script:titleBlock) {
      if ($tl -and $tl -like "*$b*") { return $true }
    }
    $blob = ("$procName $title").ToLower()
    $hit = $false
    foreach ($p in $script:procNames) {
      if ($procName -and ($procName -ieq $p -or $procName -like 'D2R*' -or $procName -like 'Diablo*')) { $hit = $true; break }
    }
    if (-not $hit) {
      foreach ($t in $script:titleHints) {
        if ($blob -like "*$t*") { $hit = $true; break }
      }
    }
    if (-not $hit) { return $true }
    $rect = New-Object TvdWin+RECT
    if (-not [TvdWin]::GetWindowRect($hwnd, [ref]$rect)) { return $true }
    $w = $rect.Right - $rect.Left
    $h = $rect.Bottom - $rect.Top
    # Fullscreen can report virtual size; allow slightly smaller borderless
    if ($w -lt 480 -or $h -lt 360) { return $true }
    $score = 0
    if ($procName -ieq 'D2R' -or $ol -eq 'd2r') { $score += 5000 }
    if ($ol -like '*d2r*' -or $ol -like '*diablo*') { $score += 2000 }
    if ($tl -like '*diablo*' -or $tl -like '*d2r*' -or $tl -like '*resurrected*') { $score += 1000 }
    if ($procName -ieq 'D2R') { $score += 100 }
    if ($title -match 'Diablo') { $score += 40 }
    # Prefer game-sized windows over tiny launchers
    $score += [Math]::Min([int](($w * $h) / 100000), 40)
    $label = if ($title) { "$procName - $title" } else { $procName }
    if (-not $script:best -or $score -gt $script:best.Score) {
      $script:best = @{
        Hwnd = $hwnd; Score = $score; W = $w; H = $h
        Left = $rect.Left; Top = $rect.Top; Label = $label
      }
    }
    return $true
  }
  $script:ownerBlock = $ownerBlock
  $script:titleBlock = $titleBlock
  $script:procNames = $procNames
  $script:titleHints = $titleHints
  $script:best = $null
  [void][TvdWin]::EnumWindows($script:enumCb, [IntPtr]::Zero)
  return $script:best
}

function Capture-WindowBitmap($target) {
  # Prefer CopyFromScreen (fast). Exclusive fullscreen / protected often returns black or fails -
  # then PrintWindow (PW_RENDERFULLCONTENT=0x2) is the real fix for D2R pin.
  $bmp = $null
  $g = $null
  try {
    $bmp = New-Object System.Drawing.Bitmap $target.W, $target.H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($target.Left, $target.Top, 0, 0, $bmp.Size)
    # Heuristic: all-black frame means exclusive fullscreen failed
    $sample = $bmp.GetPixel([int]($target.W / 2), [int]($target.H / 2))
    $blackish = ($sample.R -lt 8 -and $sample.G -lt 8 -and $sample.B -lt 8)
    if (-not $blackish) {
      return @{ Bmp = $bmp; G = $g; How = 'CopyFromScreen' }
    }
  } catch {
    if ($g) { try { $g.Dispose() } catch {} }
    if ($bmp) { try { $bmp.Dispose() } catch {} }
    $bmp = $null; $g = $null
  }
  # PrintWindow path
  try {
    if ($bmp) { try { $g.Dispose() } catch {}; try { $bmp.Dispose() } catch {} }
    $bmp = New-Object System.Drawing.Bitmap $target.W, $target.H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    try {
      # 2 = PW_RENDERFULLCONTENT (Win 8.1+) - needed for DWM / fullscreen games
      $ok = [TvdWin]::PrintWindow([IntPtr]$target.Hwnd, $hdc, 2)
      if (-not $ok) {
        [void][TvdWin]::PrintWindow([IntPtr]$target.Hwnd, $hdc, 0)
      }
    } finally {
      $g.ReleaseHdc($hdc)
    }
    return @{ Bmp = $bmp; G = $g; How = 'PrintWindow' }
  } catch {
    if ($g) { try { $g.Dispose() } catch {} }
    if ($bmp) { try { $bmp.Dispose() } catch {} }
    return $null
  }
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
  Move-Item -Force $tmp $path
  $eg.Dispose(); $eye.Dispose()
}

function Write-CapTarget([string]$mode, [string]$label) {
  $p = Join-Path $frames 'cap_target.json'
  $obj = @{ mode = $mode; label = $label; ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() }
  ($obj | ConvertTo-Json -Compress) | Set-Content -Path $p -Encoding UTF8
}

Write-Host "TV DIABLO capture (Windows) mode=$mode poll=${pollMs}ms v1412"
$lastLabel = ''
$lastGood = $null
$missStreak = 0
while ($true) {
  try {
    $target = $null
    $capMode = 'full'
    $capLabel = 'full screen'
    if ($mode -eq 'window' -or $mode -eq 'auto' -or $mode -eq 'win' -or $mode -eq 'game') {
      $target = Find-D2RWindow
      # sticky last pin: EnumWindows can glitch for a tick while D2R is exclusive fullscreen
      if (-not $target -and $lastGood -and $lastGood.Hwnd -and [TvdWin]::IsWindow([IntPtr]$lastGood.Hwnd) -and -not [TvdWin]::IsIconic([IntPtr]$lastGood.Hwnd)) {
        $rect = New-Object TvdWin+RECT
        if ([TvdWin]::GetWindowRect([IntPtr]$lastGood.Hwnd, [ref]$rect)) {
          $tw = $rect.Right - $rect.Left; $th = $rect.Bottom - $rect.Top
          if ($tw -ge 480 -and $th -ge 360) {
            $target = @{
              Hwnd = $lastGood.Hwnd; Score = $lastGood.Score; W = $tw; H = $th
              Left = $rect.Left; Top = $rect.Top; Label = $lastGood.Label
            }
          }
        }
      }
    }
    $bmp = $null
    $g = $null
    if ($target -and $mode -ne 'full') {
      if ($target.Label -ne $lastLabel) {
        $dims = '{0}x{1}' -f $target.W, $target.H
        Write-Host ("  eye pinned: {0} ({1})" -f $target.Label, $dims)
        $lastLabel = $target.Label
      }
      $cap = Capture-WindowBitmap $target
      if ($cap) {
        $bmp = $cap.Bmp; $g = $cap.G
        $capMode = 'window'
        $capLabel = $target.Label + ' via ' + $cap.How
        $lastGood = $target
        $missStreak = 0
      } else {
        Write-Host ("  pin grab failed: {0}" -f $target.Label)
        $missStreak++
      }
    }

    if (-not $bmp) {
      if ($mode -eq 'window' -or $mode -eq 'win' -or $mode -eq 'game') {
        if ($lastLabel -ne '__waiting__') {
          Write-Host '  waiting for Diablo II (D2R.exe) window...'
          $lastLabel = '__waiting__'
        }
        Write-CapTarget 'waiting' 'Diablo II (D2R.exe) not found - open the game (not only Battle.net)'
        Start-Sleep -Milliseconds 500
        continue
      }
      # auto: full virtual screen when no game (still films something so console is not DEAD)
      if ($lastLabel -ne '__full__') {
        Write-Host '  full virtual screen (no D2R window / mode=full)'
        $lastLabel = '__full__'
      }
      $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
      $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
      if ($mode -eq 'auto' -and -not $target) {
        $capLabel = 'full screen (no game window - open D2R in-game)'
        $capMode = 'waiting'
      }
    }

    # never trust a partial write: temp then promote
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
