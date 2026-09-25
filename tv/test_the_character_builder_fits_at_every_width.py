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
The entry is REAL INPUT: the Tools tab and the Character Builder card are pressed by CDP mouse events at their
centres, each hit-tested first; the helm is equipped the same way (the slot, the search box, the row), a roll is
typed with key events, and the charm is DRAGGED to another cell with a press, moves carrying buttons=1, a release.

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


# ⚠ BEFORE the import: render_check reads its port once, at import time.
os.environ["TV_RENDER_PORT"] = str(_free_port())
import render_check as RC  # noqa: E402

NO_BROWSER = "no Chrome/Chromium on this machine, so the character builder was not rendered"
WIDTHS = ((2000, 1300), (1280, 800), (1120, 628), (1024, 768), (901, 900), (800, 1000), (375, 812))
STATES = ("plain", "worn", "picker", "edit", "stash")
#: their builder at 2000 wide (spec §1): the three columns relative to the content column
THEIR_COLS = {"left": (0, 322), "main": (328, 716), "stats": (1050, 300)}
TOL = 4.0

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
    doll: rel(d.getElementById('cb-doll')) };
  out.cols.left = rel(box.querySelector('.cb-left')); out.cols.main = rel(box.querySelector('.cb-main')); out.cols.stats = rel(box.querySelector('.cb-stats'));
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
            for state in ("worn", "picker", "edit", "stash"):
                js = {"worn": "", "picker": "window._cbOpenPick('slot','head'); window._cbPickTab('select');",
                      "edit": "window._cbOpenPick('slot','head');", "stash": "window._cbOpenStash();"}[state]
                t.ev("(function(){ window.closeCharBuilder(); window.openCharBuilder(); %s return 1; })()" % js)
                time.sleep(0.35)
                res["%s %dx%d" % (state, w, h)] = json.loads(t.ev(MEASURE))
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

    def test_at_2000_the_columns_are_their_literal_322_716_300(self):
        bad = []
        for state in ("plain", "worn"):
            m = _measure()["%s 2000x1300" % state]
            self.assertFalse(m["stack"])
            for c, (x, wd) in THEIR_COLS.items():
                got = m["cols"][c]
                if not got or abs(got[0] - x) > TOL or abs(got[2] - wd) > TOL:
                    bad.append("%s %s: theirs x=%d w=%d, measured %s" % (state, c, x, wd, [round(v, 1) for v in got] if got else None))
            dl = m["doll"]
            if not dl or dl[2] < 600:
                bad.append("%s the doll does not fill the 716 centre: %s" % (state, dl))
            if m["fsTitle"] is None or abs(m["fsTitle"] - m["tokTitle"]) > 0.05:
                bad.append("%s the header type %s is not the --fs-title token %s at k=1" % (state, m["fsTitle"], m["tokTitle"]))
        self.assertEqual(bad, [], "\n  ".join(bad))

    def test_under_900_the_character_comes_first(self):
        for (w, h) in WIDTHS:
            m = _measure()["worn %dx%d" % (w, h)]
            if w >= 900:
                self.assertFalse(m["stack"], "%dx%d stacked" % (w, h))
                continue
            self.assertTrue(m["stack"], "%dx%d did not stack" % (w, h))
            self.assertLess(m["cols"]["main"][1], m["cols"]["stats"][1], "%dx%d: the doll is not above the stats" % (w, h))
            self.assertLess(m["cols"]["main"][1], m["cols"]["left"][1], "%dx%d: the doll is not above the inventory" % (w, h))


RED_PROOF = [
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
