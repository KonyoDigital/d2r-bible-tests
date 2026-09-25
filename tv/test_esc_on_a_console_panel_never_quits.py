# -*- coding: utf-8 -*-
"""REG-1304 — ESC ON A CONSOLE PANEL CLOSES THE PANEL. IT NEVER QUITS HIS CONSOLE.

The testing-phase catalogue (finding 23, 2026-09-25), confirmed in tv/control_ui.html: Esc on THE STATE OF
THIS CONSOLE (#ver-xref - its own ✕ is titled "close (Esc)"), the fleet window (#fleet-xref), the heart
(#heart-ov) or a receipt's full frame (#rcpt-full) closed the panel AND quit the console. Each panel's
listener runs first, closes the panel and does not mark the key, so the v1420 empty-page handler then saw an
empty page and POSTed /api/quit; #rcpt-full's listener is registered lazily, AFTER that handler, so the quit
ran while the frame was still on screen.

The fix reads "is anything open" at PRESS time, in a window-capture listener that runs before every handler,
knows these panels by name and treats any visible dialog as open.

  · DRIVEN (node, the SHIPPED listeners cut from control_ui.html, dispatched window-capture -> document ->
    target -> bubble, registered in the page's own order): each of the four panels closes on Esc and the
    console does NOT quit - including #rcpt-full, whose listener comes after the quit handler.
  · DRIVEN: a visible dialog nobody has written a handler for yet still keeps the console alive.
  · PREMISE: nothing open -> Esc DOES quit (v1420), so the no-quit cases can fail.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")
NODE = shutil.which("node")


def _between(src, start, end):
    assert src.count(start) == 1, "cut start is not unique: %r" % start[:60]
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _shipped():
    with io.open(UI, encoding="utf-8") as f:
        src = f.read()
    return {
        "heart": _between(src, "    document.addEventListener('keydown', function(ev){\n      if (ev.key === 'Escape' && _hOv",
                          "\n    });"),
        "verx": _between(src, "    document.addEventListener('keydown', function(ev){\n      if (ev.key === 'Escape' && _vxOv",
                         "\n    });"),
        "fleet": _between(src, "      document.addEventListener('keydown', function(ev){\n        if (ev.key === 'Escape' && !_fxOv.hidden",
                          "\n      });"),
        "rcpt": _between(src, "      document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && wrap.classList",
                         "});"),
        "snap": _between(src, "  function _consoleOverlayOpen(){", "  }, true);"),
        "quit": _between(src, "  document.addEventListener('keydown', function(e){\n    if (e.key !== 'Escape') return;\n    if (e.defaultPrevented) return;",
                         "  }, false);"),
    }


DOM = r"""
function El(tag, id){ this.tagName = (tag||'div').toUpperCase(); this.id = id || ''; this.hidden = false; this.parent = null;
  this.children = []; this.L = {cap: [], bub: []}; this.attrs = {};
  var me = this; this.classList = { _c: {}, contains: function(c){ return !!me.classList._c[c]; },
    add: function(c){ me.classList._c[c] = 1; }, remove: function(c){ delete me.classList._c[c]; } }; }
El.prototype.addEventListener = function(t, fn, cap){ if (t === 'keydown') (cap ? this.L.cap : this.L.bub).push(fn); };
El.prototype.appendChild = function(c){ c.parent = this; this.children.push(c); return c; };
El.prototype.getAttribute = function(k){ return this.attrs[k] === undefined ? null : this.attrs[k]; };
El.prototype.getClientRects = function(){ for (var x = this; x; x = x.parent) if (x.hidden) return []; return [1]; };
var body = new El('body'); var document = new El('#document'); document.body = body; body.parent = document;
document.activeElement = body;
function _all(n, out){ out.push(n); n.children.forEach(function(c){ _all(c, out); }); return out; }
document.getElementById = function(id){ return _all(body, []).filter(function(n){ return n.id === id; })[0] || null; };
document.querySelectorAll = function(sel){
  return _all(body, []).filter(function(n){ return !n.hidden && (n.attrs.role === 'dialog' || n.attrs['aria-modal'] === 'true'); });
};
var window = new El('#window');
function press(key){
  var t = document.activeElement, path = [];
  for (var x = t; x; x = x.parent) path.unshift(x);
  var ev = { key: key, target: t, defaultPrevented: false, _stop: false,
             preventDefault: function(){ this.defaultPrevented = true; }, stopPropagation: function(){ this._stop = true; } };
  window.L.cap.forEach(function(f){ if (!ev._stop) f(ev); });
  for (var i = 0; i < path.length - 1 && !ev._stop; i++) path[i].L.cap.forEach(function(f){ f(ev); });
  if (!ev._stop) t.L.cap.concat(t.L.bub).forEach(function(f){ f(ev); });
  for (var j = path.length - 2; j >= 0 && !ev._stop; j--) path[j].L.bub.forEach(function(f){ f(ev); });
}
var QUITS = [];
function fetch(url){ QUITS.push(url); return { catch: function(){} }; }
function toast(){}
var TH = {open:false}, CH = {open:false}, TLY = {open:false}, RLOG = {open:false}, LEG = {open:false};
var _hOv = body.appendChild(new El('div', 'heart-ov')); _hOv.hidden = true; _hOv.attrs.role = 'dialog';
var _vxOv = body.appendChild(new El('div', 'ver-xref')); _vxOv.hidden = true;
var _fxOv = body.appendChild(new El('div', 'fleet-xref')); _fxOv.hidden = true;
var wrap = body.appendChild(new El('div', 'rcpt-full'));
function _heartClose(){ _hOv.hidden = true; }
function _verXrefClose(){ _vxOv.hidden = true; }
function close(){ wrap.classList.remove('on'); }
"""


def _run(script):
    s = _shipped()
    # The page's own order: the three panel listeners and the snapshot are registered before the quit
    # handler; the receipt viewer's listener only when it is first opened - AFTER the quit handler.
    js = "\n".join([DOM, s["heart"], s["verx"], s["fleet"], s["snap"], s["quit"], s["rcpt"], script])
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped handlers - UNKNOWN, not passing: %s" % r.stderr[:600])
    return json.loads(r.stdout.strip().splitlines()[-1])


STATE = ("console.log(JSON.stringify({quits: QUITS, heart: _hOv.hidden, verx: _vxOv.hidden, fleet: _fxOv.hidden,"
         " rcpt: wrap.classList.contains('on')}));")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class EscOnAConsolePanelNeverQuits(unittest.TestCase):

    def test_premise_escape_on_an_empty_console_quits(self):
        self.assertEqual(_run("press('Escape');" + STATE)["quits"], ["/api/quit"],
                         "premise: the empty-page Esc must quit (v1420), or the no-quit cases prove nothing")

    def test_the_state_panel_closes_and_the_console_stays(self):
        out = _run("_vxOv.hidden = false; press('Escape');" + STATE)
        self.assertTrue(out["verx"], "Esc did not close THE STATE OF THIS CONSOLE")
        self.assertEqual(out["quits"], [], "Esc on the state panel quit his console")

    def test_the_fleet_window_closes_and_the_console_stays(self):
        out = _run("_fxOv.hidden = false; press('Escape');" + STATE)
        self.assertTrue(out["fleet"])
        self.assertEqual(out["quits"], [], "Esc on the fleet window quit his console")

    def test_the_heart_closes_and_the_console_stays(self):
        out = _run("_hOv.hidden = false; press('Escape');" + STATE)
        self.assertTrue(out["heart"])
        self.assertEqual(out["quits"], [], "Esc on the heart quit his console")

    def test_a_receipt_frame_whose_listener_comes_last_still_keeps_the_console(self):
        out = _run("wrap.classList.add('on'); press('Escape');" + STATE)
        self.assertFalse(out["rcpt"], "Esc did not close the full receipt frame")
        self.assertEqual(out["quits"], [], "the quit ran before the receipt frame's own listener (the late one)")

    def test_a_dialog_with_no_handler_yet_keeps_the_console(self):
        out = _run("var d = body.appendChild(new El('div','future-panel')); d.attrs.role = 'dialog';"
                   "press('Escape');" + STATE)
        self.assertEqual(out["quits"], [], "a visible dialog nobody wrote a handler for let Esc quit the console")

    def test_after_the_panel_closes_a_second_escape_still_quits(self):
        """v1420 is his design: once the page IS empty, Esc leaves the console. The fix must not remove that."""
        out = _run("_vxOv.hidden = false; press('Escape'); press('Escape');" + STATE)
        self.assertEqual(out["quits"], ["/api/quit"], "the snapshot latched and Esc can never quit any more")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1304 - the quit handler ignores what was open at press time: the late receipt listener and any "
               "unhandled dialog let Esc quit his console again",
        "file": "control_ui.html",
        "find": "    if (window._escOverlayAtPress) { window._escOverlayAtPress = ''; return; }   /* REG-1304 - open at press time */\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1304 - the snapshot no longer knows the receipt frame, which closes AFTER the quit already ran",
        "file": "control_ui.html",
        "find": "      if (rf && rf.classList.contains('on')) return 'rcpt-full';\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1304 - a visible dialog is no longer treated as open, so the next panel anyone adds can quit the console",
        "file": "control_ui.html",
        "find": "        if (dl[j].getClientRects && dl[j].getClientRects().length) return dl[j].id || 'a dialog';\n",
        "replace": "",
        "matches": 1,
    },
]
