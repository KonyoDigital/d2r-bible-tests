# 📺 TV DIABLO — Windows OCR fast lane (v818, Grok R4 #5b / R8 #3)
# The cousin twin of `ocr_mac --worker`: same protocol, same provisional schema.
#   stdin:  one absolute image path per line
#   stdout: one JSON line per frame: {"ms":int,"lines":[str],"confs":[float],"mode":"win-ocr"}
# Windows.Media.Ocr (inbox, no install). DARK-SHIPPED from the Mac side — final live verify
# happens on a cousin box; every failure path emits {"ms":0,"lines":[],"confs":[],"mode":"err"}
# so the agent's fast lane degrades to vision-only instead of dying.

$ErrorActionPreference = 'SilentlyContinue'

# WinRT projection + async→sync helper
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
  Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
                 $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(4000) | Out-Null
  $netTask.Result
}

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US')) }

while ($true) {
  $path = [Console]::In.ReadLine()
  if ($null -eq $path) { break }
  $path = $path.Trim()
  if (-not $path) { continue }
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $out = @{ ms = 0; lines = @(); confs = @(); mode = 'err' }
  try {
    if ($engine -and (Test-Path $path)) {
      $file   = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
      $stream = Await ($file.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
      $dec    = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
      $bmp    = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
      $res    = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
      $lines  = @()
      foreach ($l in $res.Lines) { $lines += $l.Text }
      # Windows.Media.Ocr exposes no per-line confidence — emit a flat 0.8 so the agent's
      # filter_ocr_lines confidence math has SOMETHING honest-ish to chew (documented gap).
      $out.lines = $lines
      $out.confs = @($lines | ForEach-Object { 0.8 })
      $out.mode  = 'win-ocr'
      $stream.Dispose(); $bmp.Dispose()
    }
  } catch { }
  $out.ms = [int]$sw.ElapsedMilliseconds
  [Console]::Out.WriteLine(($out | ConvertTo-Json -Compress -Depth 3))
  [Console]::Out.Flush()
}
