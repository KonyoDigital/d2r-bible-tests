# -*- coding: utf-8 -*-
"""v3773 — a click inside a tab lands while the page is still listening.

bible.html and control_ui.html are the documents this law reads. The vault used
to walk every element in the document, with getComputedStyle, on every vault
paint. That froze clicks for seconds. The move list grew its own typed
add-a-move control, which did not create a row. Rows come from placement. He
adds an item, which reads MANUAL -> target cell until a sighting fills the real
from-cell. He ticks a row off by hand.

The budget is a count, not a clock: getComputedStyle calls and whole-document
walks per tab switch and per vault repaint (v3771: ~28,000-40,000; the fix: 0).
Click p95 is printed as a report only, because a loaded box moves it.

RED_PROOF below. Every entry changes behaviour and a node or parser check
catches it inside the heart2 sandbox. The screen half launches Chrome only
outside a heart2 sandbox.
[[heart-first]] [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import json
import math
import os
import re
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

BIBLE = os.path.join(ROOT, "bible.html")
UI = os.path.join(HERE, "control_ui.html")
NODE = os.environ.get("NODE") or shutil.which("node")
NO_BROWSER = "no Chrome/Chromium on this machine"
NO_CHROME = {"flag": False}

TABS = [
    {"id": "vault", "control": "#vault-auto-intake", "search": "#vault-find-input"},
    {"id": "fsets", "control": "#tab-fsets .forge-tab, #tab-fsets button", "search": "#tab-fsets input"},
    {"id": "session", "control": "#sc-card-log button, #tab-session button", "search": "#tab-session input"},
    {"id": "forge", "control": "#tab-forge .forge-tab, #tab-forge button", "search": "#tab-forge input"},
    {"id": "funi", "control": "#tab-funi .forge-tab, #tab-funi button", "search": "#tab-funi input"},
    {"id": "crafts", "control": "#tab-crafts .forge-tab, #tab-crafts button", "search": "#tab-crafts input"},
    {"id": "d2jsp", "control": "#d2jsp-lamp", "search": "#d2jsp-find"},
    {"id": "tvd", "control": "#tvz-theatre-btn", "search": "#tab-tvd input"},
]

from input_latency import COUNT_BUDGET  # noqa: E402  (20 per tab switch / vault repaint)
MANUAL = (
    "vault-move-q",
    "_vaultMoveAddNamed",
    "_vaultMoveAddOpen",
    "Add a move",
    "ADD A MOVE",
    "Type an item, or select one",
)

BOOT = r"""
/* Counters first, before the page's own scripts: every getComputedStyle call and every
   whole-document walk ('*' selector, getElementsByTagName('*'), TreeWalker, NodeIterator). */
window.__cnt = {gcs: 0, star: 0};
(function(){
  function isStar(sel){ return /^\s*(?:html|body)?\s*\*\s*$/.test(String(sel)); }
  var gcs = window.getComputedStyle;
  window.__realGCS = gcs;
  window.getComputedStyle = function(){ window.__cnt.gcs++; return gcs.apply(window, arguments); };
  [Element.prototype, Document.prototype].forEach(function(P){
    var qsa = P.querySelectorAll, tag = P.getElementsByTagName;
    P.querySelectorAll = function(sel){ if (isStar(sel)) window.__cnt.star++; return qsa.call(this, sel); };
    P.getElementsByTagName = function(t){ if (String(t) === '*') window.__cnt.star++; return tag.call(this, t); };
  });
  var tw = Document.prototype.createTreeWalker, ni = Document.prototype.createNodeIterator;
  Document.prototype.createTreeWalker = function(){ window.__cnt.star++; return tw.apply(this, arguments); };
  Document.prototype.createNodeIterator = function(){ window.__cnt.star++; return ni.apply(this, arguments); };
})();
/* -> {"switch:<tab>": {gcs, star}, "renderVault": {gcs, star}}; synchronous work only */
window.__counts = function(tabs){
  var out = {};
  tabs.concat(['vault']).forEach(function(id, ix){
    window.__cnt.gcs = 0; window.__cnt.star = 0;
    if (typeof switchTab === 'function') switchTab(id);
    out['switch:' + id + ':' + ix] = {gcs: window.__cnt.gcs, star: window.__cnt.star};
  });
  for (var k = 0; k < 2; k++) {
    window.__cnt.gcs = 0; window.__cnt.star = 0;
    if (typeof renderVault === 'function') renderVault();
    out['renderVault:' + k] = {gcs: window.__cnt.gcs, star: window.__cnt.star};
  }
  return out;
};
window.__ltMax = null;
window.__ltOk = false;
try {
  if (typeof PerformanceObserver === 'function') {
    var po = new PerformanceObserver(function(list){
      list.getEntries().forEach(function(e){
        if (!e || typeof e.duration !== 'number') return;
        if (window.__ltMax == null || e.duration > window.__ltMax) window.__ltMax = e.duration;
      });
    });
    po.observe({entryTypes:['longtask']});
    window.__ltOk = true;
  }
} catch (eObs) { window.__ltOk = false; }
window.__probe = async function(tabs, samples, idleMs){
  idleMs = idleMs || 6000;
  function sleep(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
  function frames(){ return new Promise(function(r){ requestAnimationFrame(function(){ requestAnimationFrame(function(){ r(); }); }); }); }
  function visible(el){
    if (!el || !el.getBoundingClientRect) return false;
    var st = window.__realGCS(el);
    if (st.display === 'none' || st.visibility === 'hidden' || parseFloat(st.opacity) === 0) return false;
    var r = el.getBoundingClientRect();
    return r.width > 2 && r.height > 2;
  }
  function owned(el){
    var oc = (el.getAttribute && el.getAttribute('onclick')) || '';
    if (oc.indexOf('_chronShotPick') >= 0 || oc.indexOf('switchTab') >= 0) return false;
    if (el.type === 'file' || el.type === 'hidden') return false;
    return true;
  }
  function clearOf(el){
    var header = document.querySelector('.header');
    var hh = header ? header.getBoundingClientRect().height : 0;
    try { el.scrollIntoView({block:'center', inline:'nearest'}); } catch (eS) {}
    var r = el.getBoundingClientRect();
    if (r.top < hh + 4) window.scrollBy(0, r.top - hh - 12);
    r = el.getBoundingClientRect();
    var pts = [
      [r.left + r.width / 2, r.top + r.height / 2],
      [r.left + Math.min(8, r.width / 2), r.bottom - Math.min(6, r.height / 2)]
    ];
    for (var i = 0; i < pts.length; i++) {
      if (pts[i][0] < 0 || pts[i][1] < 0) continue;
      var top = document.elementFromPoint(pts[i][0], pts[i][1]);
      if (top === el || (el.contains && top && el.contains(top))) return false;
    }
    return true;
  }
  function pick(sel){
    if (!sel) return null;
    var list = document.querySelectorAll(sel);
    var fallback = null;
    for (var i = 0; i < list.length; i++) {
      var el = list[i];
      if (!owned(el) || !visible(el)) continue;
      if (!fallback) fallback = el;
      if (!clearOf(el)) return el;
    }
    return fallback;
  }
  function topAt(el){
    var r = el.getBoundingClientRect();
    var top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!top) return '';
    return top.id || top.className || top.tagName;
  }
  async function clickPaint(el){
    var covered = clearOf(el);
    var hit = topAt(el);
    var t0 = performance.now();
    try { el.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, cancelable:true})); } catch (eP) {}
    try { el.focus(); } catch (eF) {}
    el.click();
    await frames();
    return { ms: performance.now() - t0, covered: covered, hit: String(hit).slice(0, 80) };
  }
  var out = {tabs:{}, observer: window.__ltOk === true, error: null, counts: null};
  try { out.counts = window.__counts(tabs.map(function(t){ return t.id; })); } catch (eC) { out.error = 'counters: ' + String(eC); }
  var busy = false;
  window.__latPoll = setInterval(function(){
    if (busy) return;
    busy = true;
    try { if (typeof renderVault === 'function') renderVault(); } catch (eR) {}
    busy = false;
  }, 500);
  try {
    for (var t = 0; t < tabs.length; t++) {
      var spec = tabs[t];
      var row = {switchMs: null, control: null, search: null};
      var t0 = performance.now();
      if (typeof switchTab === 'function') switchTab(spec.id);
      await frames();
      row.switchMs = performance.now() - t0;
      await sleep(400);
      var root = document.getElementById('tab-' + spec.id);
      var btn = pick(spec.control);
      if (btn) {
        var cs = [];
        var covered = false;
        var hit = '';
        for (var i = 0; i < samples; i++) {
          var c = await clickPaint(btn);
          cs.push(c.ms);
          if (c.covered) covered = true;
          hit = c.hit || hit;
          if (btn.id === 'tvz-theatre-btn') {
            /* the TV-D button opens bible's own #tvz-theatre; close it the way the page does */
            try { if (window._tvdTheatre && window._tvdTheatre.close) window._tvdTheatre.close(); } catch (eTh) {}
            await frames();
          }
        }
        row.control = {samples: cs, covered: covered, hit: hit};
        /* after the control: is the target still the topmost element at its own centre? */
        var after = '';
        var br = btn.getBoundingClientRect();
        var topEl = document.elementFromPoint(br.left + br.width / 2, br.top + br.height / 2);
        if (!(topEl === btn || (btn.contains && topEl && btn.contains(topEl))))
          after = topEl ? String(topEl.id || topEl.className || topEl.tagName).slice(0, 80) : '(nothing)';
        row.control.coveredAfter = after;
      }
      var inp = pick(spec.search);
      if (inp) {
        var ss = [];
        var scov = false, active = true, value = true, shit = '';
        for (var j = 0; j < samples; j++) {
          var s0 = performance.now();
          try { inp.focus(); } catch (eI) {}
          inp.click();
          var token = 'shako' + j;
          inp.value = token;
          try { inp.dispatchEvent(new Event('input', {bubbles:true})); } catch (eE) {}
          await frames();
          ss.push(performance.now() - s0);
          if (document.activeElement !== inp) active = false;
          if (inp.value !== token) value = false;
          if (clearOf(inp)) scov = true;
          shit = topAt(inp) || shit;
        }
        row.search = {samples: ss, covered: scov, active: active, value: value, hit: shit};
      }
      out.tabs[spec.id] = row;
    }
    if (window._vaultAutoIntakeSet) window._vaultAutoIntakeSet(false);
    window.__ltMax = null;
    var idle0 = performance.now();
    while (performance.now() - idle0 < idleMs) await sleep(200);
    out.maxDuringIdle = window.__ltMax;
    if (window.__latPoll) { clearInterval(window.__latPoll); window.__latPoll = 0; }
    var p0 = performance.now();
    try { if (typeof renderVault === 'function') renderVault(); } catch (eV) {}
    out.renderVaultMs = performance.now() - p0;
  } catch (err) {
    out.error = String(err && err.stack || err);
  }
  if (window.__latPoll) { clearInterval(window.__latPoll); window.__latPoll = 0; }
  return out;
};
"""


def _read():
    with open(BIBLE, encoding="utf-8") as fh:
        bible = fh.read()
    with open(UI, encoding="utf-8") as fh:
        ui = fh.read()
    return bible, ui


SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
_REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^")
_REGEX_KW = ("return", "typeof", "case", "in", "of", "delete", "void", "throw", "new", "else", "do")
# A whole-document walk: the document (or its body/root) as the receiver or the walker root.
# A walk over one panel's own subtree (control_ui's label solver) is not this cost.
_DOC = r"""(?<![\w$.])(?:document|doc)(?:\s*\.\s*(?:body|documentElement))?"""
WALK_RE = re.compile(
    _DOC + r"""\s*\.\s*(?:querySelectorAll\(\s*['"]\s*(?:html|body)?\s*\*\s*['"]\s*\)"""
    r"""|getElementsByTagName\(\s*['"]\*['"]\s*\)|createTreeWalker\s*\(|createNodeIterator\s*\()"""
    r"""|(?:createTreeWalker|createNodeIterator)\s*\(\s*""" + _DOC + r"""\s*[,)]""")
FN_RE = re.compile(r"(?<![\w$])function\b[^{]*\{|=>\s*\{")


def scripts(html):
    """Inline <script> bodies with their offset in the document."""
    for m in SCRIPT_RE.finditer(html):
        if re.search(r"\bsrc\s*=", m.group(1)):
            continue
        yield m.start(2), m.group(2)


def code_mask(src):
    """src with comments, string, template and regex contents blanked to spaces (newlines
    kept), so braces and names that survive are code. The v3773 first cut did not skip
    comments or regexes and read one 3.8 MB "function"."""
    out = list(src)
    i, n = 0, len(src)
    last, word = "", ""
    tmpl, depth = [], 0

    def blank(x, y):
        for k in range(x, min(y, n)):
            if out[k] != "\n":
                out[k] = " "
    while i < n:
        c = src[i]
        if c == "/" and src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
            continue
        if c == "/" and src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, j)
            i, last, word = j + 1, c, ""
            continue
        if c == "`" or (c == "}" and tmpl and tmpl[-1] == depth):
            if c == "}":
                tmpl.pop()
            j = i + 1
            while j < n and src[j] != "`" and not src.startswith("${", j):
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, j)
            if src.startswith("${", j):
                tmpl.append(depth)
                i, last = j + 2, "{"
                continue
            i, last, word = j + 1, "`", ""
            continue
        if c == "/" and (last == "" or last in _REGEX_PREV or word in _REGEX_KW):
            j, cls = i + 1, False
            while j < n and src[j] != "\n":
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "[":
                    cls = True
                elif src[j] == "]":
                    cls = False
                elif src[j] == "/" and not cls:
                    break
                j += 1
            if j < n and src[j] == "/":
                blank(i + 1, j)
                i, last, word = j + 1, ")", ""
                continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            word, last, i = src[i:j], "a", j
            continue
        if not c.isspace():
            last, word = c, ""
        i += 1
    return "".join(out)


def _functions(src):
    """-> (masked, [(start, end)]) for every function body, nested ones included."""
    masked = code_mask(src)
    heads = {m.end() - 1: m.start() for m in FN_RE.finditer(masked)}
    stack, spans = [], []
    for k, ch in enumerate(masked):
        if ch == "{":
            stack.append(k)
        elif ch == "}" and stack:
            a = stack.pop()
            if a in heads:
                spans.append((heads[a], k + 1))
    return masked, spans


def _scan_hits(html):
    """Innermost functions that walk the whole document AND read computed style."""
    hits = []
    for off, body in scripts(html):
        masked, spans = _functions(body)
        for a, b in spans:
            if "getComputedStyle" not in masked[a:b]:
                continue
            walk = [m for m in WALK_RE.finditer(body, a, b) if masked[m.start()] != " "]
            if walk:
                hits.append((off + a, off + b))
    inner = [h for h in hits if not any(o != h and h[0] <= o[0] and o[1] <= h[1] for o in hits)]
    return ["line %d: %s" % (html.count("\n", 0, a) + 1, html[a:a + 70].replace("\n", " ")) for a, _b in inner]


def css_rules(html):
    """(selectors, {prop: (value, important)}) for every innermost CSS rule in <style> blocks."""
    out = []
    for m in re.finditer(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I):
        css = re.sub(r"/\*.*?\*/", " ", m.group(1), flags=re.S)
        for r in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            sels, depth, cur = [], 0, ""
            for ch in r.group(1):
                depth += (ch == "(") - (ch == ")")
                if ch == "," and depth == 0:
                    sels.append(cur.strip())
                    cur = ""
                else:
                    cur += ch
            sels = [x for x in sels + [cur.strip()] if x]
            decls = {}
            for d in r.group(2).split(";"):
                if ":" not in d:
                    continue
                k, v = d.split(":", 1)
                v = v.strip()
                imp = v.endswith("!important")
                decls[k.strip().lower()] = (v[:-10].strip() if imp else v, imp)
            out.append((sels, decls))
    return out


def _decl(rules, selector, prop):
    """The declarations of `prop` on rules whose selector list holds `selector` exactly."""
    norm = re.sub(r"\s+", " ", selector.strip())
    return [d[prop] for sels, d in rules if prop in d and norm in [re.sub(r"\s+", " ", x) for x in sels]]


def static_problems(bible, ui):
    bad = []
    for label, src in (("bible.html", bible), ("control_ui.html", ui)):
        hits = _scan_hits(src)
        if hits:
            bad.append("%s walks the document with getComputedStyle: %s" % (label, hits[0]))
    for needle in MANUAL:
        if needle in bible:
            bad.append("bible.html still has a manual add-a-move control (%s)" % needle)
    if "mark moved" not in bible or "vmv-mark" not in bible:
        bad.append("the per-row mark moved control is gone")
    rules = css_rules(bible)
    # The Sets/Uniques search sets outline:0 with an id selector, so the glow must be !important to show.
    glow = _decl(rules, ".tab-content :is(input,textarea,select):focus-visible", "outline")
    if not any(v.startswith("2px solid") and imp for v, imp in glow):
        bad.append("bible.html: a focused tab input (Sets #tsrch-i) does not compute the gold outline: %s" % glow)
    ui_rules = css_rules(ui)
    if not any(v.startswith("2px solid") for v, _i in _decl(ui_rules, "input:focus-visible", "outline")):
        bad.append("control_ui.html has no gold focus outline")
    pe = _decl(ui_rules, "body:not(.theatre-open) #theatre", "pointer-events")
    if ("none", True) not in pe:
        bad.append("the console theatre takes clicks while it is closed: %s" % pe)
    return bad


def _node(prog):
    raw = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
    if raw.returncode != 0:
        raise AssertionError((raw.stderr or "")[-1500:])
    lines = [ln for ln in raw.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        raise AssertionError(raw.stdout[-800:])
    return json.loads(lines[-1])


ROOM_FAKE = r"""
var COUNT = {gcs: 0, star: 0};
function mkEl(i){
  return { id: i === 0 ? 'shortcut-hint' : (i === 1 ? 'control-dock' : 'n' + i), _cz: null,
    style: { zIndex: '', setProperty: function(k, v){ this.zIndex = v; }, removeProperty: function(){ this.zIndex = ''; } },
    classList: { contains: function(){ return false; } }, contains: function(){ return false; },
    getAttribute: function(){ return null; } };
}
var ALL = [];
for (var i = 0; i < 5000; i++) ALL.push(mkEl(i));
var active = 'vault';
var document = {
  documentElement: { getAttribute: function(k){ return k === 'data-active-tab' ? active : null; } },
  body: null,
  getElementById: function(id){ for (var i = 0; i < 3; i++) if (ALL[i].id === id) return ALL[i]; return null; },
  querySelector: function(sel){ if (sel === '#shortcut-hint') return ALL[0]; if (sel === '#control-dock') return ALL[1]; return null; },
  querySelectorAll: function(sel){ if (/^\s*(?:html|body)?\s*\*\s*$/.test(sel)) COUNT.star++; return ALL.slice(); },
  getElementsByTagName: function(t){ if (t === '*') COUNT.star++; return ALL.slice(); },
  createTreeWalker: function(){ COUNT.star++; var k = -1; return { nextNode: function(){ k++; return k < ALL.length ? ALL[k] : null; } }; }
};
document.body = { querySelectorAll: document.querySelectorAll, getElementsByTagName: document.getElementsByTagName };
var window = { innerWidth: 1440, innerHeight: 900 };
function getComputedStyle(el){ COUNT.gcs++; return { display: 'block', visibility: 'visible', opacity: '1', zIndex: '150', position: 'fixed' }; }
"""


def _room_region(bible):
    from test_v3767_copy_witness import _fn
    start = bible.find("var _vaultRoomTouched = [];")
    end = bible.find("function _vaultCoverVerdict")
    if start < 0 or end < 0 or end < start:
        return None
    return bible[start:end] + "\n" + "\n".join(_fn(bible, n) for n in ("_vaultRoomStack", "_vaultRoomApply"))


def node_problems(bible):
    if not NODE:
        return ["node is not on this machine"]
    from test_v3767_copy_witness import _fn
    bad = []
    region = _room_region(bible)
    if region is None:
        return ["the room-lift state is not in bible.html"]
    # 1. load-independent cost: 5,000 elements in the document, three tab changes into and out of the vault
    count = r"""
var per = [];
['vault', 'session', 'vault'].forEach(function(t){
  active = t; COUNT.gcs = 0; COUNT.star = 0;
  try { _vaultRoomLift(); } catch (e) { per.push({err: String(e)}); return; }
  per.push({tab: t, gcs: COUNT.gcs, star: COUNT.star});
});
console.log(JSON.stringify({per: per}));
"""
    try:
        got = _node(ROOM_FAKE + region + "\n" + count)
    except Exception as e:
        return ["room-lift count raised %s" % e]
    for row in got.get("per") or []:
        if "err" in row or row["gcs"] > COUNT_BUDGET or row["star"] > 0:
            bad.append("a tab change into or out of the vault costs %s on a 5,000-element page (budget %d getComputedStyle, 0 walks)"
                       % (json.dumps(row), COUNT_BUDGET))
    # 2. a floater hidden while lowered is restored
    body = r"""
_vaultRoomTouched = [];
var el = { id: 'shortcut-hint', style: { zIndex: '150', pri: '',
  setProperty: function(k, v, p){ this.zIndex = v; this.pri = p; },
  removeProperty: function(){ this.zIndex = ''; } }, _cz: 200 };
_vaultRoomSink([el], true);
var mid = el.style.zIndex;
_vaultRoomSink([], false);
console.log(JSON.stringify({ mid: mid, back: el.style.zIndex, tracked: _vaultRoomTouched.length }));
"""
    try:
        got = _node(ROOM_FAKE + region + "\n" + body)
    except Exception as e:
        return bad + ["restore check raised %s" % e]
    if got.get("mid") != "20" or got.get("back") != "150" or got.get("tracked") != 0:
        bad.append("a floater hidden while lowered was not restored: %s" % json.dumps(got))
    # 3. Elad's ruling: a hand add reads MANUAL -> target cell, AUTO INTAKE off
    from test_v3769_vault_move_list import PREAMBLE, move_bundle
    hand = r"""
reset();
_vaultAutoIntakeSet(false);
ROUTES["Harlequin Crest"] = { id: 'uni-armor', why: 'helm' };
var added = _vaultMoveNoteAdded("Harlequin Crest");
var stored = (_vaultMoveBag().map || {})["Harlequin Crest\u0000" + 0] || null;
var t = added && added.task;
var html = t ? _vaultMoveHtml({ locks: [], groups: [{ label: 'MAIN', stash: 'Stash 1', rows: [{ name: 'Harlequin Crest', copyIx: 0, task: t, witnesses: null }] }] }) : '';
console.log(JSON.stringify({
  ok: !!(added && added.ok),
  shown: !!(added && added.shown === true),
  manual: !!(t && t.manual),
  stored: !!(stored && stored.manual === true),
  badge: html.indexOf('vmv-manual-badge">MANUAL<') >= 0,
  toCell: !!(t && t.to && t.to.cell != null) && html.indexOf('<i>TO</i>') >= 0,
  on: _vaultAutoIntakeRead().on === true
}));
"""
    try:
        row = _node(PREAMBLE + "\n" + move_bundle(bible) + "\n" + hand)
    except Exception as e:
        return bad + ["hand add raised %s" % e]
    if not (row.get("ok") and row.get("shown") and row.get("manual") and row.get("stored")
            and row.get("badge") and row.get("toCell") and not row.get("on")):
        bad.append("a hand add with AUTO INTAKE off does not read MANUAL -> target cell: %s" % json.dumps(row))
    return bad


def _eaten(hit):
    text = str(hit or "")
    return any(tok in text for tok in ("vault-ev-panel", "gsearch-scrim", "theatre", "tvz-th"))


def _pct(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(math.ceil(p * len(s))) - 1))
    return s[i]


def _summarize(raw):
    out = {"tabs": {}, "maxDuringIdle": raw.get("maxDuringIdle"),
           "renderVaultMs": raw.get("renderVaultMs"), "observer": raw.get("observer"),
           "error": raw.get("error"), "counts": raw.get("counts")}
    for name, row in (raw.get("tabs") or {}).items():
        item = {"switchMs": row.get("switchMs")}
        for key in ("control", "search"):
            block = row.get(key)
            if not block:
                item[key] = None
                continue
            samples = [x for x in (block.get("samples") or []) if isinstance(x, (int, float))]
            item[key] = {
                "n": len(samples), "p50": _pct(samples, 0.5), "p95": _pct(samples, 0.95),
                "max": max(samples) if samples else None,
                "covered": bool(block.get("covered")),
                "active": block.get("active", True), "value": block.get("value", True),
                "hit": block.get("hit"), "coveredAfter": block.get("coveredAfter", ""),
            }
        out["tabs"][name] = item
    return out


def chrome_problems(report):
    """Counts and coverage only. Click time is not judged: a loaded box moves it."""
    lines = []
    for vp, summary in report["views"].items():
        for key, row in sorted((summary.get("counts") or {}).items()):
            if row.get("gcs", 0) > COUNT_BUDGET or row.get("star", 0) > COUNT_BUDGET:
                lines.append("%s %s ran %d getComputedStyle and %d whole-document walks (budget %d)"
                             % (vp, key, row.get("gcs", 0), row.get("star", 0), COUNT_BUDGET))
        if not summary.get("counts"):
            lines.append("%s the counters did not run" % vp)
        for name in [t["id"] for t in TABS]:
            row = (summary.get("tabs") or {}).get(name)
            if not row or not row.get("control"):
                lines.append("%s %s has no clickable content control" % (vp, name))
                continue
            ctrl, search = row["control"], row.get("search")
            if _eaten(ctrl.get("hit")):
                lines.append("%s %s control is under %s" % (vp, name, ctrl.get("hit")))
            if _eaten(ctrl.get("coveredAfter")):
                lines.append("%s %s control is covered after its own click by %s" % (vp, name, ctrl["coveredAfter"]))
            if search and (_eaten(search.get("hit")) or search.get("active") is False or search.get("value") is False):
                lines.append("%s %s search did not take the typing: %s" % (vp, name, search))
        hand = report["hands"].get(vp) or {}
        if hand.get("manual"):
            lines.append("%s still has a manual add-a-move control" % vp)
        try:
            target = (json.loads(hand.get("task") or "null") or {}).get("to") or {}
        except ValueError:
            target = {}
        if target.get("cell") is not None and not (hand.get("row") and hand.get("badge")):
            lines.append("%s Add an item did not grow a MANUAL -> target cell row: %s" % (vp, hand))
        if target.get("cell") is None and hand.get("row"):
            lines.append("%s a hand add painted a row with no target cell: %s" % (vp, hand))
        if hand.get("intake") == "on":
            lines.append("%s left AUTO INTAKE on" % vp)
        if not hand.get("mark"):
            lines.append("%s row has no mark-moved control" % vp)
    return lines


def report_lines(report):
    """Click p95 per tab, as a report only."""
    out = []
    for vp, summary in report["views"].items():
        for name, row in (summary.get("tabs") or {}).items():
            ctrl = row.get("control") or {}
            out.append("%s %s switch %s ms, control p95 %s ms (report only)" % (
                vp, name, None if row.get("switchMs") is None else round(row["switchMs"]),
                None if ctrl.get("p95") is None else round(ctrl["p95"])))
    return "\n".join(out)


class TestInputStaysResponsive(unittest.TestCase):
    def test_01_the_page_does_not_scan_the_document_or_offer_a_manual_move(self):
        bible, ui = _read()
        bad = static_problems(bible, ui)
        self.assertEqual(bad, [], bad)

    def test_02_a_hidden_floater_is_restored_and_a_hand_add_grows_a_row(self):
        bible, _ui = _read()
        bad = node_problems(bible)
        self.assertEqual(bad, [], bad)

    def test_03_tab_changes_and_vault_paints_stay_under_the_count_budget(self):
        """The screen half judges on its own (no static pre-check), so it goes RED on v3771 by itself."""
        if "heart2." in os.path.abspath(__file__):
            return
        try:
            report = drive(ROOT)
        except RuntimeError as exc:
            if str(exc) == NO_BROWSER:
                NO_CHROME["flag"] = True
                return
            raise
        self.assertFalse(report.get("error"), report.get("error"))
        lines = chrome_problems(report)
        print(report_lines(report))
        self.assertEqual(lines, [], "\n".join(lines) + "\n" + json.dumps(report)[:4000])

    def test_04_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("input stays responsive: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f"
               % (n, w, bar))
        self.assertGreaterEqual(n, 10, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar, msg)


def _free_port(start):
    import socket
    p = start
    while p < start + 30:
        if p in (17771, 17772):
            p += 1
            continue
        sock = socket.socket()
        try:
            sock.bind(("127.0.0.1", p))
            return p
        except OSError:
            p += 1
        finally:
            sock.close()
    raise RuntimeError("no free port from %s" % start)


def _http(port, root):
    log = open(os.path.join(tempfile.gettempdir(), "v3773-http-%s.log" % port), "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=root, stdout=log, stderr=log)
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=2)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("http server exited %s" % proc.returncode)
            time.sleep(0.2)
    raise RuntimeError("http server did not answer on %s" % port)


def _chrome_proc(chrome, udd, port):
    logp = os.path.join(udd, "chrome.log")
    log = open(logp, "wb")
    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
        "--disable-dev-shm-usage", "--disable-extensions",
        "--remote-debugging-port=%d" % port, "--remote-allow-origins=*",
        "--user-data-dir=" + udd, "--window-size=1440,900", "about:blank",
    ], stdout=log, stderr=log)
    deadline = time.time() + 25
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("chrome exited %s\n%s" % (proc.returncode, open(logp, "rb").read()[-800:]))
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2) as fh:
                fh.read()
            return proc
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("chrome cdp did not answer")


def _new_tab(port):
    req = urllib.request.Request("http://127.0.0.1:%d/json/new?about:blank" % port, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=15) as fh:
            return json.loads(fh.read().decode())
    except Exception:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=10) as fh:
            tabs = json.loads(fh.read().decode())
        return next(t for t in tabs if t.get("type") == "page")


def _connect(ws):
    """The shared CDP client treats a 5s socket idle as a dead call. A tab probe
    is quiet for longer than that while it waits on paint, so keep reading until
    the deadline."""
    from test_v3769_vault_move_list_visual import _CDP

    class CDP(_CDP):
        def _read(self, n, deadline):
            while len(self._buf) < n:
                if time.time() > deadline:
                    raise TimeoutError("cdp read")
                self.sock.settimeout(max(0.2, min(5, deadline - time.time())))
                try:
                    chunk = self.sock.recv(1 << 20)
                except TimeoutError:
                    continue
                if not chunk:
                    raise ConnectionError("cdp closed")
                self._buf += chunk
            out, self._buf = self._buf[:n], self._buf[n:]
            return out

    return CDP(ws)


def _ev_async(cdp, expr, timeout):
    res = cdp.call("Runtime.evaluate", {
        "expression": expr, "returnByValue": True, "awaitPromise": True,
    }, timeout=timeout)
    details = res.get("exceptionDetails")
    if details:
        raise AssertionError(json.dumps(details)[:2000])
    return (res.get("result") or {}).get("value")


def _hand(cdp):
    return _ev_async(cdp, r"""
(async function(){
  if (window.__latPoll) { clearInterval(window.__latPoll); window.__latPoll = 0; }
  if (typeof switchTab === 'function') switchTab('vault');
  if (window._vaultAutoIntakeSet) window._vaultAutoIntakeSet(false);
  var manual = !!(document.getElementById('vault-move-q')
    || document.querySelector('[onclick*="_vaultMoveAddOpen"]')
    || document.querySelector('[onclick*="_vaultMoveAddNamed"]'));
  var btn = document.querySelector('button[onclick*="vaultHandOpen"]');
  if (btn) btn.click();
  var q = document.getElementById('vault-hand-q');
  var took = null;
  if (q && window.vaultHandSearch) {
    q.focus();
    q.value = 'Harlequin Crest';
    q.dispatchEvent(new Event('input', {bubbles:true}));
    window.vaultHandSearch('Harlequin Crest');
    await new Promise(function(r){ setTimeout(r, 400); });
    var opt = document.querySelector('#vault-hand-list .vault-hand-opt');
    if (opt) { opt.click(); took = 'click'; }
  }
  if (!took && window.vaultHandAdd) {
    took = window.vaultHandAdd('Harlequin Crest', new Date().toISOString(), {kind:'unique'});
    try { if (typeof renderVault === 'function') renderVault(); } catch (eR) {}
  }
  await new Promise(function(r){ requestAnimationFrame(function(){ requestAnimationFrame(function(){ r(); }); }); });
  var list = document.getElementById('vault-move-list');
  var text = list ? (list.innerText || '') : '';
  var intake = document.getElementById('vault-auto-intake');
  return {
    manual: manual,
    took: took && took.ok === false ? took : (took === 'click' ? 'click' : (took && took.mode) || took),
    row: !!(list && list.querySelector && list.querySelector('.vmv-row[data-name="Harlequin Crest"]')),
    badge: !!(list && list.querySelector && list.querySelector('.vmv-row[data-name="Harlequin Crest"] .vmv-manual-badge')),
    face: (function(){ var r = list && list.querySelector && list.querySelector('.vmv-row[data-name="Harlequin Crest"]');
      return r ? String(r.innerText || '').replace(/\s+/g, ' ').slice(0, 160) : ''; })(),
    task: (function(){ try { var e = window._vaultMoveEnsure('Harlequin Crest', 0); return JSON.stringify(e && e.task); } catch (e2) { return String(e2); } })(),
    mark: !!(list && list.querySelector && list.querySelector('.vmv-mark')),
    intake: intake ? intake.getAttribute('data-state') : null,
    say: (document.getElementById('vault-hand-say') || {}).textContent || ''
  };
})()
""", timeout=90)


def drive(root, samples=3, viewports=None, page="/bible.html"):
    """Open bible.html and measure every main tab. -> dict"""
    from test_v3769_vault_move_list_visual import _CDP, _chrome_path, _wait_fn
    chrome = _chrome_path()
    if not chrome:
        NO_CHROME["flag"] = True
        raise RuntimeError(NO_BROWSER)
    viewports = viewports or [(1280, 720), (1440, 900)]
    http_port = _free_port(17941)
    cdp_port = _free_port(http_port + 1)
    http = browser = cdp = None
    udd = tempfile.mkdtemp(prefix="v3773-chrome-")
    try:
        http = _http(http_port, root)
        browser = _chrome_proc(chrome, udd, cdp_port)
        tab = _new_tab(cdp_port)
        cdp = _connect(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": BOOT})
        url = "http://127.0.0.1:%d%s" % (http_port, page)
        cdp.call("Page.navigate", {"url": url})
        _wait_fn(cdp, "typeof window.switchTab==='function' && typeof window.renderVault==='function'", timeout=120)
        views, hands = {}, {}
        for w, h in viewports:
            cdp.call("Emulation.setDeviceMetricsOverride", {
                "width": w, "height": h, "deviceScaleFactor": 1, "mobile": False,
            })
            cdp.call("Emulation.setDeviceMetricsOverride", {
                "width": w, "height": h, "deviceScaleFactor": 1, "mobile": False,
            })
            raw = _ev_async(cdp, "window.__probe(%s, %d, 6000)" % (json.dumps(TABS), samples), timeout=180)
            key = "%dx%d" % (w, h)
            views[key] = _summarize(raw or {})
            hands[key] = _hand(cdp)
        return {"views": views, "hands": hands, "error": None}
    finally:
        if cdp:
            cdp.close()
        if browser and browser.poll() is None:
            browser.terminate()
            try:
                browser.wait(timeout=5)
            except Exception:
                browser.kill()
        if http and http.poll() is None:
            http.terminate()
            try:
                http.wait(timeout=5)
            except Exception:
                http.kill()
        shutil.rmtree(udd, ignore_errors=True)


RED_PROOF = [
    # Every entry changes what the page DOES. The node room-lift count (5,000 fake elements), the
    # node hand-add run, or the comment/regex-aware parser catches it inside heart2.
    {"why": "The vault walks every element again with doc.querySelectorAll('*') and reads each one's style.",
     "file": "bible.html",
     "find": "    _vaultRoomKnown(doc).forEach(function(el){\n      if (!el) return;",
     "replace": "    Array.prototype.slice.call(doc.querySelectorAll('*')).forEach(function(el){\n      if (!el) return;",
     "matches": 1},
    {"why": "The vault walks every element again through document.getElementsByTagName('*').",
     "file": "bible.html",
     "find": "    _vaultRoomKnown(doc).forEach(function(el){\n      if (!el) return;",
     "replace": "    Array.prototype.slice.call(document.getElementsByTagName('*')).forEach(function(el){\n      if (!el) return;",
     "matches": 1},
    {"why": "The known-floater list is filled by a TreeWalker over the whole body, one style read per node.",
     "file": "bible.html",
     "find": "return els; /* v3773 cached floaters */",
     "replace": "var tw = doc.createTreeWalker(doc.body || doc, 1), nx; while ((nx = tw.nextNode())) els.push(nx); return els;",
     "matches": 1},
    {"why": "Leaving the vault forgets a floater that was hidden while it was lowered.",
     "file": "bible.html",
     "find": "var all = _vaultRoomTouched.slice();",
     "replace": "var all = [];",
     "matches": 1},
    {"why": "A hand add writes an ordinary row, not MANUAL -> target cell.",
     "file": "bible.html",
     "find": "evidence: ens.task.evidence || [], manual: true });",
     "replace": "evidence: ens.task.evidence || [], manual: false });",
     "matches": 1},
    {"why": "A hand add says it wrote the row and stores nothing.",
     "file": "bible.html",
     "find": "var wrote = _vaultMoveCommit([{ name: nm, copyIx: 0, task: hand }]); /* v3773 manual row */",
     "replace": "var wrote = { ok: true }; /* v3773 manual row */",
     "matches": 1},
    {"why": "The move list draws a hand add's FROM as 'not seen yet' instead of the MANUAL badge.",
     "file": "bible.html",
     "find": "((t.manual && t.status === 'to-move' && !(t.from && t.from.cell != null))",
     "replace": "((false && t.status === 'to-move' && !(t.from && t.from.cell != null))",
     "matches": 1},
    {"why": "The Sets and Uniques search (#tsrch-i) loses the gold outline to its own outline:0 rule.",
     "file": "bible.html",
     "find": "outline:2px solid var(--gold-bright,#f0c060)!important;",
     "replace": "outline:2px solid var(--gold-bright,#f0c060);",
     "matches": 1},
    {"why": "A focused input in the console loses the gold outline.",
     "file": "control_ui.html",
     "find": "outline: 2px solid var(--gold, #f0c060);",
     "replace": "outline: none;",
     "matches": 1},
    {"why": "The closed console theatre takes the click.",
     "file": "control_ui.html",
     "find": "body:not(.theatre-open) #theatre { pointer-events: none !important; }",
     "replace": "body:not(.theatre-open) #theatre { pointer-events: auto !important; }",
     "matches": 1},
]


def measure_main():
    """Same click-to-paint probe on v3769, v3771 and the working tree."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from test_v3769_vault_move_list_visual import _CDP, _chrome_path, _wait_fn
    chrome = _chrome_path()
    if not chrome:
        print(NO_BROWSER)
        return 77
    blobs = {
        "v3769": subprocess.check_output(["git", "show", "38f15023:bible.html"]),
        "v3771": subprocess.check_output(["git", "show", "69817adf:bible.html"]),
        "fix": open(BIBLE, "rb").read(),
    }
    port = _free_port(17951)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/bible.html":
                key = (urllib.parse.parse_qs(parsed.query).get("v") or ["fix"])[0]
                body = blobs.get(key)
                if body is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            rel = urllib.parse.unquote(parsed.path).lstrip("/")
            path = os.path.normpath(os.path.join(ROOT, rel))
            if os.path.commonpath([ROOT, path]) != ROOT or not os.path.isfile(path):
                self.send_error(404)
                return
            with open(path, "rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    udd = tempfile.mkdtemp(prefix="v3773-measure-")
    cdp_port = _free_port(port + 1)
    browser = cdp = None
    try:
        browser = _chrome_proc(chrome, udd, cdp_port)
        tab = _new_tab(cdp_port)
        cdp = _connect(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": BOOT})
        report = {}
        for name, samples, idle, timeout, views in (
            ("v3769", 3, 6000, 180, [(1440, 900), (1280, 720)]),
            ("fix", 3, 6000, 180, [(1440, 900), (1280, 720)]),
            ("v3771", 3, 6000, 180, [(1440, 900), (1280, 720)]),
        ):
            cdp.call("Page.navigate", {"url": "http://127.0.0.1:%d/bible.html?v=%s" % (port, name)})
            try:
                _wait_fn(cdp, "typeof window.switchTab==='function'", timeout=90)
            except Exception as exc:
                report[name] = {"error": "load: %s" % exc}
                continue
            report[name] = {"views": {}}
            for w, h in views:
                cdp.call("Emulation.setDeviceMetricsOverride", {
                    "width": w, "height": h, "deviceScaleFactor": 1, "mobile": False,
                })
                try:
                    raw = _ev_async(
                        cdp, "window.__probe(%s, %d, %d)" % (json.dumps(TABS), samples, idle),
                        timeout=timeout)
                    report[name]["views"]["%dx%d" % (w, h)] = _summarize(raw or {})
                except Exception as exc:
                    report[name]["views"]["%dx%d" % (w, h)] = {"error": str(exc)[:500]}
            if name == "fix":
                try:
                    report[name]["hand"] = _hand(cdp)
                except Exception as exc:
                    report[name]["hand"] = {"error": str(exc)[:500]}
        out = os.path.join(tempfile.gettempdir(), "v3773-latency.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(report, fh)
        print(out)
        _print_latency(report)
        return 0
    finally:
        if cdp:
            cdp.close()
        if browser and browser.poll() is None:
            browser.terminate()
        httpd.shutdown()
        shutil.rmtree(udd, ignore_errors=True)


def _print_latency(report):
    for name, block in report.items():
        print("==", name)
        if block.get("error"):
            print(" ", block["error"])
        for vp, summary in (block.get("views") or {}).items():
            if summary.get("error"):
                print(" ", vp, summary["error"])
                continue
            print(" ", vp, "idle", summary.get("maxDuringIdle"), "renderVault", summary.get("renderVaultMs"))
            for tab, row in (summary.get("tabs") or {}).items():
                ctrl = row.get("control") or {}
                search = row.get("search") or {}
                print("   ", tab,
                      "switch", None if row.get("switchMs") is None else round(row["switchMs"], 1),
                      "ctrl p50/p95", None if ctrl.get("p50") is None else round(ctrl["p50"], 1),
                      None if ctrl.get("p95") is None else round(ctrl["p95"], 1),
                      "search p50/p95", None if search.get("p50") is None else round(search["p50"], 1),
                      None if search.get("p95") is None else round(search["p95"], 1))
        if block.get("hand"):
            print("  hand", json.dumps(block["hand"])[:400])


if __name__ == "__main__":
    if "--measure" in sys.argv:
        raise SystemExit(measure_main())
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestInputStaysResponsive)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    if NO_CHROME["flag"]:
        print(NO_BROWSER)
        sys.exit(77)
