# -*- coding: utf-8 -*-
"""#174 v-B2 — THE CHARACTER BUILDER FITS AT EVERY WIDTH, MEASURED IN A REAL BROWSER, NOT READ FROM ITS HTML.

The node law (test_the_character_builder_is_their_builder) proves what the builder SAYS; only layout can prove it is
SEEN. The mule window taught the class, in this same room: every length on the unit and the type fixed, so between
900 and 1250 wide words were cut while innerHTML carried them whole (test_the_mule_window_fits_at_every_width). This
builder is a new window with new words — a doll that fills the centre, a modal that must never hide the slot it
serves, a stats column, an inventory — so it is measured the same way, from the first ship.

WHAT IS MEASURED, per width (2000x1300, 1280x800, 1120x628, 1024x768, 901x900, 800x1000, 375x812), in FIVE states:
the template as it opens · with Crown of Ages on the doll and Annihilus in the inventory · the helm's picker open
(Select) · the helm in Edit (the roll boxes) · the stash list open.
  · no text node in the window is cut by an overflow:hidden/clip ancestor, or lies outside its panel unless a
    scroller holds it; no CONTROL has its box sliced by what contains it
  · nothing scrolls sideways, and the window itself never does
  · no panel header's title runs into its control
  · the modal lies inside the viewport, and in the column layouts it never covers the slot it serves: the glowing
    slot's centre hit-tests to the slot (their helm glows beside their modal, 01_helm_clicked)
  · at 2000x1300 the columns are their LITERAL 322 | 716 | 300 with 6px gutters (spec §1, ±4px), the doll fills the
    716 centre, and the header type is its token (k = 1)
#174 v-B2 FIX ROUND, by real input: at 375 and 2000 the picker's list scrolls to its LAST row under a real wheel
(Weapons, 600+ rows; Boots) - at 375 the stacked pane was unbounded, the list grew to 8715px and only ~35 rows could
ever be reached; and an ACTIVE gold button under the pointer keeps its dark label (Set 1, ! Quests, Filters, the
chosen class - the hover rule painted gold text on the gold face).
#174 v-B3: at 2000 / 1280 / 375 the Edit tab of a BASE with its picked mods - a rare Diadem with four (Devil's, Ruby,
of the Magus, of the Tiger), shut and with ADD MOD open; a magic Grand Charm with Chaotic + of Vita, and with Chaotic
alone and ADD MOD open (its suffixes listed) - nothing cut, nothing outside its panel, nothing sideways, the modal on
screen and off the glowing slot, every picked mod drawn and the open list full of options.
#174 v-B3 FIX ROUND: the open ADD MOD list lies wholly inside the Edit tab's visible box and, with more options than
fit, runs to its bottom (a fixed calc(330 x u) ran ~137px below the modal at 1280x800 and stopped at 158px on a phone
with ~220px empty under it); and ADD MOD is a combobox by REAL keys at 2000 - "res" typed, ArrowDown, Enter: focus stays
in the search box, aria-activedescendant names the second option, which is the one painted, and Enter adds exactly it.
The entry is REAL INPUT: the Tools tab and the Character Builder card are pressed by CDP mouse events at their
centres, each hit-tested first; the helm is equipped the same way (the slot, the search box, the row), a roll is
typed with key events, and the charm is DRAGGED to another cell with a press, moves carrying buttons=1, a release.
#174 v-B4 - THE CHARACTER/INVENTORY TEMPLATE IS ONE PANEL (his order 2026-09-26: "the INVENTORY under the equipment
need to be structured like this JUST LIKE IT IS IN GAME one to one", "they always open and are seen as a set together").
Theirs (planner 60/61, 15_crop): one carved-stone panel, the doll and flush under it the 10x4 grid - black cells, thin
lines, no gaps, no rounded corners. Ours was a framed doll, a caption, then a separate grid with 2px gaps and rounded
gradient cells. Measured in every plain and worn state at the 7 widths AND with three charms placed through the
builder's own picker (Annihilus 1x1, a Grand Charm 1x3, Gheed's Fortune 1x3, their ids read from the database by name)
at 2000x1300 / 1280x800 / 1120x800 / 900x800 / 375x812: the grid and the doll lie inside the ONE panel; the grid's top is
within 12px of the doll's bottom with no word between them; the caption and the status line are under the panel;
10 columns x 4 rows of equal SQUARE cells edge to edge (gap 0), radius 0; the grid never wider than the doll's inner
width; cells >= 26px from 1280 up; every item's rect inside the cells it occupies, with its art; and the charms MOVE
the stats (All Skills and Strength differ from the same build before them).

⚠ ITS OWN BROWSER, ON ITS OWN PORT, killed by the handle it holds (render_check._chrome_up / _chrome_down).
⚠ NO CHROME ON THIS MACHINE = a DECLARED skip (exit 77), never a pass.
RED_PROOF below.
"""
import io
import json
import os
import socket
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


# ⚠ BEFORE the import: render_check reads its port once, at import time. A free port by default; TV_LAW_PORT pins one
# when the caller owns a port range (parallel builders each given their own) - never 9222/9223, which are his.
_LAW_PORT = os.environ.get("TV_LAW_PORT", "").strip()
os.environ["TV_RENDER_PORT"] = _LAW_PORT if _LAW_PORT.isdigit() and _LAW_PORT not in ("9222", "9223") else str(_free_port())
import render_check as RC  # noqa: E402

NO_BROWSER = "no Chrome/Chromium on this machine, so the character builder was not rendered"
WIDTHS = ((2000, 1300), (1280, 800), (1120, 628), (1024, 768), (901, 900), (800, 1000), (375, 812))
#: #174 v-B4 - "invpick": an inventory cell's picker (Select) at every width - the grid moved into the template panel, so
#: where that picker opens moved with it, and the round-7 fallback it can still reach is at 1024 and 901, not 1120-1280
STATES = ("plain", "worn", "picker", "edit", "stash", "invpick")
#: #174 v-B3 - the Edit tab of a base with its picked mods, and with ADD MOD open, at these widths
MOD_WIDTHS = ((2000, 1300), (1280, 800), (375, 812))
_DIADEM = ("window._cbOpenPick('slot','head'); window._cbChoose('b:ci3'); window._cbQuality('rare');"
           " ['p712','p374','s175','s316'].forEach(function(i){ window._cbAddMod(i); });")
_GC = "window._cbOpenPick('inv', null, [0, 0]); window._cbChoose('b:cm3'); window._cbAddMod('p700');"
#: a magic charm with its prefix AND suffix is full (nothing left to list), so its open ADD MOD carries the prefix only
MOD_JS = {"mods": _DIADEM, "addmod": _DIADEM + " window._cbModOpen(true);",
          "gcmods": _GC + " window._cbAddMod('s338');", "gcaddmod": _GC + " window._cbModOpen(true);"}
MOD_STATES = ("mods", "addmod", "gcmods", "gcaddmod")
MOD_ROWS = {"mods": 4, "addmod": 4, "gcmods": 2, "gcaddmod": 1}
#: their builder at 2000 wide (spec §1): the three columns relative to the content column
THEIR_COLS = {"left": (0, 322), "main": (328, 716), "stats": (1050, 300)}
TOL = 4.0
#: #174 v-B4 - the widths the template is measured at with three charms placed (the builder's supported sizes)
TPL_WIDTHS = ((2000, 1300), (1280, 800), (1120, 800), (900, 800), (375, 812))
#: three charms by NAME (the ids are read from the database at run time) at their cells: 1x1, 1x3, 1x3
TPL_CHARMS = (("Annihilus", 0, 0, None), ("Grand Charm", 2, 0, "b:"), ("Gheed's Fortune", 4, 1, None))
#: their grid under their doll, measured (60/61, 15_crop): flush, ~9px of stone, no caption between
TPL_FLUSH = 12.0
TPL_MIN_CELL = 26.0

#: #174 v-B4 - the template: the ONE panel (#cb-eqp), its doll (#cb-doll) and its grid (#cb-inv), every cell, every item
TEMPLATE = r"""(function(){ try {
  var d = document, box = d.getElementById('cb-win'), cb = box && box.querySelector('.cb');
  if (!cb || box.hidden) return JSON.stringify({ err: 'the builder did not render' });
  var P = d.getElementById('cb-eqp'), D = d.getElementById('cb-doll'), G = d.getElementById('cb-inv');
  if (!P || !D || !G) return JSON.stringify({ err: 'no template: panel ' + !!P + ', doll ' + !!D + ', grid ' + !!G });
  var R = function(e){ var r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  var pr = R(P), dr = R(D), gr = R(G), gs = getComputedStyle(G);
  var out = { panel: pr, doll: dr, grid: gr, dollInner: D.clientWidth, gridInDom: P.contains(G), dollInDom: P.contains(D),
    gap: [gs.columnGap, gs.rowGap], radius: [gs.borderTopLeftRadius, gs.borderTopRightRadius, gs.borderBottomRightRadius, gs.borderBottomLeftRadius],
    cols: [], rows: [], cellRadius: [], cellW: [], cellH: [], nCells: 0, between: [], below: {}, items: [], stack: cb.classList.contains('cb-stack') };
  var cells = G.querySelectorAll('.cb-cell'), at = {}; out.nCells = cells.length;
  [].forEach.call(cells, function(c){
    var r = R(c), s = getComputedStyle(c), x = +c.getAttribute('data-x'), y = +c.getAttribute('data-y');
    at[x + ',' + y] = r; out.cellW.push(r[2] - r[0]); out.cellH.push(r[3] - r[1]);
    var rad = [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomRightRadius, s.borderBottomLeftRadius].join(' ');
    if (out.cellRadius.indexOf(rad) < 0) out.cellRadius.push(rad);
  });
  var cb0 = [1e9, 1e9, -1e9, -1e9]; Object.keys(at).forEach(function(k){ var q = at[k];
    cb0 = [Math.min(cb0[0], q[0]), Math.min(cb0[1], q[1]), Math.max(cb0[2], q[2]), Math.max(cb0[3], q[3])]; });
  out.cellsBox = cb0;   /* the cells' OWN extent: a grid box can be clamped narrower while its cells overflow it */
  for (var x = 0; x < 10; x++) if (at[x + ',0']) out.cols.push([at[x + ',0'][0], at[x + ',0'][2]]);
  for (var y = 0; y < 4; y++) if (at['0,' + y]) out.rows.push([at['0,' + y][1], at['0,' + y][3]]);
  /* every word drawn between the doll's bottom and the grid's top, over the grid's width */
  var tw = d.createTreeWalker(cb, NodeFilter.SHOW_TEXT), n;
  while ((n = tw.nextNode())){
    var t = n.textContent.trim(); if (!t) continue;
    var el = n.parentElement; if (!el || el.closest('[hidden]')) continue;
    var cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    var rg = d.createRange(); rg.selectNodeContents(n); var rr = rg.getBoundingClientRect(); if (rr.width < 0.5 || rr.height < 0.5) continue;
    var cy = (rr.top + rr.bottom) / 2;
    if (cy > dr[3] - 0.5 && cy < gr[1] + 0.5 && rr.right > gr[0] && rr.left < gr[2]) out.between.push(t.slice(0, 48));
  }
  var ds = box.querySelector('.cb-view:not([hidden]) .cb-doll-say'), is = d.getElementById('cb-inv-say');
  out.below = { caption: ds ? R(ds) : null, status: is ? R(is) : null, captionInPanel: !!(ds && P.contains(ds)), statusInPanel: !!(is && P.contains(is)) };
  [].forEach.call(G.querySelectorAll('.cb-it'), function(it){
    var a = String(it.getAttribute('data-at') || '').split(',').map(Number), r = R(it);
    var c0 = at[a[0] + ',' + a[1]], c1 = at[(a[0] + a[2] - 1) + ',' + (a[1] + a[3] - 1)];
    out.items.push({ at: a, rect: r, cells: c0 && c1 ? [c0[0], c0[1], c1[2], c1[3]] : null,
      name: String(it.getAttribute('aria-label') || '').split(' at ')[0], art: !!it.querySelector('img') });
  });
  var st = {}; [].forEach.call(box.querySelectorAll('.cb-st-r'), function(r){ var l = r.querySelector('.cb-sl'), v = r.querySelector('.cb-sv');
    if (l && v) st[l.textContent.trim()] = v.textContent.trim(); });
  out.stats = { allSkills: st['All Skills'] == null ? null : st['All Skills'], strength: st['Strength (items)'] == null ? null : st['Strength (items)'] };
  return JSON.stringify(out);
 } catch (e) { return JSON.stringify({ err: String(e) }); } })()"""
#: a fresh build through the builder's own "+ New build" (the first class the database lists), so its inventory is empty
TPL_NEW = ("(function(){ window.closeCharBuilder(); window.openCharBuilder(); window._cbOpenNew();"
           " var c = document.querySelector('#cb-modal .cb-new-cls .cb-btn'); if (!c) return 'no class button'; c.click();"
           " window._cbNewGo(); return 'ok'; })()")
#: a charm placed through the inventory cell's own picker: its id is the ONE database row with that name (and prefix)
TPL_PLACE = ("(function(n, x, y, pre){ window._cbOpenPick('inv', null, [x, y]); var rows = window._cbPickRows();"
             " var hit = rows.filter(function(r){ return r[1] === n && (!pre || r[0].indexOf(pre) === 0); });"
             " if (hit.length !== 1){ window._cbClosePick(); return JSON.stringify({ n: n, found: hit.length, of: rows.length }); }"
             " var ok = window._cbChoose(hit[0][0]); window._cbClosePick(); return JSON.stringify({ n: n, id: hit[0][0], ok: !!ok }); })(%s, %d, %d, %s)")

AIM = r"""(function(sel, i){ var e = document.querySelectorAll(sel)[i]; if (!e) return JSON.stringify(null);
  var r0 = e.getBoundingClientRect(); if (r0.top < 0 || r0.bottom > innerHeight || r0.left < 0 || r0.right > innerWidth)
    e.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
  var r = e.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  var at = document.elementFromPoint(x, y); return JSON.stringify({ x: x, y: y, hit: !!(at && (at === e || e.contains(at))) }); })(%s, %d)"""

MEASURE = r"""(function(){ try {
  var d = document, box = d.getElementById('cb-win'), cb = box && box.querySelector('.cb');
  if (!cb || box.hidden) return JSON.stringify({ err: 'the builder did not render (.cb absent)' });
  var ob = cb.getBoundingClientRect(), vw = innerWidth, vh = innerHeight;
  var rel = function(el){ if (!el) return null; var r = el.getBoundingClientRect(); return [r.left - ob.left, r.top - ob.top, r.width, r.height]; };
  var out = { stack: cb.classList.contains('cb-stack'), hscroll: [box.scrollWidth, box.clientWidth], cols: {}, cut: [], outside: [],
    sideways: [], collide: [], nText: 0, modal: null, covered: null, worn: box.querySelectorAll('.cb-slot.cb-has').length,
    inv: box.querySelectorAll('.cb-it').length, rolls: box.querySelectorAll('.cb-roll').length, opts: box.querySelectorAll('.cb-opt').length,
    mods: box.querySelectorAll('.cb-mod').length, addOpts: box.querySelectorAll('.cb-add-o').length,
    doll: rel(d.getElementById('cb-doll')), invRect: rel(d.getElementById('cb-inv')),
    invInMain: !!(d.getElementById('cb-inv') && d.getElementById('cb-inv').closest('.cb-main')) };
  out.cols.left = rel(box.querySelector('.cb-left')); out.cols.main = rel(box.querySelector('.cb-main')); out.cols.stats = rel(box.querySelector('.cb-stats'));
  var _sa = box.querySelector('.cb-stats'); out.statsLeftAbs = _sa ? _sa.getBoundingClientRect().left : null;  // #174 round 7: the VIEWPORT frame the modal rect is in
  /* #174 R2 — where STATS ends on the glass (at the window's scroll 0) and whether its own list scrolls */
  var _sp = box.querySelector('.cb-stats'), _sl = box.querySelector('.cb-st');
  out.statsBottom = _sp ? _sp.getBoundingClientRect().bottom : null; out.vh = vh;
  out.statsList = _sl ? [_sl.scrollHeight, _sl.clientHeight, getComputedStyle(_sl).overflowY] : null;
  var ht = box.querySelector('.cb-h-t'); out.fsTitle = ht ? parseFloat(getComputedStyle(ht).fontSize) : null;
  out.tokTitle = parseFloat(getComputedStyle(d.documentElement).getPropertyValue('--fs-title'));
  var m = d.getElementById('cb-modal');
  if (m && !m.hidden){
    var mr = m.getBoundingClientRect(); out.modal = [mr.left, mr.top, mr.width, mr.height];
    out.modalInside = mr.left >= -0.5 && mr.top >= -0.5 && mr.right <= vw + 0.5 && mr.bottom <= vh + 0.5;
    var sel = box.querySelector('.cb-slot.cb-picked');
    if (sel && !out.stack){ var sr = sel.getBoundingClientRect(), at = d.elementFromPoint(sr.left + sr.width / 2, sr.top + sr.height / 2);
      out.covered = !(at && (at === sel || sel.contains(at))); }
  }
  var roots = [cb]; if (m && !m.hidden) roots.push(m);
  roots.forEach(function(root){
    var tw = d.createTreeWalker(root, NodeFilter.SHOW_TEXT), n;
    while ((n = tw.nextNode())){
      var t = n.textContent.trim(); if (!t) continue;
      var el = n.parentElement; if (!el || el.closest('[hidden]') || el.closest('.cb-it') || el.closest('.cb-slot') || el.closest('option')) continue;
      var cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      var rg = d.createRange(); rg.selectNodeContents(n);
      var L = 1e9, T = 1e9, R = -1e9, B = -1e9;
      [].forEach.call(rg.getClientRects(), function(r){ if (r.width < 0.5 && r.height < 0.5) return;
        L = Math.min(L, r.left); T = Math.min(T, r.top); R = Math.max(R, r.right); B = Math.max(B, r.bottom); });
      if (L > R) continue;
      out.nText++;
      var scrolled = false;
      for (var a = el; a && a !== box; a = a.parentElement){
        var s = getComputedStyle(a); if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
        var ar = a.getBoundingClientRect(), cl = ar.left + a.clientLeft, ct = ar.top + a.clientTop, cr = cl + a.clientWidth, cbt = ct + a.clientHeight;
        var hx = (L < cl - 0.5 || R > cr + 0.5), hy = (T < ct - 0.5 || B > cbt + 0.5);
        var hid = function(o){ return o === 'hidden' || o === 'clip'; };
        if ((hx && hid(s.overflowX)) || (hy && hid(s.overflowY)))
          out.cut.push(String(a.className).slice(0, 30) + ' cuts "' + t.slice(0, 48) + '"');
        scrolled = !hid(s.overflowX) || !hid(s.overflowY);
        break;
      }
      var p = el.closest('.cb-p') || el.closest('.cb-modal');
      if (p && !scrolled){ var pr = p.getBoundingClientRect();
        if (B > pr.bottom + 0.5 || R > pr.right + 0.5 || L < pr.left - 0.5) out.outside.push('"' + t.slice(0, 40) + '" outside ' + String(p.className).slice(0, 24)); }
    }
    [].forEach.call(root.querySelectorAll('button,select,input,textarea,.cb-it'), function(e){
      if (e.closest('[hidden]')) return;
      var r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return;
      for (var a = e.parentElement; a && a !== box; a = a.parentElement){
        var s = getComputedStyle(a); if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
        var hid = function(o){ return o === 'hidden' || o === 'clip'; };
        var ar = a.getBoundingClientRect(), cl = ar.left + a.clientLeft, ct = ar.top + a.clientTop, cr = cl + a.clientWidth, cbt = ct + a.clientHeight;
        var dx = Math.max(cl - r.left, r.right - cr), dy = Math.max(ct - r.top, r.bottom - cbt);
        if ((dx > 0.5 && hid(s.overflowX)) || (dy > 0.5 && hid(s.overflowY)))
          out.cut.push(String(a.className).slice(0, 30) + ' cuts the control ' + String(e.className || e.tagName).slice(0, 30) + ' by ' + Math.max(dx, dy).toFixed(1) + 'px');
        break;
      }
    });
    [].forEach.call(root.querySelectorAll('*'), function(e){ var s = getComputedStyle(e);
      if ((s.overflowX === 'auto' || s.overflowX === 'scroll') && e.scrollWidth > e.clientWidth + 1)
        out.sideways.push(String(e.className || e.tagName).slice(0, 30) + ' ' + e.scrollWidth + '/' + e.clientWidth); });
  });
  [].forEach.call(box.querySelectorAll('.cb-h'), function(h){
    var c = h.querySelector('.cb-h-r'), t = h.querySelector('.cb-h-t'); if (!c || !c.firstElementChild || !t) return;
    var rg = d.createRange(); rg.selectNodeContents(t); var tr = rg.getBoundingClientRect(), cr = c.getBoundingClientRect();
    if (tr.right > cr.left + 0.5 && tr.bottom > cr.top && tr.top < cr.bottom) out.collide.push('"' + t.textContent.trim() + '" runs under its control'); });
  return JSON.stringify(out);
 } catch (e) { return JSON.stringify({ err: String(e) }); } })()"""

_CACHE = {}


def _press(t, sel, i=0):
    a = json.loads(t.ev(AIM % (json.dumps(sel), i)))
    if not a:
        return "no %s[%d] on the page" % (sel, i)
    time.sleep(0.15)
    a = json.loads(t.ev(AIM % (json.dumps(sel), i)))
    if not a["hit"]:
        return "the centre of %s[%d] is covered by another element" % (sel, i)
    for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
        t.send("Input.dispatchMouseEvent", type=kind, x=a["x"], y=a["y"], button="none" if kind == "mouseMoved" else "left",
               buttons=1 if kind == "mousePressed" else 0, clickCount=0 if kind == "mouseMoved" else 1)
    time.sleep(0.25)
    return None


def _drag(t, sel, i, sel2, j):
    a = json.loads(t.ev(AIM % (json.dumps(sel), i)))
    b = json.loads(t.ev(AIM % (json.dumps(sel2), j)))
    if not a or not b or not a["hit"]:
        return "cannot aim the drag: %s -> %s" % (a, b)
    t.send("Input.dispatchMouseEvent", type="mouseMoved", x=a["x"], y=a["y"], button="none", buttons=0)
    t.send("Input.dispatchMouseEvent", type="mousePressed", x=a["x"], y=a["y"], button="left", buttons=1, clickCount=1)
    for k in range(1, 9):
        t.send("Input.dispatchMouseEvent", type="mouseMoved", x=a["x"] + (b["x"] - a["x"]) * k / 8.0,
               y=a["y"] + (b["y"] - a["y"]) * k / 8.0, button="left", buttons=1)
        time.sleep(0.03)
    t.send("Input.dispatchMouseEvent", type="mouseReleased", x=b["x"], y=b["y"], button="left", buttons=0, clickCount=1)
    time.sleep(0.3)
    return None


def _type(t, text):
    for ch in text:
        t.send("Input.dispatchKeyEvent", type="keyDown", text=ch, key=ch, unmodifiedText=ch)
        t.send("Input.dispatchKeyEvent", type="keyUp", key=ch)


def _key(t, k, code):
    t.send("Input.dispatchKeyEvent", type="keyDown", key=k, code=k, windowsVirtualKeyCode=code, nativeVirtualKeyCode=code,
           **({"text": "\r"} if k == "Enter" else {}))
    t.send("Input.dispatchKeyEvent", type="keyUp", key=k, code=k, windowsVirtualKeyCode=code, nativeVirtualKeyCode=code)
    time.sleep(0.2)


def _row(t, name):
    return t.ev("(function(n){ var o = document.querySelectorAll('#cb-list .cb-opt'); for (var i = 0; i < o.length; i++) "
                "if (o[i].textContent === n) return i; return -1; })(%s)" % json.dumps(name))


LIST = r"""(function(){ var l = document.getElementById('cb-list'); if (!l) return 'null';
  var o = l.querySelectorAll('.cb-opt'), last = o[o.length - 1]; if (!last) return 'null';
  var lr = l.getBoundingClientRect(), r = last.getBoundingClientRect();
  var cx = (Math.max(lr.left, 0) + Math.min(lr.right, innerWidth)) / 2, cy = (Math.max(lr.top, 0) + Math.min(lr.bottom, innerHeight)) / 2;
  var hit = document.elementFromPoint(cx, cy), y = r.top + r.height / 2, at = (y > 0 && y < innerHeight) ? document.elementFromPoint(r.left + Math.min(20, r.width / 2), y) : null;
  return JSON.stringify({ rows: o.length, scroll: [l.scrollTop, l.scrollHeight, l.clientHeight], listH: lr.height, cx: cx, cy: cy,
    aim: !!(hit && l.contains(hit)), lastTop: r.top, lastSeen: !!(at && (at === last || last.contains(at))), name: last.textContent }); })()"""
#: #174 v-B3 fix round - the open ADD MOD list against the room of the Edit tab it sits in (#cb-ed, the modal's scroller)
FIT = r"""(function(){ var l = document.getElementById('cb-add-list'), ed = document.getElementById('cb-ed');
  if (!l || !ed) return 'null';
  var lr = l.getBoundingClientRect(), er = ed.getBoundingClientRect(), o = l.querySelectorAll('.cb-add-o'), seen = 0;
  [].forEach.call(o, function(x){ var r = x.getBoundingClientRect(); if (r.top >= lr.top - 0.5 && r.bottom <= lr.bottom + 0.5 && r.top >= er.top - 0.5 && r.bottom <= er.bottom + 0.5) seen++; });
  return JSON.stringify({ top: lr.top, bottom: lr.bottom, ch: l.clientHeight, sh: l.scrollHeight, edTop: er.top, edBottom: er.bottom, opts: o.length, seen: seen }); })()"""
#: #174 v-B3 fix round - what the keyboard left: focus, the active option (aria-activedescendant), how it is painted
COMBO = r"""(function(){ var q = document.getElementById('cb-add-q'), ae = document.activeElement, id = q && q.getAttribute('aria-activedescendant');
  var a = id ? document.getElementById(id) : null, acts = document.querySelectorAll('#cb-add-list .cb-add-o.cb-act');
  var e = null; try { var b = JSON.parse(window.LSR.getItem('d2r_charBuilds') || '{}'), k = Object.keys(b)[0]; e = b[k].sets[0].slots.head; } catch (x) {}
  return JSON.stringify({ focus: ae ? ae.id : null, role: q ? q.getAttribute('role') : null, active: id, activeId: a ? a.getAttribute('data-id') : null,
    painted: a ? getComputedStyle(a).backgroundColor : null, acts: acts.length, second: (document.querySelectorAll('#cb-add-list .cb-add-o')[1] || {}).id || null,
    stored: e && e.affixes ? e.affixes.map(function(x){ return x.id; }) : null }); })()"""
HOVER_READ = r"""(function(sel){ var e = document.querySelector(sel); if (!e) return 'null'; var cs = getComputedStyle(e);
  return JSON.stringify({ color: cs.color, bg: cs.backgroundColor, hover: e.matches(':hover'), text: e.textContent.trim() }); })(%s)"""


#: #174 round 2 (the Grok seat on v3509) - how many options are PAINTED, which one is active, which one the pointer is on
LIT = r"""(function(){ var os = document.querySelectorAll('#cb-add-list .cb-add-o'), lit = [], q = document.getElementById('cb-add-q');
  [].forEach.call(os, function(o, i){ var bg = getComputedStyle(o).backgroundColor; if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') lit.push(i); });
  var under = -1; [].forEach.call(os, function(o, i){ if (o.matches(':hover')) under = i; });
  var id = q && q.getAttribute('aria-activedescendant'), act = -1; [].forEach.call(os, function(o, i){ if (o.id === id) act = i; });
  return JSON.stringify({ n: os.length, lit: lit, under: under, active: act }); })()"""
#: #174 round 2 - every stat label that wraps: the left edge of its first line and of its second
INDENT = r"""(function(){ var out = [];
  [].forEach.call(document.querySelectorAll('#cb-win .cb-st-r:not([hidden]) .cb-sl'), function(l){
    var rg = document.createRange(); rg.selectNodeContents(l);
    var lines = {}; [].forEach.call(rg.getClientRects(), function(x){ if (x.width < 0.5) return; var k = Math.round(x.top); if (!(k in lines) || x.left < lines[k]) lines[k] = x.left; });
    var ks = Object.keys(lines).map(Number).sort(function(a, b){ return a - b; });
    if (ks.length > 1) out.push({ text: l.textContent.trim(), first: lines[ks[0]], next: lines[ks[1]] }); });
  return JSON.stringify(out); })()"""


#: #174 round 3 - rows whose value sits BELOW its label's first line, and label text running under its value
DROP = r"""(function(){ var out = [];
  [].forEach.call(document.querySelectorAll('#cb-win .cb-st-r:not([hidden])'), function(r){
    var l = r.querySelector('.cb-sl'), v = r.querySelector('.cb-sv'); if (!l || !v) return;
    var rg = document.createRange(); rg.selectNodeContents(l);
    var rs = [].slice.call(rg.getClientRects()).filter(function(x){ return x.width > 0.5; });
    if (rs.length && v.getBoundingClientRect().top > rs[0].bottom - 1) out.push(l.textContent.trim()); });
  return JSON.stringify(out); })()"""
OVER = r"""(function(){ var bad = [];
  [].forEach.call(document.querySelectorAll('#cb-win .cb-st-r:not([hidden])'), function(r){
    var l = r.querySelector('.cb-sl'), v = r.querySelector('.cb-sv'); if (!l || !v) return;
    var rg = document.createRange(); rg.selectNodeContents(l); var vr = v.getBoundingClientRect();
    [].forEach.call(rg.getClientRects(), function(x){
      if (x.width > 0.5 && x.bottom > vr.top + 1 && x.top < vr.bottom - 1 && x.right > vr.left + 0.5) bad.push(l.textContent.trim()); }); });
  return JSON.stringify(bad); })()"""
#: the same page with the hanging indent taken away - what v-B2's rule gave before round 2
FLUSH_ON = ("(function(){ var s = document.createElement('style'); s.id = 'law-flush'; s.textContent = "
            "'.cb-st-r .cb-sl{padding-left:0 !important;text-indent:0 !important;margin-right:0 !important}';"
            " document.head.appendChild(s); return 1; })()")
FLUSH_OFF = "(function(){ var s = document.getElementById('law-flush'); if (s) s.remove(); return 1; })()"
#: the band where the stats column is tight enough for a label to wrap (measured 2026-09-26: every regression was 900-1240)
SWEEP = range(900, 1401, 20)


def _point_at(t, sel, i):
    """the pointer comes to rest on the i-th match (two real moves) - no click"""
    a = json.loads(t.ev(AIM % (json.dumps(sel), i)))
    if not a or not a["hit"]:
        return "cannot aim at %s[%d]: %s" % (sel, i, a)
    for dx in (0, 1):
        t.send("Input.dispatchMouseEvent", type="mouseMoved", x=a["x"] + dx, y=a["y"], button="none")
        time.sleep(0.15)
    return None


def _wheel_list(t):
    """a REAL wheel over the picker's list: 40 notches, then is its last row on screen?"""
    b = json.loads(t.ev(LIST))
    if not b or not b["aim"]:
        return {"err": "the list is not under the pointer: %s" % b}
    for _ in range(40):
        t.send("Input.dispatchMouseEvent", type="mouseWheel", x=b["cx"], y=b["cy"], deltaX=0, deltaY=400)
        time.sleep(0.02)
    time.sleep(0.5)
    return {"before": b, "after": json.loads(t.ev(LIST))}


def _hover(t, sel):
    """the pointer comes to rest on a control (two real moves, so the hover state is the page's own)"""
    a = json.loads(t.ev(AIM % (json.dumps(sel), 0)))
    if not a or not a["hit"]:
        return {"err": "cannot aim at %s: %s" % (sel, a)}
    for dx in (0, 1):
        t.send("Input.dispatchMouseEvent", type="mouseMoved", x=a["x"] + dx, y=a["y"], button="none")
        time.sleep(0.15)
    return json.loads(t.ev(HOVER_READ % json.dumps(sel)))


def _set_size(t, w, h):
    t.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=(w < 500))
    time.sleep(0.3)


def _measure():
    if "r" in _CACHE:
        return _CACHE["r"]
    if not RC._chrome_up():
        raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d" % (RC.CHROME, RC.PORT))
    res = {"input": []}
    try:
        t = RC._Tab("about:blank")
        t.send("Page.enable")
        t.send("Runtime.enable")
        _set_size(t, 2000, 1300)
        t.send("Page.navigate", url="file://" + os.path.join(ROOT, "bible.html"))
        for _ in range(200):
            time.sleep(0.25)
            try:
                if t.ev("document.readyState==='complete' && !!window.openCharBuilder && !!window.LSR") is True:
                    break
            except Exception:
                pass
        else:
            raise AssertionError("bible.html never exposed openCharBuilder in 50s — UNKNOWN, not passing")
        time.sleep(0.6)
        # ⚠ 2026-09-26 — MEASURE AFTER THE FONTS. The page pulls Cinzel / Playfair / Inter from Google Fonts; on CI they
        # arrive over the network at a variable time, and a row measured before its font lands reflows a few px later.
        # MEASURED: the mule law read the stash-in-front EQUIPMENT panel 6 px low on one CI run of v3513 and exact on the
        # re-run of the same commit. Bounded (15 s); the status measured under is recorded, never assumed.
        for _ in range(60):
            try:
                if t.ev("document.fonts.status") == "loaded":
                    break
            except Exception:
                pass
            time.sleep(0.25)
        res["fonts"] = t.ev("document.fonts.status")
        # THE ENTRY, BY REAL INPUT: the Tools tab, then the Character Builder card
        res["input"].append(_press(t, '.tab[data-tab="tools"]'))
        time.sleep(0.8)
        res["input"].append(_press(t, "#char-builder-card .boss-header"))
        time.sleep(0.6)
        res["opened"] = t.ev("(function(){ var w = document.getElementById('cb-win'); return !!w && !w.hidden; })()")
        # plain, at every width
        for (w, h) in WIDTHS:
            _set_size(t, w, h)
            t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); return 1; })()")
            time.sleep(0.35)
            res["plain %dx%d" % (w, h)] = json.loads(t.ev(MEASURE))
            res["tpl plain %dx%d" % (w, h)] = json.loads(t.ev(TEMPLATE))
        # equip by real input at 2000: the helm slot, the search box, the row; a roll typed; a charm dropped and dragged
        _set_size(t, 2000, 1300)
        t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); return 1; })()")
        time.sleep(0.4)
        res["input"].append(_press(t, '#cb-win .cb-slot[data-slot="head"]'))
        res["input"].append(_press(t, "#cb-pick-q"))
        _type(t, "crown of ages")
        time.sleep(0.3)
        i = _row(t, "Crown of Ages")
        res["input"].append(("Crown of Ages was not listed") if i is None or i < 0 else _press(t, "#cb-list .cb-opt", i))
        res["input"].append(_press(t, "#cb-lines .cb-roll", 1))
        _type(t, "28")
        _key(t, "Enter", 13)
        _key(t, "Escape", 27)
        res["input"].append(_press(t, "#cb-inv .cb-cell", 0))
        i = _row(t, "Annihilus")
        res["input"].append(("Annihilus was not listed") if i is None or i < 0 else _press(t, "#cb-list .cb-opt", i))
        _key(t, "Escape", 27)
        res["input"].append(_drag(t, "#cb-inv .cb-it", 0, "#cb-inv .cb-cell", 25))
        res["store"] = t.ev("(function(){ var b = JSON.parse(window.LSR.getItem('d2r_charBuilds') || '{}'), k = Object.keys(b)[0];"
                            " if (!k) return null; var s = b[k].sets[0]; return JSON.stringify({ head: s.slots.head && [s.slots.head.name, s.slots.head.rolls],"
                            " inv: s.inv.map(function(e){ return [e.name, e.x, e.y]; }) }); })()")
        for (w, h) in WIDTHS:
            _set_size(t, w, h)
            for state in ("worn", "picker", "edit", "stash", "invpick"):
                js = {"worn": "", "picker": "window._cbOpenPick('slot','head'); window._cbPickTab('select');",
                      "edit": "window._cbOpenPick('slot','head');", "stash": "window._cbOpenStash();",
                      "invpick": "window._cbOpenPick('inv', null, [0, 0]);"}[state]
                t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); %s return 1; })()" % js)
                time.sleep(0.35)
                res["%s %dx%d" % (state, w, h)] = json.loads(t.ev(MEASURE))
                if state == "worn":
                    res["tpl worn %dx%d" % (w, h)] = json.loads(t.ev(TEMPLATE))
        # #174 v-B2 fix round - the picker's list, by a real wheel, at 375 and 2000
        for (w, h) in ((375, 812), (2000, 1300)):
            _set_size(t, w, h)
            for slot in ("rarm", "feet"):
                t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); return 1; })()")
                time.sleep(0.35)
                res["input"].append(_press(t, '#cb-win .cb-slot[data-slot="%s"]' % slot))
                time.sleep(0.3)
                res["wheel %s %dx%d" % (slot, w, h)] = _wheel_list(t)
        # #174 v-B3 - the Edit tab of a BASE with picked mods (a rare Diadem with four, a magic Grand Charm with two), and
        # its ADD MOD list open, at 2000 / 1280 / 375 - through the builder's own entry points (Choose -> Quality -> Add)
        for (w, h) in MOD_WIDTHS:
            _set_size(t, w, h)
            for state in MOD_STATES:
                t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); %s return 1; })()" % MOD_JS[state])
                time.sleep(0.35)
                res["%s %dx%d" % (state, w, h)] = json.loads(t.ev(MEASURE))
                if state.endswith("addmod"):
                    res["fit %s %dx%d" % (state, w, h)] = json.loads(t.ev(FIT))
                if state.startswith("gc"):
                    # #174 round 7 - the charm's Edit tile draws its in-game art, not its name in a box
                    res["gcart %s %dx%d" % (state, w, h)] = json.loads(t.ev(
                        "(function(){ var m = document.getElementById('cb-modal'); return JSON.stringify({ img: !!(m && m.querySelector('.d2art-wrap img')),"
                        " failed: !!(m && m.querySelector('.d2art-failed')) }); })()"))
                    t.ev("(function(){ window._cbUnequip(); window._cbClosePick(); return 1; })()")
        # #174 v-B3 fix round - ADD MOD by the KEYBOARD, real input at 2000: a rare Diadem with two prefixes, the search box
        # pressed, "res" typed, ArrowDown, then Enter - focus must stay in the box and the painted option be what Enter adds
        _set_size(t, 2000, 1300)
        t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); window._cbOpenPick('slot','head'); window._cbChoose('b:ci3');"
             " window._cbQuality('rare'); ['p712','s175'].forEach(function(i){ window._cbAddMod(i); }); window._cbModOpen(true); return 1; })()")
        time.sleep(0.35)
        res["input"].append(_press(t, "#cb-add-q"))
        _type(t, "res")
        time.sleep(0.3)
        combo = {"typed": json.loads(t.ev(COMBO))}
        _key(t, "ArrowDown", 40)
        combo["down"] = json.loads(t.ev(COMBO))
        _key(t, "Enter", 13)
        time.sleep(0.2)
        combo["enter"] = json.loads(t.ev(COMBO))
        res["combo"] = combo
        # #174 round 2 (the Grok seat on v3509) - the POINTER and the keys light ONE row between them: the pointer comes to
        # rest on the 4th option (real moves, no click), then a real ArrowDown with the pointer still there
        t.ev("(function(){ window._cbModOpen(true); return 1; })()")
        time.sleep(0.3)
        res["input"].append(_point_at(t, "#cb-add-list .cb-add-o", 3))
        lit = {"pointer": json.loads(t.ev(LIT))}
        _key(t, "ArrowDown", 40)
        time.sleep(0.2)
        lit["down"] = json.loads(t.ev(LIT))
        res["lit"] = lit
        t.ev("(function(){ window._cbClosePick(); return 1; })()")
        # #174 round 2 - a wrapped stat label's second line is set in (a hanging indent), at 1280 where several wrap
        _set_size(t, 1280, 800)
        t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); %s window._cbClosePick(); return 1; })()" % _DIADEM)
        time.sleep(0.35)
        res["indent"] = json.loads(t.ev(INDENT))
        # #174 round 3 (the Grok seat on v3510) - v-B2's rule at EVERY width of the tight band, not only at the fixed
        # widths above: round 2's indent dropped a value at 900 / 960 / 980 / 1200-1240, all BETWEEN them
        sweep = []
        for w in SWEEP:
            _set_size(t, w, 1300 if w >= 1280 else 800)
            time.sleep(0.2)
            real, over = json.loads(t.ev(DROP)), json.loads(t.ev(OVER))
            t.ev(FLUSH_ON)
            try:                          # the #231 eye on v3512: the injected style never outlives its measurement
                time.sleep(0.05)
                flush = json.loads(t.ev(DROP))
            finally:
                t.ev(FLUSH_OFF)
            sweep.append({"w": w, "extra": sorted(set(real) - set(flush)), "over": over, "rows": len(real) + 0})
        res["sweep"] = sweep
        # an ACTIVE button under the pointer, pressed by real input first where it is a toggle
        _set_size(t, 2000, 1300)
        t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); return 1; })()")
        time.sleep(0.35)
        hv = {}
        hv["set"] = _hover(t, "#cb-win .cb-settabs .cb-btn.cb-on")
        hv["quests"] = _hover(t, "#cb-win .cb-stats .cb-h-r .cb-btn.cb-on")
        res["input"].append(_press(t, '#cb-win .cb-slot[data-slot="glov"]'))
        res["input"].append(_press(t, "#cb-modal .cb-srow .cb-btn"))
        hv["filters"] = _hover(t, "#cb-modal .cb-srow .cb-btn.cb-on")
        _key(t, "Escape", 27)
        _key(t, "Escape", 27)
        t.ev("(function(){ window.openCharBuilder(); window._cbOpenNew(); return 1; })()")
        time.sleep(0.3)
        res["input"].append(_press(t, "#cb-modal .cb-new-cls .cb-btn", 1))
        hv["class"] = _hover(t, "#cb-modal .cb-new-cls .cb-btn.cb-on")
        res["hover"] = hv
        # #174 v-B4 - LAST, because it makes a new build the selected one: a fresh build, three charms placed through the
        # inventory cell's own picker, the template measured at the builder's five sizes
        _set_size(t, 2000, 1300)
        res["tpl new"] = t.ev(TPL_NEW)
        time.sleep(0.4)
        res["tpl before"] = json.loads(t.ev(TEMPLATE))
        res["tpl placed"] = [json.loads(t.ev(TPL_PLACE % (json.dumps(n), x, y, json.dumps(pre)))) for (n, x, y, pre) in TPL_CHARMS]
        time.sleep(0.3)
        for (w, h) in TPL_WIDTHS:
            _set_size(t, w, h)
            t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); return 1; })()")
            time.sleep(0.4)
            res["tpl charms %dx%d" % (w, h)] = json.loads(t.ev(TEMPLATE))
        res["errors"] = list(getattr(t, "page_errors", []) or [])
        try:
            t.close()
        except Exception:
            pass
    finally:
        RC._chrome_down()
    _CACHE["r"] = res
    return res


def _states():
    r = _measure()
    return [("%s %dx%d" % (s, w, h), r["%s %dx%d" % (s, w, h)]) for (w, h) in WIDTHS for s in STATES]


class TheBuilderFitsAtEveryWidth(unittest.TestCase):

    def test_the_fixture_reached_the_builder_by_real_input(self):
        """PRINT THE DENOMINATOR: a builder that rendered nothing passes every check below."""
        r = _measure()
        self.assertTrue(r.get("opened"), "the Tools card did not open the builder")
        self.assertEqual([x for x in r["input"] if x], [], "a real press or drag did not land: %s" % r["input"])
        st = json.loads(r["store"] or "null")
        self.assertEqual(st, {"head": ["Crown of Ages", {"p2": 28}], "inv": [["Annihilus", 5, 2]]},
                         "the real-input flow did not leave Crown of Ages (roll 28) worn and Annihilus dragged to 6,3")
        for label, m in _states():
            self.assertNotIn("err", m, "%s: %s" % (label, m.get("err")))
            self.assertGreaterEqual(m["nText"], 60, "%s: only %d text nodes measured" % (label, m["nText"]))
        for (w, h) in WIDTHS:
            self.assertEqual((r["worn %dx%d" % (w, h)]["worn"], r["worn %dx%d" % (w, h)]["inv"]), (1, 1))
            self.assertGreater(r["picker %dx%d" % (w, h)]["opts"], 50, "%dx%d: the helm picker listed too little" % (w, h))
            self.assertGreaterEqual(r["edit %dx%d" % (w, h)]["rolls"], 4, "%dx%d: the Edit tab drew no roll boxes" % (w, h))
        self.assertEqual(r.get("errors"), [], "the page threw while the builder was open")

    def test_the_pickers_list_scrolls_to_its_last_row_under_a_real_wheel(self):
        r = _measure()
        bad = []
        for (w, h) in ((375, 812), (2000, 1300)):
            for slot in ("rarm", "feet"):
                x = r["wheel %s %dx%d" % (slot, w, h)]
                if "err" in x:
                    bad.append("%s %dx%d: %s" % (slot, w, h, x["err"]))
                    continue
                a = x["after"]
                if a["rows"] < 40:
                    bad.append("%s %dx%d: PRINT THE DENOMINATOR - only %d rows" % (slot, w, h, a["rows"]))
                if a["listH"] > h:
                    bad.append("%s %dx%d: the list is %dpx tall in a %dpx screen - unbounded, it cannot scroll" % (slot, w, h, a["listH"], h))
                if not a["lastSeen"]:
                    bad.append("%s %dx%d: after 40 wheel notches the last row (%s) is not on screen (scroll %s)"
                               % (slot, w, h, a["name"], a["scroll"]))
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_an_active_button_keeps_its_label_under_the_pointer(self):
        hv = _measure()["hover"]
        bad = []
        for k in ("set", "quests", "filters", "class"):
            x = hv.get(k) or {}
            if "err" in x or not x:
                bad.append("%s: %s" % (k, x.get("err") if x else "not measured"))
            elif not x["hover"]:
                bad.append("%s: the pointer did not rest on it (%s) - UNKNOWN, not passing" % (k, x))
            elif x["color"] == x["bg"]:
                bad.append("%s %r: its text is %s on %s - the label disappears" % (k, x["text"], x["color"], x["bg"]))
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_no_word_or_control_is_cut_or_outside_its_panel(self):
        bad = []
        for label, m in _states():
            bad += ["%s %s" % (label, x) for x in m["cut"] + m["outside"]]
        self.assertEqual(bad, [], "text or a control in the builder is cut or spills out of its panel:\n  " + "\n  ".join(bad[:40]))

    def test_nothing_scrolls_sideways(self):
        bad = []
        for label, m in _states():
            if m["hscroll"][0] > m["hscroll"][1] + 1:
                bad.append("%s the window itself %d/%d" % (label, m["hscroll"][0], m["hscroll"][1]))
            bad += ["%s %s" % (label, x) for x in m["sideways"]]
        self.assertEqual(bad, [], "part of the builder scrolls sideways:\n  " + "\n  ".join(bad[:40]))

    def test_no_header_title_runs_under_its_control(self):
        bad = []
        for label, m in _states():
            bad += ["%s %s" % (label, x) for x in m["collide"]]
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_the_modal_is_on_screen_and_never_hides_the_slot_it_serves(self):
        bad, seen = [], 0
        for label, m in _states():
            if m["modal"] is None:
                continue
            if not m.get("modalInside"):
                bad.append("%s the modal leaves the viewport: %s" % (label, m["modal"]))
            if m["covered"] is not None:
                seen += 1
                if m["covered"]:
                    bad.append("%s the modal covers the glowing slot it serves" % label)
        self.assertGreaterEqual(seen, 8, "the slot-cover check ran in only %d column states" % seen)
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_stats_ends_inside_the_window_and_scrolls_its_own_rows(self):
        """#174 R2 — the Grok seat on R1: "the stats column is cut off at the bottom edge ... rows from Energy down are
        sliced". In columns STATS ends inside the window and its row list scrolls inside it; every row is reachable
        without scrolling the whole builder."""
        bad, seen = [], 0
        for w, h in WIDTHS:
            m = _measure()["plain %dx%d" % (w, h)]
            if m.get("stack"):
                continue
            seen += 1
            if m.get("statsBottom") is None or m["statsBottom"] > m["vh"] + 0.5:
                bad.append("%dx%d: STATS ends %s px past the window's bottom (%s)" % (w, h, None if m.get("statsBottom") is None else round(m["statsBottom"] - m["vh"], 1), m.get("statsBottom")))
            sl = m.get("statsList")
            if not sl or sl[2] not in ("auto", "scroll"):
                bad.append("%dx%d: the stats list does not scroll inside its panel: %s" % (w, h, sl))
        self.assertGreaterEqual(seen, 4, "PRINT THE DENOMINATOR: only %d column layouts measured" % seen)
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_at_2000_the_columns_are_their_literal_322_716_300(self):
        bad = []
        for state in ("plain", "worn"):
            m = _measure()["%s 2000x1300" % state]
            self.assertFalse(m["stack"])
            for c, (x, wd) in THEIR_COLS.items():
                got = m["cols"][c]
                if not got or abs(got[0] - x) > TOL or abs(got[2] - wd) > TOL:
                    bad.append("%s %s: theirs x=%d w=%d, measured %s" % (state, c, x, wd, [round(v, 1) for v in got] if got else None))
            # #174 R1 — his order: "both inventory and character together because the charms are related". The doll
            # and its 10x4 inventory SHARE the 716 centre: the doll is still big (their 292 wide x >= 1.35) and the
            # inventory sits directly under it, as wide as the doll, inside the EQUIPMENT view
            dl, iv = m["doll"], m.get("invRect")
            if not dl or dl[2] < 292 * 1.35:
                bad.append("%s the doll is not big in the centre: %s" % (state, dl))
            if not m.get("invInMain") or not iv:
                bad.append("%s the inventory is not in the EQUIPMENT view with the doll: %s" % (state, iv))
            elif not (iv[1] >= dl[1] + dl[3] and abs((iv[0] + iv[2] / 2) - (dl[0] + dl[2] / 2)) <= 2
                      and abs(iv[2] - dl[2]) <= 0.08 * dl[2]):
                bad.append("%s the inventory %s is not under the doll %s at its width" % (state, iv, dl))
            if m["fsTitle"] is None or abs(m["fsTitle"] - m["tokTitle"]) > 0.05:
                bad.append("%s the header type %s is not the --fs-title token %s at k=1" % (state, m["fsTitle"], m["tokTitle"]))
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_the_edit_tab_with_picked_mods_and_add_mod_open_fits(self):
        """#174 v-B3 - a rare Diadem with four picked mods (shut, and with ADD MOD open) and a magic Grand Charm with two
        (and with its prefix alone and ADD MOD open, its suffixes listed): nothing cut, nothing outside its panel,
        nothing sideways, the modal on screen and off the glowing slot"""
        r, bad = _measure(), []
        for (w, h) in MOD_WIDTHS:
            for state in MOD_STATES:
                label = "%s %dx%d" % (state, w, h)
                m = r[label]
                if "err" in m:
                    bad.append("%s: %s" % (label, m["err"]))
                    continue
                want = MOD_ROWS[state]
                if m["mods"] != want:
                    bad.append("%s: PRINT THE DENOMINATOR - %d picked-mod rows drawn, %d picked" % (label, m["mods"], want))
                if state.endswith("addmod") and m["addOpts"] < 20:
                    bad.append("%s: the open ADD MOD list drew only %d options" % (label, m["addOpts"]))
                if m["nText"] < 40:
                    bad.append("%s: only %d text nodes measured" % (label, m["nText"]))
                bad += ["%s %s" % (label, x) for x in m["cut"] + m["outside"] + m["sideways"] + m["collide"]]
                if m["hscroll"][0] > m["hscroll"][1] + 1:
                    bad.append("%s the window itself scrolls sideways %d/%d" % (label, m["hscroll"][0], m["hscroll"][1]))
                if m["modal"] is None or not m.get("modalInside"):
                    bad.append("%s the modal is not on screen: %s" % (label, m["modal"]))
                if m["covered"]:
                    bad.append("%s the modal covers the glowing slot it serves" % label)
            dm = r["mods %dx%d" % (w, h)]
            if "err" not in dm and dm["rolls"] < 2:
                bad.append("mods %dx%d: Ruby 31-40 and of the Tiger 21-30 drew %d roll boxes" % (w, h, dm["rolls"]))
        self.assertEqual(bad, [], "\n  ".join(bad[:40]))

    def test_the_open_add_mod_list_takes_the_room_of_its_tab(self):
        """#174 v-B3 fix round - the open list lies wholly inside the Edit tab's visible box, and where it has more options
        than fit it runs to that box's bottom: a fixed calc(330 x u) ran ~137px below the modal at 1280x800 (5 of 218
        options in view) and stopped at 158px on a phone with ~220px empty under it"""
        r, bad = _measure(), []
        for (w, h) in MOD_WIDTHS:
            for state in ("addmod", "gcaddmod"):
                label = "fit %s %dx%d" % (state, w, h)
                f = r.get(label)
                if not f:
                    bad.append("%s: no ADD MOD list was measured" % label)
                    continue
                if f["top"] < f["edTop"] - 0.5 or f["bottom"] > f["edBottom"] + 0.5:
                    bad.append("%s: the list (%.0f..%.0f) runs outside the tab's visible box (%.0f..%.0f)" % (label, f["top"], f["bottom"], f["edTop"], f["edBottom"]))
                if f["sh"] > f["ch"] + 1 and f["edBottom"] - f["bottom"] > 40:
                    bad.append("%s: the list stops at %dpx with %.0fpx of the tab empty under it (%d options)" % (label, f["ch"], f["edBottom"] - f["bottom"], f["opts"]))
                if f["seen"] < min(8, f["opts"]):
                    bad.append("%s: PRINT THE DENOMINATOR - %d of %d options in view" % (label, f["seen"], f["opts"]))
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_add_mod_is_a_combobox_by_real_keys(self):
        """#174 v-B3 fix round - their ADD MOD paints the active option, so Enter's pick is seen: by REAL key input, the
        search box keeps focus through ArrowDown, names the active option (aria-activedescendant), which is the one
        painted, the second after one ArrowDown; Enter adds exactly that option"""
        r = _measure()
        self.assertEqual([x for x in r["input"] if x], [], "a real press missed")
        c = r["combo"]
        self.assertEqual((c["typed"]["focus"], c["typed"]["role"]), ("cb-add-q", "combobox"))
        self.assertEqual(c["typed"]["acts"], 1, "after typing, not exactly one option is active: %s" % c["typed"])
        self.assertEqual(c["down"]["focus"], "cb-add-q", "ArrowDown took the focus out of the search box")
        self.assertEqual(c["down"]["active"], c["down"]["second"], "ArrowDown did not make the second option active: %s" % c["down"])
        self.assertNotIn(c["down"]["painted"], (None, "rgba(0, 0, 0, 0)", "transparent"), "the active option is not painted: %s" % c["down"])
        self.assertEqual(c["down"]["acts"], 1)
        self.assertEqual(c["enter"]["stored"], ["p712", "s175", c["down"]["activeId"]],
                         "Enter did not add the painted option %s: %s" % (c["down"]["activeId"], c["enter"]))

    def test_round2_the_pointer_and_the_keys_light_one_row(self):
        """#174 round 2 (the Grok seat on v3509, img3): the keyboard's active option and the row under the pointer were
        painted in one gold, so two rows lit and nothing said which one Enter adds. By REAL input: the pointer at rest on
        the 4th option makes it the one active and the ONLY one painted; a real ArrowDown with the pointer still there
        moves the active option on, and still exactly one row is painted"""
        r = _measure()
        self.assertEqual([x for x in r["input"] if x], [], "a real press or pointer move missed")
        p, d = r["lit"]["pointer"], r["lit"]["down"]
        self.assertGreater(p["n"], 4, "PREMISE: the open list has too few options to point at the 4th: %s" % p)
        self.assertEqual(p["under"], 3, "PREMISE: the pointer is not on the 4th option: %s" % p)
        self.assertEqual((p["active"], p["lit"]), (3, [3]), "the row under the pointer is not the one active and the only one lit: %s" % p)
        self.assertEqual((d["active"], d["lit"]), (4, [4]), "after ArrowDown under a still pointer, not exactly the new active row is lit: %s" % d)

    def test_round2_a_wrapped_stat_label_sets_its_second_line_in(self):
        """#174 round 2 (the Grok seat on v3509, img2 AND img3): "Fire" / "Resistance" with the value on the first line
        read as a row "Resistance" with no value. Every label that wraps sets its continuation line in (a hanging indent),
        so the second line reads as the rest of the label - v-B2's rule (the value keeps the first line) stands"""
        rows = _measure()["indent"]
        self.assertGreater(len(rows), 0, "PREMISE: no stat label wraps at 1280, so this measured nothing")
        flat = ["%s (first %.1f, next %.1f)" % (x["text"], x["first"], x["next"]) for x in rows if x["next"] - x["first"] < 2]
        self.assertEqual(flat, [], "these labels wrap flush, so their second line reads as a row of its own: %s" % flat)

    def test_round3_the_indent_costs_no_row_its_first_line_at_any_width(self):
        """#174 round 3 (the Grok seat on v3510, measured): round 2's hanging indent padded the label, the padding counted
        toward its min-content, and at 6 of 56 widths a value dropped under its label - v-B2's rule undone by the fix
        for the next complaint. Swept every 20px of the tight band (900-1400) against the same page with the indent
        taken away: the indent makes NO extra value drop, and no label text runs under its value"""
        sw = _measure()["sweep"]
        self.assertEqual(len(sw), len(SWEEP), "PREMISE: the band was not swept end to end: %d of %d widths" % (len(sw), len(SWEEP)))
        extra = [(x["w"], x["extra"]) for x in sw if x["extra"]]
        over = [(x["w"], x["over"]) for x in sw if x["over"]]
        self.assertEqual(extra, [], "the indent pushed these values under their labels (v-B2's rule): %s" % extra)
        self.assertEqual(over, [], "label text runs under its value at these widths: %s" % over)

    def test_round7_a_pick_never_covers_stats_and_a_charm_shows_its_art(self):
        """#174 round 7 (2026-09-26, measured): their STATS update while you pick and edit, so they stay in view - an
        inventory cell's picker fell back to the PAGE centre at 1120-1280 and covered STATS' left edge by 25-28px (a
        slot's never did). Every pick measured here (a slot's Select / Edit / mods / ADD MOD, a charm's mods / ADD MOD),
        side-by-side layout: the modal ends left of STATS. #174 v-B4: the grid sits in the template panel now, so an
        inventory cell's picker takes the side away from the GRID; its page-centre fallback is still reached at 1024x768
        and 901x900, so an inventory cell's Select is measured at every width. And a Grand Charm's Edit tile draws its in-game sprite - it
        printed "Grand Charm" in a box because only Small Charm was ever registered by its base name"""
        r, bad, seen = _measure(), [], 0
        for key, m in r.items():
            if not isinstance(m, dict) or not m.get("modal") or not m.get("cols") or m.get("stack"):
                continue
            if not key.split(" ")[0] in ("picker", "edit", "mods", "addmod", "gcmods", "gcaddmod", "invpick"):
                continue
            seen += 1
            # the modal rect is in the VIEWPORT frame; cols.* are relative to the builder box - compare like with like
            ml, mw, sl = m["modal"][0], m["modal"][2], m.get("statsLeftAbs")
            if sl is None:
                bad.append("%s: STATS' left edge was not measured" % key)
                continue
            if ml + mw > sl + 0.5:
                bad.append("%s: the modal ends at %.0f, STATS starts at %.0f (%.0fpx covered)" % (key, ml + mw, sl, ml + mw - sl))
        self.assertGreater(seen, 10, "PREMISE: only %d pick states with a modal were measured" % seen)
        self.assertEqual(bad, [], "a pick covers STATS, which their Edit keeps in view: %s" % bad)
        arts = dict((k, v) for k, v in r.items() if k.startswith("gcart "))
        self.assertEqual(len(arts), len(MOD_WIDTHS) * 2, "PREMISE: the charm's art was not probed at every width: %s" % sorted(arts))
        noart = [k for k, v in arts.items() if not v["img"] or v["failed"]]
        self.assertEqual(noart, [], "a Grand Charm's Edit tile has no art (its name in a box): %s" % noart)

    def test_under_900_the_character_comes_first(self):
        for (w, h) in WIDTHS:
            m = _measure()["worn %dx%d" % (w, h)]
            if w >= 900:
                self.assertFalse(m["stack"], "%dx%d stacked" % (w, h))
                continue
            self.assertTrue(m["stack"], "%dx%d did not stack" % (w, h))
            self.assertLess(m["cols"]["main"][1], m["cols"]["stats"][1], "%dx%d: the doll is not above the stats" % (w, h))
            self.assertLess(m["cols"]["main"][1], m["cols"]["left"][1], "%dx%d: the doll is not above the inventory" % (w, h))

    def test_v_b4_the_character_and_its_inventory_are_one_panel_the_games_grid_flush_under_the_doll(self):
        """#174 v-B4 - his words: "the character template is actually an inventory/character template they always open and
        are seen as a set together" and "the INVENTORY under the equipment need to be structured like this JUST LIKE IT IS
        IN GAME one to one". Theirs (planner 60/61, 15_crop): ONE carved-stone panel, the doll and flush under it the 10x4
        grid - black cells, thin lines, no gaps, no rounded corners. v3514's was a framed doll, a caption, then a separate
        grid with 2px gaps and rounded cells. In every plain / worn state at the 7 widths and with three charms at the
        builder's 5 sizes: the grid and the doll lie inside the one panel, flush (<= 12px, no word between), the caption
        and the status line under it, 10 x 4 equal square cells edge to edge, radius 0, the grid never wider than the
        doll's inner width, cells >= 26px from 1280 up, every item inside its cells"""
        r, bad = _measure(), []
        tpl = sorted(k for k in r if k.startswith("tpl ") and isinstance(r[k], dict) and k != "tpl before")
        want = ["tpl %s %dx%d" % (s, w, h) for s in ("plain", "worn") for (w, h) in WIDTHS] + \
               ["tpl charms %dx%d" % (w, h) for (w, h) in TPL_WIDTHS]
        self.assertEqual(sorted(want), tpl, "PRINT THE DENOMINATOR: the template was not measured in every state")
        for k in want:
            m = r[k]
            if "err" in m:
                bad.append("%s: %s" % (k, m["err"]))
                continue
            w = int(k.rsplit(" ", 1)[1].split("x")[0])
            p, dl, g = m["panel"], m["doll"], m["grid"]
            inside = lambda a: a[0] >= p[0] - 0.5 and a[1] >= p[1] - 0.5 and a[2] <= p[2] + 0.5 and a[3] <= p[3] + 0.5
            if not (m["gridInDom"] and inside(g)):
                bad.append("%s: the inventory %s is not inside the template panel %s (in its markup: %s)"
                           % (k, [round(v) for v in g], [round(v) for v in p], m["gridInDom"]))
            if not (m["dollInDom"] and inside(dl)):
                bad.append("%s: the doll %s is not inside the template panel %s" % (k, [round(v) for v in dl], [round(v) for v in p]))
            gap = g[1] - dl[3]
            if gap < -0.5 or gap > TPL_FLUSH:
                bad.append("%s: the grid's top is %.1fpx from the doll's bottom - not flush (theirs ~9, at most %d)" % (k, gap, TPL_FLUSH))
            if m["between"]:
                bad.append("%s: words between the doll and its inventory: %s" % (k, m["between"]))
            b = m["below"]
            for nm in ("caption", "status"):
                if b[nm] is None or b[nm + "InPanel"] or b[nm][1] < p[3] - 0.5:
                    bad.append("%s: the %s line is not under the template panel (%s, panel ends at %.0f)" % (k, nm, b[nm], p[3]))
            if m["nCells"] != 40 or len(m["cols"]) != 10 or len(m["rows"]) != 4:
                bad.append("%s: PRINT THE DENOMINATOR - %d cells, %d columns, %d rows (10 x 4)" % (k, m["nCells"], len(m["cols"]), len(m["rows"])))
                continue
            cw, ch = m["cellW"], m["cellH"]
            if max(cw) - min(cw) > 0.05 or max(ch) - min(ch) > 0.05 or abs(cw[0] - ch[0]) > 0.05:
                bad.append("%s: the cells are not equal squares (widths %.2f-%.2f, heights %.2f-%.2f)" % (k, min(cw), max(cw), min(ch), max(ch)))
            seams = [round(m["cols"][i + 1][0] - m["cols"][i][1], 2) for i in range(9)] + \
                    [round(m["rows"][i + 1][0] - m["rows"][i][1], 2) for i in range(3)]
            if any(abs(s) > 0.05 for s in seams) or any(x not in ("0px", "normal") for x in m["gap"]):
                bad.append("%s: the cells are not edge to edge - gap %s, seams %s" % (k, m["gap"], seams))
            if m["radius"] != ["0px"] * 4 or m["cellRadius"] != ["0px 0px 0px 0px"]:
                bad.append("%s: rounded corners - grid %s, cells %s" % (k, m["radius"], m["cellRadius"]))
            cbx = m["cellsBox"]
            if not (cbx[0] >= g[0] - 0.5 and cbx[1] >= g[1] - 0.5 and cbx[2] <= g[2] + 0.5 and cbx[3] <= g[3] + 0.5) or not inside(cbx):
                bad.append("%s: the cells %s spill out of their grid %s / the panel %s"
                           % (k, [round(v) for v in cbx], [round(v) for v in g], [round(v) for v in p]))
            span = max(g[2], cbx[2]) - min(g[0], cbx[0])
            if span > m["dollInner"] + 0.5:
                bad.append("%s: the grid and its cells (%.1fpx) are wider than the doll's inner width (%dpx)" % (k, span, m["dollInner"]))
            if w >= 1280 and cw[0] < TPL_MIN_CELL:
                bad.append("%s: a cell is %.1fpx - under %dpx from 1280 up" % (k, cw[0], TPL_MIN_CELL))
            for it in m["items"]:
                c, rc = it["cells"], it["rect"]
                if not c or rc[0] < c[0] - 0.5 or rc[1] < c[1] - 0.5 or rc[2] > c[2] + 0.5 or rc[3] > c[3] + 0.5:
                    bad.append("%s: %s at %s is drawn at %s, outside its cells %s" % (k, it["name"], it["at"], [round(v, 1) for v in rc], c and [round(v, 1) for v in c]))
            if k.startswith("tpl worn") and len(m["items"]) != 1:
                bad.append("%s: PRINT THE DENOMINATOR - %d items drawn, Annihilus alone was placed" % (k, len(m["items"])))
        # the three charms: placed through the cell's own picker, each drawn with its art in its cells, and they MOVE the stats
        placed = r.get("tpl placed") or []
        self.assertEqual(r.get("tpl new"), "ok", "the builder's + New build did not make a fresh build: %s" % r.get("tpl new"))
        self.assertEqual([(x.get("n"), x.get("ok")) for x in placed], [(n, True) for (n, _, _, _) in TPL_CHARMS],
                         "a charm was not placed through the inventory's picker: %s" % placed)
        before = r["tpl before"]
        self.assertNotIn("err", before, before.get("err"))
        self.assertEqual(before["items"], [], "PREMISE: the fresh build's inventory is not empty")
        for (w, h) in TPL_WIDTHS:
            m = r["tpl charms %dx%d" % (w, h)]
            if "err" in m:
                continue
            got = sorted((it["name"], tuple(it["at"][:2]), it["art"]) for it in m["items"])
            exp = sorted((n, (x, y), True) for (n, x, y, _) in TPL_CHARMS)
            if got != exp:
                bad.append("charms %dx%d: drawn %s, placed %s (name, cell, art)" % (w, h, got, exp))
            for key in ("allSkills", "strength"):
                if m["stats"][key] is None or before["stats"][key] is None or m["stats"][key] == before["stats"][key]:
                    bad.append("charms %dx%d: the charms did not move STATS' %s (%s before, %s with them)"
                               % (w, h, key, before["stats"][key], m["stats"][key]))
        self.assertEqual(bad, [], "the character/inventory template is not one panel with the game's grid:\n  " + "\n  ".join(bad[:40]))


RED_PROOF = [
    {
        "why": "#174 v-B4 - the inventory's 2px gaps come back: the cells are no longer edge to edge like the game's grid",
        "file": "bible.html",
        "find": ".cb-inv{--cb-inv-line:rgb(74,66,60);--cb-inv-cell:rgb(3,3,3);position:relative;margin:0 auto;display:grid;gap:0;padding:0;",
        "replace": ".cb-inv{--cb-inv-line:rgb(74,66,60);--cb-inv-cell:rgb(3,3,3);position:relative;margin:0 auto;display:grid;gap:2px;padding:0;",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the caption is drawn between the doll and its inventory again (v3514's 'Click a slot ...' line)",
        "file": "bible.html",
        "find": "    return '<div class=\"cb-eqp\" id=\"cb-eqp\">' + doll + inv + '</div>';\n",
        "replace": "    return '<div class=\"cb-eqp\" id=\"cb-eqp\">' + doll + '<div class=\"cb-doll-say\">Click a slot to choose from the entire item database</div>' + inv + '</div>';\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the inventory escapes the template panel: a separate box under the doll again, not one set",
        "file": "bible.html",
        "find": "    return '<div class=\"cb-eqp\" id=\"cb-eqp\">' + doll + inv + '</div>';\n",
        "replace": "    return '<div class=\"cb-eqp\" id=\"cb-eqp\">' + doll + '</div>' + inv;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - an item is drawn on the old gapped pitch and drifts out of the cells it occupies",
        "file": "bible.html",
        "find": "    var pitch = L.cell;   /* #174 v-B4",
        "replace": "    var pitch = L.cell + 2;   /* #174 v-B4",
        "matches": 1,
    },
    {
        "why": "#174 v-B4 - the grid's cells outgrow the doll: the inventory is wider than the doll it sits under",
        "file": "bible.html",
        "find": "  function _cbCellPx(dk){ return Math.max(12, Math.floor((CB_DOLL_WH[0] * dk - 1) / 10)); }",
        "replace": "  function _cbCellPx(dk){ return Math.max(12, Math.floor((CB_DOLL_WH[0] * dk + 40) / 10)); }",
        "matches": 1,
    },
    {
        "why": "#174 round 7 - an inventory pick falls back to the page centre again and covers STATS by 25-28px",
        "file": "bible.html",
        "find": "        if (left + W > _sl){ left = Math.max(8, _sl - W); if (left + W > _sl) W = Math.max(360, _sl - left); }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 round 7 - a Grand Charm is not registered by its base name again: its Edit tile prints its name in a box",
        "file": "bible.html",
        "find": "D2IO_ART['Grand Charm'] = 'art/hd_charm_large.png';",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 round 3 - the indent's width is not given back: at 960 and 1200 a value drops under its label again (v-B2)",
        "file": "bible.html",
        "find": "text-indent:calc(-6*var(--u));margin-right:calc(-6*var(--u))}\n",
        "replace": "text-indent:calc(-6*var(--u))}\n",
        "matches": 1,
    },
    {
        "why": "#174 round 2 - a wrapped stat label's second line sits flush again ('Resistance' reads as a row with no value)",
        "file": "bible.html",
        "find": ".cb-st-r .cb-sl{flex:1 1 0;min-width:auto;overflow-wrap:normal;padding-left:calc(6*var(--u));text-indent:calc(-6*var(--u));margin-right:calc(-6*var(--u))}\n",
        "replace": ".cb-st-r .cb-sl{flex:1 1 0;min-width:auto;overflow-wrap:normal}\n",
        "matches": 1,
    },
    {
        "why": "#174 round 2 - the pointer no longer moves the active option: the row under it is not the one Enter adds",
        "file": "bible.html",
        "find": " onmousemove=\"window._cbModHover(event)\">",
        "replace": ">",
        "matches": 1,
    },
    {
        "why": "#174 round 2 - :hover paints a second gold row beside the active one again",
        "file": "bible.html",
        "find": ".cb-add-o:focus-visible{background:rgba(214,170,90,.22);outline:none}",
        "replace": ".cb-add-o:hover,.cb-add-o:focus-visible{background:rgba(214,170,90,.22);outline:none}",
        "matches": 1,
    },
    {
        "why": "#174 R2 - the builder's STATS grows with its rows again and runs off the bottom of the window (the Grok seat: rows from Energy down sliced)",
        "file": "bible.html",
        "find": ".cb:not(.cb-stack) .cb-stats{min-height:0;height:calc(100vh - 30px - 66*var(--u))}\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the open ADD MOD list keeps a fixed height, below the modal at 1280x800",
        "file": "bible.html",
        "find": "    if (st.modOpen && st.pick) _cbFitAddList();\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the active ADD MOD option is not painted (what Enter adds is invisible)",
        "file": "bible.html",
        "find": ".cb-add-o.cb-act{background:rgba(214,170,90,.30);box-shadow:inset 3px 0 0 var(--gold)}",
        "replace": ".cb-add-o.cb-act{}",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 fix round - the search box ignores ArrowDown and Enter (ADD MOD is no combobox)",
        "file": "bible.html",
        "find": " onkeydown=\"window._cbModKey(event)\">",
        "replace": ">",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the open ADD MOD list stops scrolling inside its box and clips its options",
        "file": "bible.html",
        "find": ".cb-add-list{max-height:calc(330*var(--u));min-height:120px;overflow:auto;",
        "replace": ".cb-add-list{max-height:calc(330*var(--u));min-height:120px;overflow:hidden;",
        "matches": 1,
    },
    {
        "why": "#174 v-B3 - the Edit tab's controls row (Item level · Quality · Name · Base · Defense · Sockets · Ethereal) "
               "stops wrapping and runs out of the modal on a phone",
        "file": "bible.html",
        "find": ".cb-ctls{display:flex;flex-wrap:wrap;gap:calc(8*var(--u));margin-top:calc(10*var(--u))}",
        "replace": ".cb-ctls{display:flex;flex-wrap:nowrap;gap:calc(8*var(--u));margin-top:calc(10*var(--u))}",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 fix round - the stacked picker's pane is unbounded again: at 375 the list grows to its rows and never scrolls",
        "file": "bible.html",
        "find": ".cb-sheet .cb-pane{min-height:0}",
        "replace": ".cb-sheet .cb-pane{min-height:auto}",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 fix round - an active gold button under the pointer paints its label gold on gold again",
        "file": "bible.html",
        "find": ".cb-btn.cb-on:hover:not([disabled]){color:#1a1208;border-color:var(--gold-bright)}",
        "replace": ".cb-btn.cb-on:hover:not([disabled]){border-color:var(--gold-bright)}",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a prose panel gets a fixed height and clips its words (the class that cut the mule window)",
        "file": "bible.html",
        "find": ".cb-prim{min-height:calc(102*var(--u))}.cb-merc{min-height:calc(80*var(--u))}",
        "replace": ".cb-prim{min-height:calc(102*var(--u))}.cb-merc{height:calc(34*var(--u));overflow:hidden}",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the modal is centred, so it covers the glowing slot it serves",
        "file": "bible.html",
        "find": "      if (r.right <= cx + 1){ left = r.right + 12; W = Math.min(W0, roomR); }\n      else { W = Math.min(W0, roomL); left = r.left - 12 - W; }\n",
        "replace": "      W = W0; left = (vw - W) / 2;\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - the columns leave their literal 322 | 716",
        "file": "bible.html",
        "find": ".cb-lc{display:grid;grid-template-columns:calc(322*var(--u)) calc(716*var(--u));",
        "replace": ".cb-lc{display:grid;grid-template-columns:calc(360*var(--u)) calc(678*var(--u));",
        "matches": 1,
    },
    {
        "why": "#174 v-B2 - a phone keeps the desktop width and the builder scrolls sideways",
        "file": "bible.html",
        "find": "grid-template-areas:\"top\" \"set\" \"main\" \"stats\" \"left\" \"notes\";width:100%}",
        "replace": "grid-template-areas:\"top\" \"set\" \"main\" \"stats\" \"left\" \"notes\";width:calc(1350*var(--u))}",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if not os.path.exists(RC.CHROME):
        sys.stderr.write("⚪ SKIP — %s. UNMEASURED, declared as a skip (77), never a pass.\n" % NO_BROWSER)
        raise SystemExit(77)
    unittest.main(verbosity=2)
