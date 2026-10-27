# -*- coding: utf-8 -*-
"""REG-2321 - A HEADER TAB NEVER LEAVES "THE BOARD IS BUSY" UP FOREVER, AND ITS NAME IS ITS NAME.

Elad's Mac console, v3775, 2026-10-20: every board-routed tab (Vault, D2JSP, ...) sat on "opening VaultLOCKED - the board
is busy; it lands by itself" while TV-D and SESSIONS (which never enter shellOpen) worked. uiBeat read hidden:true,
painting:false, frozenBeats 46+ with the DOM intact - the 2026-09-07 occlusion signature: a hidden window composites
nothing new, so a veil set only to display:none can stay on his pixels.

The law drives the REAL _shellVeil / _shellOpeningEnd / _shellRoute / shellOpen lifted from tv/control_ui.html:
  * the veil label is the tab's .ht-lbl, never the lock chip's text glued on ("VaultLOCKED");
  * a hidden (occluded) document never puts the veil up, and the route still runs;
  * the veil is REMOVED from the DOM when the route ends, not only hidden;
  * a board that never gets a switchTab is reloaded once (cache-busted), then the give-up is honest and the veil is gone;
  * a switchTab that throws after the board moved is a landed route.
bible.html switchTab wraps each room's setup in its own try/catch that console.warns (#252 review), so one room cannot stall the switch silently.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _lift():
    with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        src = fh.read()
    out = []
    for start in ("  function _shellRoute(tab){", "  function _shellVeil(tab){", "  function _shellOpeningEnd(){",
                  "  function shellOpen(tab){"):
        i = src.find(start)
        if i < 0:
            return None
        j = src.find("\n  }\n", i)
        if j <= i:
            return None
        out.append(src[i:j + 4])
    return "\n".join(out)


HARNESS = r"""
var cfg = %s;
var out = {toasts: [], faults: [], ticks: 0, veilEver: false, veilText: null, srcs: [], paints: 0};
function Cls(){ var s = {}; return {add: function(c){ s[c] = 1; }, remove: function(c){ delete s[c]; },
                                    contains: function(c){ return !!s[c]; }}; }
var lbl = {textContent: 'Vault'};
var btn = {classList: Cls(), textContent: ' Vault LOCKED'.replace(' LOCKED', 'LOCKED'),
           querySelector: function(q){ return q === '.ht-lbl' ? lbl : null; }};
var active = {getAttribute: function(){ return cfg.boardActive || 'session'; }};
var bdoc = {querySelector: function(){ return active; }};
var bwin = {document: bdoc};
if (cfg.switchTab === 'ok') bwin.switchTab = function(t){ cfg.boardActive = t; };
if (cfg.switchTab === 'throws') bwin.switchTab = function(t){ cfg.boardActive = t; throw new Error('room render blew up'); };
var FRAME = {contentWindow: bwin};
Object.defineProperty(FRAME, 'src', {set: function(v){ out.srcs.push(v); }, get: function(){ return ''; }});
var VEIL = null;
var document = {visibilityState: cfg.hidden ? 'hidden' : 'visible',
                getElementById: function(id){ return id === 'tvd-eng' ? FRAME : (id === 'shell-opening' ? VEIL : null); },
                createElement: function(){ var el = {style: {}, setAttribute: function(){}};
                                           el.remove = function(){ if (VEIL === el) VEIL = null; }; return el; },
                querySelector: function(){ return btn; },
                querySelectorAll: function(){ return btn.classList.contains('ht-opening') ? [btn] : []; },
                body: {classList: Cls(), appendChild: function(el){ VEIL = el; out.veilEver = true; out.veilText = el.textContent; }}};
function _shellHeadH(){ return 64; }
function _shellPaintAgain(fn){ out.paints++; fn(); }
var _shellTab = 'tvd', _shellRouteTimer = null;
function _glide(){} function _shellSizePane(){} function _shellLight(){}
function toast(m){ out.toasts.push(m); }
function fetch(u, o){ out.faults.push(JSON.parse(o.body).kind); return {then: function(){ return this; }}; }
var q = null;
function setInterval(fn){ q = fn; return 7; }
function clearInterval(id){ if (id === 7) q = null; }
%s
shellOpen('vault');
if (VEIL) out.veilText = VEIL.textContent;
while (q && out.ticks < 3000) {
  if (cfg.landAt && out.ticks === cfg.landAt) bwin.switchTab = function(t){ cfg.boardActive = t; };
  q(); out.ticks++;
}
out.veilAfter = !!VEIL;
out.landed = cfg.boardActive === 'vault';
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ALockedTabNeverStrandsTheVeil(unittest.TestCase):

    def drive(self, **cfg):
        fn = _lift()
        self.assertIsNotNone(fn, "the shell route helpers are gone from tv/control_ui.html")
        js = HARNESS % (json.dumps(cfg), fn)
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, "the shipped shellOpen would not run: %s" % p.stderr[-800:])
        return json.loads(p.stdout)

    def test_the_label_is_the_tab_name_not_vaultlocked(self):
        out = self.drive(switchTab="none", landAt=20)
        self.assertIn("opening Vault - the board is busy", out["veilText"] or "", out)
        self.assertNotIn("LOCKED", out["veilText"] or "", "the lock chip's text is glued to the label again: %s" % out)

    def test_a_hidden_window_never_shows_the_veil_and_still_routes(self):
        out = self.drive(switchTab="none", landAt=20, hidden=True)
        self.assertFalse(out["veilEver"], "a hidden (occluded) window put up a veil its frozen pixels can strand: %s" % out)
        self.assertTrue(out["landed"], "the hidden window never routed: %s" % out)

    def test_the_veil_is_removed_when_the_route_lands(self):
        out = self.drive(switchTab="none", landAt=20)
        self.assertTrue(out["veilEver"])
        self.assertFalse(out["veilAfter"], "the veil is still in the DOM after the route landed: %s" % out)
        self.assertGreaterEqual(out["paints"], 1, "no paint pass after the veil came down: %s" % out)

    def test_a_board_without_switchtab_is_reloaded_once_then_told_honestly(self):
        out = self.drive(switchTab="none")
        self.assertEqual(len(out["srcs"]), 1, "the board was not reloaded exactly once: %s" % out)
        self.assertIn("engine=1", out["srcs"][0])
        self.assertIn("#vault", out["srcs"][0])
        self.assertEqual(len(out["toasts"]), 1)
        self.assertNotIn("busy", out["toasts"][0])
        self.assertIn("failed to load", out["toasts"][0])
        self.assertFalse(out["veilAfter"], "the veil stayed up forever on a board that never booted: %s" % out)

    def test_a_switchtab_that_throws_after_moving_is_a_landed_route(self):
        out = self.drive(switchTab="throws")
        self.assertTrue(out["landed"])
        self.assertFalse(out["veilEver"], "a room render that threw after the board moved left the tab waiting: %s" % out)
        self.assertEqual(out["toasts"], [])


RED_PROOF = [
    {
        "why": "REG-2321 - the veil label reads the whole button again: VaultLOCKED",
        "file": "tv/control_ui.html",
        "find": "      var label = (((_lb || b) && (_lb || b).textContent) || '')",
        "replace": "      var label = ((b && b.textContent) || '')",
        "matches": 1,
    },
    {
        "why": "REG-2321 - a hidden (occluded) window puts the veil up again",
        "file": "tv/control_ui.html",
        "find": "    if (!_hiddenDoc) _shellVeil(tab);",
        "replace": "    _shellVeil(tab);",
        "matches": 1,
    },
    {
        "why": "REG-2321 - the veil is only hidden, never removed",
        "file": "tv/control_ui.html",
        "find": "if (v) { v.style.display = 'none'; if (v.remove) v.remove(); }",
        "replace": "if (v) { v.style.display = 'none'; }",
        "matches": 1,
    },
    {
        "why": "REG-2321 - a board that never routes is never reloaded",
        "file": "tv/control_ui.html",
        "find": "      if (!_reloaded && (n > 750 || (n > 250 && n - _unbootedAt > 250))) {",
        "replace": "      if (false) {",
        "matches": 1,
    },
    {
        "why": "REG-2321 - a switchTab throw after the board moved fails the route again",
        "file": "tv/control_ui.html",
        "find": "        try { w.switchTab(tab); } catch (_sw) {}",
        "replace": "        w.switchTab(tab);",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
