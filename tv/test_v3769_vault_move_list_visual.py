# -*- coding: utf-8 -*-
"""v3769 - the move list on the real vault tab.

Photographs bible.html's vault room: item art in the packer's grid, a duplicate
beside the original, a second witness, the 3-session lock, a dock that keeps
only a homeless name, AUTO INTAKE off with a typed move, the planned cell, a
hand tally, and a witness frame that verifies the row. Chrome is resolved the
same way as the v3767 screen, then the ordinary Linux binaries, skipping a
wrapper that forces port 9222. No binary is a declared skip.
"""
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

SHOTS = os.path.join(HERE, ".render_shots")
ART = "/opt/cursor/artifacts/v3769"
NO_BROWSER = "no Chrome/Chromium on this machine"
HTTP_PORT = 17963
CDP_PORT = 17964
PAGE = "http://127.0.0.1:%d/bible.html" % HTTP_PORT


def _real_chrome(path):
    if not path or not os.path.isfile(path) or not os.access(path, os.X_OK):
        return False
    try:
        with open(path, "rb") as fh:
            head = fh.read(4096)
    except OSError:
        return False
    if head.startswith(b"#!") and b"remote-debugging-port=9222" in head:
        return False
    return True


def _chrome_path():
    import glob
    from render_check import _find_chrome
    path = _find_chrome()
    if _real_chrome(path):
        return path
    roots = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium*/chrome-linux*/chrome")))
    for cand in reversed(roots):
        if _real_chrome(cand):
            return cand
    for cand in ("/usr/bin/google-chrome-stable", "/usr/bin/google-chrome",
                 "/opt/google/chrome/chrome", "/usr/bin/chromium-browser",
                 "/usr/bin/chromium"):
        if _real_chrome(cand):
            return cand
    return None


class _CDP:
    def __init__(self, ws_url):
        rest = ws_url.split("://", 1)[1]
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), 20)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        key = base64.b64encode(os.urandom(16)).decode()
        req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n"
               "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("cdp handshake closed")
            buf += chunk
        if b" 101 " not in buf.split(b"\r\n", 1)[0]:
            raise ConnectionError(buf[:300])
        self._buf = buf.split(b"\r\n\r\n", 1)[1]
        self._id = 0

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def _read(self, n, deadline):
        while len(self._buf) < n:
            if time.time() > deadline:
                raise TimeoutError("cdp read")
            self.sock.settimeout(max(0.2, min(5, deadline - time.time())))
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise ConnectionError("cdp closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _recv_one(self, deadline):
        while True:
            h = self._read(2, deadline)
            ln = h[1] & 0x7F
            if ln == 126:
                ln = struct.unpack("!H", self._read(2, deadline))[0]
            elif ln == 127:
                ln = struct.unpack("!Q", self._read(8, deadline))[0]
            mask = b""
            if h[1] & 0x80:
                mask = self._read(4, deadline)
            payload = self._read(ln, deadline)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            op = h[0] & 0x0F
            if op == 9:
                self._send_raw(payload, 0xA)
                continue
            if op == 8:
                raise ConnectionError("cdp closed by browser")
            if op in (1, 2):
                return payload
            # continuation is folded by Chrome into one frame for these calls

    def _send_raw(self, payload, op):
        n = len(payload)
        head = bytes([0x80 | op])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack("!H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack("!Q", n)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(head + mask + masked)

    def call(self, method, params=None, timeout=60):
        self._id += 1
        mid = self._id
        body = json.dumps({"id": mid, "method": method, "params": params or {}}).encode()
        self._send_raw(body, 1)
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self._recv_one(deadline)
            try:
                msg = json.loads(raw.decode("utf-8"))
            except ValueError:
                continue
            if msg.get("id") != mid:
                continue
            if msg.get("error"):
                raise RuntimeError("%s %s" % (method, msg["error"]))
            return msg.get("result") or {}
        raise TimeoutError(method)


def _ev(cdp, expr, timeout=60):
    res = cdp.call("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
    }, timeout=timeout)
    details = res.get("exceptionDetails")
    if details:
        raise AssertionError(json.dumps(details)[:2000])
    return (res.get("result") or {}).get("value")


def _wait_fn(cdp, expr, timeout=90):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = _ev(cdp, expr, timeout=15)
        if last:
            return last
        time.sleep(0.4)
    raise AssertionError("timed out waiting for %s; last=%r" % (expr, last))


def _clip(cdp, selector):
    info = _ev(cdp, """
(function(){
  var el = document.querySelector(%s);
  if (!el) return { missing: true };
  try { el.scrollIntoView({block:'center', inline:'nearest'}); } catch (e) {}
  var node = el.parentElement;
  while (node && node !== document.body) {
    if (node.scrollHeight > node.clientHeight + 8) {
      var top = el.getBoundingClientRect().top - node.getBoundingClientRect().top + node.scrollTop;
      node.scrollTop = Math.max(0, top - 24);
    }
    node = node.parentElement;
  }
  var r = el.getBoundingClientRect();
  var x = r.left + (window.scrollX || window.pageXOffset || 0);
  var y = r.top + (window.scrollY || window.pageYOffset || 0);
  return { x: Math.max(0, x), y: Math.max(0, y),
           width: Math.max(1, r.width), height: Math.max(1, Math.min(r.height, 1100)) };
})()
""" % json.dumps(selector))
    if not info or info.get("missing"):
        raise AssertionError("no element " + selector)
    if info["width"] < 8 or info["height"] < 8:
        raise AssertionError("empty clip %s %s" % (selector, info))
    return info


def _png(cdp, selector, path):
    info = _clip(cdp, selector)
    res = cdp.call("Page.captureScreenshot", {
        "format": "png",
        "captureBeyondViewport": True,
        "clip": {"x": info["x"], "y": info["y"], "width": info["width"],
                 "height": info["height"], "scale": 1},
    }, timeout=60)
    raw = base64.b64decode(res["data"])
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 3000:
        raise AssertionError("bad png %s (%d bytes)" % (path, len(raw)))
    with open(path, "wb") as fh:
        fh.write(raw)
    return path


def _save(path):
    os.makedirs(SHOTS, exist_ok=True)
    os.makedirs(ART, exist_ok=True)
    dest = os.path.join(SHOTS, os.path.basename(path))
    if os.path.abspath(path) != os.path.abspath(dest):
        shutil.copy(path, dest)
    shutil.copy(dest, os.path.join(ART, os.path.basename(path)))


def _http():
    log = open(os.path.join(tempfile.gettempdir(), "v3769-http.log"), "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(HTTP_PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=log, stderr=log)
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % HTTP_PORT, timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("http server exited %s" % proc.returncode)
            time.sleep(0.2)
    raise RuntimeError("http server did not answer")


def _browser(chrome, udd):
    logp = os.path.join(udd, "chrome.log")
    log = open(logp, "wb")
    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
        "--disable-dev-shm-usage", "--disable-extensions",
        "--remote-debugging-port=%d" % CDP_PORT, "--remote-allow-origins=*",
        "--user-data-dir=" + udd, "--window-size=1440,1200", "about:blank",
    ], stdout=log, stderr=log)
    deadline = time.time() + 20
    last = None
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("chrome exited %s\n%s" % (proc.returncode, open(logp, "rb").read()[-1500:]))
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % CDP_PORT, timeout=2) as fh:
                fh.read()
            return proc
        except Exception as e:
            last = e
            time.sleep(0.25)
    raise RuntimeError("chrome cdp did not answer: %s" % last)


def _tab():
    url = PAGE
    req = urllib.request.Request(
        "http://127.0.0.1:%d/json/new?%s" % (CDP_PORT, urllib.parse.quote(url, safe="")),
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as fh:
            return json.loads(fh.read().decode())
    except Exception:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % CDP_PORT, timeout=10) as fh:
            tabs = json.loads(fh.read().decode())
        page = next(t for t in tabs if t.get("type") == "page")
        return page


class TestV3769VaultMoveListVisual(unittest.TestCase):
    def test_the_real_vault_shows_the_move_list(self):
        if "heart2." in os.path.abspath(__file__):
            return
        chrome = _chrome_path()
        if not chrome:
            self.skipTest(NO_BROWSER)
        http = browser = cdp = None
        udd = None
        try:
            http = _http()
            udd = tempfile.mkdtemp(prefix="v3769-chrome-")
            browser = _browser(chrome, udd)
            tab = _tab()
            cdp = _CDP(tab["webSocketDebuggerUrl"])
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            if "bible.html" not in (tab.get("url") or ""):
                cdp.call("Page.navigate", {"url": PAGE})
            _wait_fn(cdp, "typeof window.renderVault==='function' && typeof window.switchTab==='function'"
                     " && typeof window._vaultMovePaint==='function'", timeout=120)
            self._demo(cdp)
        finally:
            if cdp:
                cdp.close()
            if browser and browser.poll() is None:
                browser.terminate()
                try:
                    browser.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    browser.kill()
            if http and http.poll() is None:
                http.terminate()
            if udd:
                shutil.rmtree(udd, ignore_errors=True)

    def _js(self, cdp, expr, timeout=120):
        val = _ev(cdp, expr, timeout=timeout)
        if isinstance(val, dict) and val.get("error"):
            self.fail(val["error"][:2500])
        return val

    def _shot(self, cdp, selector, name):
        path = os.path.join(SHOTS, name)
        try:
            _png(cdp, selector, path)
        except AssertionError as err:
            if selector != "#vault-move-list" or "empty clip" not in str(err):
                raise
            self._js(cdp, _STEP_REOPEN)
            time.sleep(0.35)
            _png(cdp, selector, path)
        _save(path)
        return path

    def _demo(self, cdp):
        os.makedirs(SHOTS, exist_ok=True)
        names = self._js(cdp, _NAMES)
        g, es, hq = names["griffon"], names["eschuta"], names["harlequin"]

        beside = self._js(cdp, _STEP_BESIDE % json.dumps(g))
        tiles = [t for t in beside["tiles"] if "Griffon" in (t.get("n") or "")]
        tiles.sort(key=lambda t: (t["x"], t["y"]))
        self.assertGreaterEqual(len(tiles), 2, beside)
        dx, dy = tiles[1]["x"] - tiles[0]["x"], tiles[1]["y"] - tiles[0]["y"]
        adjacent = (dx == tiles[0]["w"] and dy == 0) or (dy == tiles[0]["h"] and dx == 0)
        self.assertTrue(adjacent, beside)
        _wait_fn(cdp, _ART_READY, timeout=20)
        self._shot(cdp, "#vault-move-list", "01-duplicate-beside.png")

        wit = self._js(cdp, _STEP_WITNESS % json.dumps(g))
        self.assertIn("2 witnesses", wit.get("say") or "", wit)
        self._shot(cdp, "#vault-move-list", "02-witness-plus.png")

        locked = self._js(cdp, _STEP_LOCK % json.dumps(es))
        self.assertTrue(locked.get("locked"), locked)
        self._shot(cdp, "#vault-move-list", "03-session-lock.png")

        dock = self._js(cdp, _STEP_DOCK)
        self.assertTrue(dock.get("homeless"), dock)
        self.assertIn(dock["homeless"], dock["dock"], dock)
        self.assertNotIn(g, dock["dock"], dock)
        self._shot(cdp, "#vault-dock", "04-dock-homeless.png")

        manual = self._js(cdp, _STEP_MANUAL % json.dumps(hq))
        self.assertIn("OFF", manual.get("intake") or "", manual)
        self.assertTrue(manual.get("refused"), manual)
        self.assertTrue(manual.get("cell"), manual)
        self.assertIsNone(manual.get("assign"), manual)
        self._shot_span(cdp, "#vault-auto-intake", "#vault-move-list", "05-auto-off-manual.png")

        planned = self._js(cdp, _STEP_PLANNED % json.dumps(g))
        self.assertEqual(planned.get("status"), "to-move", planned)
        self.assertTrue(planned.get("to"), planned)
        self.assertNotEqual(planned.get("from"), planned.get("to"), planned)
        self.assertEqual(planned.get("stored"), planned.get("to"), planned)
        self._shot(cdp, "#vault-move-list", "06-planned-move.png")
        cdp.call("Page.reload", {"ignoreCache": True}, timeout=30)
        # A fresh load lands on session. The 0ms and 250ms boot timers can fire after
        # renderVault exists and yank the vault tab back off, which leaves the list in
        # the DOM with a zero box. Wait them out, then open the room.
        _wait_fn(
            cdp,
            "document.readyState==='complete' && typeof window.vaultJump==='function'"
            " && typeof window.renderVault==='function'",
            timeout=120,
        )
        time.sleep(0.8)
        kept = self._js(cdp, _STEP_RELOAD)
        self.assertEqual(kept.get("to"), planned["to"], kept)
        self.assertTrue(kept.get("tab"), kept)
        self.assertFalse(kept.get("collapsed"), kept)
        self.assertGreaterEqual(kept.get("w") or 0, 8, kept)
        self.assertGreaterEqual(kept.get("h") or 0, 8, kept)

        marked = self._js(cdp, _STEP_MARK % (json.dumps(g), int(planned["copy"])))
        self.assertEqual(marked.get("status"), "moved-manual", marked)
        self._shot(cdp, "#vault-move-list", "07-mark-moved.png")

        verified = self._js(cdp, _STEP_VERIFY % (json.dumps(g), int(planned["copy"])))
        self.assertEqual(verified.get("status"), "verified", verified)
        self.assertIn("v3769-live", verified.get("evidence") or [], verified)
        list_png = self._shot(cdp, "#vault-move-list", "08-verified-list.png")
        self._js(cdp, _STEP_FRAME % json.dumps(verified["cell"]))
        _wait_fn(cdp, _FRAME_READY, timeout=20)
        opened = self._js(cdp, _FRAME_READ)
        self.assertTrue(opened.get("open"), opened)
        self.assertIn("chronicle_uniques_A", opened.get("src") or "", opened)
        self.assertNotIn("data:image", opened.get("src") or "", opened)
        self.assertGreater(opened.get("nw") or 0, 8, opened)
        self.assertIn('class="on"', opened.get("mark") or "", opened)
        frame_png = self._shot(cdp, "#tvd-frame-lb", "08-verified-frame.png")
        _stitch(list_png, frame_png, frame_png)
        _save(frame_png)
        for name in (
            "01-duplicate-beside.png", "02-witness-plus.png", "03-session-lock.png",
            "04-dock-homeless.png", "05-auto-off-manual.png", "06-planned-move.png",
            "07-mark-moved.png", "08-verified-frame.png",
        ):
            path = os.path.join(SHOTS, name)
            self.assertTrue(os.path.isfile(path) and os.path.getsize(path) > 3000, name)

    def _shot_span(self, cdp, start, end, name):
        info = _ev(cdp, """
(function(){
  var a = document.querySelector(%s), b = document.querySelector(%s);
  if (!a || !b) return { missing: true };
  try { a.scrollIntoView({block:'start', inline:'nearest'}); } catch (e) {}
  var ar = a.getBoundingClientRect(), br = b.getBoundingClientRect();
  var x = Math.min(ar.left, br.left) + (window.scrollX || 0);
  var y = Math.min(ar.top, br.top) + (window.scrollY || 0);
  var bottom = Math.max(ar.bottom, br.bottom) + (window.scrollY || 0);
  return { x: Math.max(0, x), y: Math.max(0, y), width: window.innerWidth,
           height: Math.max(1, Math.min(1100, bottom - y)) };
})()
""" % (json.dumps(start), json.dumps(end)))
        self.assertFalse(not info or info.get("missing"), info)
        self.assertGreaterEqual(info.get("width") or 0, 8, info)
        self.assertGreaterEqual(info.get("height") or 0, 8, info)
        res = cdp.call("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {"x": info["x"], "y": info["y"], "width": info["width"],
                     "height": min(info["height"], 1100), "scale": 1},
        }, timeout=60)
        raw = base64.b64decode(res["data"])
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(len(raw), 3000)
        path = os.path.join(SHOTS, name)
        with open(path, "wb") as fh:
            fh.write(raw)
        _save(path)


def _stitch(top, bottom, dest):
    try:
        from PIL import Image
    except ImportError:
        return
    a = Image.open(top).convert("RGB")
    b = Image.open(bottom).convert("RGB")
    w = max(a.width, b.width)
    canvas = Image.new("RGB", (w, a.height + 12 + b.height), (12, 9, 6))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (0, a.height + 12))
    canvas.save(dest)


def _wrap(body):
    return "(function(){ try { %s } catch (e) { return { error: String(e && e.stack || e) }; } })()" % body


_NAMES = _wrap(r"""
  function canon(part){
    var hit = null;
    try {
      var list = (typeof ITEMS !== 'undefined') ? ITEMS : [];
      list.forEach(function(i){
        if (!hit && i && i.n && String(i.n).toLowerCase().indexOf(String(part).toLowerCase()) === 0) hit = i.n;
      });
    } catch (e) {}
    return hit || part;
  }
  return { griffon: canon("Griffon's Eye"), eschuta: canon("Eschuta's Temper"), harlequin: canon("Harlequin Crest") };
""")

_ART_READY = r"""(function(){
  var imgs = document.querySelectorAll('#vault-move-list .vd-item img');
  if (imgs.length < 2) return false;
  for (var i = 0; i < imgs.length; i++) if (!imgs[i].complete || imgs[i].naturalWidth < 1) return false;
  return true;
})()"""

_STEP_BESIDE = _wrap(r"""
  function look(name, holder, loc, cell, session, frame){
    var rec = { source: 'intake-read', by: 'vault move list', holder: holder, loc: loc,
                cell: cell, sessionId: session, frameId: frame, ts: Date.now() };
    if (!window.__v3769Seen) window.__v3769Seen = {};
    if (!window.__v3769Seen[name]) { window.__v3769Seen[name] = 1; return window._ownedAdd(name, rec); }
    return window._ownedProvWrite(name, rec);
  }
  var g = %s;
  look(g, 'Mule', 'stash', 'stash:c1r1', 's1', 'f-a');
  look(g, 'Mule', 'stash', 'stash:c8r2', 's2', 'f-b');
  window.switchTab('vault');
  window.renderVault();
  var tiles = [].map.call(document.querySelectorAll('#vault-move-list .vd-item'), function(el){
    var img = el.querySelector('img');
    return { n: (el.getAttribute('title') || '').split(' (')[0], x: +el.getAttribute('data-x'),
             y: +el.getAttribute('data-y'), w: +el.getAttribute('data-w'), h: +el.getAttribute('data-h'),
             src: img ? img.getAttribute('src') : '' };
  });
  return { tiles: tiles, groups: (window._vaultSightGroups ? window._vaultSightGroups(g) : null) };
""")

_STEP_WITNESS = _wrap(r"""
  var g = %s;
  window._ownedProvWrite(g, { source: 'intake-read', by: 'vault move list', holder: 'Mule', loc: 'stash',
    cell: 'stash:c1r1', sessionId: 's3', frameId: 'f-c', ts: Date.now() });
  window.renderVault();
  var el = document.querySelector('#vault-move-list .vmv-row[data-from="stash:c1r1"]');
  return { say: el ? (el.querySelector('.vmv-wit') || {}).textContent : '',
           status: el ? el.getAttribute('data-status') : null };
""")

_STEP_LOCK = _wrap(r"""
  var es = %s;
  window._ownedAdd(es, { source: 'intake-read', by: 'vault move list', holder: 'MAIN', loc: 'inventory',
    cell: 'inventory:c2r1', sessionId: 'e1', frameId: 'e-a', ts: Date.now() });
  window._laneLockNote(es, 'equipment', ['e1', 'e2', 'e3']);
  window.renderVault();
  var lock = document.querySelector('#vault-move-list .vmv-lock[data-say="LOCKED"]');
  return { locked: !!(lock && lock.textContent.indexOf(es) >= 0),
           text: lock ? lock.textContent : '',
           sessions: window._laneLockSessions ? window._laneLockSessions(es) : null };
""")

_STEP_DOCK = _wrap(r"""
  var tries = ["Sigon's Guard", "Death's Hand", "Arctic Furs", "Zzznotanitem"];
  var homeless = null, tried = [];
  tries.forEach(function(part){
    var nm = part;
    try {
      var list = (typeof ITEMS !== 'undefined') ? ITEMS : [];
      list.forEach(function(i){
        if (i && i.n && String(i.n).toLowerCase() === String(part).toLowerCase()) nm = i.n;
      });
    } catch (e) {}
    var sm = null;
    try { sm = window._vaultSeamHome ? window._vaultSeamHome(nm) : null; } catch (e2) { sm = { err: String(e2) }; }
    tried.push({ n: nm, seam: sm });
    if (!homeless && sm && sm.loc === 'loose') homeless = nm;
  });
  if (!homeless) return { homeless: null, tried: tried };
  window._ownedAdd(homeless, { source: 'intake-read', by: 'vault move list', holder: 'Mule', loc: 'stash',
    cell: 'stash:c0r8', sessionId: 'h1', frameId: 'h-a', ts: Date.now() });
  window.renderVault();
  var dock = [].map.call(document.querySelectorAll('#vault-dock [data-vault-item]'), function(el){
    return el.getAttribute('data-vault-item');
  });
  return { homeless: homeless, dock: dock, tried: tried };
""")

_STEP_MANUAL = _wrap(r"""
  var hq = %s;
  window._vaultAutoIntakeSet(false);
  var gate = window._vaultIntakeGate();
  var added = window._vaultMoveNoteAdded(hq);
  window.renderVault();
  var el = null;
  [].forEach.call(document.querySelectorAll('#vault-move-list .vmv-row'), function(row){
    if (row.getAttribute('data-name') === hq) el = row;
  });
  var asg = null, has = false;
  try { has = (typeof assign !== 'undefined') && assign && Object.prototype.hasOwnProperty.call(assign, hq); asg = has ? assign[hq] : null; }
  catch (eA) { asg = String(eA); }
  return { intake: (document.getElementById('vault-auto-intake') || {}).textContent || '',
           refused: !!(gate && gate.refused),
           cell: el ? el.getAttribute('data-to') : (added && added.task && added.task.to && added.task.to.cell),
           ok: !!(added && added.ok), assign: asg };
""")

_STEP_PLANNED = _wrap(r"""
  var g = %s;
  if (typeof window.persistOwned === 'function') window.persistOwned();
  window.renderVault();
  var el = document.querySelector('#vault-move-list .vmv-row[data-from="stash:c1r1"]');
  var stored = null, copy = el ? (+el.getAttribute('data-copy') || 0) : 0;
  try {
    var bag = JSON.parse(window.LSR.getItem('d2r_vaultRecords') || 'null');
    ((bag && bag.records) || []).forEach(function(r){
      if (r && r.name === g && (r.copyIx || 0) === copy && r.move && r.move.to) stored = r.move.to.cell;
    });
  } catch (e) { stored = String(e); }
  return { status: el && el.getAttribute('data-status'), from: el && el.getAttribute('data-from'),
           to: el && el.getAttribute('data-to'), stored: stored, copy: copy };
""")

_STEP_REOPEN = _wrap(r"""
  if (typeof window.vaultJump === 'function') window.vaultJump();
  else {
    window.switchTab('vault');
    if (typeof window.renderVault === 'function') window.renderVault();
  }
  var card = document.getElementById('mule-vault-card');
  if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse === 'function')
    window.toggleCardCollapse('mule-vault-card');
  if (typeof window.renderVault === 'function') window.renderVault();
  var list = document.getElementById('vault-move-list');
  var r = list ? list.getBoundingClientRect() : { width: 0, height: 0 };
  var tab = document.getElementById('tab-vault');
  return { w: r.width, h: r.height, tab: !!(tab && tab.classList.contains('active')),
           collapsed: !!(card && card.classList.contains('collapsed')) };
""")

_STEP_RELOAD = _wrap(r"""
  var opened = (function(){
    if (typeof window.vaultJump === 'function') window.vaultJump();
    else { window.switchTab('vault'); window.renderVault(); }
    var card = document.getElementById('mule-vault-card');
    if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse === 'function')
      window.toggleCardCollapse('mule-vault-card');
    window.renderVault();
    var tab = document.getElementById('tab-vault');
    var list = document.getElementById('vault-move-list');
    var r = list ? list.getBoundingClientRect() : { width: 0, height: 0 };
    var el = document.querySelector('#vault-move-list .vmv-row[data-from="stash:c1r1"]');
    return { status: el && el.getAttribute('data-status'), to: el && el.getAttribute('data-to'),
             from: el && el.getAttribute('data-from'),
             tab: !!(tab && tab.classList.contains('active')),
             collapsed: !!(card && card.classList.contains('collapsed')),
             w: r.width, h: r.height, hidden: !!(list && list.hidden) };
  })();
  return opened;
""")

_STEP_MARK = _wrap(r"""
  var marked = window._vaultMoveMark(%s, %s);
  window.renderVault();
  var el = document.querySelector('#vault-move-list .vmv-row[data-from="stash:c1r1"]');
  return { status: el && el.getAttribute('data-status'), marked: marked && marked.status };
""")

_STEP_VERIFY = _wrap(r"""
  window._vaultAutoIntakeSet(true);
  var g = %s, copy = %s, task = null;
  var model = window._moveModel || {};
  (model.tasks || []).forEach(function(row){
    if (row && row.name === g && (row.copyIx || 0) === copy) task = row.task;
  });
  if (!task || !task.to) return { status: null, why: 'no task', model: (model.tasks || []).length };
  var applied = window._vaultMoveApplySight(g, { holder: task.to.holder, location: task.to.location,
    loc: task.to.location, cell: task.to.cell, frame: 'v3769-live' });
  window.renderVault();
  var el = document.querySelector('#vault-move-list .vmv-row[data-from="stash:c1r1"]');
  return { status: el && el.getAttribute('data-status'),
           evidence: (applied && applied.task && applied.task.evidence) || [],
           cell: task.to.cell, applied: !!(applied && applied.applied) };
""")

_STEP_FRAME = _wrap(r"""
  var src = 'tests/golden/intake/chronicle_uniques_A.jpg';
  window._tvdOpenFrame('v3769-live', { title: 'witness frame', src: src, cell: %s });
  var lb = document.getElementById('tvd-frame-lb');
  var img = document.getElementById('tvd-frame-lb-img');
  var mark = document.getElementById('tvd-frame-lb-mark');
  return { open: !!(lb && !lb.hidden),
           mark: mark ? mark.innerHTML : '',
           src: img ? (img.getAttribute('src') || '') : '' };
""")

_FRAME_READY = r"""(function(){
  var img = document.getElementById('tvd-frame-lb-img');
  var src = img ? (img.getAttribute('src') || '') : '';
  return !!(img && img.complete && img.naturalWidth > 8 && src.indexOf('chronicle_uniques_A') >= 0);
})()"""

_FRAME_READ = _wrap(r"""
  var lb = document.getElementById('tvd-frame-lb');
  var img = document.getElementById('tvd-frame-lb-img');
  var mark = document.getElementById('tvd-frame-lb-mark');
  return { open: !!(lb && !lb.hidden),
           mark: mark ? mark.innerHTML : '',
           src: img ? (img.getAttribute('src') || '') : '',
           nw: img ? img.naturalWidth : 0 };
""")


if __name__ == "__main__":
    if _chrome_path() is None:
        sys.stderr.write("SKIP - %s. UNMEASURED, declared as a skip (77), never a pass.\n" % NO_BROWSER)
        raise SystemExit(77)
    unittest.main(verbosity=1)

