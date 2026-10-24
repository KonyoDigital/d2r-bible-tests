# -*- coding: utf-8 -*-
"""GBL 2026-10-24 - A ROSTER NAME OPENS ITS ROW WITH THE EYES, AND THE CROSS-REFERENCE STILL OPENS EXACTLY AS IT DID.

Elad's rulings, in order (mock: two frames, row then modal):
  · the hover card is NOT changed;
  · clicking a name does two things: the row opens inline with an HD two-eyes button (and STAYS open), and the
    cross-reference modal opens exactly as today, same place, same template, SETS/UNIQUES and its three columns;
  · the eyes are NOT inside the modal; they route to shadow for THAT profile (roster:<owner>:profile);
  · only the modal's diagnostic block changes: every line kept, folded under ADVANCED and set as data, and no fact
    of it (the 'last walk' age was clipped in the mock) is cut off.

HOW: the SHIPPED control_ui.html and the same file at BASE (the commit before this change) are rendered in one
headless Chrome over the same stubbed /api/fleet with the clock frozen, and their DOM is compared - the hover card
byte for byte, the modal byte for byte once the ADVANCED fold is unwrapped. A clone without BASE in its history
fails loudly; it never skips. Nothing real is touched: file:// pages, fetch stubbed, its own Chrome port.
[[unknown-stays-unknown]] [[visual-regression-detector]]
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_the_fleet_card_says_how_each_pc_films_and_drains as F  # noqa: E402  (sets the law's own Chrome port)

RC = F.RC
BASE = "694e4378"          # gbl/shadow before the row eyes (control_ui.html as Elad knows it; also what the v3796 stamp sat on)
NOW_MS = 1790000000000
OWNERS = {"box-a": "Konyo \u00b7 Mac", "box-b": "Konyo \u00b7 ALT", "box-c": "Wife PC", "box-d": ""}

CLOCK = r"""(function(){ var N = %d, D = Date;
  function FD(){ if (!arguments.length) return new D(N);
    return new (Function.prototype.bind.apply(D, [null].concat([].slice.call(arguments))))(); }
  FD.now = function(){ return N; }; FD.parse = D.parse; FD.UTC = D.UTC; FD.prototype = D.prototype; window.Date = FD; })();"""

SNAP = r"""(function(){
  var rows = [].map.call(document.querySelectorAll('#fleet-list .fleet-row'), function(r){
    var c = r.cloneNode(true), e = c.querySelector('.fleet-open-eyes'); if (e) e.remove();
    c.classList.remove('fleet-open'); ['onclick', 'onkeydown', 'aria-expanded'].forEach(function(a){ c.removeAttribute(a); });
    var t = r.querySelector('.ftt');
    return { m: r.getAttribute('data-fleet-machine'), ftt: t ? t.outerHTML : null, row: c.outerHTML }; });
  return JSON.stringify(rows); })()"""

XREF = r"""(function(){ var x = document.getElementById('fleet-xref'); if (!x || x.hidden) return JSON.stringify({ err: 'closed' });
  var c = x.cloneNode(true), adv = c.querySelector('details.fx-adv'), inside = !!c.querySelector('.fleet-hd-eyes');
  var summ = adv ? adv.querySelector('summary').textContent : null, open = adv ? adv.open : null;
  if (adv) adv.replaceWith(adv.querySelector('.fx-sys'));
  return JSON.stringify({ html: c.innerHTML, adv: summ, open: open, eyesInside: inside }); })()"""

CLIP = r"""(function(){ var x = document.getElementById('fleet-xref'), adv = x && x.querySelector('details.fx-adv');
  if (!adv) return JSON.stringify({ err: 'no fold' }); adv.open = true;
  var win = x.querySelector('.fxr-win'), wr = win.getBoundingClientRect(), bad = [], n = 0;
  function clippedBy(f) { for (var a = f.parentElement; a && a !== document.body; a = a.parentElement) {
      var cs = getComputedStyle(a); if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
        var r = a.getBoundingClientRect(), b = f.getBoundingClientRect();
        if (b.right > r.right + 0.5 || b.left < r.left - 0.5 || b.bottom > r.bottom + 0.5 || b.top < r.top - 0.5) return a.className || a.tagName; }
      if (cs.position === 'fixed') break; }
    return null; }
  [].forEach.call(adv.querySelectorAll('.fs-f, .fs-k'), function(f){ n++; var b = f.getBoundingClientRect(), cs = getComputedStyle(f);
    if (b.width === 0) { bad.push('unrendered: ' + f.textContent); return; }
    if (f.scrollWidth > f.clientWidth + 1) bad.push('wider than its box: ' + f.textContent);
    if (cs.textOverflow === 'ellipsis' || cs.whiteSpace === 'nowrap') bad.push('cut style: ' + f.textContent);
    if (b.right > wr.right + 0.5 || b.left < wr.left - 0.5 || b.bottom > wr.bottom + 0.5 || b.top < wr.top - 0.5)
      bad.push('outside the modal window: ' + f.textContent);
    var by = clippedBy(f); if (by) bad.push('clipped by ' + by + ': ' + f.textContent); });
  var walk = [].filter.call(adv.querySelectorAll('.fs-f'), function(f){ return /last walk/.test(f.textContent); }).length;
  adv.open = false;
  return JSON.stringify({ bad: bad, n: n, walk: walk }); })()"""


def _base_ui():
    try:
        src = subprocess.check_output(["git", "-C", ROOT, "show", BASE + ":tv/control_ui.html"], stderr=subprocess.STDOUT)
    except Exception as e:
        raise AssertionError("BASE %s is not in this clone's history, so 'unchanged' cannot be proved - UNKNOWN, not "
                             "passing (%s)" % (BASE, e))
    fd, p = tempfile.mkstemp(suffix=".html", dir=HERE, prefix=".law_base_ui_")
    with os.fdopen(fd, "wb") as fh:
        fh.write(src)
    return p


def _fixture():
    real = F.time.time
    F.time.time = lambda: NOW_MS / 1000.0
    try:
        fx = F._fixture()
    finally:
        F.time.time = real
    fx["online"][0]["platform"] = "mac"                 # Konyo on a mac publishes as Konyo · Mac
    fx["online"][1]["nickname"] = "Konyo \u00b7 ALT"
    fx["offline"].append({"nickname": "Laptop", "machine": "box-d", "ver": "v3401", "mode": "idle",
                          "t": F._iso(NOW_MS - 6 * 86400 * 1000), "system": {"tree": "ok", "reels": 1}})
    return fx


_CACHE = {}


def _open(t, path, w, h):
    t.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
    t.send("Page.navigate", url="file://" + path)
    for _ in range(160):
        time.sleep(0.25)
        try:
            if t.ev("document.readyState==='complete' && typeof window._fleetRefresh === 'function'") is True:
                break
        except Exception:
            pass
    else:
        raise AssertionError("%s never exposed _fleetRefresh in 40s - UNKNOWN, not passing" % path)
    time.sleep(0.8)
    t.ev("(function(){ try { window._fleetRefresh(); } catch (e) {} return 1; })()")
    for _ in range(60):
        time.sleep(0.25)
        if t.ev("document.querySelectorAll('#fleet-list .fleet-row').length") == 4:
            return
    raise AssertionError("%s drew %r fleet rows of 4" % (path, t.ev("document.querySelectorAll('#fleet-list .fleet-row').length")))


def _wait_head(t):
    for _ in range(60):
        time.sleep(0.2)
        if t.ev("!!document.querySelector('#fleet-xref:not([hidden]) .fx-head')"):
            return True
    return False


def _render():
    if "r" in _CACHE:
        return _CACHE["r"]
    base = _base_ui()
    res = {"base": {}, "ship": {}}
    if not RC._chrome_up():
        os.unlink(base)
        raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d" % (RC.CHROME, RC.PORT))
    try:
        t = RC._Tab("about:blank")
        t.send("Page.enable")
        t.send("Runtime.enable")
        t.send("Page.addScriptToEvaluateOnNewDocument", source=(CLOCK % NOW_MS) + F.STUB % json.dumps(_fixture()))
        for which, path in (("base", base), ("ship", F.UI_PATH)):
            for (w, h) in ((1440, 900), (375, 812)):
                k = "%dx%d" % (w, h)
                _open(t, path, w, h)
                out = {"rows": json.loads(t.ev(SNAP)), "xref": {}, "clip": {}}
                for mach in OWNERS:
                    t.ev("(function(){ window._fleetCompare(%s); return 1; })()" % json.dumps(mach))
                    _wait_head(t)
                    time.sleep(0.2)
                    out["xref"][mach] = json.loads(t.ev(XREF))
                    if which == "ship":
                        out["clip"][mach] = json.loads(t.ev(CLIP))
                    t.ev("document.getElementById('fleet-xref').hidden = true")
                if which == "ship":
                    # a REAL click on each row: the modal opens, the row opens and stays open through a second click
                    # and a fleet refresh; its eyes route to that profile and do not reopen the modal
                    out["click"] = json.loads(t.ev(r"""(function(){
                      var calls = [], opened = [], real = window._fleetCompare;
                      window._shadowOpen = function(o){ opened.push(o); };
                      window._fleetCompare = function(m, l){ calls.push(m); return real.apply(this, arguments); };
                      var out = {};
                      [].forEach.call(document.querySelectorAll('#fleet-list .fleet-row'), function(r){
                        var m = r.getAttribute('data-fleet-machine'), before = r.classList.contains('fleet-open');
                        var eb = r.querySelector('.fleet-hd-eyes'), vis0 = eb ? eb.getBoundingClientRect().height : -1;
                        r.click(); var c1 = calls.length;
                        var vis1 = eb ? eb.getBoundingClientRect().height : -1;
                        r.click();
                        var modal = !document.getElementById('fleet-xref').hidden, esc = null;
                        if (eb && !eb.disabled) { eb.focus();
                          eb.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
                          esc = document.getElementById('fleet-xref').hidden; }
                        out[m] = { esc: esc, before: before, open: r.classList.contains('fleet-open'),
                                   aria: r.getAttribute('aria-expanded'), calls: c1, calls2: calls.length,
                                   modal: modal, vis0: vis0, vis1: vis1,
                                   owner: eb ? eb.getAttribute('data-roster-owner') : null, disabled: eb ? eb.disabled : null };
                        document.getElementById('fleet-xref').hidden = true;
                        calls.length = 0;
                        if (eb && !eb.disabled) { eb.click(); out[m].routed = opened.slice(); out[m].callsOnEyes = calls.length; }
                        opened.length = 0; calls.length = 0;
                      });
                      window._fleetCompare = real;
                      return JSON.stringify(out); })()"""))
                    t.ev("(function(){ window._fleetRefresh(); return 1; })()")
                    time.sleep(1.5)
                    out["afterRefresh"] = t.ev("[].map.call(document.querySelectorAll('#fleet-list .fleet-row'), "
                                               "function(r){ return r.classList.contains('fleet-open'); })")
                res[which][k] = out
        res["errors"] = list(getattr(t, "page_errors", []) or [])
        try:
            t.close()
        except Exception:
            pass
    finally:
        RC._chrome_down()
        os.unlink(base)
    _CACHE["r"] = res
    return res


@unittest.skipUnless(os.path.exists(RC.CHROME), "no Chrome on this machine - the card was not rendered (declared skip 77)")
class ARosterNameOpensItsRowWithTheEyes(unittest.TestCase):

    def test_the_hover_card_is_byte_for_byte_what_it_was(self):
        r = _render()
        for k in r["ship"]:
            b = dict((x["m"], x) for x in r["base"][k]["rows"])
            s = dict((x["m"], x) for x in r["ship"][k]["rows"])
            self.assertEqual(sorted(b), sorted(s), k)
            for m in s:
                self.assertTrue(s[m]["ftt"], "%s %s: no hover card at all" % (k, m))
                self.assertEqual(s[m]["ftt"], b[m]["ftt"], "%s %s: the hover card changed" % (k, m))
                self.assertEqual(s[m]["row"], b[m]["row"], "%s %s: the row changed beyond its eyes" % (k, m))

    def test_the_cross_reference_is_unchanged_but_for_the_folded_diagnostics(self):
        r = _render()
        for k in r["ship"]:
            for m in OWNERS:
                b, s = r["base"][k]["xref"][m], r["ship"][k]["xref"][m]
                self.assertNotIn("err", s, "%s %s: the modal did not open" % (k, m))
                self.assertEqual(s["html"], b["html"], "%s %s: the modal changed beyond the ADVANCED fold" % (k, m))
                self.assertEqual(s["adv"], u"ADVANCED \u00b7 DIAGNOSTICS", "%s %s: no ADVANCED fold" % (k, m))
                self.assertFalse(s["open"], "%s %s: the diagnostics are not collapsed" % (k, m))
                self.assertFalse(s["eyesInside"], "%s %s: the eyes are inside the modal" % (k, m))
                self.assertIn("fxr-tab", s["html"])

    def test_every_profile_row_has_its_eyes_and_they_route_to_that_profile(self):
        r = _render()
        for k in r["ship"]:
            c = r["ship"][k]["click"]
            self.assertEqual(sorted(c), sorted(OWNERS), k)
            for m, owner in OWNERS.items():
                got = c[m]
                if owner:
                    self.assertTrue(got["esc"], "%s %s: Escape on the eyes did not close the modal" % (k, m))
                    self.assertEqual(got["owner"], owner, "%s %s: the eyes name another profile" % (k, m))
                    self.assertEqual(got["routed"], [owner], "%s %s: the eyes routed to %r" % (k, m, got.get("routed")))
                    self.assertEqual(got["callsOnEyes"], 0, "%s %s: pressing the eyes reopened the modal" % (k, m))
                else:
                    self.assertTrue(got["disabled"], "%s %s: a PC with no roster profile got live eyes" % (k, m))
                    self.assertNotIn("routed", got)

    def test_one_click_opens_the_row_and_the_modal_and_the_row_stays_open(self):
        r = _render()
        for k in r["ship"]:
            for m, got in r["ship"][k]["click"].items():
                self.assertFalse(got["before"], "%s %s: a row was open before any click" % (k, m))
                self.assertEqual(got["vis0"], 0, "%s %s: the eyes showed before the click" % (k, m))
                self.assertGreater(got["vis1"], 0, "%s %s: the click did not show the eyes on the row" % (k, m))
                self.assertEqual(got["calls"], 1, "%s %s: the click did not open the cross-reference" % (k, m))
                self.assertTrue(got["modal"], "%s %s: the modal is not open after the click" % (k, m))
                self.assertTrue(got["open"] and got["aria"] == "true", "%s %s: a second click shut the row" % (k, m))
            self.assertEqual(r["ship"][k]["afterRefresh"], [True] * 4, "%s: a fleet refresh shut the open rows" % k)

    def test_no_diagnostic_fact_is_clipped_last_walk_included(self):
        r = _render()
        walks = 0
        for k in r["ship"]:
            for m, c in r["ship"][k]["clip"].items():
                self.assertNotIn("err", c, "%s %s" % (k, m))
                self.assertGreater(c["n"], 0, "%s %s: PRINT THE DENOMINATOR - no fact read" % (k, m))
                self.assertEqual(c["bad"], [], "%s %s: %s" % (k, m, c["bad"]))
                walks += c["walk"]
        self.assertGreater(walks, 0, "PREMISE - no 'last walk' fact was rendered, so its clipping was never measured")
        self.assertEqual(r.get("errors"), [], "the page threw: %s" % r.get("errors"))


RED_PROOF = [
    {"why": "Grok r1 - the eyes swallow every key again, so Escape no longer closes the cross-reference",
     "file": "tv/control_ui.html",
     "find": "window._shadowOpen(this.getAttribute(\\'data-roster-owner\\'))\">'",
     "replace": "window._shadowOpen(this.getAttribute(\\'data-roster-owner\\'))\" onkeydown=\"event.stopPropagation()\">'",
     "matches": 1},
    {"why": "GBL 2026-10-24 - the click opens the modal but no longer opens the row with its eyes",
     "file": "tv/control_ui.html",
     "find": "' onclick=\"window._fleetRowOpen(this);window._fleetCompare(",
     "replace": "' onclick=\"window._fleetCompare(",
     "matches": 1},
    {"why": "GBL 2026-10-24 - the eyes route to the wrong profile",
     "file": "tv/control_ui.html",
     "find": "    if (nick === 'Konyo' && m && m.platform === 'mac') return 'Konyo \\u00b7 Mac';\n",
     "replace": "    if (nick === 'Konyo' && m && m.platform === 'mac') return 'Dean';\n",
     "matches": 1},
    {"why": "GBL 2026-10-24 - the diagnostics are not collapsed under ADVANCED",
     "file": "tv/control_ui.html",
     "find": "        _sys = '<details class=\"fx-adv\"><summary>",
     "replace": "        _sys = '<details open class=\"fx-adv\"><summary>",
     "matches": 1},
    {"why": "GBL 2026-10-24 - a fleet refresh shuts the row he opened",
     "file": "tv/control_ui.html",
     "find": "    if (mach) window._fleetOpenRows[mach] = 1;\n",
     "replace": "",
     "matches": 1},
    {"why": "GBL 2026-10-24 - a diagnostic fact is clipped with an ellipsis again",
     "file": "tv/control_ui.html",
     "find": "white-space: normal; overflow: visible; text-overflow: clip; }",
     "replace": "white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }",
     "matches": 1},
    {"why": "GBL 2026-10-24 - the hover card's words change with the eyes",
     "file": "tv/control_ui.html",
     "find": "click: how this PC films and drains, and their set pieces against yours</div>';",
     "replace": "click: how this PC films and drains, their set pieces against yours, and the eyes</div>';",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
