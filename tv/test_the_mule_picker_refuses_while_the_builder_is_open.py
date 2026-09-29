# -*- coding: utf-8 -*-
"""#41 rank 21 (REG-1535, 2026-09-29) — THE REVERSE DOOR: A MULE PICKER OVER THE OPEN BUILDER REFUSES AND SAYS WHY.

The heart audit (verified list, rank 21): "Opening a mule picker while the builder is open is unguarded. _cbHostOpen
overwrites st.pick with host 'mule', and the builder is not focus-trapped. Not driven, so whether it reproduces is
UNKNOWN." The Characters room guards html.cb-lock (#245 review: no delete under the open planner); the mule host did
not. Reproduced here first: with the builder open, _cbHostOpen took the mule host and the builder's own picker state
was gone.

WHAT THIS LAW DRIVES, in the SHIPPED blocks (the ⟦cb-builder-js⟧ block and the mule window's own _mpHostSync and
_mpPick, cut from bible.html between their real boundaries, run in node over the same stand-in
test_the_characters_tab_is_manual_and_separate uses):
  · THE DOOR: with the builder open (html.cb-lock on), window._cbHostOpen refuses (false), the mule host is NOT on
    (_cbHostOn is false for the slot and for an inventory cell), window._cbHostRefusedWhy names the builder, and the
    host draws no second #cb-modal — the builder's own one is the only one on the page.
  · THE POSITIVE CONTROL: the same call before the builder opens, and again after it closes, opens the host, says
    nothing, and draws exactly one host #cb-modal.
  · THE MULE WINDOW SAYS WHY: _mpHostSync (the one caller for a slot) keeps the slot picked and writes the refusal
    into _mpPickErr — the string its picker footer prints; a keyboard/click pick (window._mpPick, what Enter on a slot
    button runs) reaches the same refusal; once the builder closes, the same pick opens the host and clears the error.
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

from test_the_characters_tab_is_manual_and_separate import NODE, _between, _run, _src   # the shipped harness

CTX = ("{ slot: 'head', set: 'setI', mule: 'Mule One', cur: function(){ return null; }, write: function(){}, "
       "render: function(){}, close: function(){} }")
INV = ("{ kind: 'inv', cell: [0, 0], mule: 'Mule One', fits: function(){ return true; }, cur: function(){ return null; }, "
       "write: function(){}, render: function(){}, close: function(){} }")


def _mule_cuts(s):
    """the mule window's host caller and its slot pick, cut between their own boundaries (never re-typed)"""
    sync = "function _mpHostSync(){" + _between(s, "  function _mpHostSync(){", "\n  /* ── #174 v-B5 — THE INVENTORY'S PICKER: ONE PICKER, A THIRD PLACE IT OPENS") + "\n"
    pick = "window._mpPick = function(slot){" + _between(s, "  window._mpPick = function(slot){", "\n  window._mpChoose = function(i){") + "\n"
    return sync + pick


def _modal_count(html):
    return 'OUT.__K__ = (String(__H__).match(/id="cb-modal"/g) || []).length;'.replace("__H__", html)


@unittest.skipIf(NODE is None, "node is not on this machine")
class TheMulePickerRefusesWhileTheBuilderIsOpen(unittest.TestCase):

    def test_the_door_refuses_under_the_open_builder_and_opens_once_it_closes(self):
        body = r"""
seed('bHAM');
function host(){ try { return window._cbHostHtml({ html: '', n: 0, total: 0 }) || ''; } catch (e) { return 'THREW ' + (e && e.message); } }
OUT.before = { opened: window._cbHostOpen(__CTX__), why: window._cbHostRefusedWhy, on: window._cbHostOn('head') };
OUT.beforeModals = (host().match(/id="cb-modal"/g) || []).length;
window._cbHostClose();
window.openCharBuilder('bHAM');
OUT.lock = HTML.classList.contains('cb-lock');
OUT.refused = { opened: window._cbHostOpen(__CTX__), why: window._cbHostRefusedWhy, on: window._cbHostOn('head'), host: host() };
OUT.invRefused = { opened: window._cbHostOpen(__INV__), why: window._cbHostRefusedWhy, on: window._cbHostOn('inv') };
OUT.pageModals = (String(ELS['cb-win']._html).match(/id="cb-modal"/g) || []).length;
window.closeCharBuilder();
OUT.lockAfter = HTML.classList.contains('cb-lock');
OUT.after = { opened: window._cbHostOpen(__CTX__), why: window._cbHostRefusedWhy, on: window._cbHostOn('head') };
OUT.afterModals = (host().match(/id="cb-modal"/g) || []).length;
""".replace("__CTX__", CTX).replace("__INV__", INV)
        out = _run(body)
        self.assertEqual({"opened": True, "why": "", "on": True}, out["before"], "the positive control: the host does not open with the builder closed")
        self.assertEqual(1, out["beforeModals"], "the open host draws no #cb-modal of its own (baseline)")
        self.assertTrue(out["lock"], "the builder did not lock the page")
        self.assertFalse(out["refused"]["opened"], "the mule host opened OVER the open builder")
        self.assertFalse(out["refused"]["on"], "the host is ON although the door refused")
        self.assertIn("Character Builder is open", out["refused"]["why"], "the refusal does not say why")
        self.assertEqual("", out["refused"]["host"], "a refused host still drew markup: %r" % out["refused"]["host"][:80])
        self.assertFalse(out["invRefused"]["opened"], "the inventory-cell door walked in")
        self.assertFalse(out["invRefused"]["on"])
        self.assertIn("Character Builder is open", out["invRefused"]["why"])
        self.assertEqual(1, out["pageModals"], "the page holds %d #cb-modal — the builder's own must be the only one" % out["pageModals"])
        self.assertFalse(out["lockAfter"])
        self.assertEqual({"opened": True, "why": "", "on": True}, out["after"], "closing the builder did not reopen the door")
        self.assertEqual(1, out["afterModals"])

    def test_the_mule_window_keeps_the_slot_and_prints_why_then_opens_once_the_builder_closes(self):
        body = _mule_cuts(_src()) + r"""
var _mpPickAt = null, _mpInvAt = null, _mpPickErr = '', _mpFocusNext = null, openMuleId = 'm1', _mpSwap = 1, RENDERS = 0;
var MP_SLOT_WEARS = { head: ['helm'] };
function muleById(id){ return { id: id, name: 'Mule One' }; }
function _mpHostWrite(){ return { ok: true }; }
function _mpSetOf(slot, swap){ return 'setI'; }
function _mpInvHostOpen(){ OUT.invOpened = true; }
window._mpCbEntryAt = function(){ return null; };
window.openMuleCard = function(){ RENDERS++; };
seed('bHAM');
window.openCharBuilder('bHAM');
/* Enter on a slot button runs its onclick: window._mpPick(slot) */
window._mpPick('head');
OUT.under = { at: _mpPickAt, err: _mpPickErr, on: window._cbHostOn('head'), renders: RENDERS };
/* the render's own retry (the picker panel calls _mpHostSync again when the host is not on) keeps the reason */
_mpHostSync();
OUT.retry = { at: _mpPickAt, err: _mpPickErr, on: window._cbHostOn('head') };
window.closeCharBuilder();
window._mpPick('head');
OUT.after = { at: _mpPickAt, err: _mpPickErr, on: window._cbHostOn('head'), renders: RENDERS };
"""
        out = _run(body)
        self.assertEqual({"slot": "head", "set": "setI"}, out["under"]["at"], "the slot was dropped, so the footer that says why is gone")
        self.assertIn("Character Builder is open", out["under"]["err"], "the mule window does not carry the reason")
        self.assertFalse(out["under"]["on"])
        self.assertGreaterEqual(out["under"]["renders"], 1, "the window was not re-drawn to show the reason")
        self.assertIn("Character Builder is open", out["retry"]["err"])
        self.assertFalse(out["retry"]["on"])
        self.assertEqual({"slot": "head", "set": "setI"}, out["after"]["at"])
        self.assertEqual("", out["after"]["err"], "the reason outlived the builder")
        self.assertTrue(out["after"]["on"], "with the builder closed the same pick did not open the host")


RED_PROOF = [
    {
        "why": "#41 rank 21 - the host door walks in over the open builder again",
        "file": "../bible.html",
        "find": "    if (document.documentElement.classList.contains('cb-lock')){ window._cbHostRefusedWhy = CB_HOST_BUSY_WHY; return false; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 21 - the door refuses but says nothing: the reason is blank",
        "file": "../bible.html",
        "find": "window._cbHostRefusedWhy = CB_HOST_BUSY_WHY; return false; }",
        "replace": "window._cbHostRefusedWhy = ''; return false; }",
        "matches": 1,
    },
    {
        "why": "#41 rank 21 - the mule window ignores the refusal: its picker footer never prints why",
        "file": "../bible.html",
        "find": "    })){ _mpPickErr = window._cbHostRefusedWhy || 'the picker could not open'; }\n",
        "replace": "    })){ }\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the mule host door was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
