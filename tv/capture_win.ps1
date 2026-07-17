# 📺 TV DIABLO — Windows capture loop (v772: pin to native D2R window)
# Zero installs: .NET System.Drawing. Read-only screenshots only.
#
#   TV_CAPTURE=auto|window|full   (default auto)
#   TV_WINDOW_MATCH=extra,tokens  optional title needles
#
# Prefers the native Diablo II Resurrected window (D2R.exe). Falls back to
# full virtual screen if the game isn't found (unless TV_CAPTURE=window).
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
}
"@

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $here 'frames'
New-Item -ItemType Directory -Force -Path $frames | Out-Null

$mode = if ($env:TV_CAPTURE) { $env:TV_CAPTURE.ToLower() } else { 'auto' }
$extra = @()
if ($env:TV_WINDOW_MATCH) {
  $extra = $env:TV_WINDOW_MATCH.Split(',') | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
}

# Native Windows D2R process names + title needles
$procNames = @('D2R', 'Diablo II Resurrected', 'DiabloII', 'Diablo II')
$titleHints = @(
  'diablo ii', 'diablo 2', 'diablo ii: resurrected', 'diablo ii resurrected',
  'd2r', 'resurrected'
) + $extra

function Get-WindowTitle([IntPtr]$hwnd) {
  $len = [TvdWin]::GetWindowTextLength($hwnd)
  if ($len -le 0) { return '' }
  $sb = New-Object System.Text.StringBuilder ($len + 1)
  [void][TvdWin]::GetWindowText($hwnd, $sb, $sb.Capacity)
  return $sb.ToString()
}

function Find-D2RWindow {
  $best = $null  # @{ Hwnd; Score; W; H; Label }
  $script:enumCb = {
    param([IntPtr]$hwnd, [IntPtr]$lp)
    if (-not [TvdWin]::IsWindowVisible($hwnd)) { return $true }
    if ([TvdWin]::IsIconic($hwnd)) { return $true }
    $title = Get-WindowTitle $hwnd
    $pid = 0
    [void][TvdWin]::GetWindowThreadProcessId($hwnd, [ref]$pid)
    $procName = ''
    try { $procName = (Get-Process -Id $pid -ErrorAction SilentlyContinue).ProcessName } catch {}
    $blob = ("$procName $title").ToLower()
    $hit = $false
    foreach ($p in $procNames) {
      if ($procName -and $procName -ieq $p) { $hit = $true; break }
    }
    if (-not $hit) {
      foreach ($t in $titleHints) {
        if ($blob -like "*$t*") { $hit = $true; break }
      }
    }
    if (-not $hit) { return $true }
    $rect = New-Object TvdWin+RECT
    if (-not [TvdWin]::GetWindowRect($hwnd, [ref]$rect)) { return $true }
    $w = $rect.Right - $rect.Left
    $h = $rect.Bottom - $rect.Top
    if ($w -lt 640 -or $h -lt 400) { return $true }
    $score = 0
    if ($procName -ieq 'D2R') { $score += 100 }
    if ($title -match 'Diablo') { $score += 40 }
    $score += [Math]::Min([int](($w * $h) / 100000), 20)
    $label = if ($title) { "$procName · $title" } else { $procName }
    if (-not $script:best -or $score -gt $script:best.Score) {
      $script:best = @{
        Hwnd = $hwnd; Score = $score; W = $w; H = $h
        Left = $rect.Left; Top = $rect.Top; Label = $label
      }
    }
    return $true
  }
  $script:best = $null
  [void][TvdWin]::EnumWindows($script:enumCb, [IntPtr]::Zero)
  return $script:best
}

Write-Host "📺 TV DIABLO capture (Windows) — pin D2R window when found · mode=$mode"
$lastLabel = ''
while ($true) {
  try {
    $target = $null
    if ($mode -ne 'full') {
      $target = Find-D2RWindow
    }
    if ($target) {
      if ($target.Label -ne $lastLabel) {
        Write-Host "  🎯 window: $($target.Label) ($($target.W)x$($target.H))"
        $lastLabel = $target.Label
      }
      $bmp = New-Object System.Drawing.Bitmap $target.W, $target.H
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      $g.CopyFromScreen($target.Left, $target.Top, 0, 0, $bmp.Size)
    } elseif ($mode -eq 'window') {
      # strict: wait for game
      if ($lastLabel -ne '__waiting__') {
        Write-Host "  ⏳ waiting for Diablo II (D2R.exe) window…"
        $lastLabel = '__waiting__'
      }
      Start-Sleep -Milliseconds 500
      continue
    } else {
      if ($lastLabel -ne '__full__') {
        Write-Host "  🖥 full virtual screen (D2R window not found)"
        $lastLabel = '__full__'
      }
      $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
      $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
      $g = [System.Drawing.Graphics]::FromImage($bmp)
      $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
    }
    $tmp = Join-Path $frames 'live.tmp.bmp'
    $out = Join-Path $frames 'live.bmp'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Bmp)
    Move-Item -Force $tmp $out
    $png = Join-Path $frames 'live.png'
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
  } catch { Write-Host "  capture error: $_" }
  Start-Sleep -Milliseconds 500
}
