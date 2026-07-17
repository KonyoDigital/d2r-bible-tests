# 📺 TV DIABLO — Windows capture loop (the cousin's side)
# Zero installs: uses .NET System.Drawing (built into Windows). Read-only by
# construction — this only screenshots what is already on screen. It never
# touches the game process.
#
# Run this in ONE terminal:        powershell -ExecutionPolicy Bypass -File tv\capture_win.ps1
# Run the reader in ANOTHER:       python tv\tv_diablo.py --watch
#   (the reader's vision calls run through YOUR `claude` login — your
#    subscription, your plan limits, zero API keys)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $here 'frames'
New-Item -ItemType Directory -Force -Path $frames | Out-Null
Write-Host "📺 TV DIABLO capture (Windows) — frames -> $frames  (Ctrl-C to stop)"
while ($true) {
  try {
    $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
    # one rolling file — the reader md5-diffs it, so a constant name is correct
    $tmp = Join-Path $frames 'live.tmp.bmp'
    $out = Join-Path $frames 'live.bmp'
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Bmp)
    Move-Item -Force $tmp $out
    # PNG twin — the vision reader needs a compressed format (BMP made claude's Read choke)
    $png = Join-Path $frames 'live.png'
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
  } catch { Write-Host "  capture error: $_" }
  Start-Sleep -Milliseconds 500   # aligned with the agent's half-second eyes (POLL_S)
}
