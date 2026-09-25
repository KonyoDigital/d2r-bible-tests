# -*- coding: utf-8 -*-
"""#174 — THE MULE WINDOW FITS AT EVERY WIDTH, MEASURED IN A REAL BROWSER, NOT READ FROM ITS HTML.

THE DEFECT THIS EXISTS FOR, and why the sibling law could not see it. test_the_mule_window_is_the_planner_shell
drives the shipped openMuleCard in node and reads the HTML it writes. Every panel said what would fill it — the
law checked the words were THERE. On screen, between 900 and 1250 wide, they were not all visible:

    1120x628 (his console width)  the MERCENARY note's last line, the one carrying "(v-C)", cut in half
    1024x768                      "STRENGTHS AND WEAKNESSES" read "TRENGTHS AND WEAKNESSE"; the Stash button
                                  touching the EQUIPMENT title; "Character — none bound…" clipped
    920x800                       the Stash button over the title ("EQUIPMEN"); three notes under their panels
    375x812                       the stash's gold box and the mule tab row scrolling sideways; the header
                                  sub-line ellipsized

Every length in the window was N * --u and the type was fixed px, so the boxes shrank and the words did not.
innerHTML cannot show that: a clipped sentence and a visible one are the same string. Only layout can.
[[visual-regression-detector]] [[regression-guard]] (a presence-law is not a reachability-law)

WHAT IS MEASURED, per width (2000x1300, 1280x800, 1120x628, 1024x768, 901x900, 800x1000, 375x812):
  · no text node in the window is cut by an overflow:hidden/clip ancestor, or lies outside its panel unless it
    is inside a scroller (one scroll away is reachable; cut is destroyed) — and no CONTROL (a tab, a button, a
    slot) has its box sliced by what contains it, words or not
  · nothing in the window scrolls sideways, and the window itself never scrolls sideways
  · no panel header's title runs into its control
  · the window's type is its token times min(1, k), floored at the smallest token (--fs-micro)
  · at 2000x1300 the panels and the ten doll slots are their measured rects (spec §1); at 1280 they are those
    rects times k
and once, on a phone (390x844): a keyboard opening (a HEIGHT-only resize) leaves the Stats search box the SAME
node with the caret in it, and a background re-render (an item assigned while it is up) puts the caret back.

#174 v-B — THE SAME QUESTIONS, ASKED AGAIN WITH THE DOLL IN USE. Every width is measured a second time with three
items equipped (a weapon, two rings — worn art, the ✕ controls, stat values with their source tags) and the picker
open on the left hand (its list, its "left out" footer): new words in new boxes are exactly what v-A's pass cannot
see. And the geometry at 2000 is their rects with the ONE declared upgrade (spec §5): the EQUIPMENT body on the
doll's unit, DOLL_K = 1.25 — THEIR_PANELS stays their capture, `_ours()` applies the upgrade to it.

#174 v-B review — THE EQUIP PASS IS REAL INPUT, and THE GOLD BOX IS ONE LINE.
  · The doll is filled the way he fills it: a CDP mouse press and release at the centre of the slot, then at the
    centre of the option — each time checking the point lands on that element (elementFromPoint), so a control
    covered by something else fails here instead of being clicked through by a programmatic .click().
  · "N worn on the doll · M on this mule" wrapped the stash's gold box to two lines at 2000 wide; the stash cell
    budget (_mpLayout) assumes one, so the stash view scrolled 1.5px and cut the box's border. Every width in
    columns now requires the gold box to be one line and the stash view not to scroll, plain and with the doll in use.
  · The worn weapon is Lightsabre (one-handed): beside Windforce the left hand now offers only its quiver, which
    this locker does not hold — an empty picker would measure nothing.

⚠ ITS OWN BROWSER, ON ITS OWN PORT. A free port is chosen here and exported before render_check is imported,
so this law never adopts a Chrome something else started (REG-1258) and two lanes of heart2 never share one.
The Chrome it starts is killed by the handle it holds, and its temp profile goes with it.
⚠ NO CHROME ON THIS MACHINE = a DECLARED skip (exit 77), never a pass. Chrome installed and refusing to start is
a FAILURE, not a venue fact.
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


# ⚠ BEFORE the import: render_check reads its port once, at import time.
os.environ["TV_RENDER_PORT"] = str(_free_port())
import render_check as RC  # noqa: E402

from test_the_mule_window_is_the_planner_shell import THEIR_SLOTS, DOLL_K, THEIR_EQ  # noqa: E402  ONE witness table

NO_BROWSER = "no Chrome/Chromium on this machine, so the mule window was not rendered"
WIDTHS = ((2000, 1300), (1280, 800), (1120, 628), (1024, 768), (901, 900), (800, 1000), (375, 812))
MULE = "uni-weap"
ITEMS = ["Windforce", "Doombringer", "The Grandfather", "Stormlash", "Lightsabre", "Nagelring", "Raven Frost"]

# their builder at 2000x1300, relative to the content column (spec §1): x, y, w, h
THEIR_PANELS = {
    "mp-set": (0, 98, 1044, 84), "mp-eq": (0, 188, 322, 400), "mp-prim": (0, 594, 322, 102),
    "mp-merc": (0, 702, 322, 80), "mp-loot": (0, 788, 322, 88), "mp-sw": (0, 882, 322, 57),
    "mp-cp": (328, 188, 716, 628), "mp-notes": (328, 822, 716, 206),
    "mp-auth": (1050, 0, 300, 150), "mp-show": (1050, 156, 300, 150), "mp-stats": (1050, 312, 300, 726),
}
TOL_2000 = 4.0          # spec §4: ±4 px at 2000 wide
SW_TOL = 4.0            # S&W is measured off their PNG (182..239), the least exact of the reference numbers
LEFT_PANELS = ("mp-eq", "mp-prim", "mp-merc", "mp-loot", "mp-sw")
CENTRE_PANELS = ("mp-cp", "mp-notes")


def _ours(c):
    """THEIR panel rect with the one declared v-B upgrade: the LEFT column is their 322 on the doll's unit, the
    EQUIPMENT panel their 36px header + their 364px body on it, so every left panel below EQUIPMENT moves down by
    what EQUIPMENT grew and the centre moves right and narrows by what LEFT grew. Nothing else moves."""
    x, y, w, h = THEIR_PANELS[c]
    grow_w = 322 * DOLL_K - 322
    grow_h = (THEIR_EQ[0] + THEIR_EQ[1] * DOLL_K) - sum(THEIR_EQ)
    if c in LEFT_PANELS:
        w = 322 * DOLL_K
        if c == "mp-eq":
            h = THEIR_EQ[0] + THEIR_EQ[1] * DOLL_K
        else:
            y += grow_h
    elif c in CENTRE_PANELS:
        x, w = x + grow_w, w - grow_w
    return (x, y, w, h)


def _our_slot(s):
    """their slot rect, on the doll's unit, under their 36px header"""
    x, y, w, h = THEIR_SLOTS[s]
    return (x * DOLL_K, THEIR_EQ[0] + (y - THEIR_EQ[0]) * DOLL_K, w * DOLL_K, h * DOLL_K)

SEED = r"""(function(items, mule){
  try { localStorage.setItem('d2r_ownerClaim','*'); } catch(e){}
  var ok = 0;
  items.forEach(function(n){ try { window.tvVaultRegister(n); window.vaultAssign(n, mule); ok++; } catch(e){} });
  return ok; })(%s, %s)"""

MEASURE = r"""(function(){ try {
  var d = document, box = d.getElementById('vault-detail'), mp = box && box.querySelector('.mp');
  if (!mp) return JSON.stringify({ err: 'the mule window did not render (.mp absent)' });
  var ob = mp.getBoundingClientRect();
  var rel = function(el, b){ if (!el) return null; var r = el.getBoundingClientRect(); b = b || ob;
    return [r.left - b.left, r.top - b.top, r.width, r.height]; };
  var sv = box.querySelector('.mp-v-stash'), gb = box.querySelector('.mp-v-stash .vd-goldbox'), gl = null;
  if (gb && sv && !sv.hidden){ var gs = getComputedStyle(gb), gr = gb.getBoundingClientRect();
    gl = (gr.height - parseFloat(gs.paddingTop) - parseFloat(gs.paddingBottom) - parseFloat(gs.borderTopWidth) - parseFloat(gs.borderBottomWidth)) / parseFloat(gs.lineHeight); }
  var out = { k: +mp.getAttribute('data-k'), goldLines: gl, goldText: gb ? gb.textContent : null,
    stashScroll: (sv && !sv.hidden) ? [sv.scrollHeight, sv.clientHeight] : null,
    stack: mp.classList.contains('mp-stack'), hscroll: [box.scrollWidth, box.clientWidth], panels: {}, slots: {},
    cut: [], outside: [], sideways: [], collide: [], nText: 0,
    worn: box.querySelectorAll('.mp-slot.mp-has').length, sv: box.querySelectorAll('.mp-sv').length,
    pick: box.querySelectorAll('.mp-pick').length, opts: box.querySelectorAll('.mp-pick .mp-opt').length };
  ['mp-set','mp-eq','mp-prim','mp-merc','mp-loot','mp-sw','mp-cp','mp-notes','mp-auth','mp-show','mp-stats'].forEach(function(c){
    out.panels[c] = rel(box.querySelector('.' + c)); });
  var eo = box.querySelector('.mp-eq').getBoundingClientRect();
  [].forEach.call(box.querySelectorAll('.mp-slot'), function(s){ out.slots[s.getAttribute('data-slot')] = rel(s, eo); });
  var root = getComputedStyle(d.documentElement);
  out.tokens = { title: parseFloat(root.getPropertyValue('--fs-title')), meta: parseFloat(root.getPropertyValue('--fs-meta')),
                 micro: parseFloat(root.getPropertyValue('--fs-micro')) };
  var ht = box.querySelector('.mp-h-t'), em = box.querySelector('.mp-left .mp-empty');
  out.fs = { title: ht ? parseFloat(getComputedStyle(ht).fontSize) : null, meta: em ? parseFloat(getComputedStyle(em).fontSize) : null };
  /* every visible text node: the first ancestor that does not show overflow decides its fate */
  var tw = d.createTreeWalker(mp, NodeFilter.SHOW_TEXT), n;
  while ((n = tw.nextNode())){
    var t = n.textContent.trim(); if (!t) continue;
    var el = n.parentElement; if (el.closest('[hidden]')) continue;
    /* an item TILE clips its own art by design — a 1x1 ring is one grid cell, and when the art file is absent
       (a sandbox has no art/) its fallback glyph is art too, read by its tooltip. Prose is what must not be cut. */
    if (el.closest('.vd-item')) continue;
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
      var ar = a.getBoundingClientRect(), cl = ar.left + a.clientLeft, ct = ar.top + a.clientTop,
          cr = cl + a.clientWidth, cb = ct + a.clientHeight;
      var hx = (L < cl - 0.5 || R > cr + 0.5), hy = (T < ct - 0.5 || B > cb + 0.5);
      var hid = function(o){ return o === 'hidden' || o === 'clip'; };
      if ((hx && hid(s.overflowX)) || (hy && hid(s.overflowY)))
        out.cut.push(String(a.className).slice(0, 30) + ' cuts "' + t.slice(0, 48) + '"'
          + (hx ? ' by ' + Math.max(cl - L, R - cr).toFixed(1) + 'px across' : '') + (hy ? ' by ' + Math.max(ct - T, B - cb).toFixed(1) + 'px down' : ''));
      scrolled = !hid(s.overflowX) || !hid(s.overflowY);
      break;
    }
    var p = el.closest('.mp-p');
    if (p && !scrolled){ var pr = p.getBoundingClientRect();
      if (B > pr.bottom + 0.5 || R > pr.right + 0.5 || L < pr.left - 0.5)
        out.outside.push('"' + t.slice(0, 40) + '" outside ' + String(p.className).replace('mp-p ', '')); }
  }
  /* a CONTROL cut by its container is the same defect with no words in it: a tab whose right edge is sliced off
     reads as a broken tab even when its label survives. Its whole border box must be inside what clips it. */
  [].forEach.call(mp.querySelectorAll('button,[onclick],.mp-settab,.mp-slot,.mp-box,.mp-cls,.mp-search'), function(e){
    if (e.closest('.vd-item') || e.closest('[hidden]')) return;
    var r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return;
    for (var a = e.parentElement; a && a !== box; a = a.parentElement){
      var s = getComputedStyle(a); if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
      var hid = function(o){ return o === 'hidden' || o === 'clip'; };
      var ar = a.getBoundingClientRect(), cl = ar.left + a.clientLeft, ct = ar.top + a.clientTop,
          cr = cl + a.clientWidth, cb = ct + a.clientHeight;
      var dx = Math.max(cl - r.left, r.right - cr), dy = Math.max(ct - r.top, r.bottom - cb);
      if ((dx > 0.5 && hid(s.overflowX)) || (dy > 0.5 && hid(s.overflowY)))
        out.cut.push(String(a.className).slice(0, 30) + ' cuts the control ' + String(e.className || e.tagName).slice(0, 34)
          + ' "' + (e.textContent || '').trim().slice(0, 30) + '" by ' + Math.max(dx, dy).toFixed(1) + 'px');
      break;
    }
  });
  [].forEach.call(mp.querySelectorAll('*'), function(e){ var s = getComputedStyle(e);
    if ((s.overflowX === 'auto' || s.overflowX === 'scroll') && e.scrollWidth > e.clientWidth + 1)
      out.sideways.push(String(e.className).slice(0, 30) + ' ' + e.scrollWidth + '/' + e.clientWidth); });
  /* the title is its own span, or — on markup that lost it — the header's first words; either way it is ink */
  [].forEach.call(box.querySelectorAll('.mp-h'), function(h){
    var c = h.querySelector('.mp-h-r'); if (!c || !c.firstElementChild) return;
    var t = h.querySelector('.mp-h-t');
    if (!t) for (var x = h.firstChild; x; x = x.nextSibling) if (x.nodeType === 3 && x.textContent.trim()){ t = x; break; }
    if (!t) return;
    var rg = d.createRange(); rg.selectNodeContents(t); var tr = rg.getBoundingClientRect(), cr = c.getBoundingClientRect();
    if (tr.right > cr.left + 0.5 && tr.bottom > cr.top && tr.top < cr.bottom)
      out.collide.push('"' + t.textContent.trim() + '" runs ' + (tr.right - cr.left).toFixed(1) + 'px under its control'); });
  return JSON.stringify(out);
 } catch(e){ return JSON.stringify({ err: String(e) }); } })()"""

#: #174 v-B review — equip through the window's own picker with REAL INPUT: the centre of an element, scrolled into
#: view, is hit-tested (elementFromPoint must be that element or inside it) and then pressed with CDP mouse events.
#: A programmatic .click() skips hit-testing, so a covered or clipped control would be "clicked" anyway.
AIM = r"""(function(sel, i){ var e = document.querySelectorAll(sel)[i]; if (!e) return JSON.stringify(null);
  e.scrollIntoView({ block: 'center', inline: 'nearest' }); var r = e.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  var at = document.elementFromPoint(x, y); return JSON.stringify({ x: x, y: y, hit: !!(at && (at === e || e.contains(at))) }); })(%s, %d)"""
OPT_AT = r"""(function(want){ var o = document.querySelectorAll('#vault-detail .mp-pick .mp-opt');
  for (var i = 0; i < o.length; i++) if ((o[i].textContent || '').indexOf(want) >= 0) return i; return -1; })(%s)"""
WEAR = [["rarm", "Lightsabre"], ["rrin", "Nagelring"], ["lrin", "Raven Frost"]]


def _press(t, sel, i=0):
    """a real mouse press + release at the centre of sel[i] -> None, or why it could not be pressed"""
    a = json.loads(t.ev(AIM % (json.dumps(sel), i)))
    if not a:
        return "no %s[%d] on the page" % (sel, i)
    if not a["hit"]:
        return "the centre of %s[%d] is covered by another element" % (sel, i)
    for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
        t.send("Input.dispatchMouseEvent", type=kind, x=a["x"], y=a["y"], button="none" if kind == "mouseMoved" else "left",
               clickCount=0 if kind == "mouseMoved" else 1)
    time.sleep(0.2)
    return None


def _equip(t, mule, want):
    """open the picker on each slot and choose the item, by real input -> [names equipped] + [why not]"""
    t.ev("(function(){ window.vaultCloseCard(); window.openMuleCard(%s); return 1; })()" % json.dumps(mule))
    time.sleep(0.3)
    got = []
    for slot, name in want:
        why = _press(t, '#vault-detail .mp-slot[data-slot="%s"]' % slot)
        if why:
            got.append("NOT PRESSED: " + why)
            continue
        i = t.ev(OPT_AT % json.dumps(name))
        why = ("%s was not offered for the %s" % (name, slot)) if i is None or i < 0 else _press(t, "#vault-detail .mp-pick .mp-opt", i)
        got.append(("NOT CHOSEN: " + why) if why else name)
    return got

FOCUS_TYPE = r"""(function(){ var i = document.querySelector('#vault-detail .mp-search input'); if (!i) return 'no search box';
  i.focus(); i.value = 'fire'; window._mpFilter('fire'); i.setSelectionRange(2, 3); window.__mpBox = i;
  return document.activeElement === i ? 'typing' : 'focus refused'; })()"""
FOCUS_READ = r"""(function(){ var i = document.querySelector('#vault-detail .mp-search input'), ae = document.activeElement;
  return JSON.stringify({ focused: !!i && ae === i, same: i === window.__mpBox, value: i ? i.value : null,
    caret: i ? [i.selectionStart, i.selectionEnd] : null, activeTag: ae ? ae.tagName : null }); })()"""

_CACHE = {}


def _measure():
    """Render the window once per process at every width. -> dict, or raises with the reason."""
    if "r" in _CACHE:
        return _CACHE["r"]
    bible = os.path.join(ROOT, "bible.html")
    if not RC._chrome_up():
        raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d — that is a failure on a venue "
                             "that is supposed to measure, not a venue without a browser" % (RC.CHROME, RC.PORT))
    res = {}
    try:
        t = RC._Tab("about:blank")
        t.send("Page.enable")
        t.send("Runtime.enable")
        t.send("Emulation.setDeviceMetricsOverride", width=WIDTHS[0][0], height=WIDTHS[0][1],
               deviceScaleFactor=1, mobile=False)
        try:
            t.send("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception:
            pass
        t.send("Page.navigate", url="file://" + bible)
        ready = False
        for _ in range(160):
            time.sleep(0.25)
            try:
                if t.ev("(function(){try{return !!(window.openMuleCard&&window.vaultAssign&&window.tvVaultRegister"
                        "&&window._mpLayout)}catch(e){return false}})()") is True:
                    ready = True
                    break
            except Exception:
                pass
        if not ready:
            raise AssertionError("bible.html never exposed openMuleCard in 40s — UNKNOWN, not passing")
        time.sleep(0.5)
        res["seeded"] = t.ev(SEED % (json.dumps(ITEMS), json.dumps(MULE)))
        for (w, h) in WIDTHS:
            t.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=(w < 500))
            time.sleep(0.25)
            t.ev("(function(){ window.vaultCloseCard(); window.openMuleCard(%s); return 1; })()" % json.dumps(MULE))
            time.sleep(0.35)
            res["%dx%d" % (w, h)] = json.loads(t.ev(MEASURE))
        # #174 v-B — the same widths with the doll in use and the picker open on the left hand
        t.send("Emulation.setDeviceMetricsOverride", width=WIDTHS[0][0], height=WIDTHS[0][1], deviceScaleFactor=1,
               mobile=False)
        time.sleep(0.25)
        res["equipped"] = _equip(t, MULE, WEAR)
        for (w, h) in WIDTHS:
            t.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=(w < 500))
            time.sleep(0.25)
            t.ev("(function(){ window.vaultCloseCard(); window.openMuleCard(%s); window._mpPick('larm'); return 1; })()"
                 % json.dumps(MULE))
            time.sleep(0.35)
            res["eq %dx%d" % (w, h)] = json.loads(t.ev(MEASURE))
        t.ev("(function(){ window._mpPick(null); return 1; })()")
        # the phone: type in the Stats search, open a keyboard (height-only resize), then re-render underneath
        t.send("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=1, mobile=True)
        time.sleep(0.25)
        t.ev("(function(){ window.vaultCloseCard(); window.openMuleCard(%s); return 1; })()" % json.dumps(MULE))
        time.sleep(0.35)
        res["typing"] = t.ev(FOCUS_TYPE)
        t.send("Emulation.setDeviceMetricsOverride", width=390, height=464, deviceScaleFactor=1, mobile=True)
        time.sleep(0.6)                      # past the handler's 160ms debounce
        res["keyboard"] = json.loads(t.ev(FOCUS_READ))
        t.ev("(function(){ window.tvVaultRegister('Lacerator'); window.vaultAssign('Lacerator', %s); return 1; })()"
             % json.dumps(MULE))
        time.sleep(0.3)
        res["refresh"] = json.loads(t.ev(FOCUS_READ))
        res["errors"] = list(getattr(t, "page_errors", []) or [])
        try:
            t.close()
        except Exception:
            pass
    finally:
        RC._chrome_down()
    _CACHE["r"] = res
    return res


def _near(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def _states():
    """(label, measurement) for every width, plain and with the doll in use + the picker open"""
    r = _measure()
    out = []
    for w, h in WIDTHS:
        out.append(("%dx%d" % (w, h), r["%dx%d" % (w, h)]))
        out.append(("%dx%d equipped+picker" % (w, h), r["eq %dx%d" % (w, h)]))
    return out


class TheWindowFitsAtEveryWidth(unittest.TestCase):

    def test_the_fixture_reached_the_window(self):
        """PRINT THE DENOMINATOR: a window that rendered no text passes every check below."""
        r = _measure()
        self.assertEqual(r.get("seeded"), len(ITEMS), "the fixture did not put its items in the locker")
        for label, m in _states():
            self.assertNotIn("err", m, "%s: %s" % (label, m.get("err")))
            self.assertGreaterEqual(m["nText"], 120, "%s: only %d text nodes measured" % (label, m["nText"]))
        self.assertEqual(r.get("errors"), [], "the page threw while the window was open")

    def test_the_doll_in_use_was_really_measured(self):
        """#174 v-B — the equipped pass is only a check if the doll WAS in use: three items worn through the picker,
        stat values drawn, the picker open with choices in it — at every width."""
        r = _measure()
        self.assertEqual(r.get("equipped"), [p[1] for p in WEAR], "the picker did not equip the fixture's items")
        for w, h in WIDTHS:
            m = r["eq %dx%d" % (w, h)]
            self.assertEqual((m["worn"], m["pick"]), (len(WEAR), 1), "%dx%d: worn %s, picker %s" % (w, h, m["worn"], m["pick"]))
            self.assertGreater(m["sv"], 0, "%dx%d: no stat value was drawn from the worn gear" % (w, h))
            self.assertGreater(m["opts"], 0, "%dx%d: the left-hand picker offered nothing" % (w, h))

    def test_no_word_or_control_is_cut_or_outside_its_panel(self):
        bad = []
        for label, m in _states():
            bad += ["%s %s" % (label, x) for x in m["cut"] + m["outside"]]
        self.assertEqual(bad, [], "text or a control in the mule window is cut or spills out of its panel:\n  "
                         + "\n  ".join(bad))

    def test_nothing_scrolls_sideways(self):
        bad = []
        for label, m in _states():
            if m["hscroll"][0] > m["hscroll"][1] + 1:
                bad.append("%s the window itself %d/%d" % (label, m["hscroll"][0], m["hscroll"][1]))
            bad += ["%s %s" % (label, x) for x in m["sideways"]]
        self.assertEqual(bad, [], "part of the mule window scrolls sideways:\n  " + "\n  ".join(bad))

    def test_the_gold_box_is_one_line_and_the_stash_never_scrolls(self):
        """#174 v-B review — the stash cell budget assumes a one-line gold box; a second line scrolled the stash view
        and cut the box's border at 2000 wide. In columns, plain and with the doll in use, at every width."""
        bad, seen = [], 0
        for label, m in _states():
            if m.get("stack") or m.get("goldLines") is None:
                continue
            seen += 1
            if round(m["goldLines"]) != 1:
                bad.append("%s the gold box is %.2f lines: %r" % (label, m["goldLines"], m["goldText"]))
            if m["stashScroll"] and m["stashScroll"][0] > m["stashScroll"][1]:
                bad.append("%s the stash view scrolls %d/%d" % (label, m["stashScroll"][0], m["stashScroll"][1]))
        self.assertGreaterEqual(seen, 10, "the gold box was measured at only %d column-layout states" % seen)
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_no_header_title_runs_under_its_control(self):
        bad = []
        for label, m in _states():
            bad += ["%s %s" % (label, x) for x in m["collide"]]
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_the_type_is_its_token_times_the_unit_never_below_the_floor(self):
        r = _measure()
        for w, h in WIDTHS:
            m = r["%dx%d" % (w, h)]
            # the LAW, not the numbers: the root tokens are read off the page, so a retuned scale still grades
            tok = m["tokens"]
            for key in ("title", "meta", "micro"):
                self.assertTrue(tok.get(key) and tok[key] > 0, "%dx%d: the root --fs-%s token could not be read "
                                                                "off the page — UNKNOWN, not passing" % (w, h, key))
            kf = min(1.0, m["k"])
            for key in ("title", "meta"):
                self.assertIsNotNone(m["fs"][key], "%dx%d: no %s text to read a size from (.mp-h-t / .mp-left "
                                                   ".mp-empty) — the markup this law reads has moved" % (w, h, key))
                want = max(tok["micro"], tok[key] * kf)
                self.assertAlmostEqual(m["fs"][key], want, delta=0.05,
                                       msg="%dx%d (k=%.4f): the %s type is %.2fpx, not max(--fs-micro %g, --fs-%s %g "
                                           "x %.4f) = %.2fpx" % (w, h, m["k"], key, m["fs"][key], tok["micro"], key,
                                                                tok[key], kf, want))

    def test_at_2000_the_panels_and_the_doll_are_their_measured_rects(self):
        """their rects, with the one declared upgrade (_ours / _our_slot) — plain and with the doll in use"""
        bad = []
        for key in ("2000x1300", "eq 2000x1300"):
            m = _measure()[key]
            self.assertEqual(m["k"], 1.0)
            for c in THEIR_PANELS:
                want, got = _ours(c), m["panels"][c]
                if not got or not _near(got, want, SW_TOL if c == "mp-sw" else TOL_2000):
                    bad.append("%s %s %s, measured %s" % (key, c, [round(v, 2) for v in want],
                                                          [round(x, 2) for x in got] if got else None))
            for s in THEIR_SLOTS:
                want, got = _our_slot(s), m["slots"].get(s)
                if not got or not _near(got, want, 0.5):
                    bad.append("%s slot %s %s, measured %s" % (key, s, list(want), got))
        self.assertEqual(bad, [], "at 2000x1300 the window left their geometry:\n  " + "\n  ".join(bad))

    def test_at_1280_the_fixed_panels_are_their_rects_times_the_unit(self):
        m = _measure()["1280x800"]
        k = m["k"]
        self.assertLess(k, 1.0)
        bad = []
        for c in ("mp-eq", "mp-cp", "mp-notes", "mp-stats", "mp-set"):
            want = [v * k for v in _ours(c)]
            if not _near(m["panels"][c], want, 1.0):
                bad.append("%s %s, measured %s" % (c, [round(v, 1) for v in want], [round(v, 1) for v in m["panels"][c]]))
        self.assertEqual(bad, [], "at 1280 the window is not their geometry times k:\n  " + "\n  ".join(bad))

    def test_a_keyboard_opening_leaves_the_search_box_he_is_typing_in(self):
        r = _measure()
        self.assertEqual(r["typing"], "typing", "the Stats search box could not be focused at all")
        kb = r["keyboard"]
        self.assertTrue(kb["same"], "a HEIGHT-only resize (a phone keyboard opening) rebuilt the window and "
                                    "replaced the search box he was typing in: %s" % kb)
        self.assertTrue(kb["focused"] and kb["value"] == "fire" and kb["caret"] == [2, 3], kb)

    def test_a_re_render_underneath_him_puts_the_caret_back(self):
        rf = _measure()["refresh"]
        self.assertTrue(rf["focused"], "an item assigned in the background re-rendered the window and left the "
                                       "focus on %s, not the search box he was typing in" % rf["activeTag"])
        self.assertEqual((rf["value"], rf["caret"]), ("fire", [2, 3]), rf)


RED_PROOF = [
    {
        # #174 v-B moved the tightest prose panel: the LEFT column is now their 322 on the doll's unit, so MERCENARY's
        # sentence fits its 80u at every width (scanned 320..1600 with the panel fixed: never cut), while STRENGTHS
        # AND WEAKNESSES, fixed at its 57u, cuts its sentence at 1024, 960, 920 and 901 wide. The defect class is the
        # same — a prose panel with a fixed height cuts its own sentence — so the proof now aims where it still bites.
        "why": "#174 - a prose panel (STRENGTHS AND WEAKNESSES) is a fixed height again, so its sentence is cut where the words out-grow it",
        "file": "bible.html",
        "find": ".mp-sw{min-height:calc(57*var(--u))}\n",
        "replace": ".mp-sw{height:calc(57*var(--u))}\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B - the picker's choice never reaches the doll, so the equipped pass measures an empty doll and calls it fitting",
        "file": "bible.html",
        "find": "      try { _mpEqWrite(r.all); }\n",
        "replace": "      try { void 0; }\n",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - the gold box says its worn copies in a sentence that wraps it, and the stash view scrolls",
        "file": "bible.html",
        "find": "+ ' in inventory · ' + _wornHere + ' worn</div>'",
        "replace": "+ ' in inventory · ' + _wornHere + ' worn on the doll · ' + (_thisMuleN + _wornHere) + ' on this mule</div>'",
        "matches": 1,
    },
    {
        "why": "#174 v-B review - a doll slot stops taking the pointer, so real input cannot open it (a .click() would have)",
        "file": "bible.html",
        "find": ".mp-slot.mp-gone{border-color:var(--hell);border-style:dashed}\n",
        "replace": ".mp-slot.mp-gone{border-color:var(--hell);border-style:dashed}\n.mp-slot{pointer-events:none}\n",
        "matches": 1,
    },
    {
        "why": "#174 - openMuleCard stops writing --kf, so the window's type no longer rides its unit",
        "file": "bible.html",
        "find": "style=\"--u:'+k.toFixed(4)+'px;--kf:'+Math.min(1, k).toFixed(4)+'\"",
        "replace": "style=\"--u:'+k.toFixed(4)+'px\"",
        "matches": 1,
    },
    {
        "why": "#174 - the stash's gold box stops wrapping, so a phone scrolls the stash view sideways",
        "file": "bible.html",
        "find": ".mp-v-stash .vd-goldbox{margin-top:6px;width:auto;max-width:100%;padding:4px 14px;",
        "replace": ".mp-v-stash .vd-goldbox{margin-top:6px;width:auto;max-width:100%;padding:4px 14px;white-space:nowrap;",
        "matches": 1,
    },
    {
        "why": "#174 - the mule tabs stop wrapping on a phone, so the ghost tab scrolls off the edge",
        "file": "bible.html",
        "find": ".mp.mp-stack .mp-settabs{flex-wrap:wrap;",
        "replace": ".mp.mp-stack .mp-settabs{flex-wrap:nowrap;",
        "matches": 1,
    },
    {
        "why": "#174 - a height-only resize (a phone keyboard) rebuilds the window under his typing again",
        "file": "bible.html",
        "find": "      if (mp && mp.getAttribute('data-sig') === _mpLayout(window.innerWidth || 1440, window.innerHeight || 900).sig) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#174 - a background re-render no longer puts the caret back in the Stats search box",
        "file": "bible.html",
        "find": "      if (_in){ try { _in.focus({ preventScroll: true }); _in.setSelectionRange(_keep.q[0], _keep.q[1]); } catch (e) {} }\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    # A class-level skip would print OK (skipped=N) and exit 0, which run_gates reads as a PASS. With no browser
    # binary at all this is a DECLARED skip (77) that the gate's skip_ok names; everything else runs and can fail.
    if not os.path.exists(RC.CHROME):
        sys.stderr.write("⚪ SKIP — %s. UNMEASURED, declared as a skip (77), never a pass.\n" % NO_BROWSER)
        raise SystemExit(77)
    unittest.main(verbosity=2)
