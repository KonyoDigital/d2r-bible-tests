#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE WHOLE PAGE IN NODE - every inline <script> of bible.html, run in order over a small DOM and storage stand-in.

V1c (#152 item 4, #111 item 6). The vault laws before this one cut a few functions out of the page and stubbed the
rest (cb_node_harness, the vault L1 cuts). A hand add is not a few functions: it walks the owned door, the router,
the move planner, the records, the dock and the paint, and its cost lives in how often each of them asks the others.
That can only be measured on the page as it ships, so this runs ALL of it:

  * every inline script, in page order, in ONE global world (as a browser does: a script that throws stops only
    itself, and its error is reported, never swallowed);
  * a document whose getElementById answers the ids the page's markup carries and the ids its own innerHTML writes;
  * localStorage / sessionStorage in memory, starting EMPTY (a fresh install - never his stores);
  * no network: fetch, XMLHttpRequest, WebSocket, EventSource and sendBeacon are inert, so nothing here can reach
    his live console or any other host;
  * timers queued, run only when the body calls H.flush() (a deferred paint runs; a poll never does);
  * optional fixed clock and seeded randomness, so two runs of one body can be compared byte for byte.

The body runs after DOMContentLoaded and load. It sees the page's globals, H (RAW, flush, now, ls counters) and OUT,
and OUT is what run() returns. A PRELUDE runs before the first page script (a law sets up its counters there). PATCHES are exact find/replace pairs applied to the page source before it runs (a law
uses them to count calls); each must match exactly as often as it says, or the run fails naming the anchor that moved.

The program travels on STDIN (#242: never on argv). Node is resolved by cb_node_harness.node_path (env, PATH, then
the known install locations). Nothing is written to disk.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from cb_node_harness import node_path  # noqa: E402  (one resolver for every node law)

NODE = node_path()
BIBLE = os.path.join(ROOT, "bible.html")

HARNESS_JS = r"""
'use strict';
const fs = require('fs');
const vm = require('vm');
const CFG = __CFG;
let src = fs.readFileSync(CFG.bible, 'utf8').replace(/\r\n/g, '\n');
(CFG.patches || []).forEach(function (p) {
  const find = p[0], repl = p[1], want = (p.length > 2 && p[2] != null) ? p[2] : 1;
  const n = src.split(find).length - 1;
  if (n !== want) throw new Error('PATCH ANCHOR MOVED: ' + JSON.stringify(find.slice(0, 80)) + ' matched ' + n + ' times, not ' + want);
  src = src.split(find).join(repl);
});

/* ---- the scripts, the JSON blocks and the ids the markup carries ---- */
const scripts = [], jsonById = {};
let stripped = '';
{
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let m, last = 0, line = 1, at = 0;
  while ((m = re.exec(src))) {
    stripped += src.slice(last, m.index);
    last = re.lastIndex;
    const attrs = m[1] || '';
    const idm = /\bid\s*=\s*"([^"]+)"/.exec(attrs);
    const typem = /\btype\s*=\s*"([^"]+)"/.exec(attrs);
    const type = typem ? typem[1].toLowerCase() : '';
    if (/\bsrc\s*=/.test(attrs)) continue;
    if (type && type !== 'text/javascript' && type !== 'module' && type !== 'application/javascript') {
      if (idm) jsonById[idm[1]] = m[2];
      continue;
    }
    for (; at < m.index; at++) if (src.charCodeAt(at) === 10) line++;
    scripts.push({ id: idm ? idm[1] : null, code: m[2], line: line });
  }
  stripped += src.slice(last);
}
const STATIC_IDS = new Set();
{ const re = /\bid\s*=\s*"([^"]+)"/g; let m; while ((m = re.exec(stripped))) STATIC_IDS.add(m[1]); }

/* ---- storage: in memory, empty at boot ---- */
const RAW = new Map();
const LS_COUNT = { get: 0, set: 0, byKeyGet: {}, byKeySet: {} };
const localStorage = {
  getItem(k) { k = String(k); LS_COUNT.get++; LS_COUNT.byKeyGet[k] = (LS_COUNT.byKeyGet[k] || 0) + 1; return RAW.has(k) ? RAW.get(k) : null; },
  setItem(k, v) { k = String(k); LS_COUNT.set++; LS_COUNT.byKeySet[k] = (LS_COUNT.byKeySet[k] || 0) + 1; RAW.set(k, String(v)); },
  removeItem(k) { RAW.delete(String(k)); },
  key(i) { const ks = Array.from(RAW.keys()); return i < ks.length ? ks[i] : null; },
  clear() { RAW.clear(); },
  get length() { return RAW.size; }
};

/* ---- timers: queued; H.flush runs the short ones ---- */
let timerSeq = 1;
const timers = new Map();
function addTimer(fn, ms, args) { const id = timerSeq++; if (typeof fn === 'function') timers.set(id, { fn: fn, ms: +ms || 0, args: args || [] }); return id; }

/* ---- the document ---- */
const ELS = new Map();
function classList() {
  const c = new Set();
  return { add(...x) { x.forEach(v => c.add(v)); }, remove(...x) { x.forEach(v => c.delete(v)); }, contains(x) { return c.has(x); },
    toggle(x, on) { if (on === undefined) on = !c.has(x); if (on) c.add(x); else c.delete(x); return on; },
    get length() { return c.size; }, item(i) { return Array.from(c)[i] || null; }, forEach(f) { Array.from(c).forEach(f); },
    get value() { return Array.from(c).join(' '); } };
}
function styleObj() { const s = {}; s.setProperty = function (k, v) { s[k] = v; }; s.removeProperty = function (k) { delete s[k]; }; s.getPropertyValue = function (k) { return s[k] || ''; }; return s; }
class El {
  constructor(tag, id) {
    this.tagName = String(tag || 'div').toUpperCase(); this.nodeName = this.tagName; this.nodeType = 1;
    this._id = id || ''; this.hidden = false; this.attrs = {}; this._html = ''; this._text = '';
    this.style = styleObj(); this.classList = classList(); this.dataset = {}; this.children = []; this.childNodes = this.children;
    this.parentNode = null; this.parentElement = null; this.value = ''; this.checked = false; this.disabled = false;
    this.scrollTop = 0; this.scrollLeft = 0; this.scrollHeight = 0; this.scrollWidth = 0; this.clientWidth = 0; this.clientHeight = 0;
    this.offsetWidth = 0; this.offsetHeight = 0; this.offsetTop = 0; this.offsetLeft = 0; this.offsetParent = null;
    this.title = ''; this.className = ''; this.src = ''; this.href = ''; this.type = ''; this.name = ''; this.open = false;
    this.files = []; this.options = []; this.selectedIndex = -1; this.ownerDocument = null;
  }
  get id() { return this._id; }
  set id(v) { this._id = String(v); if (v) ELS.set(String(v), this); }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'id') this.id = v; if (k === 'class') this.className = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : (k === 'id' ? (this._id || null) : null); }
  hasAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k); }
  removeAttribute(k) { delete this.attrs[k]; }
  toggleAttribute(k, on) { if (on === undefined) on = !this.hasAttribute(k); if (on) this.attrs[k] = ''; else delete this.attrs[k]; return on; }
  querySelector(sel) { const m = /^#([\w\-:.]+)$/.exec(String(sel).trim()); return m ? (ELS.get(m[1]) || null) : null; }
  querySelectorAll() { return []; }
  getElementsByClassName() { return []; }
  getElementsByTagName() { return []; }
  closest() { return null; }
  matches() { return false; }
  contains(x) { return x === this; }
  appendChild(c) { if (c && typeof c === 'object') { this.children.push(c); c.parentNode = this; c.parentElement = this; } return c; }
  append(...cs) { cs.forEach(c => this.appendChild(c)); }
  prepend(...cs) { cs.forEach(c => this.appendChild(c)); }
  insertBefore(c) { return this.appendChild(c); }
  insertAdjacentHTML(pos, html) { this._html += String(html); registerIds(String(html), this); }
  insertAdjacentElement(pos, c) { return this.appendChild(c); }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); return c; }
  replaceChild(n, o) { this.removeChild(o); return this.appendChild(n); }
  replaceChildren(...cs) { this.children.length = 0; cs.forEach(c => this.appendChild(c)); }
  remove() { if (this.parentNode && this.parentNode.removeChild) this.parentNode.removeChild(this); if (this._id && ELS.get(this._id) === this) ELS.delete(this._id); }
  replaceWith() { this.remove(); }
  cloneNode() { const e = new El(this.tagName); e._html = this._html; return e; }
  addEventListener() {} removeEventListener() {} dispatchEvent() { return true; }
  getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0, x: 0, y: 0 }; }
  getClientRects() { return []; }
  focus() {} blur() {} click() {} select() {} scrollIntoView() {} scrollTo() {} scrollBy() {} showModal() {} close() {}
  setSelectionRange() {} animate() { return { finished: Promise.resolve(), cancel() {}, onfinish: null }; }
  requestFullscreen() { return Promise.resolve(); }
  getContext() { return null; }
  get firstChild() { return this.children[0] || null; }
  get firstElementChild() { return this.children[0] || null; }
  get lastChild() { return this.children[this.children.length - 1] || null; }
  get lastElementChild() { return this.lastChild; }
  get nextSibling() { return null; } get previousSibling() { return null; }
  get nextElementSibling() { return null; } get previousElementSibling() { return null; }
  get childElementCount() { return this.children.length; }
  get isConnected() { return true; }
  get innerHTML() { return this._html; }
  set innerHTML(v) { this._html = String(v); this.children.length = 0; registerIds(this._html, this); }
  get outerHTML() { return '<' + this.tagName.toLowerCase() + '>' + this._html + '</' + this.tagName.toLowerCase() + '>'; }
  set outerHTML(v) { registerIds(String(v), this.parentNode || this); }
  get textContent() { return this._text || this._html.replace(/<[^>]*>/g, ''); }
  set textContent(v) { this._text = String(v); this._html = ''; this.children.length = 0; }
  get innerText() { return this.textContent; }
  set innerText(v) { this.textContent = v; }
}
function registerIds(html, parent) {
  const re = /\bid\s*=\s*"([^"]+)"/g; let m;
  while ((m = re.exec(html))) { const e = new El('div'); e._id = m[1]; e.parentNode = parent; e.parentElement = parent; ELS.set(m[1], e); }
}
const listeners = { window: {}, document: {} };
function on(bucket, t, f) { (listeners[bucket][t] = listeners[bucket][t] || []).push(f); }
const document = {
  nodeType: 9, readyState: 'loading', title: 'D2R', cookie: '', referrer: '', hidden: false, visibilityState: 'visible',
  body: new El('body', 'body'), documentElement: new El('html'), head: new El('head'), activeElement: null,
  getElementById(id) {
    id = String(id);
    if (ELS.has(id)) return ELS.get(id);
    if (Object.prototype.hasOwnProperty.call(jsonById, id)) { const e = new El('script'); e._id = id; e._text = jsonById[id]; ELS.set(id, e); return e; }
    if (STATIC_IDS.has(id)) { const e = new El('div'); e._id = id; ELS.set(id, e); return e; }
    return null;
  },
  createElement(t) { return new El(t); },
  createElementNS(ns, t) { return new El(t); },
  createTextNode(t) { const e = new El('#text'); e._text = String(t); return e; },
  createDocumentFragment() { return new El('#fragment'); },
  createTreeWalker() { return { nextNode() { return null; } }; },
  createRange() { return { selectNodeContents() {}, getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0 }; } }; },
  querySelector(sel) { const m = /^#([\w\-:.]+)$/.exec(String(sel).trim()); return m ? document.getElementById(m[1]) : null; },
  querySelectorAll() { return []; },
  getElementsByClassName() { return []; }, getElementsByTagName() { return []; }, getElementsByName() { return []; },
  addEventListener(t, f) { on('document', t, f); }, removeEventListener() {}, dispatchEvent() { return true; },
  execCommand() { return false; }, hasFocus() { return true; },
  fonts: { ready: Promise.resolve(), load() { return Promise.resolve([]); }, check() { return true; }, add() {} },
  getSelection() { return { removeAllRanges() {}, addRange() {}, toString() { return ''; } }; },
  elementFromPoint() { return null; }, elementsFromPoint() { return []; }
};
document.body.ownerDocument = document;
ELS.set('body', document.body);

/* ---- the global world (no network) ---- */
const G = globalThis;
G.window = G; G.self = G; G.top = G; G.parent = G; G.frames = G;
G.document = document;
Object.defineProperty(G, 'localStorage', { value: localStorage, configurable: true, writable: true });
Object.defineProperty(G, 'sessionStorage', { value: { getItem() { return null; }, setItem() {}, removeItem() {}, key() { return null; }, clear() {}, length: 0 }, configurable: true, writable: true });
G.location = { href: 'http://127.0.0.1/bible.html', search: '', hash: '', pathname: '/bible.html', hostname: '127.0.0.1', host: '127.0.0.1',
  protocol: 'http:', origin: 'http://127.0.0.1', port: '', reload() {}, replace() {}, assign() {} };
G.history = { replaceState() {}, pushState() {}, back() {}, state: null, length: 1 };
Object.defineProperty(G, 'navigator', { value: { userAgent: 'vault_page_node', language: 'en-US', languages: ['en-US'], platform: 'node', onLine: false,
  clipboard: { writeText() { return Promise.resolve(); }, readText() { return Promise.resolve(''); } }, sendBeacon() { return true; },
  hardwareConcurrency: 4, maxTouchPoints: 0, serviceWorker: undefined, storage: { estimate() { return Promise.resolve({}); }, persist() { return Promise.resolve(false); } } },
  configurable: true, writable: true });
G.screen = { width: 1440, height: 900, availWidth: 1440, availHeight: 900 };
G.innerWidth = 1440; G.innerHeight = 900; G.outerWidth = 1440; G.outerHeight = 900; G.devicePixelRatio = 2;
G.scrollX = 0; G.scrollY = 0; G.pageXOffset = 0; G.pageYOffset = 0;
G.scrollTo = function () {}; G.scrollBy = function () {}; G.print = function () {}; G.focus = function () {}; G.open = function () { return null; };
G.alert = function () {}; G.confirm = function () { return false; }; G.prompt = function () { return null; };
G.addEventListener = function (t, f) { on('window', t, f); };
G.removeEventListener = function () {}; G.dispatchEvent = function () { return true; };
G.getComputedStyle = function () { return { getPropertyValue() { return ''; }, display: 'block', visibility: 'visible' }; };
G.matchMedia = function () { return { matches: false, media: '', addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }; };
G.setTimeout = function (fn, ms, ...a) { return addTimer(fn, ms, a); };
G.clearTimeout = function (id) { timers.delete(id); };
G.setInterval = function () { return timerSeq++; };
G.clearInterval = function () {};
G.requestAnimationFrame = function (fn) { return addTimer(fn, 16, [0]); };
G.cancelAnimationFrame = function (id) { timers.delete(id); };
G.requestIdleCallback = function (fn) { return addTimer(fn, 50, [{ timeRemaining() { return 50; }, didTimeout: false }]); };
G.cancelIdleCallback = function (id) { timers.delete(id); };
G.fetch = function () { return new Promise(function () {}); };
G.XMLHttpRequest = function () { this.open = function () {}; this.send = function () {}; this.setRequestHeader = function () {}; this.abort = function () {}; this.addEventListener = function () {}; };
G.WebSocket = function () { this.send = function () {}; this.close = function () {}; this.addEventListener = function () {}; };
G.EventSource = function () { this.close = function () {}; this.addEventListener = function () {}; };
G.BroadcastChannel = function () { this.postMessage = function () {}; this.close = function () {}; this.addEventListener = function () {}; this.onmessage = null; };
G.MutationObserver = function () { this.observe = function () {}; this.disconnect = function () {}; this.takeRecords = function () { return []; }; };
G.ResizeObserver = function () { this.observe = function () {}; this.unobserve = function () {}; this.disconnect = function () {}; };
G.IntersectionObserver = function () { this.observe = function () {}; this.unobserve = function () {}; this.disconnect = function () {}; };
G.PerformanceObserver = function () { this.observe = function () {}; this.disconnect = function () {}; };
G.PerformanceObserver.supportedEntryTypes = [];
G.Image = function () { return new El('img'); };
G.Audio = function () { return { play() { return Promise.resolve(); }, pause() {}, addEventListener() {} }; };
G.DOMParser = function () { this.parseFromString = function () { return document; }; };
G.CustomEvent = function (t, o) { this.type = t; this.detail = o && o.detail; };
G.Event = G.Event || function (t) { this.type = t; };
G.KeyboardEvent = function (t, o) { this.type = t; Object.assign(this, o || {}); };
G.MouseEvent = function (t, o) { this.type = t; Object.assign(this, o || {}); };
G.HTMLElement = El; G.Element = El; G.Node = El; G.HTMLCanvasElement = El; G.HTMLInputElement = El; G.HTMLDocument = function () {};
G.Document = function () {};
G.CSS = { escape: function (s) { return String(s).replace(/[^\w-]/g, function (c) { return '\\' + c; }); }, supports() { return false; } };
G.getSelection = document.getSelection;
G.Notification = function () {}; G.Notification.permission = 'denied'; G.Notification.requestPermission = function () { return Promise.resolve('denied'); };
G.visualViewport = { width: 1440, height: 900, scale: 1, addEventListener() {}, removeEventListener() {} };
if (CFG.clock) {
  const T = Date.parse(CFG.clock), RealDate = Date;
  class FixedDate extends RealDate { constructor(...a) { if (a.length === 0) super(T); else super(...a); } static now() { return T; } }
  FixedDate.parse = RealDate.parse; FixedDate.UTC = RealDate.UTC;
  G.Date = FixedDate;
}
if (CFG.seed) {
  let seed = (+CFG.seed) >>> 0 || 1;
  Math.random = function () { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const hex = function (n) { let o = ''; while (o.length < n) o += Math.floor(Math.random() * 16).toString(16); return o; };
  Object.defineProperty(G, 'crypto', { value: { randomUUID: function () { const h = hex(32); return h.slice(0, 8) + '-' + h.slice(8, 12) + '-' + h.slice(12, 16) + '-' + h.slice(16, 20) + '-' + h.slice(20); },
    getRandomValues: function (a) { for (let i = 0; i < a.length; i++) a[i] = Math.floor(Math.random() * 256); return a; } }, configurable: true, writable: true });
}

/* the page's own console goes to stderr, so stdout carries only the one OUT line */
['log', 'info', 'warn', 'debug', 'trace', 'table', 'group', 'groupEnd', 'groupCollapsed', 'dir'].forEach(function (k) {
  console[k] = function () { try { process.stderr.write('[page] ' + Array.prototype.map.call(arguments, String).join(' ').slice(0, 300) + '\n'); } catch (e) {} };
});
const ERRS = [];
const H = {
  RAW: RAW, ls: LS_COUNT, ELS: ELS,
  flush(maxMs, rounds) {
    maxMs = maxMs == null ? 60 : maxMs; rounds = rounds || 3;
    let ran = 0;
    for (let r = 0; r < rounds; r++) {
      const due = Array.from(timers.entries()).filter(function (e) { return e[1].ms <= maxMs; });
      if (!due.length) break;
      due.forEach(function (e) { timers.delete(e[0]); });
      due.forEach(function (e) {
        try { e[1].fn.apply(G, e[1].args); } catch (x) { ERRS.push('timer: ' + String(x && x.message || x)); }
        ran++;
      });
    }
    return ran;
  },
  now() { return Number(process.hrtime.bigint()) / 1e6; },
  errors: ERRS
};
G.H = H;
const OUT = {};
G.OUT = OUT;

const BOOT = [];
if (__PRELUDE) vm.runInThisContext(__PRELUDE, { filename: 'law-prelude.js' });
scripts.forEach(function (s, i) {
  try { vm.runInThisContext(s.code, { filename: 'bible.html#script' + i + '@' + s.line }); }
  catch (e) { BOOT.push({ script: i, line: s.line, id: s.id, err: String(e && e.message || e).slice(0, 300) }); }
});
function fire(bucket, type) {
  (listeners[bucket][type] || []).slice().forEach(function (f) {
    try { f.call(bucket === 'window' ? G : document, { type: type, target: document, preventDefault() {}, stopPropagation() {} }); }
    catch (e) { ERRS.push(bucket + ':' + type + ': ' + String(e && e.message || e).slice(0, 200)); }
  });
}
document.readyState = 'interactive'; fire('document', 'DOMContentLoaded');
document.readyState = 'complete'; fire('window', 'load');
H.flush(60, 3);
OUT.__boot = { scripts: scripts.length, errors: BOOT, listenerErrors: ERRS.slice() };
ERRS.length = 0;
vm.runInThisContext(__BODY, { filename: 'law-body.js' });
process.stdout.write('\n__VAULT_PAGE_NODE_OUT__' + JSON.stringify(OUT) + '\n');
"""


def program(body, bible=None, patches=(), clock=None, seed=None, prelude=""):
    """The node program: config + prelude + body + harness, as ONE string for stdin. -> str"""
    cfg = {"bible": os.path.abspath(bible or BIBLE), "patches": [list(p) for p in (patches or ())],
           "clock": clock, "seed": seed}
    return ("var __CFG = " + json.dumps(cfg) + ";\nvar __PRELUDE = " + json.dumps(prelude or "") + ";\nvar __BODY = "
            + json.dumps(body) + ";\n" + HARNESS_JS)


def run(body, bible=None, patches=(), clock=None, seed=None, timeout=600, prelude=""):
    """Boot the whole page in node, run `body`, return the OUT it filled. -> dict

    A missing node raises (the caller decides whether that venue may skip); a crash, a timeout, an anchor that moved
    or output that is not JSON raises with node's own words. OUT['__boot'] carries every script that did not run."""
    if not NODE:
        raise FileNotFoundError("node is not on this machine")
    r = subprocess.run([NODE, "-"], input=program(body, bible, patches, clock, seed, prelude), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise AssertionError("the page did not run in node (exit %s): %s" % (r.returncode, (r.stderr or r.stdout)[-2500:]))
    mark = "__VAULT_PAGE_NODE_OUT__"
    lines = [ln[len(mark):] for ln in (r.stdout or "").splitlines() if ln.startswith(mark)]
    if len(lines) != 1:
        raise AssertionError("the page ran in node and did not print its one OUT line (%d): %s"
                             % (len(lines), ((r.stdout or "")[-500:] + (r.stderr or "")[-1000:])))
    return json.loads(lines[0])


if __name__ == "__main__":
    out = run("OUT.vault = typeof window.vaultHandAdd; OUT.render = typeof window.renderVault;")
    print(json.dumps(out, indent=1)[:2000])
