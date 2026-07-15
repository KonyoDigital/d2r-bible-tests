#!/usr/bin/env python3
"""
v689 PHASE-Z performance build
──────────────────────────────
Reads bible.monolith.html (or bible.html if still monolithic) and writes:

  bible.html              thin shell (no-cache)
  assets/z/<hash>/…       CSS + JS chunks (long-cache, immutable)
  assets/z/sw.js          service worker (cache assets; network-first HTML)
  assets/z/build.json     manifest

Also extracts large base64 payloads into art/perf/ and rewrites references.

Doctrine (v657 + Fable):
  • HTML always revalidates (no ghost builds)
  • Art + hashed assets may cache forever
  • Script execution order preserved (defer, in document order)
  • No behavioral rewrite of game logic
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONOLITH = ROOT / "bible.monolith.html"
FALLBACK = ROOT / "bible.html"
OUT_HTML = ROOT / "bible.html"
ASSETS = ROOT / "assets" / "z"
ART_PERF = ROOT / "art" / "perf"
BUILD_ID = "v689"


def sha10(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:10]


def read_source() -> str:
    src = MONOLITH if MONOLITH.exists() else FALLBACK
    text = src.read_text(encoding="utf-8", errors="replace")
    # if bible.html was already split, prefer monolith
    if "assets/z/" in text and MONOLITH.exists():
        text = MONOLITH.read_text(encoding="utf-8", errors="replace")
    if len(text) < 500_000 and MONOLITH.exists():
        text = MONOLITH.read_text(encoding="utf-8", errors="replace")
    return text


def extract_base64(html: str) -> str:
    """Pull large data-URLs into art/perf/* and rewrite to relative URLs."""
    ART_PERF.mkdir(parents=True, exist_ok=True)
    # only extract sizeable payloads
    pat = re.compile(
        r'(["\'])data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=\s]{800,})\1',
        re.I,
    )
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        q, fmt, b64 = m.group(1), m.group(2).lower(), re.sub(r"\s+", "", m.group(3))
        if fmt == "jpg":
            fmt = "jpeg"
        ext = "jpg" if fmt == "jpeg" else fmt
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception:
            return m.group(0)
        if len(raw) < 600:  # tiny cursors stay inline
            return m.group(0)
        name = f"b64_{sha10(raw)}.{ext}"
        path = ART_PERF / name
        if not path.exists():
            path.write_bytes(raw)
        n += 1
        return f"{q}art/perf/{name}{q}"

    out = pat.sub(repl, html)
    print(f"  base64 extracted: {n} files → art/perf/")
    return out


def strip_html_comments(html: str) -> str:
    # keep IE conditionals none; strip <!-- ... --> but not in scripts (rough)
    parts = re.split(r"(<script\b[^>]*>.*?</script>)", html, flags=re.S | re.I)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:  # script
            out.append(p)
        else:
            out.append(re.sub(r"<!--(?!\[if)[\s\S]*?-->", "", p))
    return "".join(out)


def minify_css(css: str) -> str:
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,])\s*", r"\1", css)
    return css.strip()


def light_minify_js(js: str) -> str:
    """Conservative: strip block comments not containing url( or regex-ish danger; keep strings intact via crude pass."""
    # only remove /* ... */ that don't look like they contain strings with */
    def strip_block(m: re.Match) -> str:
        body = m.group(0)
        if "http://" in body or "https://" in body or "${" in body:
            return body
        return "\n"

    js = re.sub(r"/\*[\s\S]*?\*/", strip_block, js)
    # collapse runs of blank lines
    js = re.sub(r"\n{3,}", "\n\n", js)
    return js


PERF_CSS = """
/* v689 PHASE-Z render containment — offscreen tabs cost almost nothing to paint */
.tab-content:not(.active){
  content-visibility:auto;
  contain-intrinsic-size:auto 900px;
}
/* session paints first-class */
#tab-session.active{content-visibility:visible}
/* reduce font flash: optional system fallback already present */
img[loading="lazy"]{content-visibility:auto}
"""


def process(html: str) -> tuple[str, dict]:
    html = extract_base64(html)
    html = strip_html_comments(html)

    # collect styles
    style_re = re.compile(r"<style([^>]*)>(.*?)</style>", re.S | re.I)
    styles = style_re.findall(html)
    css_blob = "\n".join(s[1] for s in styles) + "\n" + PERF_CSS
    css_blob = minify_css(css_blob)

    # collect inline scripts (preserve order); leave src= scripts alone
    script_re = re.compile(r"<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>", re.S | re.I)
    scripts = list(script_re.finditer(html))

    # wipe asset dir for this build id folder after hash known
    tmp_chunks: list[tuple[str, bytes]] = []
    css_bytes = css_blob.encode("utf-8")
    css_hash = sha10(css_bytes)
    tmp_chunks.append((f"bible.{css_hash}.css", css_bytes))

    js_manifest = []
    for i, m in enumerate(scripts):
        body = m.group(2)
        if not body.strip():
            continue
        body = light_minify_js(body)
        raw = body.encode("utf-8")
        h = sha10(raw)
        name = f"chunk-{i:02d}.{h}.js"
        tmp_chunks.append((name, raw))
        js_manifest.append(name)

    # content hash of whole asset set for folder name
    cat = b"".join(b for _, b in tmp_chunks)
    set_hash = sha10(cat)
    out_dir = ASSETS / set_hash
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, raw in tmp_chunks:
        (out_dir / name).write_bytes(raw)

    # replace styles with single link
    html2 = style_re.sub("", html, count=len(styles))
    # replace each inline script in order with src
    # rebuild by walking matches on original positions — safer: sequential replace empty
    # Insert link in head
    link_tag = (
        f'<link rel="stylesheet" href="assets/z/{set_hash}/bible.{css_hash}.css" '
        f'id="z-css">\n'
        f'<link rel="preload" href="assets/z/{set_hash}/bible.{css_hash}.css" as="style">\n'
    )
    # preload largest JS chunks first (core data lives in the big ones)
    size_by_name = {n: len(b) for n, b in tmp_chunks if n.endswith(".js")}
    biggest = sorted(js_manifest, key=lambda n: -size_by_name.get(n, 0))[:4]
    preloads = [
        f'<link rel="preload" href="assets/z/{set_hash}/{name}" as="script">'
        for name in biggest
    ]
    link_tag += "\n".join(preloads) + "\n"

    if re.search(r"</head>", html2, re.I):
        html2 = re.sub(r"</head>", link_tag + "</head>", html2, count=1, flags=re.I)
    else:
        html2 = link_tag + html2

    # Replace scripts: process from end so positions stable... use sub with counter
    idx = {"i": 0}

    def script_sub(m: re.Match) -> str:
        body = m.group(2)
        if not body.strip():
            return ""
        # find corresponding name
        i = idx["i"]
        idx["i"] += 1
        if i >= len(js_manifest):
            return m.group(0)
        name = js_manifest[i]
        # defer keeps order among deferred scripts; DOM ready before run
        return (
            f'<script src="assets/z/{set_hash}/{name}" defer data-z-chunk="{i}"></script>'
        )

    html2 = script_re.sub(script_sub, html2)

    # lazy-load images outside session (add loading=lazy if missing)
    def img_lazy(m: re.Match) -> str:
        tag = m.group(0)
        if "loading=" in tag:
            return tag
        if "tab-session" in tag:  # unlikely on img
            return tag
        return tag[:-1] + ' loading="lazy" decoding="async">'

    html2 = re.sub(r"<img\b[^>]*>", img_lazy, html2, flags=re.I)

    # build meta
    html2 = re.sub(
        r'<meta name="d2r-build" content="[^"]*"\s*/?>',
        f'<meta name="d2r-build" content="{BUILD_ID}">',
        html2,
        count=1,
    )
    if 'name="d2r-build"' not in html2:
        html2 = html2.replace(
            "<head>",
            f'<head>\n<meta name="d2r-build" content="{BUILD_ID}">\n<meta name="d2r-perf" content="phase-z">',
            1,
        )
    else:
        if 'name="d2r-perf"' not in html2:
            html2 = html2.replace(
                f'<meta name="d2r-build" content="{BUILD_ID}">',
                f'<meta name="d2r-build" content="{BUILD_ID}">\n<meta name="d2r-perf" content="phase-z">',
                1,
            )

    # title touch
    html2 = re.sub(
        r"<title>.*?</title>",
        f"<title>Konyo's D2R Farming Bible {BUILD_ID} · Phase Z</title>",
        html2,
        count=1,
        flags=re.S,
    )

    # boot splash + SW registration (tiny inline — only allowed inline)
    boot = f"""
<script id="z-boot">
window.D2R_BUILD=Object.assign(window.D2R_BUILD||{{}},{{id:'{BUILD_ID}',perf:'phase-z',assets:'assets/z/{set_hash}'}});
window.D2R_ASSET_SET='{set_hash}';
// progressive: mark shell ready; chunks are defer
document.documentElement.classList.add('z-shell');
window.addEventListener('DOMContentLoaded',function(){{
  document.documentElement.classList.add('z-dom');
}});
window.addEventListener('load',function(){{
  document.documentElement.classList.add('z-loaded');
  try{{
    if('serviceWorker' in navigator){{
      navigator.serviceWorker.register('sw.js',{{scope:'./'}}).catch(function(){{}});
    }}
  }}catch(e){{}}
}});
</script>
<style id="z-shell-css">
html.z-shell body{{opacity:1}}
#z-boot-bar{{position:fixed;top:0;left:0;right:0;height:2px;z-index:100000;
  background:linear-gradient(90deg,#d4a847,#f0c060);transform-origin:left;
  animation:zbar 1.2s ease-in-out infinite alternate}}
html.z-loaded #z-boot-bar{{display:none}}
@keyframes zbar{{from{{transform:scaleX(.15)}}to{{transform:scaleX(1)}}}}
</style>
"""
    if "<body" in html2:
        html2 = re.sub(
            r"(<body[^>]*>)",
            r"\1\n<div id=\"z-boot-bar\" aria-hidden=\"true\"></div>\n" + boot,
            html2,
            count=1,
            flags=re.I,
        )
    else:
        html2 = boot + html2

    # service worker at stable path assets/z/sw.js (not hashed — must update carefully)
    sw = f"""/* D2R Bible Phase-Z SW — cache hashed assets only; HTML always network-first */
const ZSET = '{set_hash}';
const CACHE = 'd2r-z-' + ZSET;
const ASSET_PREFIX = '/d2r/assets/z/' + ZSET + '/';
const ART_PREFIX = '/d2r/art/';

self.addEventListener('install', (e) => {{
  self.skipWaiting();
}});
self.addEventListener('activate', (e) => {{
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k.startsWith('d2r-z-') && k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
}});
self.addEventListener('fetch', (e) => {{
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // never cache APIs
  if (url.pathname.startsWith('/api/')) return;
  // HTML shell: network-first (v657 anti-ghost)
  if (
    url.pathname === '/d2r/' ||
    url.pathname === '/d2r/index.html' ||
    url.pathname.endsWith('/bible.html')
  ) {{
    e.respondWith(
      fetch(req)
        .then((res) => res)
        .catch(() => caches.match(req))
    );
    return;
  }}
  // hashed assets + art: cache-first
  if (url.pathname.startsWith(ASSET_PREFIX) || url.pathname.startsWith(ART_PREFIX) || url.pathname.startsWith('/d2r/art/perf/')) {{
    e.respondWith(
      caches.open(CACHE).then(async (cache) => {{
        const hit = await cache.match(req);
        if (hit) return hit;
        try {{
          const res = await fetch(req);
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        }} catch (err) {{
          return hit || Response.error();
        }}
      }})
    );
  }}
}});
"""
    (ASSETS / "sw.js").parent.mkdir(parents=True, exist_ok=True)
    (ASSETS / "sw.js").write_text(sw, encoding="utf-8")

    manifest = {
        "build": BUILD_ID,
        "set": set_hash,
        "css": f"bible.{css_hash}.css",
        "js": js_manifest,
        "html_bytes": len(html2.encode("utf-8")),
        "css_bytes": len(css_bytes),
        "js_bytes": sum(len(b) for n, b in tmp_chunks if n.endswith(".js")),
        "chunks": len(js_manifest),
    }
    (out_dir / "build.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ASSETS / "latest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return html2, manifest


def main() -> int:
    print("Phase-Z build…")
    src = read_source()
    print(f"  source bytes: {len(src):,}")
    html, man = process(src)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"  shell html:   {man['html_bytes']:,}")
    print(f"  css:          {man['css_bytes']:,}")
    print(f"  js chunks:    {man['chunks']} files / {man['js_bytes']:,} bytes")
    print(f"  asset set:    assets/z/{man['set']}/")
    print(f"  wrote:        {OUT_HTML}")
    # size sanity
    if man["html_bytes"] > 1_500_000:
        print("WARN: shell still large — check extraction", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
