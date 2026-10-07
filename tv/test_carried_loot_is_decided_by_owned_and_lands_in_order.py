# -*- coding: utf-8 -*-
"""CARRIED LOOT IS DECIDED BY `owned` AND LANDS IN ORDER — the review of 7cded0c1 (round 5 of the vault evidence route),
every finding reproduced by the reviewer first and driven here on the SHIPPED code. His rulings (HANDOFF_GROK.md):
  §31  carried loot is OWNED right away, NOT locked; it LANDS on a stash / mule sighting; it LEAVES ONLY on a drop / vendor /
       trade signal; ABSENCE NEVER UN-OWNS IT.   §29  worn gear and standing kit are LOCKED to the character.

WHAT THIS LAW HOLDS, one class per finding:
  M-1  A PICK-UP OF A NAME HE DOES NOT OWN IS A PICK-UP. The M-3 line read `cur` beside `owned`, so a receipt a door left
       behind when it un-owned the name (the unique card's un-tick, the menu-page import) stopped the next real pick-up from
       being carried, and the later real drop never left (the v2346 item stayed owned). Now `owned` decides; the stale
       receipt is kept as history (pastReceipts); a name that IS owned is still never re-marked (M-3 stands).
  M-2  A LANDING HAS THE SAME TIME ORDER AS A DROP. A reclose replayed an OLDER session's stash / worn sighting onto carried
       loot a NEWER session picked up and landed it there (a worn one would have LOCKED it, §29) — his later real drop then
       never left. A holding look lands only what it postdates; an older one is history (pastLandings); an undated one is
       UNKNOWN (unorderedLandings) and lands nothing. BASELINE: a newer stash look still lands.
  M-3  EVERY UN-OWN IS HIS WORD, JOURNALED. "Delete unsorted", "These look like a chronicle page", the TV unvault and the
       unique card's un-tick took names out of `owned` beside the removal journal, so REG-1391's "his removal outranks every
       older read" could not see them and the next reclose re-owned what he deleted. Three doors are driven through the
       REAL removal door (cut from the page) and replayed; the un-tick (inside the 140-line toggleOwned) is pinned as code.
  L-1  THE NAME THE REGISTER OWNS. A removal of "Worldstone Shard (any)" blocks a bare "Worldstone Shard" read; a drop read as
       "Harlequin Crest" leaves the "(Shako)" he carries — the read's name goes through the register's ONE resolution slice
       (window._vaultResolveName, the real one) before a removal, a leave or a backfill key is matched.
  L-2  A TIME THE READ DID NOT CARRY IS NOT ITS TIME. An undated pick-up has at / ts null, tsMeasured false and recordedAt
       set; H-1 then says UNKNOWN for a later drop instead of ordering it against the wall clock; a later MEASURED look of
       the same item restores the order and the drop leaves.
  L-3  WITH THE MULE MAP UNREADABLE, FILED / NOT FILED ARE UNKNOWN TOO — the population line says so and Auto-Sort waits.
  L-4  A BARE NAME SEVERAL KNOWN ITEMS SHARE IS NOT A MATCH — Crescent Moon (the runeword beside the amulet):
       window._vaultNameAmbiguity names the candidates, the register refuses it (or settles it by the read's kind) and
       HOLDS the read in the Chronicle inbox naming them (the ask), and _aicIsGrailName no longer resolves it to whichever
       one the codex holds. ROUND-5 REVIEW (HIGH, reproduced on the real name lists): ambiguity is about DIFFERENT items,
       not spellings — a bare "Hellmouth" (one unique the tables spell two ways) is that unique; a bare "Spirit" (two
       runewords of one name) is ONE registrable item whose base is UNKNOWN; a bare "Worldstone Shard" is the "(any)"
       bucket the resolver already answers. Driven through the REAL register head on the TV live witness (no kind).
  R-5  THE RING FORGETS; HIS WORD MUST NOT (round-5 review, MED). Every removal that is his word is noted per name in
       d2r_vaultRemovedAt (never evicted); a card-click removal 25 un-ticks ago still blocks the older read's replay and the
       backfill. The TV's thrown items are ONE batch per read with the read's frame as proof — and a 'tv-unvault' batch
       with no frame un-owns but outranks no older read. The unique card's un-tick keeps the mule filing (LOW: his
       "never delete a mule filing"), journaled with keepFiling.
Driven in node on the board's own code (cut by markers and anchors, never re-typed). RED_PROOF below — each proven one at a
time by heart2 --prove.
"""
import io
import json
import os
import re
import shutil
import sys
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

import test_every_owned_door_writes_provenance as P  # noqa: E402 — the ONE harness for the owned door
import test_carried_loot_keeps_its_order as C  # noqa: E402 — its lock / MAIN cuts
import test_carried_loot_holds_its_time_and_its_name as R4  # noqa: E402 — the board's name lists + the real resolver slice

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")
T = 1790400000000        # a fixture clock (2026-09-26, in the past); every dated read below carries its own time from it

VR_FROM = "  var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
VR_TO = "  // v342.3 — throw out a Magic & Rare keeper"
DOOR_CLEAR = "  window.vaultClearUnsorted = async function(){\n"
#: #264 (REG-2021) - Delete unsorted asks the ONE dock list; it is cut whole beside the door, never stubbed (a stub would
#: be a second copy of "what is loose", the defect REG-2021 closed)
DOCK_FROM = "  function _inMagicRare(n){\n"
DOCK_TO = "  window._vaultInMagicRare = _inMagicRare;\n"
DOOR_MENU = "  window.vaultDropMenuImport = async function(){\n"
DOOR_TV = "  window.tvVaultUnregisterMany = function(names, proof){\n"
DOOR_TV1 = "  window.tvVaultUnregister = function(name, proof){\n"
DOOR_HOLD = "  window._vaultHoldAmbiguous = function(name, amb, witness){\n"
TV_MS_LINE = "  function _tvFrameMs(f){ var m = /^(?:.*\\/)?f_(\\d{12,14})/.exec(String(f || '')); return m ? +m[1] : null; }\n"
REG_HEAD_TO = "      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(name);"
UNTICK_FROM = "  if (_gi){\n    wasOwned = _gFound(name);"
UNTICK_TO = "  } else {\n    /* 2026-08-20 — THIS BRANCH IS DELIBERATELY UNGUARDED"
GRAIL_FROM = "  function _aicIsGrailName(nm){\n"
SORT_FROM = "window.vaultAutoAssign = function(){\n"


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _iso(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000.0, datetime.timezone.utc).isoformat()


def _door(s, head):
    """A door from its head to its own closing `  };` line — bounded by the block, never by a byte count."""
    assert s.count(head) == 1, "door %r matched %d times" % (head.strip()[:50], s.count(head))
    i = s.index(head)
    j = s.index("\n  };\n", i) + len("\n  };\n")
    return s[i:j]


#: the REAL removal journal and the three un-own doors, cut whole, over the harness's stores
DOORS_JS = r"""
var assign = {};
function _provDrop(names){ var all = _provAll(), n = 0; (Array.isArray(names) ? names : [names]).forEach(function(k){
  if (k && Object.prototype.hasOwnProperty.call(all, k)){ delete all[k]; n++; } }); if (n) STORE['d2r_vaultProv'] = JSON.stringify(all); return n; }
function persistOwned(){ STORE['d2r_owned'] = JSON.stringify(Array.from(owned)); }
function saveA(){ STORE['d2r_muleAssign'] = JSON.stringify(assign); }
function renderVault(){} function refreshOpenCard(){} function status(){} function muleById(){ return null; }
function ownedPool(){ return Array.from(owned); } function isSharedStash(){ return false; }
window.uiConfirm = function(){ return Promise.resolve(true); };
window._repaintOwned = function(){};
globalThis.document = { getElementById: function(){ return null; } };
%(vr)s
%(dock)s
%(clear)s
%(menu)s
%(tvms)s
%(tv)s
%(tv1)s
%(hold)s
function journal(){ return JSON.parse(STORE['d2r_vaultRemoved'] || '[]'); }
function noted(){ return JSON.parse(STORE['d2r_vaultRemovedAt'] || '{}'); }
function inbox(){ return JSON.parse(STORE['d2r_chronicleInbox'] || '[]'); }
/* the REAL register's head — the ambiguity gate and the resolution, up to the socket-base stub — cut whole, so a bare name
   is driven through the lines the live doors run (never a stub's) on their own witness shapes */
function REG_HEAD(name, witness){
  try {
%(reghead)s
    return { name: name, amb: _ambV };
  } catch (e) { return { threw: String(e && e.message || e) }; }
}
"""

SCRIPT = r"""
OUT.err = {};
function section(k, f){ try { f(); } catch (e) { OUT.err[k] = String(e && e.stack || e).slice(0, 600); } }
async function asection(k, f){ try { await f(); } catch (e) { OUT.err[k] = String(e && e.stack || e).slice(0, 600); } }
function stateOf(n){ return window._ownedState(n).state; }
function row(n){ return prov()[n] || {}; }
function frames(list){ return (list || []).map(function(d){ return d && d.frame; }); }
// the real resolver slice stands where the page's does, and the stub register files the RESOLVED name as the real one does
window._vaultResolveName = RESOLVE;
var _reg0 = window.tvVaultRegister;
window.tvVaultRegister = function(name, w){ return _reg0(window._vaultResolveName(name), w); };
// the door's own answer to the last add (the stub register discards it), so a law can read the write's mode
var _add0 = window._ownedAdd, LAST_ADD = null;
window._ownedAdd = function(n, r){ LAST_ADD = _add0(n, r); return LAST_ADD; };
// ══ M-1 — a standing receipt for a name he does NOT own never decides; a pick-up is a pick-up ══
section('m1', function(){
  reset({ Shako: { kind: 'owned', source: 'ledger-restore', by: 'the un-seed undo', ts: T0 + 100, at: new Date(T0 + 100).toISOString(), looks: [] } }, []);
  var pick = LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'm1p', sessionId: 's_m1', firstSeenTs: T0 + 100000 });
  var after = row('Shako'), pickAdd = LAST_ADD;
  var drop = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'm1d', sessionId: 's_m1', firstSeenTs: T0 + 200000 });
  OUT.m1 = { pick: pick.route, carried: after.carried === true, source: after.source || null, mode: (pickAdd && pickAdd.prov && pickAdd.prov.mode) || null,
             past: (after.pastReceipts || []).map(function(r){ return r.source; }), drop: drop.route, owned: owned.has('Shako'),
             journal: journal().map(function(b){ return b.lane; }) };
  // the same receipt for a name he DOES own: still never re-marked (M-3 stands)
  reset({ Shako: { kind: 'owned', source: 'ledger-restore', by: 'the un-seed undo', ts: T0 + 100, at: new Date(T0 + 100).toISOString(), looks: [] } }, ['Shako']);
  LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'm1q', sessionId: 's_m1b', firstSeenTs: T0 + 100000 });
  var fl = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'm1e', sessionId: 's_m1b', firstSeenTs: T0 + 200000 });
  OUT.m1owned = { carried: row('Shako').carried === true, floor: fl.route, owned: owned.has('Shako'), state: stateOf('Shako') };
});
// ══ M-2 — an OLDER holding look never lands newer carried loot; a NEWER one does; an undated one is UNKNOWN ══
section('m2', function(){
  reset({}, []);
  var pick = LIVE({ name: 'Magefist', loc: 'inventory', scene: 'inventory', frameId: 'm2p', sessionId: 's_new', firstSeenTs: T0 + 100000 });
  var oldStash = LIVE({ name: 'Magefist', loc: 'stash', scene: 'stash', frameId: 'm2s', sessionId: 's_old', firstSeenTs: T0 + 5000 });
  var r1 = row('Magefist');
  var oldWorn = LIVE({ name: 'Magefist', loc: 'equipped', scene: 'inventory', frameId: 'm2w', sessionId: 's_older', firstSeenTs: T0 + 4000 });
  var r2 = row('Magefist');
  var undated = LIVE({ name: 'Magefist', loc: 'stash', scene: 'stash', frameId: 'm2u', sessionId: 's_und' });
  var r3 = row('Magefist');
  var drop = LIVE({ name: 'Magefist', loc: 'floor', scene: 'loot', frameId: 'm2d', sessionId: 's_new', firstSeenTs: T0 + 200000 });
  OUT.m2 = { pick: pick.route, oldStash: oldStash.route, afterStash: { carried: r1.carried, landed: r1.landed || null, state: null, past: frames(r1.pastLandings), lastAt: r1.lastAt || null },
             afterWorn: { carried: r2.carried, landed: r2.landed || null, past: frames(r2.pastLandings) },
             afterUndated: { carried: r3.carried, landed: r3.landed || null, unordered: frames(r3.unorderedLandings), past: frames(r3.pastLandings) },
             stateBeforeDrop: null, drop: drop.route, owned: owned.has('Magefist'),
             proof: journal().filter(function(b){ return b.lane === 'carried-left'; }).map(function(b){ return b.proof && b.proof.frame; }) };
  // the state after the older looks, read before the drop (a second run of the same order)
  reset({}, []);
  LIVE({ name: 'Magefist', loc: 'inventory', scene: 'inventory', frameId: 'm2p', sessionId: 's_new', firstSeenTs: T0 + 100000 });
  LIVE({ name: 'Magefist', loc: 'stash', scene: 'stash', frameId: 'm2s', sessionId: 's_old', firstSeenTs: T0 + 5000 });
  LIVE({ name: 'Magefist', loc: 'equipped', scene: 'inventory', frameId: 'm2w', sessionId: 's_older', firstSeenTs: T0 + 4000 });
  OUT.m2.stateBeforeDrop = stateOf('Magefist');
  // BASELINE — a NEWER stash look still lands, and the landed item no longer leaves on a drop (H2)
  reset({}, []);
  LIVE({ name: 'Nagelring', loc: 'inventory', scene: 'inventory', frameId: 'm2b1', sessionId: 's_b', firstSeenTs: T0 + 100000 });
  LIVE({ name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'm2b2', sessionId: 's_b', firstSeenTs: T0 + 150000 });
  var rb = row('Nagelring');
  var bd = LIVE({ name: 'Nagelring', loc: 'floor', scene: 'loot', frameId: 'm2b3', sessionId: 's_b', firstSeenTs: T0 + 200000 });
  OUT.m2base = { carried: rb.carried, landedFrame: rb.landed && rb.landed.frame, state: stateOf('Nagelring'), drop: bd.route, owned: owned.has('Nagelring') };
});
// ══ M-3 — the three un-own doors, through the REAL removal door, then the same older read replayed ══
await asection('m3', async function(){
  reset({}, []);
  var read = { name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'm3n', sessionId: 's_m3', firstSeenTs: T0 + 5000 };
  LIVE(read);
  var ownedBefore = owned.has('Nagelring');
  await window.vaultClearUnsorted();
  var j1 = journal();
  var back = LIVE(read);
  OUT.m3clear = { ownedBefore: ownedBefore, ownedAfterClear: owned.has('Nagelring'), lanes: j1.map(function(b){ return b.lane; }),
                  names: j1.map(function(b){ return b.names; }), replay: back.route, removedAfter: back.removedAfter || null,
                  ownedAfterReplay: owned.has('Nagelring'), provAfter: prov()['Nagelring'] || null };
  reset({}, []);
  var read2 = { name: 'Magefist', loc: 'stash', scene: 'stash', frameId: 'm3m', sessionId: 's_m3', firstSeenTs: T0 + 5000 };
  LIVE(read2);
  window._menuRunVerdict = { isMenu: true, armed: true, names: ['Magefist'], why: 'the law' };
  await window.vaultDropMenuImport();
  var j2 = journal();
  var back2 = LIVE(read2);
  OUT.m3menu = { ownedAfter: owned.has('Magefist'), lanes: j2.map(function(b){ return b.lane; }), replay: back2.route,
                 removedAfter: back2.removedAfter || null, ownedAfterReplay: owned.has('Magefist') };
  reset({}, []);
  var read3 = { name: 'Windforce', loc: 'stash', scene: 'stash', frameId: 'm3w', sessionId: 's_m3', firstSeenTs: T0 + 5000 };
  var read3b = { name: 'Titan\'s Revenge', loc: 'stash', scene: 'stash', frameId: 'm3w', sessionId: 's_m3', firstSeenTs: T0 + 5000 };
  LIVE(read3); LIVE(read3b);
  // R-5 — the TV door hands the WHOLE thrown list as ONE batch, with the frame that saw them thrown (its own stamp is the time)
  var tv = window.tvVaultUnregisterMany(['Windforce', 'Titan\'s Revenge'], { frame: 'f_' + (T0 + 60000) + '.jpg' });
  var j3 = journal();
  var back3 = LIVE(read3);
  OUT.m3tv = { ok: tv && tv.ok, ownedAfter: owned.has('Windforce'), lanes: j3.map(function(b){ return b.lane; }), replay: back3.route,
               removedAfter: back3.removedAfter || null, ownedAfterReplay: owned.has('Windforce'),
               batchNames: j3.map(function(b){ return b.names; }), proof: j3.map(function(b){ return b.proof; }),
               noted: noted()['windforce'] || null };
  // BASELINE — a pick-up NEWER than the removal is his again
  var again = LIVE({ name: 'Windforce', loc: 'stash', scene: 'stash', frameId: 'm3w2', sessionId: 's_m3b', firstSeenTs: T0 + 90000 });
  OUT.m3tv.again = again.route; OUT.m3tv.ownedAgain = owned.has('Windforce');
  // R-5 — a TV unvault with NO frame un-owns the name (as before) but is not his word: the older read comes back
  reset({}, []);
  LIVE(read3);
  var bare = window.tvVaultUnregister('Windforce');
  var ownedAfterBare = owned.has('Windforce');   // read BEFORE the replay, which (rightly) owns it again
  var jb = journal();
  var backB = LIVE(read3);
  OUT.m3tvbare = { ok: bare && bare.ok, ownedAfter: ownedAfterBare, lanes: jb.map(function(b){ return b.lane; }),
                   proof: jb.map(function(b){ return b.proof; }), replay: backB.route, ownedAfterReplay: owned.has('Windforce'),
                   noted: noted()['windforce'] || null, word: window._removalIsHisWord(jb[0] || null) };
});
// ══ R-5 — the ring forgets; his word must not ══
section('r5ring', function(){
  reset({}, []);
  var readN = { name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'r5n', sessionId: 's_r5', firstSeenTs: T0 + 5000 };
  LIVE(readN);
  var _dn = Date.now; Date.now = function(){ return T0 + 50000; };
  try { window.vaultRemove(['Nagelring'], { lane: 'card-click', why: 'not mine' }); } finally { Date.now = _dn; }
  OUT.r5ring = { notedAfterClick: noted()['nagelring'] || null };
  // 25 un-ticks of other names, each its own batch (M-3): the ring keeps 20, so the card-click batch is evicted
  for (var i = 0; i < 25; i++){ var fn = 'Filler Unique ' + i; owned.add(fn); window.vaultRemove([fn], { lane: 'un-tick', quiet: true, keepFiling: true, why: 'un-ticked' }); }
  var jr = journal();
  OUT.r5ring.ring = jr.length;
  OUT.r5ring.clickInRing = jr.some(function(b){ return (b.names || []).indexOf('Nagelring') >= 0; });
  var back = LIVE(readN);
  OUT.r5ring.replay = back.route; OUT.r5ring.removedAfter = back.removedAfter || null; OUT.r5ring.owned = owned.has('Nagelring');
  // and the backfill reads the same record: the older inbox row of the removed name is skipped as removed-by-him
  STORE['d2r_chronicleInboxLog'] = JSON.stringify([{ name: 'Nagelring', status: 'in-chronicle', source: 'kai-register', sessionId: 's_r5',
    frameId: 'r5n', firstSeenTs: T0 + 5000, loc: 'stash', scene: 'stash' }]);
  var bf = window._ownedProvBackfill();
  OUT.r5ring.bf = { filed: (bf.receipt || {}).filed, skipped: (bf.receipt || {}).skipped, owned: owned.has('Nagelring') };
  // a NEWER pick-up is his again (a removal is not a ban)
  var again = LIVE({ name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'r5n2', sessionId: 's_r5b', firstSeenTs: T0 + 90000 });
  OUT.r5ring.again = again.route;
  // an unreadable per-name record is UNKNOWN: the read waits, nothing is replayed
  STORE['d2r_vaultRemovedAt'] = '{';
  var wait = LIVE({ name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'r5n', sessionId: 's_r5', firstSeenTs: T0 + 5000 });
  OUT.r5ring.unread = { route: wait.route, why: wait.why || '' };
});
// ══ R-5 — the un-tick keeps the mule filing (his ruling), journaled; a plain removal still takes it ══
section('r5keep', function(){
  reset({ Shako: { mule: 'uni-armor', source: 'stash', by: 'reader', tier: 'PROVEN' } }, ['Shako', 'Windforce']);
  assign = { Shako: 'uni-armor', Windforce: 'uni-weap' }; saveA();
  var r1 = window.vaultRemove(['Shako'], { lane: 'un-tick', quiet: true, keepFiling: true, why: 'un-ticked on its item card' });
  var r2 = window.vaultRemove(['Windforce'], { lane: 'card-click', quiet: true, why: 'not mine' });
  var jk = journal();
  OUT.r5keep = { removed: [r1.removed, r2.removed], ownedShako: owned.has('Shako'), assignShako: assign['Shako'] || null,
                 provShako: prov()['Shako'] || null, storeAssign: JSON.parse(STORE['d2r_muleAssign'] || '{}'),
                 assignWind: assign['Windforce'] || null, batches: jk.map(function(b){ return { lane: b.lane, keepFiling: b.keepFiling, filed: b.filed }; }) };
});
// ══ L-1 — the name the register owns ══
section('l1', function(){
  reset({}, []);
  var pick = LIVE({ name: 'Harlequin Crest', loc: 'inventory', scene: 'inventory', frameId: 'l1p', sessionId: 's_l1', firstSeenTs: T0 + 100000 });
  var ownedAs = Array.from(owned);
  var drop = LIVE({ name: 'Harlequin Crest', loc: 'floor', scene: 'loot', frameId: 'l1d', sessionId: 's_l1', firstSeenTs: T0 + 200000 });
  OUT.l1drop = { pick: pick.route, ownedAs: ownedAs, drop: drop.route, left: drop.left || null, owned: Array.from(owned),
                 proof: journal().filter(function(b){ return b.lane === 'carried-left'; }).map(function(b){ return b.names; }) };
  reset({}, []);
  LIVE({ name: 'Worldstone Shard', loc: 'stash', scene: 'stash', frameId: 'l1w', sessionId: 's_l1', firstSeenTs: T0 + 5000 });
  var ownedWs = Array.from(owned);
  var _dn = Date.now; Date.now = function(){ return T0 + 50000; };
  try { window.vaultRemove(['Worldstone Shard (any)'], { lane: 'card-click', why: 'not mine' }); } finally { Date.now = _dn; }
  var back = LIVE({ name: 'Worldstone Shard', loc: 'stash', scene: 'stash', frameId: 'l1w', sessionId: 's_l1', firstSeenTs: T0 + 5000 });
  OUT.l1rm = { ownedAs: ownedWs, resolved: RESOLVE('Worldstone Shard'), replay: back.route, removedAfter: back.removedAfter || null, owned: Array.from(owned) };
  // the backfill keys a bare row through the same resolution: a removal of the (any) he owned skips the bare row
  reset({}, []);
  STORE['d2r_chronicleInboxLog'] = JSON.stringify([{ name: 'Worldstone Shard', status: 'in-chronicle', source: 'kai-register', sessionId: 's_bf',
    frameId: 'l1bf', firstSeenTs: T0 + 5000, loc: 'stash', scene: 'stash' }]);
  STORE['d2r_vaultRemoved'] = JSON.stringify([{ ts: T0 + 50000, names: ['Worldstone Shard (any)'], lane: 'card-click' }]);
  var bf = window._ownedProvBackfill();
  OUT.l1bf = { filed: (bf.receipt || {}).filed, skipped: (bf.receipt || {}).skipped, owned: Array.from(owned) };
});
// ══ L-2 — a time the read did not carry is not its time ══
section('l2', function(){
  reset({}, []);
  var pick = LIVE({ name: 'Stormshield', loc: 'inventory', scene: 'inventory', frameId: 'l2p', sessionId: 's_l2' });
  var r = row('Stormshield');
  var drop = LIVE({ name: 'Stormshield', loc: 'floor', scene: 'loot', frameId: 'l2d', sessionId: 's_l2', firstSeenTs: T0 + 200000 });
  OUT.l2 = { pick: pick.route, at: r.at, ts: r.ts, measured: r.tsMeasured, recordedAt: r.recordedAt || null, lookAt: (r.looks || []).map(function(k){ return k.at; }),
             drop: drop.route, why: drop.why, owned: owned.has('Stormshield'), ev: window._vaultEvidenceOf('Stormshield').when };
  // a later MEASURED look restores the order, and the drop after it leaves
  var look = LIVE({ name: 'Stormshield', loc: 'inventory', scene: 'inventory', frameId: 'l2q', sessionId: 's_l2b', firstSeenTs: T0 + 100000 });
  var lastAtAfterLook = row('Stormshield').lastAt || null;   // read BEFORE the drop takes the receipt away
  var drop2 = LIVE({ name: 'Stormshield', loc: 'floor', scene: 'loot', frameId: 'l2e', sessionId: 's_l2b', firstSeenTs: T0 + 200000 });
  OUT.l2later = { look: look.route, lastAt: lastAtAfterLook, drop: drop2.route, owned: owned.has('Stormshield') };
});
// ══ L-3 — the population line with the mule map unreadable ══
section('l3', function(){
  OUT.l3 = { unread: window._vaultPopHtml({ owned: 13, shared: 0, filed: null, carried: null, loose: null, sp: 0 }),
             known: window._vaultPopHtml({ owned: 13, shared: 0, filed: 2, carried: 1, loose: 10, sp: 1 }) };
});
// ══ L-4 — a bare name several known items share ══
section('l4', function(){
  OUT.l4 = { cm: window._vaultNameAmbiguity('Crescent Moon'), cmRw: window._vaultNameAmbiguity('Crescent Moon', { kind: 'runeword' }),
             cmUni: window._vaultNameAmbiguity('Crescent Moon', { kind: 'unique' }), amulet: window._vaultNameAmbiguity('Crescent Moon (amulet)'),
             spirit: window._vaultNameAmbiguity('Spirit'), spiritRw: window._vaultNameAmbiguity('Spirit', { kind: 'runeword' }),
             hell: window._vaultNameAmbiguity('Hellmouth'), hellUni: window._vaultNameAmbiguity('Hellmouth', { kind: 'unique' }),
             ws: window._vaultNameAmbiguity('Worldstone Shard'), aldur: window._vaultNameAmbiguity("Aldur's Watchtower"),
             gris: window._vaultNameAmbiguity("Griswold's Legacy"), hc: window._vaultNameAmbiguity('Harlequin Crest'),
             shako: window._vaultNameAmbiguity('Shako') };
  // the REAL register head on the two kind-less witness shapes the live doors hand it: the TV live read and the inbox accept
  reset({}, []);
  var tvW = { lane: 'stash', by: 'tv-live', sessions: [{ session: 's_l4', frame: 'f_' + (T0 + 5000) + '.jpg', conf: 0.9 }] };
  var handW = { by: 'hand', at: new Date(T0 + 5000).toISOString(), where: 'the Chronicle inbox (accept and vault)', lane: 'stash', scene: 'stash', reel: 's_l4', frame: 'f_l4' };
  OUT.l4reg = {};
  ['Spirit', 'Hellmouth', 'Worldstone Shard', "Aldur's Watchtower", 'Crescent Moon', 'Shako'].forEach(function(n){
    OUT.l4reg[n] = { tv: REG_HEAD(n, tvW), hand: REG_HEAD(n, handW) };
  });
  OUT.l4hold = { inbox: inbox(), records: RECORDS.filter(function(r){ return r && r.ask; }) };
  // the same refusal twice is ONE inbox row; the receipt of a same-kind pair says its base is UNKNOWN
  REG_HEAD('Crescent Moon', tvW);
  OUT.l4hold.inboxAfterTwice = inbox().length;
  var sp = window.tvVaultRegister('Spirit', tvW);
  OUT.l4hold.spiritReceipt = row('Spirit');
});
"""


def _drive():
    s = _src()
    extra = C.EXTRA % {"locks": P._between(s, C.LOCK_FROM, C.LOCK_TO), "main": P._between(s, C.MAIN_FROM, C.MAIN_TO)}
    assert s.count(TV_MS_LINE) == 1, "the TV frame-stamp line is not where this law cuts it (%d)" % s.count(TV_MS_LINE)
    head = P._between(s, P.REG_FROM, REG_HEAD_TO).split("\n")
    assert head[0].strip().startswith("window.tvVaultRegister = function") and head[1].strip() == "try {", head[:2]
    doors = DOORS_JS % {"vr": P._between(s, VR_FROM, VR_TO), "dock": P._between(s, DOCK_FROM, DOCK_TO), "clear": _door(s, DOOR_CLEAR), "menu": _door(s, DOOR_MENU),
                        "tvms": TV_MS_LINE, "tv": _door(s, DOOR_TV), "tv1": _door(s, DOOR_TV1), "hold": _door(s, DOOR_HOLD),
                        "reghead": "\n".join(head[2:])}
    head = "var T0 = %d;\n" % T
    prog = P.HARNESS % {"origin": P._origin_line(s), "lanes": P._lanes(s) + "\n" + R4._names_js(s) + "\n" + R4._resolver_js(s),
                        "furn": P._between(s, P.FURN_FROM, P.FURN_TO), "region": P.owned_prov_region(s),
                        "evidence": P._marked(s, P.EV_BEGIN, P.EV_END), "rec": P._between(s, P.REC_FROM, P.REC_TO),
                        "script": head + extra + doors + SCRIPT}
    return P._node(prog, "r5")


_CACHE = {}


def out():
    if "o" not in _CACHE:
        _CACHE["o"] = _drive()
    return _CACHE["o"]


def sec(k):
    """One driven section's result — or a failure naming what threw in it (UNKNOWN, never a pass)."""
    o = out()
    sk = {"m1owned": "m1", "m2base": "m2", "m3clear": "m3", "m3menu": "m3", "m3tv": "m3", "m3tvbare": "m3", "l1drop": "l1", "l1rm": "l1",
          "l1bf": "l1", "l2later": "l2", "l4reg": "l4", "l4hold": "l4"}.get(k, k)
    if sk in o.get("err", {}):
        raise AssertionError("the %s section threw on this board — UNKNOWN, not passing: %s" % (sk, o["err"][sk]))
    if k not in o:
        raise AssertionError("the %s section produced nothing — UNKNOWN, not passing" % k)
    return o[k]


@unittest.skipIf(NODE is None, "node is absent — the owned door was not driven (a declared skip, never a pass)")
class M1CarriedIsDecidedByOwned(unittest.TestCase):

    def test_a_pick_up_over_a_stale_receipt_is_carried_and_leaves_on_a_later_drop(self):
        o = sec("m1")
        self.assertEqual("carried", o["pick"], "a receipt that outlived its name stopped a real pick-up from being carried (M-1)")
        self.assertTrue(o["carried"])
        self.assertEqual("renewed", o["mode"], "the pick-up did not start a fresh receipt over the stale one")
        self.assertEqual(["ledger-restore"], o["past"], "the stale receipt was not kept as history")
        self.assertEqual("left", o["drop"], "the later real drop did not leave — the v2346 item stayed owned")
        self.assertFalse(o["owned"])
        self.assertEqual(["carried-left"], o["journal"])

    def test_a_name_he_owns_is_still_never_re_marked(self):
        o = sec("m1owned")
        self.assertFalse(o["carried"], "M-3: an owned item's receipt was re-marked carried by an inventory read")
        self.assertTrue(o["owned"], "a same-named floor label un-owned an item he owns")
        self.assertNotEqual("left", o["floor"])


@unittest.skipIf(NODE is None, "node is absent — the landing order was not driven")
class M2ALandingHasATimeOrder(unittest.TestCase):

    def test_an_older_stash_or_worn_replay_never_lands_newer_carried_loot(self):
        o = sec("m2")
        self.assertEqual("carried", o["pick"], "BASELINE: the pick-up must be carried")
        self.assertEqual("vault", o["oldStash"], "BASELINE: the older stash read must still route as a holding look")
        self.assertIs(True, o["afterStash"]["carried"], "an OLDER stash replay landed newer carried loot (M-2)")
        self.assertIsNone(o["afterStash"]["landed"])
        self.assertEqual(["m2s"], o["afterStash"]["past"], "the older look was not kept as history")
        self.assertIs(True, o["afterWorn"]["carried"], "an OLDER worn replay landed (and would have locked, §29) newer carried loot")
        self.assertEqual(["m2s", "m2w"], o["afterWorn"]["past"])
        self.assertEqual("carried", o["stateBeforeDrop"])
        self.assertEqual("left", o["drop"], "his later real drop no longer leaves — the item read as landed")
        self.assertFalse(o["owned"])
        self.assertEqual(["m2d"], o["proof"])

    def test_an_undated_holding_look_is_unknown_and_lands_nothing(self):
        o = sec("m2")["afterUndated"]
        self.assertIs(True, o["carried"], "a look with no time landed carried loot")
        self.assertEqual(["m2u"], o["unordered"], "the undated look was not said to be unorderable")
        self.assertNotIn("m2u", o["past"], "an undated look was ordered as if it were older")

    def test_the_last_look_never_moves_backwards(self):
        o = sec("m2")["afterStash"]
        self.assertTrue(str(o["lastAt"]).startswith(_iso(T + 100000)[:19]),
                        "an older replayed look moved 'last seen' backwards: %r (the pick-up was at %s)" % (o["lastAt"], _iso(T + 100000)))

    def test_baseline_a_newer_stash_look_still_lands(self):
        o = sec("m2base")
        self.assertIs(False, o["carried"])
        self.assertEqual("m2b2", o["landedFrame"])
        self.assertEqual("landed", o["state"])
        self.assertNotEqual("left", o["drop"], "H2: a landed item left on a floor label")
        self.assertTrue(o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the doors were not driven")
class M3EveryUnOwnIsJournaled(unittest.TestCase):

    def test_delete_unsorted_is_journaled_and_a_reclose_never_re_owns_it(self):
        o = sec("m3clear")
        self.assertTrue(o["ownedBefore"], "BASELINE: the stash read must own it first")
        self.assertFalse(o["ownedAfterClear"])
        self.assertEqual(["clear-unsorted"], o["lanes"], "'Delete unsorted' left no removal journal row (M-3)")
        self.assertEqual([["Nagelring"]], o["names"])
        self.assertEqual("not-held", o["replay"], "the reclose replayed the older read and owned what he deleted")
        self.assertEqual("clear-unsorted", (o["removedAfter"] or {}).get("lane"))
        self.assertFalse(o["ownedAfterReplay"])
        self.assertIsNone(o["provAfter"], "the receipt outlived the delete")

    def test_the_menu_page_import_is_journaled_and_a_reclose_never_re_owns_it(self):
        o = sec("m3menu")
        self.assertFalse(o["ownedAfter"])
        self.assertEqual(["menu-import"], o["lanes"], "'These look like a chronicle page' left no removal journal row (M-3)")
        self.assertEqual("not-held", o["replay"])
        self.assertEqual("menu-import", (o["removedAfter"] or {}).get("lane"))
        self.assertFalse(o["ownedAfterReplay"])

    def test_the_tv_unvault_is_journaled_and_a_newer_pick_up_is_his_again(self):
        o = sec("m3tv")
        self.assertTrue(o["ok"])
        self.assertFalse(o["ownedAfter"])
        self.assertEqual(["tv-unvault"], o["lanes"], "the TV unvault left no removal journal row (M-3)")
        self.assertEqual("not-held", o["replay"])
        self.assertFalse(o["ownedAfterReplay"])
        self.assertEqual(("vault", True), (o["again"], o["ownedAgain"]), "a read NEWER than the removal must own it again — a removal is not a ban")

    def test_the_tv_hands_one_batch_per_read_with_its_frame_as_proof(self):
        """R-5 (round-5 review, MED): two thrown names are ONE batch, its proof the read's frame and that frame's own stamp."""
        o = sec("m3tv")
        self.assertEqual([["Windforce", "Titan's Revenge"]], o["batchNames"], "the TV's thrown list was journaled one batch per name")
        self.assertEqual([{"frame": "f_%d.jpg" % (T + 60000), "at": T + 60000}], o["proof"], "the batch does not carry the frame that saw them thrown")
        self.assertEqual(T + 60000, (o["noted"] or {}).get("at"), "the per-name record was not written for the TV's word: %r" % o["noted"])
        self.assertEqual("f_%d.jpg" % (T + 60000), (o["removedAfter"] or {}).get("frame"))

    def test_a_tv_unvault_with_no_frame_un_owns_but_outranks_no_older_read(self):
        """R-5: a machine's claim with no proof frame is not his word — the name leaves owned (as before), the replay of an older
        read owns it again, and nothing is noted per name for it."""
        o = sec("m3tvbare")
        self.assertTrue(o["ok"])
        self.assertFalse(o["ownedAfter"], "the bare TV unvault no longer un-owns the name")
        self.assertEqual(["tv-unvault"], o["lanes"])
        self.assertEqual([None], o["proof"])
        self.assertIsNone(o["word"], "a 'tv-unvault' batch with no frame was taken as his word")
        self.assertEqual(("vault", True), (o["replay"], o["ownedAfterReplay"]), "a clock-stamped machine claim outranked the older read")
        self.assertIsNone(o["noted"])

    def test_the_unique_cards_un_tick_goes_through_the_removal_door(self):
        # raw source, bounded by the branch's own anchors: the needles are CALLS (a comment does not carry `([name], {`)
        s = _src()
        blk = P._between(s, UNTICK_FROM, UNTICK_TO)
        self.assertIn("window.vaultRemove([name], { lane: 'un-tick', quiet: true, keepFiling: true", blk,
                      "the unique card's un-tick takes the name out of owned beside the removal journal (M-3) and keeps the filing (R-5)")
        self.assertIn("window._ownedProvForget(name)", blk, "the un-tick's fallback leaves the receipt standing (M-1)")


@unittest.skipIf(NODE is None, "node is absent — the ring was not driven")
class R5TheRingForgetsHisWordDoesNot(unittest.TestCase):

    def test_a_removal_the_ring_evicted_still_blocks_the_older_read_and_the_backfill(self):
        o = sec("r5ring")
        self.assertEqual(T + 50000, (o["notedAfterClick"] or {}).get("at"), "the card-click removal was not noted per name: %r" % o["notedAfterClick"])
        self.assertEqual("card-click", (o["notedAfterClick"] or {}).get("lane"))
        self.assertEqual(20, o["ring"], "PREMISE: the ring holds 20 batches")
        self.assertFalse(o["clickInRing"], "PREMISE: 25 un-ticks evicted the card-click batch from the ring")
        self.assertEqual("not-held", o["replay"], "a removal the ring evicted no longer outranks the older read (R-5)")
        self.assertEqual("card-click", (o["removedAfter"] or {}).get("lane"))
        self.assertFalse(o["owned"])
        self.assertEqual([], o["bf"]["filed"], "the backfill re-filed a row of a name whose removal the ring evicted")
        self.assertEqual(1, (o["bf"]["skipped"] or {}).get("removed-by-him"), o["bf"])
        self.assertFalse(o["bf"]["owned"])
        self.assertEqual("vault", o["again"], "a NEWER pick-up must be his again")

    def test_an_unreadable_per_name_record_is_unknown_and_the_read_waits(self):
        o = sec("r5ring")
        self.assertEqual("wait", o["unread"]["route"], o["unread"])
        self.assertIn("UNKNOWN", o["unread"]["why"])

    def test_the_un_tick_keeps_the_mule_filing_and_a_plain_removal_takes_it(self):
        o = sec("r5keep")
        self.assertEqual([["Shako"], ["Windforce"]], o["removed"])
        self.assertFalse(o["ownedShako"], "the un-tick no longer takes the name out of owned")
        self.assertEqual("uni-armor", o["assignShako"], "the un-tick deleted the mule filing (his ruling: never)")
        self.assertEqual("uni-armor", o["storeAssign"].get("Shako"))
        self.assertEqual("uni-armor", (o["provShako"] or {}).get("mule"), "the un-tick dropped the filing's witness row")
        self.assertIsNone(o["assignWind"], "BASELINE: a plain removal still takes the filing")
        self.assertEqual([{"lane": "un-tick", "keepFiling": True, "filed": {}}, {"lane": "card-click", "keepFiling": False, "filed": {"Windforce": "uni-weap"}}],
                         o["batches"])

    def test_the_per_name_record_forks_like_the_ring(self):
        import test_the_removal_journal_forks_like_the_store as F
        lp = F._fork_set("_LP_FORKED")
        self.assertIn("d2r_vaultRemoved", lp, "PREMISE: the ring is in _LP_FORKED")
        self.assertIn("d2r_vaultRemovedAt", lp, "the per-name removal record does not fork with the ring and d2r_owned")


@unittest.skipIf(NODE is None, "node is absent — the resolution was not driven")
class L1TheNameTheRegisterOwns(unittest.TestCase):

    def test_a_drop_read_bare_leaves_the_suffixed_name_he_carries(self):
        o = sec("l1drop")
        self.assertEqual(["Harlequin Crest (Shako)"], o["ownedAs"], "PREMISE: the register owns the resolved name")
        self.assertEqual("left", o["drop"], "a drop read as 'Harlequin Crest' never left the '(Shako)' he carried (L-1)")
        self.assertEqual([], o["owned"])
        self.assertEqual([["Harlequin Crest (Shako)"]], o["proof"])

    def test_a_removal_of_the_owned_name_blocks_the_bare_read(self):
        o = sec("l1rm")
        self.assertEqual("Worldstone Shard (any)", o["resolved"], "PREMISE: the bare shard resolves to (any)")
        self.assertEqual(["Worldstone Shard (any)"], o["ownedAs"])
        self.assertEqual("not-held", o["replay"], "a removal of 'Worldstone Shard (any)' no longer blocked the bare read (L-1)")
        self.assertEqual("card-click", (o["removedAfter"] or {}).get("lane"))
        self.assertEqual([], o["owned"])

    def test_the_backfill_keys_a_bare_row_through_the_same_resolution(self):
        o = sec("l1bf")
        self.assertEqual([], o["filed"], "the backfill re-filed a bare row of a name he removed under its owned spelling")
        self.assertEqual(1, (o["skipped"] or {}).get("removed-by-him"), o["skipped"])
        self.assertEqual([], o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the receipt time was not driven")
class L2ATimeTheReadDidNotCarryIsNotItsTime(unittest.TestCase):

    def test_an_undated_pick_up_is_not_stamped_with_the_clock(self):
        o = sec("l2")
        self.assertEqual("carried", o["pick"])
        self.assertIsNone(o["at"], "the receipt was stamped with the wall clock as if the read had said when (L-2)")
        self.assertIsNone(o["ts"])
        self.assertIs(False, o["measured"])
        self.assertTrue(o["recordedAt"], "the moment of writing was not kept beside it, labelled")
        self.assertEqual([None], o["lookAt"])
        self.assertIn("UNKNOWN", o["ev"] or "", "the evidence card shows the write time as when it was seen")
        self.assertIn("recorded", o["ev"] or "")

    def test_a_later_drop_is_unknown_not_older(self):
        o = sec("l2")
        self.assertNotEqual("left", o["drop"])
        self.assertIn("UNKNOWN", o["why"], "the drop was ordered against a time the read never carried: %s" % o["why"])
        self.assertNotIn("OLDER", o["why"])
        self.assertTrue(o["owned"])

    def test_a_later_measured_look_restores_the_order_and_the_drop_leaves(self):
        o = sec("l2later")
        self.assertTrue(str(o["lastAt"]).startswith(_iso(T + 100000)[:19]), o["lastAt"])
        self.assertEqual("left", o["drop"], "with a measured look on the receipt the later drop must leave")
        self.assertFalse(o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the population line was not rendered")
class L3FiledIsUnknownWhenTheMapWillNotRead(unittest.TestCase):

    def test_the_line_says_unknown_for_filed_and_not_filed(self):
        o = sec("l3")
        self.assertIn("filed to mules <b>UNKNOWN</b>", o["unread"])
        self.assertIn("not filed <b>UNKNOWN</b>", o["unread"])
        self.assertNotIn("<b>0</b> filed", o["unread"], "the line counted 0 filed off a map that would not read (L-3)")
        self.assertNotIn("still loose", o["unread"])
        self.assertIn("<b>2</b> filed to mules", o["known"], "BASELINE: a readable map is still counted")

    def test_render_vault_and_the_sorter_read_the_unreadable_map(self):
        # raw source: the needles below are code shapes (a key: value pair, a call) that no comment carries [[source-reading-guard]]
        s = _src()
        i = s.find("    var _carUnknown = (_carried === null);")
        j = s.find("dock.innerHTML = unsorted.map(", i)
        self.assertGreater(j, i, "renderVault's anchors moved — re-point this law rather than leaving it green")
        code = s[i:j]
        self.assertIn("filed: _asgUnread ? null : _filed", code, "the population line is not told the map would not read")
        self.assertIn("window._muleStoreUnread(AK)", code)
        sort = P._between(s, SORT_FROM, "\n    var n=0, suggested=0, suggestedRows=[];")
        self.assertIn("window._muleStoreUnread(AK)", sort, "Auto-Sort sorts over a mule map that would not read")
        self.assertIn("refused: 'mule-map-unreadable'", sort)


@unittest.skipIf(NODE is None, "node is absent — the ambiguity was not driven")
class L4ABareNameSeveralItemsShareIsNotAMatch(unittest.TestCase):

    def test_crescent_moon_is_ambiguous_and_settled_only_by_its_kind(self):
        o = sec("l4")
        self.assertIsNotNone(o["cm"], "a bare 'Crescent Moon' resolved silently to one of two known items (L-4)")
        self.assertEqual(["crescent moon", "crescent moon (amulet)"], o["cm"]["among"])
        self.assertIsNone(o["cm"]["settled"])
        self.assertIn("ambiguity is not a match", o["cm"]["why"])
        self.assertEqual("Crescent Moon", (o["cmRw"] or {}).get("settled"), "the read's kind (runeword) did not settle it")
        self.assertEqual("Crescent Moon (amulet)", (o["cmUni"] or {}).get("settled"), "the read's kind (unique) did not settle it")
        self.assertIsNone(o["amulet"], "a suffixed name names itself")
        self.assertIsNone(o["hc"], "Harlequin Crest has one known item under its stem")
        self.assertIsNone(o["shako"])

    def test_a_same_kind_pair_is_one_item_with_its_base_unknown_and_a_spelling_is_not_ambiguous(self):
        """Round-5 review (HIGH, reproduced): a bare 'Spirit' (two runewords of one name) is ONE registrable item whose base is
        UNKNOWN — settled to 'Spirit', never refused under every kind; a bare 'Hellmouth' is the one unique the tables spell two
        ways — not ambiguous at all."""
        o = sec("l4")
        sp = o["spirit"] or {}
        self.assertEqual(["spirit (shield)", "spirit (sword)"], sp.get("among"), "the two runewords are not the candidates")
        self.assertEqual("Spirit", sp.get("settled"), "a bare 'Spirit' was refused instead of filed with its base UNKNOWN (round-5 HIGH)")
        self.assertIs(True, sp.get("baseUnknown"))
        self.assertIn("UNKNOWN", sp.get("why") or "")
        self.assertEqual("Spirit", (o["spiritRw"] or {}).get("settled"), "the kind tap (runeword) refused it too")
        self.assertIsNone(o["hell"], "a bare 'Hellmouth' (one unique, two spellings) was refused as ambiguous: %r" % o["hell"])
        self.assertIsNone(o["hellUni"])

    def test_the_any_bucket_is_the_kind_unknown_answer(self):
        """A bare Worldstone Shard / Aldur's Watchtower / Griswold's Legacy is the '(any)' bucket the resolver already gives (the
        L-1 premise), never a refusal on the kind-less doors."""
        o = sec("l4")
        self.assertEqual("Worldstone Shard (any)", (o["ws"] or {}).get("settled"), "a bare Worldstone Shard was refused with no kind: %r" % o["ws"])
        self.assertEqual("any", (o["ws"] or {}).get("bucket"))
        self.assertEqual("Aldur's Watchtower (any)", (o["aldur"] or {}).get("settled"), o["aldur"])
        self.assertEqual("Griswold's Legacy (any)", (o["gris"] or {}).get("settled"), o["gris"])

    def test_the_real_register_head_on_the_kind_less_doors_files_the_names_and_refuses_only_crescent_moon(self):
        """The REAL register's head (its ambiguity gate + resolution, cut whole) on the TV live witness and the hand witness —
        the two doors that pass no kind. Only a bare name whose siblings are DIFFERENT kinds is refused, and that refusal is
        an ASK: held in the Chronicle inbox naming the candidates, once per name."""
        o = sec("l4reg")
        for door in ("tv", "hand"):
            self.assertEqual("Spirit", o["Spirit"][door].get("name"), "%s door: %r" % (door, o["Spirit"][door]))
            self.assertIs(True, (o["Spirit"][door].get("amb") or {}).get("baseUnknown"))
            self.assertEqual("Hellmouth", o["Hellmouth"][door].get("name"), "%s door: %r" % (door, o["Hellmouth"][door]))
            self.assertIsNone(o["Hellmouth"][door].get("amb"))
            self.assertEqual("Worldstone Shard (any)", o["Worldstone Shard"][door].get("name"), "%s door: %r" % (door, o["Worldstone Shard"][door]))
            self.assertEqual("Aldur's Watchtower (any)", o["Aldur's Watchtower"][door].get("name"), "%s door: %r" % (door, o["Aldur's Watchtower"][door]))
            self.assertEqual("Shako", o["Shako"][door].get("name"))
            cm = o["Crescent Moon"][door]
            self.assertEqual("ambiguous", cm.get("refused"), "%s door: a bare Crescent Moon (runeword vs amulet) was filed as one of them: %r" % (door, cm))
            self.assertEqual("inbox", cm.get("held"), "%s door: the refusal was not surfaced as an inbox hold: %r" % (door, cm))
        h = sec("l4hold")
        names = [x.get("name") for x in h["inbox"]]
        self.assertEqual(["Crescent Moon"], names, "the ask did not reach the Chronicle inbox once: %r" % h["inbox"])
        self.assertEqual(["crescent moon", "crescent moon (amulet)"], h["inbox"][0].get("candidates"))
        self.assertIn("which item?", h["inbox"][0].get("triageWhy") or "")
        self.assertEqual("tv-live", h["inbox"][0].get("source"))
        self.assertEqual(1, h["inboxAfterTwice"], "the same refusal twice made two inbox rows")
        self.assertTrue(any(r.get("name") == "Crescent Moon" and r.get("ask") == "which" for r in h["records"]), h["records"])
        self.assertIn("UNKNOWN", (h["spiritReceipt"] or {}).get("baseUnknown") or "", "the Spirit receipt does not say its base is UNKNOWN: %r" % h["spiritReceipt"])

    def test_the_register_and_the_ai_checker_ask_the_same_rule(self):
        # raw source, bounded by the register's own head: the needles are calls and a returned literal [[source-reading-guard]]
        s = _src()
        reg = P._between(s, "  window.tvVaultRegister = function(name, witness){\n", "      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(name);")
        self.assertIn("window._vaultNameAmbiguity(name, { kind:", reg, "the register does not ask the ambiguity rule")
        self.assertIn("refused:'ambiguous'", reg)
        self.assertIn("window._vaultHoldAmbiguous(name, _ambV, witness)", reg, "the refusal is not held in the inbox (round-5 HIGH)")
        self.assertIn("name = window._vaultResolveName(name);", reg, "the register no longer resolves through the ONE published slice")
        i = s.index(GRAIL_FROM)
        j = s.index("\n  function ", i + len(GRAIL_FROM))
        self.assertIn("if (_ambG && !_ambG.settled) return null;", s[i:j], "_aicIsGrailName still resolves a bare ambiguous name to the codex's item")
        # the harness stub every owned-door law drives carries the register's REAL gate (the reviewer's L-1 vs L-4 contradiction)
        self.assertIn("window._vaultNameAmbiguity(name, { kind:", P.amb_gate(s))
        self.assertIn("__AMB_GATE__", P.HARNESS)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {"why": "M-1: a receipt that outlived its name stops a real pick-up from being carried again (the round-4 line)",
     "file": "bible.html",
     "find": "    if (fresh.carried === true && owned.has(nm)) fresh.carried = null;\n",
     "replace": "    if (fresh.carried === true && (cur || owned.has(nm))) fresh.carried = null;\n",
     "matches": 1},
    {"why": "M-1: the pick-up merges into the stale receipt instead of starting a fresh carried one",
     "file": "bible.html",
     "find": "      if (fresh.carried === true && !owned.has(nm)){\n",
     "replace": "      if (false){\n",
     "matches": 1},
    {"why": "M-2: an older holding look lands newer carried loot again",
     "file": "bible.html",
     "find": "        } else if (landT <= ownT0){\n",
     "replace": "        } else if (false){\n",
     "matches": 1},
    {"why": "M-2: an undated holding look is ordered as if it had a time (null reads as 0)",
     "file": "bible.html",
     "find": "        if (landT == null || ownT0 == null){\n",
     "replace": "        if (false){\n",
     "matches": 1},
    {"why": "M-3: 'Delete unsorted' takes the names out beside the removal journal again",
     "file": "bible.html",
     "find": "    try { window.vaultRemove(unsorted, { lane: 'clear-unsorted', quiet: true, why: 'Delete unsorted — the dock button' }); } catch(e){}\n",
     "replace": "    unsorted.forEach(function(name){ try{ owned.delete(name); }catch(e){} delete assign[name]; });\n    try { _provDrop(unsorted); } catch(e){}\n",
     "matches": 1},
    {"why": "M-3: the menu-page import takes the names out beside the removal journal again",
     "file": "bible.html",
     "find": "    try { var vrM = window.vaultRemove(takeM, { lane: 'menu-import', quiet: true, why: 'These look like a chronicle page — taken out of owned' });\n",
     "replace": "    try { var vrM = { removed: takeM }; takeM.forEach(function(name){ owned.delete(name); });\n",
     "matches": 1},
    {"why": "M-3: the TV unvault takes the names out beside the removal journal again",
     "file": "bible.html",
     "find": "    if (held.length){ try { batch = window.vaultRemove(held, { lane: 'tv-unvault', quiet: true, why: 'the TV saw it thrown', proof: pf }); } catch(e){ batch = null; } }\n",
     "replace": "",
     "matches": 1},
    {"why": "R-5: the TV's batch drops the frame that saw the items thrown, so a machine claim with no proof blocks nothing (and the ring evicts it)",
     "file": "bible.html",
     "find": "    if (held.length){ try { batch = window.vaultRemove(held, { lane: 'tv-unvault', quiet: true, why: 'the TV saw it thrown', proof: pf }); } catch(e){ batch = null; } }\n",
     "replace": "    if (held.length){ try { batch = window.vaultRemove(held, { lane: 'tv-unvault', quiet: true, why: 'the TV saw it thrown', proof: null }); } catch(e){ batch = null; } }\n",
     "matches": 1},
    {"why": "R-5: a 'tv-unvault' batch with no frame is taken as his word again, so a clock-stamped machine claim outranks his older reads",
     "file": "bible.html",
     "find": "    if (lane === 'tv-unvault' && !frame) return null;\n",
     "replace": "",
     "matches": 1},
    {"why": "R-5: the removal door stops writing the per-name record, so a removal the ring evicts is forgotten",
     "file": "bible.html",
     "find": "      try { if (typeof window._vaultRemovalNote === 'function') batch.noted = window._vaultRemovalNote(batch); } catch(e){}\n",
     "replace": "",
     "matches": 1},
    {"why": "R-5: the journal reader ignores the per-name record, so only the 20-deep ring is his word",
     "file": "bible.html",
     "find": "      var r = noted[k]; if (!r || typeof r !== 'object') return;\n",
     "replace": "      return;\n",
     "matches": 1},
    {"why": "R-5: an unreadable per-name record reads as empty instead of UNKNOWN",
     "file": "bible.html",
     "find": "    if (!noted || typeof noted !== 'object' || Array.isArray(noted)) return { unknown: 'the per-name removal record would not read — whether you removed it after this read is UNKNOWN' };\n",
     "replace": "    if (!noted || typeof noted !== 'object' || Array.isArray(noted)) noted = {};\n",
     "matches": 1},
    {"why": "R-5: the backfill ignores the per-name record, so a row of a name whose removal the ring evicted is re-filed",
     "file": "bible.html",
     "find": "      if (k) _rmAt[k] = Math.max(_rmAt[k] || 0, t || 1); });\n",
     "replace": "      if (false) _rmAt[k] = Math.max(_rmAt[k] || 0, t || 1); });\n",
     "matches": 1},
    {"why": "R-5 (LOW): the removal door deletes the mule filing on every lane again, the un-tick included",
     "file": "bible.html",
     "find": "      if (!opts.keepFiling) delete assign[nm];\n",
     "replace": "      delete assign[nm];\n",
     "matches": 1},
    {"why": "R-5 (LOW): the per-name record is dropped from _LP_FORKED, so ladder and main share his removals",
     "file": "bible.html",
     "find": "  'd2r_vaultRemovedAt',\n",
     "replace": "",
     "matches": 1},
    {"why": "M-3: the unique card's un-tick no longer goes through the removal door",
     "file": "bible.html",
     "find": "          try { if (typeof window.vaultRemove === 'function') _vrUT = window.vaultRemove([name], { lane: 'un-tick', quiet: true, keepFiling: true, why: 'un-ticked on its item card' }); } catch(e){ _vrUT = null; }\n",
     "replace": "",
     "matches": 1},
    {"why": "L-1: a removal is matched on the read's name only, so a removal of the owned (any) no longer blocks the bare read",
     "file": "bible.html",
     "find": "    var keys = {}, k0 = _cnV(name), k1 = _cnV(_regName(name));\n",
     "replace": "    var keys = {}, k0 = _cnV(name), k1 = k0;\n",
     "matches": 1},
    {"why": "L-1: a drop read bare never leaves the suffixed name he carries",
     "file": "bible.html",
     "find": "    if (!owned.has(nm)){ var rnm = _regName(nm); if (rnm === nm || !owned.has(rnm)) return null; nm = rnm; }\n",
     "replace": "    if (!owned.has(nm)) return null;\n",
     "matches": 1},
    {"why": "L-1: the backfill keys removals and owned names on the raw fold again",
     "file": "bible.html",
     "find": "    var _cf = function(n){ return window._vaultCanonName(_regName(n)); };\n",
     "replace": "    var _cf = window._vaultCanonName;\n",
     "matches": 1},
    {"why": "L-2: an undated read is stamped with the wall clock as its time again",
     "file": "bible.html",
     "find": "    var fresh = _receipt(rec, tsM || Date.now(), tsM != null);\n",
     "replace": "    var fresh = _receipt(rec, tsM || Date.now(), true);\n",
     "matches": 1},
    {"why": "L-3: the population line counts 0 filed off a map that would not read",
     "file": "bible.html",
     "find": "    if (p.filed === null){\n",
     "replace": "    if (false){\n",
     "matches": 1},
    {"why": "L-3: renderVault hands the line a count instead of UNKNOWN",
     "file": "bible.html",
     "find": "filed: _asgUnread ? null : _filed",
     "replace": "filed: _filed",
     "matches": 1},
    {"why": "L-4: a bare name several known items share is never called ambiguous",
     "file": "bible.html",
     "find": "    if (st !== f) return null;\n    var sib = K.stems[st];\n    if (!sib || Object.keys(sib).length < 2) return null;\n",
     "replace": "    return null;\n    var sib = K.stems[st];\n    if (!sib || Object.keys(sib).length < 2) return null;\n",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): a spelling variant of ONE unique (Hellmouth / Hellmouth (gloves)) is refused as two items again",
     "file": "bible.html",
     "find": "    if (oneKind && sib[f]) return null;\n",
     "replace": "    if (false && oneKind && sib[f]) return null;\n",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): a same-kind pair (Spirit) is refused under every kind again instead of filed with its base UNKNOWN",
     "file": "bible.html",
     "find": "    if (oneKind) return { name: said, among: among, settled: said, kind: oneKind, baseUnknown: true,\n",
     "replace": "    if (false) return { name: said, among: among, settled: said, kind: oneKind, baseUnknown: true,\n",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): the '(any)' bucket no longer settles a bare shard / set name on the kind-less doors",
     "file": "bible.html",
     "find": "    if (anyB.length === 1) return { name: said, among: among, settled: K.names[anyB[0]] || anyB[0], bucket: 'any',\n",
     "replace": "    if (false) return { name: said, among: among, settled: K.names[anyB[0]] || anyB[0], bucket: 'any',\n",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): the register refuses silently again — the ask never reaches the Chronicle inbox",
     "file": "bible.html",
     "find": "        try { if (typeof window._vaultHoldAmbiguous === 'function') _heldV = window._vaultHoldAmbiguous(name, _ambV, witness); } catch(eH){ _heldV = null; }\n",
     "replace": "",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): the same refusal makes a new inbox row every time",
     "file": "bible.html",
     "find": "      if (!has){ ib.push(row);",
     "replace": "      if (true){ ib.push(row);",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): the receipt of a same-kind pair no longer says its base is UNKNOWN",
     "file": "bible.html",
     "find": "                   baseUnknown: (_ambV && _ambV.baseUnknown) ? String(_ambV.why) : null };\n",
     "replace": "                   baseUnknown: null };\n",
     "matches": 1},
    {"why": "L-4 (round-5 HIGH): the AI checker reads a SETTLED answer (Spirit, the (any) bucket) as UNKNOWN again",
     "file": "bible.html",
     "find": "          if (_ambG && !_ambG.settled) return null; } catch(eA){}\n",
     "replace": "          if (_ambG) return null; } catch(eA){}\n",
     "matches": 1},
]
