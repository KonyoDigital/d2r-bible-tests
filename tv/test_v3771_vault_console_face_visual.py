# -*- coding: utf-8 -*-
"""v3771 — the vault console face on the real vault tab.

Drives bible.html, not a sandbox. Item art sits in the packer's grid cells.
Photographs AUTO INTAKE off and on, the restyled move list, the unseen-location
group, and a duplicate beside its original. Scrolls the list into the MF / TZ /
quick-set bar and refuses the shot when that bar's box covers a row. A reload
keeps the same room. Chrome is resolved the same way as the v3769 screen.
No binary is a declared skip. Ports are scratch, never 17771 or 17772.
"""
import json
import os
import shutil
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

from test_v3769_vault_move_list_visual import (  # noqa: E402
    _CDP, _chrome_path, _ev, _png, _wait_fn, _wrap,
)

NO_BROWSER = "no Chrome/Chromium on this machine"

SHOTS = os.path.join(HERE, ".render_shots")
ART = "/opt/cursor/artifacts/v3771"
HTTP_PORT = 17981
CDP_PORT = 17982
PAGE = "http://127.0.0.1:%d/bible.html" % HTTP_PORT

SHOT_NAMES = (
    "01-auto-intake-off.png",
    "02-auto-intake-on.png",
    "03-restyled-move-list.png",
    "04-no-cover.png",
    "05-unknown-location.png",
    "06-duplicate-beside.png",
    "07-after-reload.png",
    "08-no-cover-landing.png",
    "09-no-cover-bottom.png",
    "10-no-cover-middle.png",
)


def _http():
    log = open(os.path.join(tempfile.gettempdir(), "v3771-http.log"), "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(HTTP_PORT), "--bind", "127.0.0.1"],
        cwd=ROOT, stdout=log, stderr=log)
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % HTTP_PORT, timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("http server exited %s" % proc.returncode)
            time.sleep(0.2)
    raise RuntimeError("http server did not answer on %s" % HTTP_PORT)


def _browser(chrome, udd):
    logp = os.path.join(udd, "chrome.log")
    log = open(logp, "wb")
    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
        "--disable-dev-shm-usage", "--disable-extensions",
        "--remote-debugging-port=%d" % CDP_PORT, "--remote-allow-origins=*",
        "--user-data-dir=" + udd, "--window-size=1440,1200", "about:blank",
    ], stdout=log, stderr=log)
    deadline = time.time() + 25
    last = None
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("chrome exited %s\n%s" % (
                proc.returncode, open(logp, "rb").read()[-1500:]))
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % CDP_PORT, timeout=2) as fh:
                fh.read()
            return proc
        except Exception as e:
            last = e
            time.sleep(0.25)
    raise RuntimeError("chrome cdp did not answer: %s" % last)


def _tab():
    req = urllib.request.Request(
        "http://127.0.0.1:%d/json/new?%s" % (CDP_PORT, urllib.parse.quote(PAGE, safe="")),
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=20) as fh:
            return json.loads(fh.read().decode())
    except Exception:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % CDP_PORT, timeout=10) as fh:
            tabs = json.loads(fh.read().decode())
        return next(t for t in tabs if t.get("type") == "page")


def _save(path):
    os.makedirs(SHOTS, exist_ok=True)
    os.makedirs(ART, exist_ok=True)
    dest = os.path.join(SHOTS, os.path.basename(path))
    if os.path.abspath(path) != os.path.abspath(dest):
        shutil.copy(path, dest)
    shutil.copy(dest, os.path.join(ART, os.path.basename(path)))


def _viewport(cdp, name):
    res = cdp.call("Page.captureScreenshot", {"format": "png"}, timeout=60)
    import base64
    raw = base64.b64decode(res["data"])
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 3000:
        raise AssertionError("bad png %s (%d bytes)" % (name, len(raw)))
    path = os.path.join(SHOTS, name)
    with open(path, "wb") as fh:
        fh.write(raw)
    _save(path)
    return path


class TestV3771VaultConsoleFaceVisual(unittest.TestCase):
    def test_the_real_vault_wears_the_console_and_clears_the_bar(self):
        if "heart2." in os.path.abspath(__file__):
            self.skipTest("heart2 sandbox does not launch a browser")
        chrome = _chrome_path()
        if not chrome:
            self.skipTest(NO_BROWSER)
        http = browser = cdp = None
        udd = None
        try:
            http = _http()
            udd = tempfile.mkdtemp(prefix="v3771-chrome-")
            browser = _browser(chrome, udd)
            tab = _tab()
            cdp = _CDP(tab["webSocketDebuggerUrl"])
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            if "bible.html" not in (tab.get("url") or ""):
                cdp.call("Page.navigate", {"url": PAGE})
            _wait_fn(cdp, "typeof window.vaultJump==='function' && typeof window.renderVault==='function'"
                     " && typeof window._vaultMoveCovered==='function'", timeout=120)
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
        if selector == "#v3771-beside":
            _png_beside(cdp, path)
        else:
            _png(cdp, selector, path)
        _save(path)
        return path

    def _shot_pad(self, cdp, selector, name):
        import base64
        info = _ev(cdp, """
(function(){
  var el = document.querySelector(%s);
  if (!el) return { missing: true };
  try { el.scrollIntoView({block:'center', inline:'nearest'}); } catch (e) {}
  var r = el.getBoundingClientRect();
  var x = Math.max(0, r.left - 24 + (window.scrollX || 0));
  var y = Math.max(0, r.top - 18 + (window.scrollY || 0));
  return { x: x, y: y, width: Math.max(320, r.width + 48), height: Math.max(72, r.height + 36) };
})()
""" % json.dumps(selector))
        self.assertFalse(not info or info.get("missing"), info)
        res = cdp.call("Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True,
            "clip": {"x": info["x"], "y": info["y"], "width": info["width"],
                     "height": info["height"], "scale": 1},
        }, timeout=60)
        raw = base64.b64decode(res["data"])
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(len(raw), 3000, len(raw))
        path = os.path.join(SHOTS, name)
        with open(path, "wb") as fh:
            fh.write(raw)
        _save(path)

    def _click(self, cdp, selector):
        box = self._js(cdp, _CLICK_BOX % json.dumps(selector))
        self.assertTrue(box and box.get("w", 0) >= 8 and box.get("h", 0) >= 8, box)
        clicked = self._js(cdp, "(function(){ var el = document.querySelector(%s); if (!el) return { missing: true }; el.click(); return { id: el.id || '', cls: el.className || '' }; })()" % json.dumps(selector))
        self.assertFalse(clicked.get("missing"), clicked)
        return box

    def _demo(self, cdp):
        os.makedirs(SHOTS, exist_ok=True)
        opened = self._js(cdp, _OPEN)
        self.assertTrue(opened.get("tab"), opened)
        self.assertGreaterEqual(opened.get("h") or 0, 8, opened)

        names = self._js(cdp, _NAMES)
        g, hq = names["griffon"], names["harlequin"]
        beside = self._js(cdp, _BESIDE % json.dumps(g))
        tiles = [t for t in beside["tiles"] if "Griffon" in (t.get("n") or "")]
        tiles.sort(key=lambda t: (t["x"], t["y"]))
        self.assertGreaterEqual(len(tiles), 2, beside)
        self.assertTrue(all(t.get("src") for t in tiles[:2]), beside)
        dx, dy = tiles[1]["x"] - tiles[0]["x"], tiles[1]["y"] - tiles[0]["y"]
        adjacent = (dx == tiles[0]["w"] and dy == 0) or (dy == tiles[0]["h"] and dx == 0)
        self.assertTrue(adjacent, beside)
        _wait_fn(cdp, _ART_READY, timeout=25)
        self.assertTrue(beside.get("tagged"), beside)
        self._shot(cdp, "#v3771-beside", "06-duplicate-beside.png")

        added = self._js(cdp, _TYPE % json.dumps(hq))
        self.assertTrue(added.get("shown"), added)
        self.assertTrue(added.get("manual"), added)  # v3773 Elad: MANUAL -> target cell
        unseen = self._js(cdp, _UNSEEN % json.dumps(hq))
        self.assertTrue(unseen.get("group"), unseen)
        self.assertIn("Location not seen yet", unseen.get("text") or "", unseen)
        self.assertIn("Take a screenshot", unseen.get("text") or "", unseen)
        self.assertNotIn("UNKNOWN · UNKNOWN", unseen.get("list") or "", unseen)
        self.assertEqual(unseen.get("last"), "Location not seen yet", unseen)
        self._shot(cdp, "#vault-move-list .vmv-unseen", "05-unknown-location.png")

        face = self._js(cdp, _FACE)
        for key in ("intake", "mark", "chip", "gh"):
            self.assertIn("Cinzel", face.get(key) or "", face)
        self.assertFalse(face.get("manual"), face)
        if face.get("dock"):
            self.assertIn("Cinzel", face["dock"], face)

        off = self._js(cdp, _INTAKE)
        self.assertEqual(off.get("state"), "off", off)
        self._shot_pad(cdp, "#vault-auto-intake", "01-auto-intake-off.png")
        self._click(cdp, "#vault-auto-intake")
        on = self._js(cdp, _INTAKE)
        self.assertEqual(on.get("state"), "on", on)
        self.assertIn("ON", on.get("text") or "", on)
        self._shot_pad(cdp, "#vault-auto-intake", "02-auto-intake-on.png")
        self._click(cdp, "#vault-auto-intake")
        off2 = self._js(cdp, _INTAKE)
        self.assertEqual(off2.get("state"), "off", off2)

        self._shot(cdp, "#vault-move-list", "03-restyled-move-list.png")
        self._cover(cdp, "landing", "04-no-cover.png")

        cdp.call("Page.reload", {"ignoreCache": True}, timeout=30)
        _wait_fn(
            cdp,
            "document.readyState==='complete' && typeof window.vaultJump==='function'"
            " && typeof window._vaultMoveCovered==='function'",
            timeout=120,
        )
        time.sleep(0.8)
        again = self._js(cdp, _REOPEN % json.dumps(hq))
        self.assertTrue(again.get("tab"), again)
        self.assertTrue(again.get("group"), again)
        self.assertGreaterEqual(len(again.get("griffon") or []), 2, again)
        _viewport(cdp, "07-after-reload.png")
        landed = self._cover(cdp, "landing", "08-no-cover-landing.png")
        self.assertEqual(landed.get("dockOpacity"), "0", landed)
        self._cover(cdp, "end", "09-no-cover-bottom.png")
        self._cover(cdp, "center", "10-no-cover-middle.png")

        for name in SHOT_NAMES:
            path = os.path.join(ART, name)
            self.assertTrue(os.path.isfile(path) and os.path.getsize(path) > 3000, path)

    def _cover(self, cdp, where, name):
        cover = self._js(cdp, _COVER_AT % json.dumps(where))
        self.assertIs(cover.get("covered"), False, cover)
        self.assertGreaterEqual(cover.get("samples") or 0, 4, cover)
        self.assertGreaterEqual(cover.get("visible") or 0, 8, cover)
        self.assertFalse(cover.get("painted"), cover)
        self.assertTrue(all(h.get("onBar") is False for h in (cover.get("hits") or [])), cover)
        self.assertEqual(cover.get("hintZ"), "20", cover)
        _viewport(cdp, name)
        return cover


def _stop(proc):
    if proc and proc.poll() is None:
        proc.terminate()


_OPEN = _wrap(r"""
  window.vaultJump();
  var card = document.getElementById('mule-vault-card');
  if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse === 'function')
    window.toggleCardCollapse('mule-vault-card');
  window.renderVault();
  var tab = document.getElementById('tab-vault');
  var list = document.getElementById('vault-move-list');
  var r = list ? list.getBoundingClientRect() : { width: 0, height: 0 };
  return { tab: !!(tab && tab.classList.contains('active')),
           attr: document.documentElement.getAttribute('data-active-tab'),
           w: r.width, h: r.height };
""")

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
  return { griffon: canon("Griffon's Eye"), harlequin: canon("Harlequin Crest") };
""")

def _png_beside(cdp, path):
    """Stamp the two-item grid in the same turn that measures it.

    A later vault paint replaces the move-list nodes, so an id set on an earlier
    turn is gone by the time the clip looks. The stamp and the measure share one
    evaluation.
    """
    import base64
    info = _ev(cdp, _STAMP_AND_CLIP, timeout=60)
    if isinstance(info, dict) and info.get("error"):
        raise AssertionError(info["error"][:2500])
    if not info or info.get("missing"):
        raise AssertionError("no element #v3771-beside %s" % (info,))
    if info["width"] < 8 or info["height"] < 8:
        raise AssertionError("empty clip #v3771-beside %s" % (info,))
    res = cdp.call("Page.captureScreenshot", {
        "format": "png", "captureBeyondViewport": True,
        "clip": {"x": info["x"], "y": info["y"], "width": info["width"],
                 "height": info["height"], "scale": 1},
    }, timeout=60)
    raw = base64.b64decode(res["data"])
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 3000:
        raise AssertionError("bad png %s (%d bytes)" % (path, len(raw)))
    with open(path, "wb") as fh:
        fh.write(raw)
    return path


_STAMP_AND_CLIP = r"""(function(){
  try {
    var host = document.getElementById('vault-move-list');
    [].forEach.call(document.querySelectorAll('#vault-move-list .vmv-grid'), function(grid){
      var n = grid.querySelectorAll('.vd-item').length;
      if (n >= 2 && !document.getElementById('v3771-beside')) grid.id = 'v3771-beside';
    });
    var el = document.getElementById('v3771-beside');
    if (!el) return { missing: true, grids: host ? host.querySelectorAll('.vmv-grid').length : 0,
                      items: host ? host.querySelectorAll('.vd-item').length : 0 };
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
             width: Math.max(1, r.width), height: Math.max(1, Math.min(r.height, 1100)),
             items: el.querySelectorAll('.vd-item').length };
  } catch (e) { return { error: String(e && e.stack || e) }; }
})()"""

_BESIDE = _wrap(r"""
  function look(name, holder, loc, cell, session, frame){
    var rec = { source: 'intake-read', by: 'vault console face', holder: holder, loc: loc,
                cell: cell, sessionId: session, frameId: frame, ts: Date.now() };
    if (!window.__v3771Seen) window.__v3771Seen = {};
    if (!window.__v3771Seen[name]) { window.__v3771Seen[name] = 1; return window._ownedAdd(name, rec); }
    return window._ownedProvWrite(name, rec);
  }
  var g = %s;
  look(g, 'Mule', 'stash', 'stash:c1r1', 's1', 'f-a');
  look(g, 'Mule', 'stash', 'stash:c8r2', 's2', 'f-b');
  window.renderVault();
  [].forEach.call(document.querySelectorAll('#vault-move-list .vmv-grid'), function(grid){
    var n = grid.querySelectorAll('.vd-item').length;
    if (n >= 2 && !document.getElementById('v3771-beside')) grid.id = 'v3771-beside';
  });
  var tiles = [].map.call(document.querySelectorAll('#vault-move-list .vd-item'), function(el){
    var img = el.querySelector('img');
    return { n: (el.getAttribute('title') || '').split(' (')[0], x: +el.getAttribute('data-x'),
             y: +el.getAttribute('data-y'), w: +el.getAttribute('data-w'), h: +el.getAttribute('data-h'),
             src: img ? (img.getAttribute('src') || '') : '' };
  });
  return { tiles: tiles, tagged: !!document.getElementById('v3771-beside') };
""")

_ART_READY = r"""(function(){
  var imgs = document.querySelectorAll('#vault-move-list .vd-item img');
  if (imgs.length < 2) return false;
  for (var i = 0; i < imgs.length; i++) if (!imgs[i].complete || imgs[i].naturalWidth < 1) return false;
  return true;
})()"""

_TYPE = _wrap(r"""
  var name = %s;
  if (typeof window._vaultAutoIntakeSet === 'function') window._vaultAutoIntakeSet(false);
  var added = (typeof window._vaultMoveNoteAdded === 'function') ? window._vaultMoveNoteAdded(name) : null;
  window.renderVault();
  return { shown: !!(added && added.shown), manual: !!(added && added.task && added.task.manual),
           ok: !!(added && added.ok), why: added && added.why };
""")

_CLICK_BOX = r"""(function(){
  var el = document.querySelector(%s);
  if (!el) return { missing: true };
  try { el.scrollIntoView({block:'center', inline:'nearest'}); } catch (e) {}
  var r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height };
})()"""

_UNSEEN = _wrap(r"""
  var name = %s;
  window.renderVault();
  var g = document.querySelector('#vault-move-list .vmv-unseen');
  var groups = [].map.call(document.querySelectorAll('#vault-move-list .vmv-group'), function(el){
    return el.getAttribute('data-holder');
  });
  var row = document.querySelector('#vault-move-list .vmv-row[data-name="' + name + '"]');
  return { group: !!(g && g.getAttribute('data-unseen') === '1'),
           text: g ? g.textContent : '',
           list: (document.getElementById('vault-move-list') || {}).textContent || '',
           last: groups.length ? groups[groups.length - 1] : null,
           groups: groups,
           row: row ? row.getAttribute('data-name') : null,
           from: row ? (row.querySelector('.vmv-place') || {}).textContent : '' };
""")

_FACE = _wrap(r"""
  function face(sel){
    var el = document.querySelector(sel);
    if (!el) return '';
    return (getComputedStyle(el).fontFamily || '');
  }
  return { intake: face('#vault-auto-intake'),
           mark: face('#vault-move-list .vmv-mark'),
           chip: face('#vault-move-list .vmv-chip'),
           gh: face('#vault-move-list .vmv-gh'),
           dock: face('.vdb-label'),
           manual: !!document.getElementById('vault-move-q') || !!document.querySelector('[onclick*="_vaultMoveAddOpen"]') };
""")

_INTAKE = _wrap(r"""
  var b = document.getElementById('vault-auto-intake');
  return { state: b ? b.getAttribute('data-state') : null, text: b ? b.textContent : '' };
""")

_COVER_AT = _wrap(r"""
  var mode = %s;
  var list = document.getElementById('vault-move-list');
  if (!list) return { covered: true, why: 'no list', samples: 0, visible: 0, painted: ['missing'], hits: [] };
  if (mode === 'end') { try { list.scrollIntoView({block:'end', inline:'nearest'}); } catch (e1) {} }
  else if (mode === 'center') { try { list.scrollIntoView({block:'center', inline:'nearest'}); } catch (e2) {} }
  else if (mode === 'start') { try { list.scrollIntoView({block:'start', inline:'nearest'}); } catch (e3) {} }
  var sh = document.getElementById('shortcut-hint');
  if (sh) sh.classList.add('show');
  var cover = window._vaultMoveCovered();
  cover.hintZ = sh ? getComputedStyle(sh).zIndex : null;
  return cover;
""")

_REOPEN = _wrap(r"""
  window.vaultJump();
  var card = document.getElementById('mule-vault-card');
  if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse === 'function')
    window.toggleCardCollapse('mule-vault-card');
  window.renderVault();
  var name = %s;
  var g = document.querySelector('#vault-move-list .vmv-unseen');
  var tab = document.getElementById('tab-vault');
  var griffon = [].map.call(document.querySelectorAll('#vault-move-list .vd-item'), function(el){
    return (el.getAttribute('title') || '').split(' (')[0];
  }).filter(function(n){ return n.indexOf('Griffon') >= 0; });
  return { tab: !!(tab && tab.classList.contains('active')),
           group: !!(g && g.getAttribute('data-unseen') === '1' && g.textContent.indexOf(name) >= 0),
           text: g ? g.textContent : '',
           griffon: griffon };
""")


if __name__ == "__main__":
    if _chrome_path() is None:
        sys.stderr.write("SKIP - %s. UNMEASURED, declared as a skip (77), never a pass.\n" % NO_BROWSER)
        raise SystemExit(0)
    unittest.main(verbosity=1)
