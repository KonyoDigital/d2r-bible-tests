# TV DIABLO - Windows capture loop (v1423)
# Zero installs: .NET System.Drawing. Read-only screenshots only.
#
#   TV_CAPTURE=auto|full|window   (default AUTO - pin D2R.exe when present, else full)
#   TV_CAPTURE_MS=350
#
# Writes:
#   frames/live.bmp, live.png (every 5th), eye.jpg, cap_target.json
#   frames/win_pin_debug.json, capture_heartbeat.txt, capture_stage.txt
#
# v1418: Pure C# Find+PrintWindow (no PowerShell EnumWindows callbacks - those hang under D2R).
#         Always write eye.jpg when we have pixels. Never BitBlt (desktop z-order lie).
# v1421: Promote frames with File.Copy(overwrite) so agent locks no longer kill film.
# v1422: Light capture under D2R - eye first, PNG rare, 350ms poll, unique tmp names.
# v1423: Per-monitor DPI awareness - 150% displays were 1920x1080 physical but capture
#         used 1280x720 logical coords = TOP-LEFT CROP only (Konyo screenshot proof).
# Pure ASCII + BOM for Hebrew PowerShell 5.1.

# v1423 - declare DPI awareness BEFORE any window measure / System.Drawing call.
# Without this, GetWindowRect returns logical 1280x720 on a 1920x1080@150% screen and
# PrintWindow only paints the top-left third of the real D2R framebuffer into the film.
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class TvdDpi {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("shcore.dll")] public static extern int SetProcessDpiAwareness(int value);
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr value);
  // DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
  public static void Arm() {
    try {
      if (SetProcessDpiAwarenessContext((IntPtr)(-4))) return;
    } catch {}
    try {
      if (SetProcessDpiAwareness(2) == 0) return; // PROCESS_PER_MONITOR_DPI_AWARE
    } catch {}
    try { SetProcessDPIAware(); } catch {}
  }
}
"@
[TvdDpi]::Arm()

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -ReferencedAssemblies System.Drawing,System.Windows.Forms -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

public static class TvdCap {
  public struct RECT { public int Left, Top, Right, Bottom; }
  public struct POINT { public int X, Y; }
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);

  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] static extern bool IsWindow(IntPtr hWnd);
  [DllImport("user32.dll")] static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr hWnd, ref POINT lpPoint);
  [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern uint GetDpiForWindow(IntPtr hWnd);
  [DllImport("gdi32.dll")] static extern int GetDeviceCaps(IntPtr hdc, int nIndex);
  [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr hWnd);
  [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

  public class Hit {
    public IntPtr Hwnd;
    public int Left, Top, W, H;
    public string Title;
    public string Proc;
    public int Score;
    public bool IsFg;
    public int Dpi;
  }

  static readonly string[] ProcNames = new string[] { "D2R", "DiabloIIResurrected", "DiabloII" };

  public static string DpiInfo() {
    try {
      IntPtr hdc = GetDC(IntPtr.Zero);
      int logical = GetDeviceCaps(hdc, 8);   // HORZRES
      int physical = GetDeviceCaps(hdc, 118); // DESKTOPHORZRES
      ReleaseDC(IntPtr.Zero, hdc);
      return "logical=" + logical + " physical=" + physical;
    } catch { return "dpi=?"; }
  }

  public static List<Hit> FindD2R() {
    var want = new HashSet<int>();
    var names = new Dictionary<int, string>();
    foreach (var n in ProcNames) {
      try {
        foreach (var p in Process.GetProcessesByName(n)) {
          want.Add(p.Id);
          names[p.Id] = p.ProcessName;
          try { p.Dispose(); } catch {}
        }
      } catch {}
    }
    var hits = new List<Hit>();
    if (want.Count == 0) return hits;
    IntPtr fg = GetForegroundWindow();
    EnumWindows((h, lp) => {
      try {
        if (!IsWindow(h) || IsIconic(h)) return true;
        uint pidU = 0;
        GetWindowThreadProcessId(h, out pidU);
        int pid = (int)pidU;
        if (!want.Contains(pid)) return true;
        RECT wr;
        if (!GetWindowRect(h, out wr)) return true;
        int left = wr.Left, top = wr.Top;
        int w = wr.Right - wr.Left, hh = wr.Bottom - wr.Top;
        RECT cr;
        if (GetClientRect(h, out cr)) {
          int cw = cr.Right - cr.Left, ch = cr.Bottom - cr.Top;
          if (cw >= 320 && ch >= 240) {
            POINT pt; pt.X = 0; pt.Y = 0;
            if (ClientToScreen(h, ref pt)) { left = pt.X; top = pt.Y; w = cw; hh = ch; }
          }
        }
        // v1423 - after DPI-aware arm, W/H are PHYSICAL pixels. Reject tiny tools only.
        if (w < 640 || hh < 400) return true;
        var sb = new StringBuilder(512);
        GetWindowText(h, sb, 512);
        string title = sb.ToString() ?? "";
        string tl = title.ToLowerInvariant();
        if (tl.Contains("battle.net") || tl.Contains("tv diablo") || tl.Contains("farming bible")) return true;
        string proc = names.ContainsKey(pid) ? names[pid] : "D2R";
        bool isFg = (h == fg);
        int score = 8000 + (isFg ? 500 : 0);
        if (tl.Contains("resurrected") || tl.Contains("diablo ii")) score += 1500;
        // Prefer the largest window (true fullscreen game over tiny helper hwnds).
        score += Math.Min((w * hh) / 80000, 200);
        int dpi = 96;
        try { dpi = (int)GetDpiForWindow(h); if (dpi < 72) dpi = 96; } catch {}
        hits.Add(new Hit {
          Hwnd = h, Left = left, Top = top, W = w, H = hh,
          Title = title, Proc = proc, Score = score, IsFg = isFg, Dpi = dpi
        });
      } catch {}
      return true;
    }, IntPtr.Zero);
    hits.Sort((a, b) => b.Score.CompareTo(a.Score));
    return hits;
  }

  public static bool D2RProcessAlive() {
    foreach (var n in ProcNames) {
      try {
        var ps = Process.GetProcessesByName(n);
        if (ps != null && ps.Length > 0) {
          foreach (var p in ps) try { p.Dispose(); } catch {}
          return true;
        }
      } catch {}
    }
    return false;
  }

  public static string Grab(Hit hit, string framesDir) {
    if (hit == null || hit.Hwnd == IntPtr.Zero || hit.W < 32 || hit.H < 32) return null;
    // v1423 - re-measure EVERY grab in physical pixels (window may move / DPI path may
    // have been wrong at find-time). Prefer FULL window rect for PrintWindow so chrome
    // + client land 1:1; fall back to stored client size.
    int left = hit.Left, top = hit.Top, bw = hit.W, bh = hit.H;
    try {
      RECT wr;
      if (GetWindowRect(hit.Hwnd, out wr)) {
        int ww = wr.Right - wr.Left, wh = wr.Bottom - wr.Top;
        if (ww >= 640 && wh >= 400) { left = wr.Left; top = wr.Top; bw = ww; bh = wh; }
      }
      RECT cr;
      if (GetClientRect(hit.Hwnd, out cr)) {
        int cw = cr.Right - cr.Left, ch = cr.Bottom - cr.Top;
        // Borderless: client ~= window. Windowed: prefer client (no title bar in film).
        if (cw >= 640 && ch >= 400 && cw * ch >= (int)(bw * bh * 0.85)) {
          POINT pt; pt.X = 0; pt.Y = 0;
          if (ClientToScreen(hit.Hwnd, ref pt)) {
            left = pt.X; top = pt.Y; bw = cw; bh = ch;
          }
        }
      }
    } catch {}
    hit.Left = left; hit.Top = top; hit.W = bw; hit.H = bh;

    Bitmap bmp = null;
    Graphics g = null;
    string how = null;
    try {
      bmp = new Bitmap(bw, bh);
      g = Graphics.FromImage(bmp);
      IntPtr hdc = g.GetHdc();
      try {
        // 2 = PW_RENDERFULLCONTENT (DWM composition / DirectX games)
        bool ok = PrintWindow(hit.Hwnd, hdc, 2);
        if (!ok) PrintWindow(hit.Hwnd, hdc, 0);
      } finally {
        g.ReleaseHdc(hdc);
      }
      if (!MostlyBlack(bmp)) {
        how = "PrintWindow";
      } else {
        // Foreground CopyFromScreen uses PHYSICAL coords after DPI arm.
        if (GetForegroundWindow() == hit.Hwnd) {
          g.CopyFromScreen(left, top, 0, 0, new Size(bw, bh));
          if (!MostlyBlack(bmp)) how = "CopyFromScreen-fg";
        }
      }
      if (how == null) return null;
      SaveAll(bmp, framesDir);
      return how;
    } catch {
      return null;
    } finally {
      try { if (g != null) g.Dispose(); } catch {}
      try { if (bmp != null) bmp.Dispose(); } catch {}
    }
  }

  public static void GrabPrimary(string framesDir) {
    var b = System.Windows.Forms.Screen.PrimaryScreen.Bounds;
    using (var bmp = new Bitmap(b.Width, b.Height))
    using (var g = Graphics.FromImage(bmp)) {
      g.CopyFromScreen(b.X, b.Y, 0, 0, bmp.Size);
      SaveAll(bmp, framesDir);
    }
  }

  public static void GrabVirtual(string framesDir) {
    var b = System.Windows.Forms.SystemInformation.VirtualScreen;
    using (var bmp = new Bitmap(b.Width, b.Height))
    using (var g = Graphics.FromImage(bmp)) {
      g.CopyFromScreen(b.Left, b.Top, 0, 0, bmp.Size);
      SaveAll(bmp, framesDir);
    }
  }

  static bool MostlyBlack(Bitmap bmp) {
    try {
      int[] xs = new int[] { bmp.Width/2, bmp.Width/4, 3*bmp.Width/4, bmp.Width/4, 3*bmp.Width/4 };
      int[] ys = new int[] { bmp.Height/2, bmp.Height/4, bmp.Height/4, 3*bmp.Height/4, 3*bmp.Height/4 };
      int dark = 0;
      for (int i = 0; i < 5; i++) {
        Color c = bmp.GetPixel(xs[i], ys[i]);
        if (c.R < 12 && c.G < 12 && c.B < 12) dark++;
      }
      return dark >= 4;
    } catch { return true; }
  }

  // v1421 — promote via Copy(overwrite) not Delete+Move. Under ON AIR the agent holds
  // live.bmp / eye.jpg for freezes; Delete fails, Move throws "file already exists",
  // and film stalls (eyeAge 7s+) with primary/virtual fail spam in the log.
  // v1422 — unique tmp names (GUID) so a killed mid-write never leaves a sticky .tmp that
  // blocks the next Save. Eye first (film), then BMP (agent), PNG rare (CPU killer under D2R).
  static int _saveN = 0;

  static void Promote(string tmp, string finalPath) {
    try {
      File.Copy(tmp, finalPath, true);
    } catch {
      try {
        if (File.Exists(finalPath)) File.Delete(finalPath);
        File.Move(tmp, finalPath);
        return;
      } catch { return; }
    }
    try { File.Delete(tmp); } catch {}
  }

  static string TmpPath(string framesDir, string tag, string ext) {
    return Path.Combine(framesDir, "._tvd_" + tag + "_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ext);
  }

  static void SaveAll(Bitmap bmp, string framesDir) {
    _saveN++;
    string liveBmp = Path.Combine(framesDir, "live.bmp");
    string livePng = Path.Combine(framesDir, "live.png");
    string eyeJpg = Path.Combine(framesDir, "eye.jpg");

    // 1) EYE FIRST — console film / UX lamp. JPEG scale is cheap vs PNG.
    int maxPx = 900;
    int nw = bmp.Width, nh = bmp.Height;
    if (nw > maxPx || nh > maxPx) {
      double scale = Math.Min(maxPx / (double)nw, maxPx / (double)nh);
      nw = Math.Max(1, (int)(bmp.Width * scale));
      nh = Math.Max(1, (int)(bmp.Height * scale));
    }
    string tmpEye = TmpPath(framesDir, "eye", ".jpg");
    using (var eye = new Bitmap(nw, nh))
    using (var eg = Graphics.FromImage(eye)) {
      eg.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.Bilinear;
      eg.DrawImage(bmp, 0, 0, nw, nh);
      eye.Save(tmpEye, ImageFormat.Jpeg);
    }
    Promote(tmpEye, eyeJpg);

    // 2) live.bmp — agent motion/settle. Raw write is fast; unique tmp avoids sticky locks.
    string tmpBmp = TmpPath(framesDir, "bmp", ".bmp");
    bmp.Save(tmpBmp, ImageFormat.Bmp);
    Promote(tmpBmp, liveBmp);

    // 3) live.png — ONLY every 5th frame. Full PNG encode of 1280x720 under D2R was the
    // #1 capture death (stage stuck on 'grab', eye age 100s+, control status dead).
    // Agent vision uses BMP->JPEG convert (v1421); PNG is a soft fallback only.
    if ((_saveN % 5) == 0) {
      string tmpPng = TmpPath(framesDir, "png", ".png");
      try {
        bmp.Save(tmpPng, ImageFormat.Png);
        Promote(tmpPng, livePng);
      } catch {
        try { if (File.Exists(tmpPng)) File.Delete(tmpPng); } catch {}
      }
    }
  }
}
"@

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $here 'frames'
New-Item -ItemType Directory -Force -Path $frames | Out-Null
# scrub sticky temps from prior crash
Get-ChildItem -LiteralPath $frames -Filter '._tvd_*' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $frames -Filter '*.tmp' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$mode = if ($env:TV_CAPTURE) { $env:TV_CAPTURE.ToLower().Trim() } else { 'auto' }
# v1422 — default 350ms (was 200). 5fps full BMP+PNG under D2R froze capture + control status.
$pollMs = 350
if ($env:TV_CAPTURE_MS) {
  try { $pollMs = [Math]::Max(120, [int]$env:TV_CAPTURE_MS) } catch { $pollMs = 350 }
}

function Write-Stage([string]$s) {
  try { Set-Content -LiteralPath (Join-Path $frames 'capture_stage.txt') -Value $s -Encoding UTF8 } catch {}
}

function Write-CapTarget([string]$mode, [string]$label) {
  $p = Join-Path $frames 'cap_target.json'
  $alive = $false
  try { $alive = [TvdCap]::D2RProcessAlive() } catch {}
  $obj = @{
    mode = $mode
    label = $label
    ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    d2rProcess = $alive
  }
  # v1419: UTF-8 WITHOUT BOM — agent json.load('utf-8') used to miss pin when BOM present
  $json = ($obj | ConvertTo-Json -Compress)
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($p, $json, $utf8NoBom)
  try {
    [System.IO.File]::WriteAllText((Join-Path $frames 'cap_target.txt'), "$mode|$label", $utf8NoBom)
  } catch {}
}

function Write-PinDebug($hits) {
  try {
    $debug = @()
    foreach ($h in $hits) {
      $debug += @{
        proc = $h.Proc; title = $h.Title; score = $h.Score
        w = $h.W; h = $h.H; left = $h.Left; top = $h.Top
        dpi = $h.Dpi
      }
    }
    $best = $null
    if ($hits -and $hits.Count -gt 0) { $best = ($hits[0].Proc + ' - ' + $hits[0].Title) }
    $dpiInfo = ''
    try { $dpiInfo = [TvdCap]::DpiInfo() } catch {}
    $obj = @{
      ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      d2rProcessAlive = [TvdCap]::D2RProcessAlive()
      candidateCount = @($hits).Count
      best = $best
      dpi = $dpiInfo
      candidates = $debug
    }
    ($obj | ConvertTo-Json -Depth 5 -Compress) | Set-Content -LiteralPath (Join-Path $frames 'win_pin_debug.json') -Encoding UTF8
  } catch {}
}

Write-Host ("TV DIABLO capture (Windows) mode=$mode poll=${pollMs}ms v1423 DPI-aware full frame + light eye")
try { Write-Host ("  dpi: " + [TvdCap]::DpiInfo()) } catch {}
$lastLabel = ''
$loopN = 0
while ($true) {
  $loopN++
  try {
    Set-Content -LiteralPath (Join-Path $frames 'capture_heartbeat.txt') -Value ("n={0} t={1}" -f $loopN, [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -Encoding UTF8
  } catch {}
  try {
    Write-Stage 'find'
    $d2rAlive = $false
    try { $d2rAlive = [TvdCap]::D2RProcessAlive() } catch {}
    $hits = @()
    $best = $null
    if ($mode -ne 'full') {
      try { $hits = [TvdCap]::FindD2R() } catch { Write-Host "  find err: $_" }
      Write-PinDebug $hits
      if ($hits -and $hits.Count -gt 0) { $best = $hits[0] }
    }

    if ($best -and $mode -ne 'full') {
      Write-Stage 'grab'
      if ($best.Title -ne $lastLabel) {
        Write-Host ("  eye pinned: {0} - {1} ({2}x{3})" -f $best.Proc, $best.Title, $best.W, $best.H)
        $lastLabel = $best.Title
      }
      $how = $null
      try { $how = [TvdCap]::Grab($best, $frames) } catch { Write-Host "  grab err: $_" }
      # heartbeat after grab so a hung Save is visible in capture_stage + stale hb
      try {
        Set-Content -LiteralPath (Join-Path $frames 'capture_heartbeat.txt') -Value ("n={0} t={1} postgrab" -f $loopN, [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -Encoding UTF8
      } catch {}
      if ($how) {
        Write-Stage ("ok:" + $how)
        Write-CapTarget 'window' ("{0} - {1} via {2}" -f $best.Proc, $best.Title, $how)
        Start-Sleep -Milliseconds $pollMs
        continue
      }
      if ($best.IsFg) {
        Write-Stage 'primary-fg'
        try {
          [TvdCap]::GrabPrimary($frames)
          Write-CapTarget 'window' 'D2R foreground - primary monitor'
          Start-Sleep -Milliseconds $pollMs
          continue
        } catch { Write-Host "  primary fail: $_" }
      } else {
        Write-Stage 'need-focus'
        if ($lastLabel -ne '__need_focus__') {
          Write-Host '  D2R pin found but grab black and not focused - click GAME window'
          $lastLabel = '__need_focus__'
        }
        Write-CapTarget 'waiting' 'D2R running - click Diablo window (PrintWindow black; not filming chat)'
        Start-Sleep -Milliseconds 400
        continue
      }
    }

    if ($mode -eq 'window' -or $mode -eq 'win' -or $mode -eq 'game') {
      Write-Stage 'waiting-d2r'
      $msg = if ($d2rAlive) {
        'D2R.exe running but no capturable window - try borderless windowed'
      } else {
        'D2R.exe not found - open Diablo II Resurrected in-game (not only Battle.net)'
      }
      Write-CapTarget 'waiting' $msg
      Start-Sleep -Milliseconds 500
      continue
    }

    Write-Stage 'virtual'
    if ($lastLabel -ne '__full__') {
      Write-Host '  full virtual screen (no D2R pin)'
      $lastLabel = '__full__'
    }
    try {
      [TvdCap]::GrabVirtual($frames)
      Write-CapTarget $(if ($d2rAlive) { 'window' } else { 'waiting' }) $(if ($d2rAlive) { 'D2R alive - full virtual fallback' } else { 'full screen (no D2R)' })
    } catch {
      Write-Host "  virtual fail: $_"
    }
  } catch {
    Write-Host "  loop err: $_"
    Write-Stage ("err:" + $_)
  }
  Start-Sleep -Milliseconds $pollMs
}
