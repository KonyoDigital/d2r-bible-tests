# -*- coding: utf-8 -*-
"""REG-2521 FIX ROUND (V1 round 3; the review of REG-2521, minors S1-S5 + the reconcile) - A REMOVAL THE DOOR REFUSED IS
NEVER WALKED AROUND, NEVER SAID AS DONE, AND NEVER STAMPS A ONE-TIME RUN AS RUN.

The reviewer sabotaged five of REG-2520 / REG-2521's behaviour changes one at a time on a copy of the page and ran the 16
related laws: every one stayed green (sabotage.py S1-S5, red=[] each). The behaviours had no law:
  S1  the TV unvault (tvVaultUnregisterMany) asks the hold before anything, and returns on a refused batch - without
      them its residue loop takes names out of owned / the map / the witness rows with no journal row (the r7 class);
  S2  Delete unsorted returns the door's refusal - without it the board says "🗑 cleared N" over a removal that refused;
  S3  vaultFile never answers moved / filed over a mule map the door would not write ('not-written');
  S4  the one-time seed cleanse does not stamp itself done when the removal door refused;
  S5  the re-tick redo says the journal would not read - never "another removal came after".
And (review of REG-2521, minor) the one-time SET-PIECE RECONCILE still ran while the door refused: it folded nothing and
stamped itself done (stamped:true, removed:[]), so the bare/slotted pair stayed double-counted for good and the run armed
the records (p4). Swept with it: while the vault is HELD the seed cleanse and the reconcile do not run at all - `owned`
in memory is a stand-in for a held store then, so a run would find nothing and stamp itself done over his real residue
(the provenance backfill's rule, REG-2521).

WHAT IS DRIVEN, cut whole from bible.html, in node: the store door, the boot, the vault module's head and filing block
(store_door_harness.vault_page) with the removal journal, vaultRemove, tvVaultUnregisterMany and vaultClearUnsorted; and,
over their own stubs, _seedCleanse, _setPieceReconcile and _tickRedoRestore. RED_PROOF below. A missing node is the only
skip.
"""
import json
import os
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

import store_door_harness as D  # noqa: E402

#: the removal journal cut short mid-write (the review's r7 bytes)
JOURNAL_CUT = ('[{"ts":1760000000000,"lane":"hand","names":["Shako"],"filed":{"Shako":"uni-armor"}},'
               '{"ts":1760000100000,"lane":"hand","names":["Enigma"],"filed":{"Enigma":"uni-armor"},"prov')
ROW = {"mule": "uni-armor", "holder": "UNI-ARMOR", "source": "stash", "by": "reader", "at": "2026-10-01T10:00:00Z",
       "sessions": [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9}, {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85}],
       "looks": [{"id": "s_a", "conf": 0.9}, {"id": "s_b", "conf": 0.85}]}
GRIEF = {"mule": "uni-weap", "holder": "UNI-WEAPONS", "source": "hand", "by": "hand", "at": "2026-10-01", "where": "the vault manager",
         "sessions": [], "looks": []}
L2 = "[{session:'s_a',frame:'f_a.jpg',conf:0.9},{session:'s_b',frame:'f_b.jpg',conf:0.85}]"


def _page_pieces(s):
    extra = ("var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
             + D.between(s, "  function _vrRead(){", "  /* the heart and the console read the journal through here", keep_b=False)
             + D.between(s, "  window.vaultRemove = function(names, opts){", "  // v342.3 — throw out a Magic & Rare keeper", keep_b=False)
             + D.fn(s, "_tvFrameMs") + "\n" + D.window_fn(s, "tvVaultUnregisterMany") + "\n"
             + D.start_to_close(s, s.index("  window.vaultClearUnsorted = async function(){"), "vaultClearUnsorted") + ";\n"
             + "window.__V = { assign: function(){ return assign; } };\n"
             # the dock list he sees, stood in (the real one reads the whole page): declared last, so it is the one in scope
             + "function _dockNames(){ return DOCK.slice(); }\n")
    pre = ("window._vaultResolveName = function(n){ return n; };\nvar EXTRA_ITEMS = {};\n"
           "window._ownedAdd = function(n){ owned.add(n); return { ok: true }; };\n"
           "window._vaultRemovalNote = function(){ return { noted: 0 }; };\n"
           "var DOCK = [];\n"
           "window.uiConfirm = function(){ return Promise.resolve(true); };\n"
           "var VST = new El('vault-status'); ELS['vault-status'] = VST;\n")
    return D.vault_page(s, extra).replace(D.VAULT_DOOR_STUBS, D.VAULT_DOOR_STUBS + pre, 1)


WRITES = ("var WROTE = [], REFUSE = {}; var _set = window.LSR.setItem; window.LSR.setItem = function(k, v){ WROTE.push(k);"
          " if (REFUSE[k]) return false; return _set.call(window.LSR, k, v); };\n")


def _page(body, seed):
    s = D.src()
    return D.page(_page_pieces(s), WRITES + body, seed=seed)


def _seed(**more):
    out = {"d2r_owned": '["Grief","Enigma"]', "d2r_muleAssign": '{"Grief":"uni-weap","Shako":"uni-armor"}',
           "d2r_vaultProv": json.dumps({"Grief": GRIEF, "Shako": ROW})}
    out.update(more)
    return out


def _node(prog):
    r = subprocess.run([D.NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped code would not run in node - UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED removal doors; UNMEASURED, not passing")
class ARefusedRemovalIsNeverWalkedAround(unittest.TestCase):

    def test_s1_the_tv_unvault_asks_the_hold_before_its_residue_loop(self):
        """Shako is filed and witnessed but not owned (a residue): with d2r_copies cut short the vault is held, and the
        TV unvault must not drop its filing or its witness row while the map write is refused"""
        o = _page("WROTE.length = 0; OUT.r = window.tvVaultUnregisterMany(['Shako'], null);"
                  "OUT.wrote = WROTE.slice(); OUT.prov = RAW['d2r_vaultProv']; OUT.map = JSON.parse(JSON.stringify(window.__V.assign()));"
                  "OUT.said = VST.textContent || '';", _seed(d2r_copies='{"Grief":2'))
        self.assertEqual(o["r"].get("refused"), "held", "the TV unvault ran over a held vault: %r" % o["r"])
        self.assertEqual(o["wrote"], [], "the TV unvault wrote %r while the vault is held" % o["wrote"])
        self.assertEqual(json.loads(o["prov"]), {"Grief": GRIEF, "Shako": ROW}, "a witness row was dropped while held")
        self.assertEqual(o["map"], {"Grief": "uni-weap", "Shako": "uni-armor"}, "a filing was dropped in memory while held")
        self.assertIn("TV unvault waits", o["said"])
        self.assertIn("d2r_copies", o["said"], "the wait does not name the store")

    def test_s1_a_batch_the_door_refused_is_never_walked_around_by_the_residue_loop(self):
        """whatever the door's reason, a refused batch ends the unvault: no owned.delete, no map delete, no row drop"""
        s = D.src()
        prog = (r"""
var window = globalThis, owned = new Set(['Grief', 'Enigma']), assign = { Grief: 'uni-weap', Enigma: 'runewords' };
var DROPPED = [], SAVED = 0, VST = { textContent: '' };
var document = { getElementById: function(id){ return id === 'vault-status' ? VST : null; } };
window._vaultProvHeld = function(){ return null; }; window._vaultRemovalHeld = function(){ return null; };
window.vaultRemovalLog = function(){ return []; };
window.vaultRemove = function(names){ return { requested: names.length, removed: [], skipped: [], ts: null, batch: null,
  refused: 'held', held: ['d2r_vaultRemovedAt'], why: 'the per-item removal record would not read' }; };
function _provDrop(n){ DROPPED.push(n); } function persistOwned(){ SAVED++; } function saveA(){ SAVED++; } function renderVault(){}
""" + D.fn(s, "_tvFrameMs") + "\n" + D.window_fn(s, "tvVaultUnregisterMany") + r"""
var r = window.tvVaultUnregisterMany(['Grief'], { frame: 'f_1790549355102.jpg' });
process.stdout.write(JSON.stringify({ r: r, owned: Array.from(owned).sort(), assign: assign, dropped: DROPPED, saved: SAVED }));
""")
        o = _node(prog)
        self.assertFalse(o["r"]["ok"], "a refused batch was answered ok: %r" % o["r"])
        self.assertEqual(o["r"].get("refused"), "held")
        self.assertEqual(o["owned"], ["Enigma", "Grief"], "the residue loop took a name out of owned with no journal row")
        self.assertEqual(o["assign"], {"Grief": "uni-weap", "Enigma": "runewords"}, "the residue loop dropped a filing")
        self.assertEqual(o["dropped"], [], "the residue loop dropped a witness row")
        self.assertEqual(o["saved"], 0, "a store was written after the door refused")

    def test_s2_delete_unsorted_says_the_refusal_never_cleared_n(self):
        o = _page("DOCK = ['Enigma']; window.__ASYNC = true; STATUS.length = 0;"
                  "window.vaultClearUnsorted().then(function(r){ OUT.r = r; OUT.status = STATUS.slice();"
                  " OUT.owned = Array.from(owned).sort(); OUT.raw = RAW['d2r_owned']; done(); });",
                  _seed(d2r_vaultRemoved=JOURNAL_CUT))
        self.assertEqual((o["r"] or {}).get("refused"), "held", "PREMISE: the removal door did not refuse: %r" % o["r"])
        self.assertEqual(o["owned"], ["Enigma", "Grief"], "a name left owned over a refused removal")
        self.assertEqual(o["raw"], '["Grief","Enigma"]', "d2r_owned was written over a refused removal")
        self.assertFalse(any("cleared" in m for m in o["status"]), "the dock said 'cleared' over a refusal: %r" % o["status"])
        self.assertTrue(o["status"] and "nothing removed" in o["status"][-1], "the refusal was not the last word: %r" % o["status"])

    def test_s3_vault_file_never_answers_moved_or_filed_over_a_map_it_could_not_write(self):
        o = _page("REFUSE['d2r_muleAssign'] = true;"
                  "OUT.move = window.vaultFile('Grief', null, { move: true, mule: 'uni-armor', by: 'hand' });"
                  "OUT.file = window.vaultFile('Enigma', { by: 'reader', lane: 'stash', sessions: " + L2 + " }, { mule: 'uni-armor' });"
                  "OUT.map = JSON.parse(JSON.stringify(window.__V.assign())); OUT.prov = JSON.parse(RAW['d2r_vaultProv']);"
                  "OUT.rawMap = RAW['d2r_muleAssign'];", _seed())
        for door in ("move", "file"):
            r = o[door]
            self.assertFalse(r["ok"], "vaultFile's %s answered ok over a map it could not write: %r" % (door, r))
            self.assertEqual(r.get("refused"), "not-written", r)
        self.assertEqual(o["map"], {"Grief": "uni-weap", "Shako": "uni-armor"}, "memory kept a move / filing the map refused")
        self.assertEqual(o["rawMap"], '{"Grief":"uni-weap","Shako":"uni-armor"}')
        self.assertEqual(o["prov"]["Grief"]["mule"], "uni-weap", "the row was left saying the refused move's home: %r" % o["prov"]["Grief"])


SEED_CLEANSE = r"""
var window = globalThis, RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
console.info = function(){};
var _SC_KEY = 'd2r_seedCleanse', _SC_VER = 1;
function _iso(ms){ return new Date(ms).toISOString(); } function _hereWorld(){ return 'main'; }
function _read(){ return {}; } function _assignMap(){ return {}; } function _stateOf(){ return {}; }
var owned = new Set(['Harlequin Crest']);
window._laneLockWhy = function(){ return null; };
var CALLS = 0, HELD = null;
window._vaultHeld = function(){ return HELD; };
window.vaultRemove = function(names){ CALLS++; return { requested: names.length, removed: [], skipped: [], ts: null, batch: null,
  refused: 'held', held: ['d2r_vaultRemoved'], why: 'the removal journal (d2r_vaultRemoved) would not read' }; };
%(bf)s
%(fn)s
var OUT = {};
OUT.refused = window._seedCleanse({ names: ['Harlequin Crest'], mainLedger: 'absent' });
OUT.stampAfterRefused = RAW[_SC_KEY] || null; OUT.callsRefused = CALLS;
HELD = { keys: ['d2r_owned'], why: 'the vault is held - d2r_owned will not parse' }; CALLS = 0;
OUT.held = window._seedCleanse({ names: ['Harlequin Crest'], mainLedger: 'absent' });
OUT.stampAfterHeld = RAW[_SC_KEY] || null; OUT.callsHeld = CALLS;
process.stdout.write(JSON.stringify(OUT));
"""

RECONCILE = r"""
var window = globalThis, RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
console.info = function(){};
var _SPR_KEY = 'd2r_setPieceReconcile', _SPR_VER = 3;
function _iso(ms){ return new Date(ms).toISOString(); } function _hereWorld(){ return 'main'; }
var owned = new Set(["Natalya's Totem", "Natalya's Totem (helm)"]), copies = {};
var AMAP = { "Natalya's Totem (helm)": 'sets-rest' };
function _assignMap(){ return AMAP; }
window._vfCanon = function(n){ return n === "Natalya's Totem" ? "Natalya's Totem (helm)" : n; };
window._ownedPutBack = function(){};
var CALLS = 0, HELD = null;
window._vaultHeld = function(){ return HELD; };
/* the removal door's own answer while it refuses (REG-2521): nothing removed, refused, said */
window.vaultRemove = function(names){ CALLS++; return { requested: names.length, removed: [], skipped: [], ts: null, batch: null,
  refused: 'held', held: ['d2r_vaultRemoved'], why: 'the removal journal (d2r_vaultRemoved) would not read' }; };
%(bf)s
%(fn)s
%(may)s
var OUT = {};
var r = window._setPieceReconcile({});
OUT.first = { ran: r.ran, stamped: r.stamped, why: r.why || null, may: _vaultRecordsMayArm(r) };
OUT.stamp = RAW[_SPR_KEY] || null; OUT.calls = CALLS;
var again = window._setPieceReconcile({});
OUT.second = { ran: again.ran, already: !!again.already };
HELD = { keys: ['d2r_copies'], why: 'the vault is held - d2r_copies will not parse' }; CALLS = 0;
var h = window._setPieceReconcile({});
OUT.held = { ran: h.ran, why: h.why || null, calls: CALLS, stamp: RAW[_SPR_KEY] || null, may: _vaultRecordsMayArm(h) };
OUT.owned = Array.from(owned).sort();
process.stdout.write(JSON.stringify(OUT));
"""

RETICK = r"""
var window = globalThis, RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var RESTORED = 0;
window.vaultRemovalLog = function(){ return null; };                      /* the journal would not read: UNKNOWN */
window.vaultRestoreLast = function(){ RESTORED++; return { restored: 1, kept: 0 }; };
%(fn)s
var out = window._tickRedoRestore('Grief', { vaultTs: 1760000000000 });
process.stdout.write(JSON.stringify({ out: out, say: (typeof window._tickRedoSay === 'function') ? window._tickRedoSay(out) : null, restored: RESTORED }));
"""


def _bf(s):
    return D.between(s, "  function _bfJson(k, dflt){", "catch (e) { return undefined; } }\n")


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED one-time runs; UNMEASURED, not passing")
class AOneTimeRunNeverStampsOverARefusal(unittest.TestCase):

    def test_s4_the_seed_cleanse_does_not_stamp_over_a_refused_removal_or_run_while_held(self):
        s = D.src()
        o = _node(SEED_CLEANSE % {"bf": _bf(s), "fn": D.window_fn(s, "_seedCleanse")})
        self.assertFalse(o["refused"].get("ran"), "a cleanse the door refused was a cleanse that ran: %r" % o["refused"])
        self.assertIn("asks again next load", o["refused"].get("why", ""), "the wait was not said")
        self.assertIsNone(o["stampAfterRefused"], "the cleanse stamped itself done over a refused removal")
        self.assertEqual(o["callsRefused"], 1, "PREMISE: the cleanse never reached the removal door")
        self.assertFalse(o["held"].get("ran"), "the cleanse ran while the vault is held: %r" % o["held"])
        self.assertIn("the vault is held", o["held"].get("why", ""))
        self.assertIsNone(o["stampAfterHeld"], "the cleanse stamped itself done while the vault is held")
        self.assertEqual(o["callsHeld"], 0, "the cleanse went to the removal door while the vault is held")

    def test_the_set_piece_reconcile_does_not_stamp_over_a_refused_removal_or_run_while_held(self):
        s = D.src()
        o = _node(RECONCILE % {"bf": _bf(s), "fn": D.window_fn(s, "_setPieceReconcile"), "may": D.fn(s, "_vaultRecordsMayArm")})
        self.assertEqual(o["calls"], 1, "PREMISE: the reconcile never reached the removal door")
        self.assertFalse(o["first"]["ran"], "a reconcile the door refused was a reconcile that ran: %r" % o["first"])
        self.assertIn("asks again next load", o["first"]["why"] or "", "the wait was not said")
        self.assertIsNone(o["stamp"], "the reconcile stamped itself done over a refused removal (the pair stays double-counted)")
        self.assertFalse(o["first"]["may"], "a refused reconcile armed the records")
        self.assertFalse(o["second"]["already"], "the next load answers 'already' - the pair is never folded")
        self.assertFalse(o["held"]["ran"], "the reconcile ran while the vault is held: %r" % o["held"])
        self.assertIn("the vault is held", o["held"]["why"] or "")
        self.assertEqual(o["held"]["calls"], 0, "the reconcile went to the removal door while the vault is held")
        self.assertIsNone(o["held"]["stamp"])
        self.assertFalse(o["held"]["may"], "a held reconcile armed the records")
        self.assertEqual(o["owned"], ["Natalya's Totem", "Natalya's Totem (helm)"], "a name left owned")

    def test_s5_the_re_tick_redo_says_the_journal_would_not_read(self):
        s = D.src()
        o = _node(RETICK % {"fn": D.window_fn(s, "_tickRedoRestore") + "\n" + D.window_fn(s, "_tickRedoSay")})
        self.assertEqual(o["restored"], 0, "the redo undid a removal over a journal it could not read")
        why = (o["out"].get("vault") or {}).get("why", "")
        self.assertIn("would not read", why, "an UNKNOWN journal was not said: %r" % o["out"])
        self.assertNotIn("another removal came after", why, "an UNKNOWN journal was said as 'another removal came after'")
        self.assertIn("would not read", o["say"] or "", "the bar does not say the journal would not read: %r" % o["say"])


RED_PROOF = [
    {"why": "REG-2521 fix round (S1) - the TV unvault no longer asks the hold: its residue loop drops a filed name's row while "
            "the map write is refused",
     "file": "bible.html", "matches": 1,
     "find": "    if (_hTv){\n      var _stTh",
     "replace": "    if (false){\n      var _stTh"},
    {"why": "REG-2521 fix round (S1) - the TV unvault walks around a batch the removal door refused",
     "file": "bible.html", "matches": 1,
     "find": "    if (batch && batch.refused) return { ok:false, refused: batch.refused, why: batch.why, labels: list };",
     "replace": "    if (false) return { ok:false, refused: batch.refused, why: batch.why, labels: list };"},
    {"why": "REG-2521 fix round (S2) - Delete unsorted says 'cleared N' over a refused removal",
     "file": "bible.html", "matches": 1,
     "find": "    if (_vrCU && _vrCU.refused) return _vrCU;\n",
     "replace": "\n"},
    {"why": "REG-2521 fix round (S3) - vaultFile answers 'moved' over a mule map it could not write",
     "file": "bible.html", "matches": 1,
     "find": "      if (saveA() === false){ assign[nm] = _fromM;\n",
     "replace": "      saveA(); if (false){ assign[nm] = _fromM;\n"},
    {"why": "REG-2521 fix round (S3) - vaultFile answers 'filed' over a mule map it could not write",
     "file": "bible.html", "matches": 1,
     "find": "    if (saveA() === false){ if (_fromF == null) delete assign[nm]; else assign[nm] = _fromF;\n",
     "replace": "    saveA(); if (false){ if (_fromF == null) delete assign[nm]; else assign[nm] = _fromF;\n"},
    {"why": "REG-2521 fix round (S3) - a refused move leaves the witness row saying the home the map never took",
     "file": "bible.html", "matches": 1,
     "find": "        if (_rowM0){ try { var pmB = _provAll();",
     "replace": "        if (false){ try { var pmB = _provAll();"},
    {"why": "REG-2521 fix round (S4) - the seed cleanse stamps itself done over a refused removal",
     "file": "bible.html", "matches": 1,
     "find": "    if (vr && vr.refused) return { ran: false, why: 'the removal door refused (' + String(vr.why || vr.refused) + ') — nothing was stamped; it asks again next load' };\n",
     "replace": ""},
    {"why": "REG-2521 fix round - the seed cleanse runs (and stamps) while the vault is held",
     "file": "bible.html", "matches": 1,
     "find": "    if (_hSc) return { ran: false, why: _hSc.why + ' — nothing was removed or stamped; it asks again next load' };\n",
     "replace": ""},
    {"why": "REG-2521 fix round - the set-piece reconcile stamps itself done over a refused removal",
     "file": "bible.html", "matches": 1,
     "find": "    if (vr && vr.refused) return { ran: false, why: 'the removal door refused (' + String(vr.why || vr.refused) + ') — nothing was folded or stamped; it asks again next load' };\n",
     "replace": ""},
    {"why": "REG-2521 fix round - the set-piece reconcile runs (and stamps) while the vault is held",
     "file": "bible.html", "matches": 1,
     "find": "    if (_hSpr) return { ran: false, why: _hSpr.why + ' — nothing was folded or stamped; it asks again next load' };\n",
     "replace": ""},
    {"why": "REG-2521 fix round (S5) - the re-tick redo reads an UNKNOWN journal as 'another removal came after'",
     "file": "bible.html", "matches": 1,
     "find": "        out.vault = (log === null)\n          ? { restored: 0, why: 'the vault removal journal would not read - its bytes are kept aside (see the notice at the top)' }\n          : (last && last.ts === r.vaultTs)\n",
     "replace": "        out.vault = (last && last.ts === r.vaultTs)\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
