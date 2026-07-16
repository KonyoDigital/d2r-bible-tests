// tv/ocr_mac.swift — local Vision OCR fast lane (v732)
// Usage:
//   ocr_mac <image>                 one-shot JSON to stdout
//   ocr_mac --worker                stdin paths → stdout JSON lines (warm process)
// Target: warm single-ROI OCR ~10–50ms. No network. macOS Vision only.
import Foundation
import Vision
import CoreGraphics
import ImageIO

struct Out: Encodable {
    let ms: Int
    let lines: [String]
    let confs: [Double]
    let mode: String
}

func loadCG(_ path: String, maxSide: Int) -> CGImage? {
    let url = URL(fileURLWithPath: path)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
    let opts: [CFString: Any] = [
        kCGImageSourceShouldCache: false,
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceThumbnailMaxPixelSize: maxSide,
    ]
    return CGImageSourceCreateThumbnailAtIndex(src, 0, opts as CFDictionary)
}

func ocrImage(_ path: String) -> Out {
    let t0 = CFAbsoluteTimeGetCurrent()
    // 800px + single mid-screen ROI: warm ~10–20ms on M-series; labels still legible
    guard let full = loadCG(path, maxSide: 800) else {
        return Out(ms: Int((CFAbsoluteTimeGetCurrent() - t0) * 1000), lines: [], confs: [], mode: "fail-load")
    }
    let w = CGFloat(full.width), h = CGFloat(full.height)
    // Ground loot labels + tooltips cluster in the playfield (skip most chrome)
    let rect = CGRect(x: w * 0.12, y: h * 0.18, width: w * 0.76, height: h * 0.64).integral
    guard let crop = full.cropping(to: rect) else {
        return Out(ms: Int((CFAbsoluteTimeGetCurrent() - t0) * 1000), lines: [], confs: [], mode: "fail-crop")
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .fast
    req.usesLanguageCorrection = false
    req.minimumTextHeight = 0.018
    do {
        try VNImageRequestHandler(cgImage: crop, options: [:]).perform([req])
    } catch {
        return Out(ms: Int((CFAbsoluteTimeGetCurrent() - t0) * 1000), lines: [], confs: [], mode: "fail-ocr")
    }
    var seen = Set<String>()
    var lines: [String] = []
    var confs: [Double] = []
    for obs in (req.results ?? []) {
        guard let c = obs.topCandidates(1).first, c.confidence >= 0.35 else { continue }
        let s = c.string.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.count < 2 || s.count > 48 { continue }
        if s.range(of: #"[A-Za-z]"#, options: .regularExpression) == nil { continue }
        let k = s.lowercased()
        if seen.contains(k) { continue }
        seen.insert(k)
        lines.append(s)
        confs.append(Double(c.confidence))
        if lines.count >= 24 { break }
    }
    let ms = Int((CFAbsoluteTimeGetCurrent() - t0) * 1000)
    return Out(ms: ms, lines: lines, confs: confs, mode: "roi-fast")
}

func emit(_ o: Out) {
    let enc = JSONEncoder()
    if let data = try? enc.encode(o), let s = String(data: data, encoding: .utf8) {
        print(s)
        fflush(stdout)
    }
}

let args = CommandLine.arguments
if args.contains("--worker") {
    while let line = readLine() {
        let path = line.trimmingCharacters(in: .whitespacesAndNewlines)
        if path.isEmpty || path == "quit" { break }
        emit(ocrImage(path))
    }
} else if args.count >= 2 {
    emit(ocrImage(args[1]))
} else {
    fputs("usage: ocr_mac <image> | ocr_mac --worker\n", stderr)
    exit(2)
}
