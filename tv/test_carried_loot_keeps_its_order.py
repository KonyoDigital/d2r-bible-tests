# -*- coding: utf-8 -*-
"""CARRIED LOOT KEEPS ITS ORDER — the review of bd976210 (round 3 of the vault evidence route), every finding driven.

His rulings, recorded in HANDOFF_GROK.md:
  §31.2  carried loot is OWNED right away, shown on a carried strip, NOT locked. It LANDS when seen in a stash or on a
         mule. It LEAVES only on a drop (vendor / trade: a signal the reader cannot send yet). ABSENCE NEVER UN-OWNS IT.
  §29    worn gear and grid standing kit are pinned and LOCKED to the character until his manual unlock.
  v2346  "picked it up, identified it ... thrown back out to the ground" must NOT own it.
  #166   a manual tally is witness enough and is monotonic.

WHAT THIS LAW HOLDS, one class per finding (each reproduced on bd976210 by an adversarial reviewer first):
  H1  THE SEED CLEANSE — the board's own load path (the grail floor's slice, cut by anchors both trees carry) booted
      twice over a store holding a carried found unique: it stays owned and on the strip, worn / landed / hand / filed /
      shared-stash names stay, only true residue goes — once per world — and every removal is in the removal journal.
      An unanswered MAIN ledger on the owner console removes nothing.
  H2  CARRIED IS A STATE WITH AN ORDER — stash -> an inventory read -> a floor label: still owned, still filed.
      Worn (and lane-locked) -> an inventory read -> a floor label of the same name: still owned, still locked.
  H3  TIME ORDER — the SHIPPED register compiles his v2346 shape (inventory at t1, the ground at t2) and the board does
      not own it; the reverse order is carried; an item already owned as carried LEAVES with the drop's own frame.
  M1  THE PER-NAME PLACE DECIDES — inventory inside a 'loot' frame is carried, and the register agrees with the board on
      every (place, scene) pair about what holds and what leaves.
  M2  THE BACKFILL READS THE SAME ORDER — the measured pick-up-look-drop shapes (Storm Emblem, Cloudy Sphere, a Small
      Charm of Good Luck, five set pieces) are not filed; the reverse order still is; one function, not a copy.
  M3  ONE ITEM, EVERY SPELLING — a removal of a straight-apostrophe / other-case name keeps the curly / other spelling
      out, and an owned name gets its receipt under the spelling it is owned by.
  M4  NOTHING NAMES THE CHARACTER — a production-shaped propose (the shipped register, the console's builder: no
      character) renders ONE carried row that says so in words; a named character still gets its own.
  L2  NO FALSE PROMISE — every carried surface says it leaves on a drop and that vendor / trade reads are not supported.
  L4  THE NAME AND ITS TIME READ WHOLE — no carried-chip rule ellipsises or refuses to wrap them.
Driven in node on the board's own code (cut by markers and anchors, never re-typed). RED_PROOF below.
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

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")

LOCK_FROM, LOCK_TO = "var _LANE_LOCK_KEY = 'd2r_laneLock';", "/* THE FURNITURE LAW"
MAIN_FROM, MAIN_TO = "window.MAIN_LOCKS = null;", "window._mainLocksRefresh = function(){"
SLICE_FROM = "      // one-time vault cleanse: the v659-v676 floors put ledger names INTO owned"
SLICE_TO = "      // v682 — SET-PIECE floor:"


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _shared_keep(s):
    m = re.search(r"var _SHARED_KEEP = (/.+?/i);", s)
    assert m, "the shipped _SHARED_KEEP regex is gone"
    return m.group(1)


EXTRA = r"""
%(locks)s
%(main)s
var LIVE = function(o){ return window._liveReadRoute(Object.assign({ source: 'kai-register' }, o)); };
function assignOf(n){ return (JSON.parse(STORE['d2r_muleAssign'] || '{}'))[n] || null; }
"""

SCRIPT = r"""
// each section runs on its own: a board missing one door fails ITS case, never every case (a harness that dies on the
// first absent function measures nothing about the rest)
OUT.err = {};
function section(k, f){ try { f(); } catch (e) { OUT.err[k] = String(e && e.stack || e).slice(0, 400); } }
function stateOf(n){ return (typeof window._ownedState === 'function') ? window._ownedState(n).state : 'this board has no _ownedState'; }
// ══ H2 — stash -> an inventory read -> a floor label: still owned, still filed ══
section('h2stash', function(){
  reset({}, []);
  FILES['Shako'] = 'uni-armor';
  LIVE({ name: 'Shako', loc: 'stash', scene: 'stash', frameId: 'h2_1', sessionId: 's_h2', firstSeenTs: 1790600000000 });
  var h2a = { filedAfterStash: assignOf('Shako'), carriedAfterStash: prov()['Shako'] && prov()['Shako'].carried };
  LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'h2_2', sessionId: 's_h2', firstSeenTs: 1790600100000 });
  h2a.carriedAfterInv = prov()['Shako'] && prov()['Shako'].carried;
  var h2aFloor = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'h2_3', sessionId: 's_h2', firstSeenTs: 1790600200000 });
  h2a.floor = { route: h2aFloor.route, why: h2aFloor.why, left: h2aFloor.left || null };
  h2a.owned = owned.has('Shako'); h2a.filed = assignOf('Shako');
  h2a.removed = REMOVED.filter(function(b){ return b.names.indexOf('Shako') >= 0; }).length;
  // the same, unfiled: a stash RECEIPT (landed by place) is never re-marked carried either
  LIVE({ name: 'Nagelring', loc: 'stash', scene: 'stash', frameId: 'h2_4', sessionId: 's_h2', firstSeenTs: 1790600300000 });
  LIVE({ name: 'Nagelring', loc: 'inventory', frameId: 'h2_5', sessionId: 's_h2', firstSeenTs: 1790600400000 });
  LIVE({ name: 'Nagelring', loc: 'floor', frameId: 'h2_6', sessionId: 's_h2', firstSeenTs: 1790600500000 });
  h2a.nagel = { owned: owned.has('Nagelring'), carried: prov()['Nagelring'] && prov()['Nagelring'].carried, state: stateOf('Nagelring') };
  OUT.h2stash = h2a;
});
// ══ H2 — worn (and lane-locked, §29) -> an inventory read -> a floor label of the same name ══
section('h2worn', function(){
  reset({}, []);
  STORE['d2r_laneLock'] = JSON.stringify({ 'Arachnid Mesh': { lane: 'equipment', sessions: ['s_a', 's_b', 's_c'] } });
  LIVE({ name: 'Arachnid Mesh', loc: 'equipped', scene: 'inventory', frameId: 'w_1', sessionId: 's_w', firstSeenTs: 1790610000000 });
  LIVE({ name: 'Arachnid Mesh', loc: 'inventory', frameId: 'w_2', sessionId: 's_w', firstSeenTs: 1790610100000 });
  var wFloor = LIVE({ name: 'Arachnid Mesh', loc: 'floor', frameId: 'w_3', sessionId: 's_w', firstSeenTs: 1790610200000 });
  // worn by its receipt alone (no lane lock at all)
  LIVE({ name: 'String of Ears', loc: 'equipped', frameId: 'w_4', sessionId: 's_w', firstSeenTs: 1790610300000 });
  LIVE({ name: 'String of Ears', loc: 'inventory', frameId: 'w_5', sessionId: 's_w', firstSeenTs: 1790610400000 });
  var wFloor2 = LIVE({ name: 'String of Ears', loc: 'floor', frameId: 'w_6', sessionId: 's_w', firstSeenTs: 1790610500000 });
  // his own tick (a manual tally is monotonic)
  window._ownedAdd('Magefist', { source: 'hand', by: 'toggleOwned', where: 'the item card tick' });
  LIVE({ name: 'Magefist', loc: 'inventory', frameId: 'w_7', sessionId: 's_w', firstSeenTs: 1790610600000 });
  var hFloor = LIVE({ name: 'Magefist', loc: 'floor', frameId: 'w_8', sessionId: 's_w', firstSeenTs: 1790610700000 });
  OUT.h2worn = { owned: Array.from(owned).sort(), mesh: prov()['Arachnid Mesh'] || {}, lock: window._laneLockWhy('Arachnid Mesh'),
                 meshState: stateOf('Arachnid Mesh'), soeState: stateOf('String of Ears'), handState: stateOf('Magefist'),
                 wFloor: wFloor.left || null, wFloor2: wFloor2.left || null, hFloor: hFloor.left || null, removed: REMOVED.length,
                 strip: (window._carriedNames(function(){ return false; }) || []).map(function(c){ return c.name; }) };
});
// BASELINE — a carried item DOES still leave on a real drop (the guard above is not a leave that never fires)
section('baselineLeave', function(){
  reset({}, []);
  LIVE({ name: 'Shako', loc: 'inventory', frameId: 'b_1', sessionId: 's_b', firstSeenTs: 1790620000000 });
  var bl = LIVE({ name: 'Shako', loc: 'floor', frameId: 'b_2', sessionId: 's_b', firstSeenTs: 1790620100000 });
  OUT.baselineLeave = { route: bl.route, owned: owned.has('Shako'), batches: REMOVED.map(function(b){ return b.lane + ':' + (b.proof && b.proof.frame); }) };
});
// ══ H3 — the SHIPPED register's items, routed by the board ══
section('h3', function(){
  reset({}, []);
  OUT.h3 = REGISTER_ITEMS.map(function(it){ var r = LIVE(it); return { name: it.name, route: r.route, why: r.why, frame: r.frame,
    dropped: r.dropped || null, owned: owned.has(it.name), carried: !!(prov()[it.name] && prov()[it.name].carried) }; });
});
// already owned as carried (an earlier compile of the same session saw only the pick-up) -> it leaves with the DROP's frame
section('h3leave', function(){
  reset({}, []);
  var pick = REGISTER_ITEMS.filter(function(it){ return it.name === 'Harlequin Crest'; })[0];
  LIVE(Object.assign({}, pick, { latestLoc: null, latestScene: null, latestFrame: null, latestTs: null }));
  var ownedBefore = owned.has('Harlequin Crest');
  var lv = LIVE(pick);
  OUT.h3leave = { ownedBefore: ownedBefore, route: lv.route, owned: owned.has('Harlequin Crest'),
                  proof: REMOVED.filter(function(b){ return b.lane === 'carried-left'; }).map(function(b){ return b.proof && b.proof.frame; }) };
});
// an unordered pair waits (a sighting with no time cannot be put in order)
section('h3wait', function(){
  OUT.h3wait = window._sightingsRoute([{ loc: 'inventory', frame: 'u_1', ts: 1790630000000, tag: 'held', held: true },
                                       { loc: 'floor', frame: 'u_2', ts: null, tag: 'latest' }], 'Shako').route;
});
// ══ M1 — the per-name place decides ══
section('m1', function(){
  OUT.m1 = [['inventory', 'loot', 'Shako'], ['stash', 'loot', null], [null, 'loot', null], ['equipped', 'loot', null],
            ['floor', 'inventory', null], ['inventory', 'vendor', 'Shako'], [null, 'vendor', null], ['floor', null, null],
            ['inventory', 'inventory', 'Shako'], ['stash', 'stash', null], [null, 'inventory', null], ['stash', 'chronicle', null],
            [null, 'chronicle', null], ['inventory', 'chronicle', 'Shako'], ['vendor', null, null], [null, null, null]]
    .map(function(p){ var v = window._vaultHoldingRoute(p[0], p[1], p[2]); return [p[0], p[1], p[2], v.route, !!v.leave]; });
  reset({}, []);
  var m1live = LIVE({ name: 'Shako', loc: 'inventory', scene: 'loot', frameId: 'm1_1', sessionId: 's_m1', firstSeenTs: 1790640000000 });
  OUT.m1live = { route: m1live.route, owned: owned.has('Shako') };
});
// ══ M2 + M3 — the backfill ══
section('backfill', function(){
  reset({}, ['Arachnid Mesh']);
  STORE['d2r_chronicleInboxLog'] = JSON.stringify(BACKFILL_LOG);
  STORE['d2r_vaultRemoved'] = JSON.stringify([{ ts: 1790700000000, names: ["Tal Rasha's Horadric Crest"] },
                                              { ts: 1790700000001, names: ['harlequin crest'] }]);
  var bf = window._ownedProvBackfill();
  OUT.backfill = { r: bf, owned: Array.from(owned).sort(), prov: prov() };
});
// ══ M4 + L2 — a production-shaped propose renders ONE row that says who is UNKNOWN; no carried surface over-promises ══
section('l2', function(){
  reset({}, []);
  PROD_ITEMS.forEach(function(it){ LIVE(it); });
  OUT.l2 = { rule: window.CARRIED_RULE || 'this board has no CARRIED_RULE', ev: window._vaultEvidenceOf(PROD_ITEMS[0].name).seen,
             routeWhy: window._vaultHoldingRoute('inventory', null, 'Shako').why };
});
section('m4', function(){
  reset({}, []);
  PROD_ITEMS.forEach(function(it){ LIVE(it); });
  var carried = window._carriedNames(function(){ return false; });
  OUT.m4 = { names: carried.map(function(c){ return c.name + '|' + c.character; }), html: window._carriedStripHtml(carried),
             unknown: window.CARRIED_WHO_UNKNOWN };
  window._ownedAdd('Windforce', { source: 'kai-register', loc: 'inventory', frameId: 'n_1', carried: true, character: 'KonyoSorc' });
  OUT.m4named = window._carriedStripHtml(window._carriedNames(function(){ return false; }));
});
"""

#: H1 — the grail floor's cleanse slice, booted as a page load, twice
BOOT = r"""
var window = globalThis, STORE = {}, REMOVED = [], LOGS = [];
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
               setItem: function(k, v){ STORE[k] = String(v); }, removeItem: function(k){ delete STORE[k]; } };
window.D2R_BUILD = { id: 'vTEST' }; window.D2R_PROFILE = 'main';
console.info = function(){ LOGS.push(Array.prototype.join.call(arguments, ' ')); };
var owned = new Set();
var LS = window.LSR;
function _safeJsonParse(s, d){ try { var v = JSON.parse(s); return v == null ? d : v; } catch (e) { return d; } }
window._grailStamp = function(){ return 'STAMP'; };
%(lanes)s
%(furn)s
%(region)s
%(locks)s
%(main)s
window.vaultRemove = function(names, opts){
  var p = JSON.parse(STORE['d2r_vaultProv'] || '{}'), a = JSON.parse(STORE['d2r_muleAssign'] || '{}'), took = [];
  names.forEach(function(n){ if (!owned.has(n)) return; owned['delete'](n); delete p[n]; delete a[n]; took.push(n); });
  STORE['d2r_vaultProv'] = JSON.stringify(p); STORE['d2r_muleAssign'] = JSON.stringify(a);
  if (took.length){ var lg = JSON.parse(STORE['d2r_vaultRemoved'] || '[]');
    lg.push({ ts: Date.now(), names: took, lane: opts && opts.lane, why: opts && opts.why }); STORE['d2r_vaultRemoved'] = JSON.stringify(lg); }
  REMOVED.push({ names: names.slice(), lane: opts && opts.lane });
  return { removed: took, ts: took.length ? Date.now() : null };
};
var _GRAIL_SEED = { 'Harlequin Crest': 'Jul 2', 'Crown of Ages': 'Jul 3', 'Bone Break': 'Jul 1', 'Arachnid Mesh': 'Jul 4',
                    'Stormshield': 'Jul 5', 'Nagelring': 'Jul 6', 'Magefist': 'Jul 7', 'Wisp Projector': 'Jul 8' };
var _UNI_EXTRA = { "Gheed's Wager": 1 };
var _SHARED_KEEP = %(keep)s;
var _realST = setTimeout, LOADS = [], TIMERS = [];
window.document = { readyState: 'loading' };
window.addEventListener = function(ev, fn){ if (ev === 'load') LOADS.push(fn); };
globalThis.setTimeout = function(fn){ TIMERS.push(fn); return 0; };
window._mainLocksReachable = function(){ return !!window.__CONSOLE; };
window._mainLocksRefresh = function(){ return Promise.resolve(false); };
async function boot(){
  owned = new Set(JSON.parse(STORE['d2r_owned'] || '[]'));
  var _gfl = JSON.parse(STORE['d2r_foundLog'] || '{}'), _gch = false, _gflCh = false;
  LOADS = []; TIMERS = [];
%(slice)s
  if (_gch) STORE['d2r_owned'] = JSON.stringify(Array.from(owned));
  if (_gflCh) STORE['d2r_foundLog'] = JSON.stringify(_gfl);
  LOADS.forEach(function(f){ f(); });
  while (TIMERS.length){ var t = TIMERS.shift(); t(); await new Promise(function(r){ _realST(r, 0); }); }
  STORE['d2r_owned'] = JSON.stringify(Array.from(owned));
}
function strip(){ var c = (typeof window._carriedNames === 'function') ? window._carriedNames(function(){ return false; }) : null;
  return (c || []).map(function(x){ return x.name; }); }
var OUT = {};
(async function(){
  STORE['d2r_owned'] = JSON.stringify(['Harlequin Crest', 'Crown of Ages', 'Bone Break', 'Arachnid Mesh', 'Stormshield', 'Nagelring',
                                        "Gheed's Wager", 'Magefist', 'Not A Seed Name']);
  STORE['d2r_muleAssign'] = JSON.stringify({ 'Stormshield': 'uni-armor' });
  STORE['d2r_laneLock'] = JSON.stringify({ 'Magefist': { lane: 'equipment', sessions: ['s1', 's2', 's3'] } });
  STORE['d2r_vaultProv'] = JSON.stringify({
    'Harlequin Crest': { kind: 'owned', source: 'kai-register', loc: 'inventory', carried: true, frameId: 'c_1', ts: 1790500000000,
                         looks: [{ id: 's_c', frame: 'c_1', at: '2026-09-28T10:00:00Z' }] },
    'Arachnid Mesh': { kind: 'owned', source: 'kai-register', loc: 'equipped', frameId: 'c_2', ts: 1790500000001 },
    'Nagelring': { kind: 'owned', source: 'kai-register', loc: 'inventory', carried: false,
                   landed: { loc: 'stash', frame: 'c_3', at: '2026-09-28T10:05:00Z' } },
    "Gheed's Wager": { kind: 'owned', source: 'hand', by: 'toggleOwned', where: 'the item card tick' } });
  window.__CONSOLE = true;                       // the owner console, whose MAIN ledger has NOT answered
  await boot();
  OUT.unanswered = { owned: JSON.parse(STORE['d2r_owned']).sort(), journal: STORE['d2r_vaultRemoved'] || null,
                     stamp: STORE['d2r_seedCleanse'] || null };
  window.__CONSOLE = false;                      // a page with no console to ask: the MAIN ledger is absent, not UNKNOWN
  await boot();
  OUT.first = { owned: JSON.parse(STORE['d2r_owned']).sort(), journal: JSON.parse(STORE['d2r_vaultRemoved'] || '[]'),
                found: JSON.parse(STORE['d2r_foundLog'] || '{}'), stamp: JSON.parse(STORE['d2r_seedCleanse'] || 'null'),
                strip: strip(), receipt: (JSON.parse(STORE['d2r_vaultProv'] || '{}'))['Harlequin Crest'] || null };
  // the reload: a residue name that reappears is NOT stripped again (one-time), and the carried item still stands
  var o = JSON.parse(STORE['d2r_owned']); o.push('Wisp Projector'); STORE['d2r_owned'] = JSON.stringify(o);
  await boot();
  OUT.second = { owned: JSON.parse(STORE['d2r_owned']).sort(), journal: JSON.parse(STORE['d2r_vaultRemoved'] || '[]'),
                 strip: strip() };
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write('THREW ' + (e && e.stack || e)); process.exit(3); });
"""

#: M2 — the measured pick-up-look-drop shapes, and the reverse (a ledger row per name, as _chLogUpsert keeps it)
_T0 = 1790550000000


def _row(name, loc, ts, frame, **kw):
    r = {"name": name, "status": "in-chronicle", "source": "kai-register", "sessionId": "s_bf", "frameId": frame,
         "firstSeenTs": ts, "loc": loc, "scene": kw.pop("scene", None)}
    r.update(kw)
    return r


SET_PIECES = ["Sigon's Visor", "Cathan's Mesh", "Tancred's Weird", "Arctic Horn", "Iratha's Collar"]
BACKFILL_LOG = (
    # one row, the register's three tuples: held in the inventory, then LATER on the ground
    [_row("Storm Emblem", "inventory", _T0, "m2_1", heldLoc="inventory", heldFrame="m2_1", heldTs=_T0,
          latestLoc="floor", latestScene="loot", latestFrame="m2_2", latestTs=_T0 + 5000)]
    # two spellings of one item (fold joins them): the ground row logged FIRST, the inventory row after it
    + [_row("Cloudy sphere", "floor", _T0 + 9000, "m2_4", scene="loot"),
       _row("Cloudy Sphere", "inventory", _T0 + 1000, "m2_3", heldLoc="inventory", heldFrame="m2_3", heldTs=_T0 + 1000)]
    # standing kit: never carried loot whatever the order
    + [_row("Small Charm of Good Luck", "inventory", _T0 + 2000, "m2_5", heldLoc="inventory", heldFrame="m2_5", heldTs=_T0 + 2000,
            latestLoc="floor", latestFrame="m2_6", latestTs=_T0 + 3000)]
    # five set pieces, picked up and let go
    + [_row(nm, "inventory", _T0 + 10000 * (i + 1), "sp_%d_a" % i, heldLoc="inventory", heldFrame="sp_%d_a" % i,
            heldTs=_T0 + 10000 * (i + 1), latestLoc="floor", latestFrame="sp_%d_b" % i, latestTs=_T0 + 10000 * (i + 1) + 500)
       for i, nm in enumerate(SET_PIECES)]
    # BASELINE, the reverse order: seen on the ground, then picked up -> carried, and filed as such
    + [_row("Laying of Hands", "floor", _T0 + 90000, "rv_1", scene="loot", heldLoc="inventory", heldFrame="rv_2",
            heldTs=_T0 + 91000, latestLoc="inventory", latestFrame="rv_2", latestTs=_T0 + 91000)]
    # M3 — a removal of the straight spelling keeps the curly one out; a removal in lower case keeps the (Shako) one out
    + [_row("Tal Rasha’s Horadric Crest", "stash", _T0 + 1, "m3_1", scene="stash"),
       _row("Harlequin Crest (Shako)", "stash", _T0 + 2, "m3_2", scene="stash")]
    # M3 — owned as "Arachnid Mesh", logged in lower case: the receipt lands on the OWNED spelling, nothing is filed
    + [_row("arachnid mesh", "equipped", _T0 + 3, "m3_3", scene="inventory")])


def _register_items(rows):
    """The SHIPPED register compiles `rows`; the items are built exactly as control_app's propose builder builds them
    (held and latest tuples beside the first sighting, no character — nothing produces one yet)."""
    import control_app as ca
    reg = ca._kai_compile_register(rows)
    out = []
    for x in reg:
        it = {"name": x.get("name"), "firstSeenTs": x.get("firstSeenTs"), "frameId": x.get("frameId"), "tier": x.get("tier"),
              "sessionId": "s_h3", "loc": x.get("loc"), "scene": x.get("scene")}
        if x.get("heldLoc"):
            it.update({"heldLoc": x.get("heldLoc"), "heldScene": x.get("heldScene"), "heldFrame": x.get("heldFrame"),
                       "heldTs": x.get("heldTs")})
        if x.get("latestLoc") or x.get("latestScene"):
            it.update({"latestLoc": x.get("latestLoc"), "latestScene": x.get("latestScene"),
                       "latestFrame": x.get("latestFrame"), "latestTs": x.get("latestTs")})
        out.append(it)
    return reg, out


#: his v2346 shape and its reverse, as the deep reader journals them
H3_ROWS = [
    {"lane": "deep", "ts": 1790560000000, "frameId": "30_1790560000000", "sessionId": "s_h3", "scene": "inventory",
     "names": ["Harlequin Crest"], "names_loc": {"Harlequin Crest": "inventory"}},
    {"lane": "deep", "ts": 1790560030000, "frameId": "31_1790560030000", "sessionId": "s_h3", "scene": "loot",
     "names": ["Harlequin Crest"], "names_loc": {"Harlequin Crest": "floor"}},
    {"lane": "deep", "ts": 1790560100000, "frameId": "32_1790560100000", "sessionId": "s_h3", "scene": "loot",
     "names": ["Magefist"], "names_loc": {"Magefist": "floor"}},
    {"lane": "deep", "ts": 1790560130000, "frameId": "33_1790560130000", "sessionId": "s_h3", "scene": "inventory",
     "names": ["Magefist"], "names_loc": {"Magefist": "inventory"}},
    # a Chronicle page AFTER the drop says nothing about where it is now — it must not hide the drop
    {"lane": "deep", "ts": 1790560200000, "frameId": "34_1790560200000", "sessionId": "s_h3", "scene": "inventory",
     "names": ["War Traveler"], "names_loc": {"War Traveler": "inventory"}},
    {"lane": "deep", "ts": 1790560230000, "frameId": "35_1790560230000", "sessionId": "s_h3", "scene": "loot",
     "names": ["War Traveler"], "names_loc": {"War Traveler": "floor"}},
    {"lane": "deep", "ts": 1790560260000, "frameId": "36_1790560260000", "sessionId": "s_h3", "scene": "chronicle",
     "names": ["War Traveler"], "names_loc": {}}]

#: M4 — a production-shaped session: one inventory read, no character anywhere
PROD_ROWS = [{"lane": "deep", "ts": 1790570000000, "frameId": "40_1790570000000", "sessionId": "s_p", "scene": "inventory",
              "names": ["Harlequin Crest"], "names_loc": {"Harlequin Crest": "inventory"}}]


def _drive():
    s = _src()
    _reg, items = _register_items(H3_ROWS)
    _preg, prod = _register_items(PROD_ROWS)
    extra = EXTRA % {"locks": P._between(s, LOCK_FROM, LOCK_TO), "main": P._between(s, MAIN_FROM, MAIN_TO)}
    script = ("var REGISTER_ITEMS = %s;\nvar PROD_ITEMS = %s;\nvar BACKFILL_LOG = %s;\n"
              % (json.dumps(items), json.dumps(prod), json.dumps(BACKFILL_LOG))) + extra + SCRIPT
    prog = P.HARNESS % {"lanes": P._lanes(s), "furn": P._between(s, P.FURN_FROM, P.FURN_TO), "region": P.owned_prov_region(s),
                        "evidence": P._marked(s, P.EV_BEGIN, P.EV_END), "rec": P._between(s, P.REC_FROM, P.REC_TO),
                        "script": script}
    out = P._node(prog, "order")
    out["_register"] = {r["name"]: r for r in _reg}
    return out


def _boot():
    s = _src()
    prog = BOOT % {"lanes": P._lanes(s), "furn": P._between(s, P.FURN_FROM, P.FURN_TO), "region": P.owned_prov_region(s),
                   "locks": P._between(s, LOCK_FROM, LOCK_TO), "main": P._between(s, MAIN_FROM, MAIN_TO),
                   "keep": _shared_keep(s), "slice": P._between(s, SLICE_FROM, SLICE_TO)}
    return P._node(prog, "boot")


_CACHE = {}


def out():
    if "o" not in _CACHE:
        _CACHE["o"] = _drive()
    return _CACHE["o"]


def boot():
    if "b" not in _CACHE:
        _CACHE["b"] = _boot()
    return _CACHE["b"]


def sec(k):
    """One driven section's result — or a failure naming what threw in it (UNKNOWN, never a pass)."""
    o = out()
    sk = {"m1live": "m1", "m4named": "m4"}.get(k, k)
    if sk in o.get("err", {}):
        raise AssertionError("the %s section threw on this board — UNKNOWN, not passing: %s" % (sk, o["err"][sk]))
    if k not in o:
        raise AssertionError("the %s section produced nothing — UNKNOWN, not passing" % k)
    return o[k]


@unittest.skipIf(NODE is None, "node is absent — the seed cleanse was not driven (a declared skip, never a pass)")
class H1TheSeedCleanseNeverTakesCarriedLoot(unittest.TestCase):
    """⚠ H1: the grail floor's 'one-time vault cleanse' ran on EVERY owner load and deleted every owned seed name with no
    mule filing — carried loot is never mule-filed, so a carried found unique left owned on the next reload, unjournaled."""

    def test_a_carried_found_unique_survives_two_reloads_and_stays_on_the_strip(self):
        b = boot()
        for k in ("first", "second"):
            self.assertIn("Harlequin Crest", b[k]["owned"], "%s load: a CARRIED found unique was deleted from owned by the "
                                                              "seed cleanse (§31.2: absence never un-owns it)" % k)
            self.assertIn("Harlequin Crest", b[k]["strip"], "%s load: the carried item left the carried strip" % k)

    def test_worn_landed_hand_filed_locked_and_shared_names_are_never_taken(self):
        own = boot()["first"]["owned"]
        for nm, why in (("Arachnid Mesh", "worn (§29)"), ("Nagelring", "landed in a stash"), ("Gheed's Wager", "his own tick"),
                        ("Stormshield", "filed to a mule"), ("Magefist", "lane-locked (§29)"), ("Bone Break", "the shared stash"),
                        ("Not A Seed Name", "in no seed")):
            self.assertIn(nm, own, "the seed cleanse took %s — %s" % (nm, why))

    def test_only_residue_goes_and_every_removal_is_in_the_journal(self):
        f = boot()["first"]
        self.assertNotIn("Crown of Ages", f["owned"], "BASELINE: true residue (no filing, no receipt, no lock) must still "
                                                      "go, or the cleanse proves nothing")
        batches = [bt for bt in f["journal"] if bt.get("lane") == "seed-cleanse"]
        self.assertEqual([["Crown of Ages"]], [bt["names"] for bt in batches],
                         "a removal the cleanse made is not in the removal journal (dated, listed, undoable)")
        self.assertEqual("Jul 3", f["found"].get("Crown of Ages"), "the found ledger lost a name the cleanse took (no unfind)")
        self.assertEqual(["Crown of Ages"], f["stamp"]["removed"])
        self.assertTrue(f["receipt"] and f["receipt"]["carried"], "the carried receipt was dropped")

    def test_it_is_one_time_per_world(self):
        s = boot()["second"]
        self.assertIn("Wisp Projector", s["owned"], "the cleanse ran again on the next load — it is not one-time")
        self.assertEqual(1, len([bt for bt in s["journal"] if bt.get("lane") == "seed-cleanse"]))
        o = P._node((P.ROUTER % {"router": P._between(_src(), P.ROUTER_FROM, P.ROUTER_TO, include_b=True)})
                    .replace("OUT.mainStamp = window.LSR.key('d2r_ownedProvBackfill');",
                             "OUT.mainStamp = window.LSR.key('d2r_seedCleanse'); OUT.lstamp = LSTAMP;")
                    .replace("var OUT = { stamp:", "var LSTAMP = window.LSR.key('d2r_seedCleanse'); var OUT = { stamp:"), "router")
        self.assertEqual(o["owned"].replace("d2r_owned", ""), o["lstamp"].replace("d2r_seedCleanse", ""),
                         "the cleanse stamp and d2r_owned resolve to different worlds")
        self.assertEqual("d2r_seedCleanse", o["mainStamp"])

    def test_an_unanswered_main_ledger_on_the_console_removes_nothing(self):
        u = boot()["unanswered"]
        self.assertIn("Crown of Ages", u["owned"], "the cleanse deleted while the MAIN ledger was UNKNOWN")
        self.assertIsNone(u["stamp"], "a refused run stamped itself done")
        self.assertIsNone(u["journal"])


@unittest.skipIf(NODE is None, "node is absent — the carried state was not driven")
class H2CarriedIsAStateWithAnOrder(unittest.TestCase):

    def test_stash_then_an_inventory_read_then_a_floor_label_is_still_owned_and_filed(self):
        o = sec("h2stash")
        self.assertEqual("uni-armor", o["filedAfterStash"], "BASELINE: the stash read must file it, or this proves nothing")
        self.assertNotEqual(True, o["carriedAfterInv"], "an inventory read re-marked a FILED item carried")
        self.assertTrue(o["owned"], "a same-named floor label un-owned a stashed, filed item")
        self.assertEqual("uni-armor", o["filed"], "a same-named floor label deleted its mule filing")
        self.assertEqual(0, o["removed"])
        self.assertTrue(o["nagel"]["owned"], "a stash receipt (unfiled) was un-owned by a floor label")
        self.assertNotEqual(True, o["nagel"]["carried"])
        self.assertEqual("landed", o["nagel"]["state"])

    def test_worn_locked_and_hand_ticked_items_never_become_carried_or_leave(self):
        o = sec("h2worn")
        for nm in ("Arachnid Mesh", "String of Ears", "Magefist"):
            self.assertIn(nm, o["owned"], "%s was un-owned by a same-named floor label" % nm)
        self.assertNotEqual(True, o["mesh"].get("carried"), "an inventory read re-marked WORN gear carried")
        self.assertTrue(o["lock"], "the §29 lock was lost")
        self.assertEqual(("locked", "worn", "hand"), (o["meshState"], o["soeState"], o["handState"]))
        self.assertEqual([], o["strip"], "worn / locked / hand-ticked items sit on the carried strip")
        for k in ("wFloor", "wFloor2", "hFloor"):
            self.assertFalse(o[k]["left"])
        self.assertEqual(0, o["removed"])

    def test_baseline_a_carried_item_still_leaves_on_a_real_drop(self):
        o = sec("baselineLeave")
        self.assertEqual("left", o["route"], "BASELINE: carried loot must still leave on a drop, or the guard is a leave "
                                             "that never fires")
        self.assertFalse(o["owned"])
        self.assertEqual(["carried-left:b_2"], o["batches"])


@unittest.skipIf(NODE is None, "node is absent — the time order was not driven")
class H3TheSightingsAreReadInTimeOrder(unittest.TestCase):

    def test_the_register_keeps_the_latest_sighting_whole(self):
        reg = out()["_register"]
        hc = reg["Harlequin Crest"]
        self.assertEqual(("floor", "loot", "31_1790560030000", 1790560030000),
                         (hc.get("latestLoc"), hc.get("latestScene"), hc.get("latestFrame"), hc.get("latestTs")),
                         "the register threw the later floor sighting away: %r" % hc)
        self.assertEqual(("inventory", "30_1790560000000"), (hc.get("heldLoc"), hc.get("heldFrame")))
        wt = reg["War Traveler"]
        self.assertEqual("35_1790560230000", wt.get("latestFrame"), "a later Chronicle page hid the drop behind it")

    def test_his_v2346_case_is_not_owned_and_the_reverse_is_carried(self):
        by = {r["name"]: r for r in sec("h3")}
        hc = by["Harlequin Crest"]
        self.assertFalse(hc["owned"], "picked up, looked at, thrown back out to the ground — and OWNED (v2346)")
        self.assertEqual("not-held", hc["route"])
        self.assertIn("LATER on the ground", hc["why"])
        self.assertEqual({"held": "30_1790560000000", "drop": "31_1790560030000"}, hc["dropped"])
        self.assertFalse(by["War Traveler"]["owned"], "a Chronicle page after the drop brought it back")
        mf = by["Magefist"]
        self.assertEqual(("carried", True, True), (mf["route"], mf["owned"], mf["carried"]),
                         "seen on the ground, then picked up — must be carried: %r" % mf)

    def test_already_carried_it_leaves_with_the_drops_own_frame(self):
        o = sec("h3leave")
        self.assertTrue(o["ownedBefore"], "BASELINE: the pick-up alone must own it (§31.2)")
        self.assertEqual("left", o["route"])
        self.assertFalse(o["owned"])
        self.assertEqual(["31_1790560030000"], o["proof"], "the leave did not carry the drop's frame as its receipt")

    def test_a_pair_that_cannot_be_ordered_waits(self):
        self.assertEqual("wait", sec("h3wait"))

    def test_the_console_hands_the_latest_sighting_to_the_board(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            ca = fh.read()
        self.assertEqual(1, ca.count('"latestFrame": x.get("latestFrame"), "latestTs": x.get("latestTs")}'),
                         "the console's propose builder no longer hands the latest sighting to the board")
        base = P._code_only(P._between(_src(), "        var base = {\n          name: nm, firstSeenTs: it.firstSeenTs || 0,",
                                       "        var why = window.kaiChronicleSettledWhy(nm);"))
        self.assertIn("latestLoc:it.latestLoc", base.replace(" ", ""), "kaiChroniclePropose drops the latest sighting")


@unittest.skipIf(NODE is None, "node is absent — the per-name place was not driven")
class M1ThePerNamePlaceDecides(unittest.TestCase):

    def test_inventory_inside_a_loot_frame_is_carried(self):
        got = {(a, b, c): (r, lv) for a, b, c, r, lv in sec("m1")}
        self.assertEqual(("carried", False), got[("inventory", "loot", "Shako")],
                         "a name the reader placed in his inventory inside a loot frame answered leave")
        self.assertEqual(("vault", False), got[("stash", "loot", None)])
        self.assertEqual(("not-held", True), got[(None, "loot", None)], "BASELINE: a loot frame with no place still leaves")
        self.assertEqual(("found-only", False), got[("stash", "chronicle", None)], "§28: a Chronicle page still overrules")
        self.assertEqual(("carried", True), (sec("m1live")["route"], sec("m1live")["owned"]))

    def test_the_register_agrees_with_the_board_on_every_pair(self):
        import control_app as ca
        lanes = ca._vault_claim_lanes()
        self.assertTrue(lanes, "BASELINE: the register could not read the board's lanes")
        bad = []
        for a, b, c, route, leave in sec("m1"):
            if ca._kai_sighting_leaves(a, b) != leave:
                bad.append(("leave", a, b, leave))
            reg = ca._kai_compile_register([{"lane": "deep", "ts": 5, "frameId": "f", "sessionId": "s", "scene": b,
                                             "names": ["Magefist"], "names_loc": ({"Magefist": a} if a else {})}])
            held = bool(reg and reg[0].get("heldLoc"))
            if c and held != (route in ("vault", "carried", "kit")):
                bad.append(("held", a, b, route))
        self.assertEqual([], bad, "the register and the board disagree about what holds or leaves (M1)")


@unittest.skipIf(NODE is None, "node is absent — the backfill was not driven")
class M2M3TheBackfillReadsTheSameOrder(unittest.TestCase):

    def test_the_measured_pick_up_look_drop_shapes_are_not_filed(self):
        o = sec("backfill")
        rc = o["r"]["receipt"]
        filed = [f["name"] for f in rc["filed"]]
        for nm in ["Storm Emblem", "Cloudy Sphere", "Cloudy sphere", "Small Charm of Good Luck"] + SET_PIECES:
            self.assertNotIn(nm, o["owned"], "%s — picked up, looked at, let go — was backfilled as owned carried loot" % nm)
            self.assertNotIn(nm, filed)
        dropped = sorted(d["name"] for d in rc["dropped"])
        self.assertEqual(sorted(["Storm Emblem", "Cloudy Sphere"] + SET_PIECES), dropped)

    def test_the_reverse_order_is_still_carried(self):
        o = sec("backfill")
        self.assertIn("Laying of Hands", o["owned"], "BASELINE: ground then pick-up must still be carried")
        self.assertTrue(o["prov"]["Laying of Hands"]["carried"])

    def test_one_function_not_a_copy(self):
        blk = P._code_only(P._between(_src(), "  window._ownedProvBackfill = function(opts){", "  window._ownedProvBackfillUndo"))
        self.assertIn("window._sightingsRoute(custody,", blk, "the backfill decides the order with its own copy of the rule")
        self.assertNotIn("window._vaultHoldingRoute(", blk, "the backfill routes a single sighting again")

    def test_a_removed_name_stays_out_whatever_its_spelling(self):
        o = sec("backfill")
        for nm in ("Tal Rasha’s Horadric Crest", "Tal Rasha's Horadric Crest", "Harlequin Crest (Shako)", "Harlequin Crest"):
            self.assertNotIn(nm, o["owned"], "%s came back through the backfill after he removed it (another spelling)" % nm)
        self.assertEqual(2, o["r"]["receipt"]["skipped"].get("removed-by-him"))

    def test_an_owned_name_gets_its_receipt_under_the_spelling_it_is_owned_by(self):
        o = sec("backfill")
        self.assertEqual(["Arachnid Mesh"], [n for n in o["owned"] if "rachnid" in n],
                         "a lower-case ledger row minted a second vault item beside the owned one")
        self.assertEqual("m3_3", (o["prov"].get("Arachnid Mesh") or {}).get("frameId"),
                         "the owned item did not get its receipt from its own (other-case) row")


@unittest.skipIf(NODE is None, "node is absent — the carried strip was not rendered")
class M4NothingNamesTheCharacterYet(unittest.TestCase):

    def test_a_production_shaped_propose_renders_one_row_that_says_who_is_unknown(self):
        o = sec("m4")
        self.assertEqual(["Harlequin Crest|null"], o["names"], "BASELINE: the production read must be carried, or this proves nothing")
        self.assertEqual(1, o["html"].count('class="vcar-row"'), "a per-character layout was rendered with no character known")
        self.assertIn("the reader does not name the character yet", o["html"])
        self.assertIn("#54", o["html"])
        self.assertIn(o["unknown"], o["html"].replace("&amp;", "&"))

    def test_a_named_character_still_gets_its_own_row(self):
        h = sec("m4named")
        self.assertEqual(2, h.count('class="vcar-row"'))
        self.assertLess(h.index('data-carried-char="KonyoSorc"'), h.index("the reader does not name the character yet"),
                        "the named character's row is not first")


@unittest.skipIf(NODE is None, "node is absent — the carried wording was not rendered")
class L2NoFalsePromise(unittest.TestCase):

    def test_every_carried_surface_says_it_leaves_on_a_drop_and_vendor_trade_is_not_supported(self):
        o = sec("l2")
        for k in ("routeWhy", "ev", "rule"):
            self.assertIn("not supported yet", o[k], "%s promises a vendor / trade leave the reader cannot send" % k)
        self.assertIn("leaves on a drop", o["rule"])

    def test_the_strip_says_the_same_rule(self):
        self.assertIn(sec("l2")["rule"], sec("m4")["html"])

    def test_an_empty_dock_beside_carried_loot_does_not_say_every_item_has_a_home(self):
        """Swept with M4 / L2: 'every owned item has a home' is false while carried loot is still in his hands."""
        s = _src()
        self.assertIn('.vault-dock[data-owned="1"][data-carried="1"]:empty::after{content:"nothing loose', s)
        blk = P._between(s, "    try { dock.setAttribute('data-owned', pool.length ? '1' : '0'); } catch(e){}",
                         "    var dbar=document.getElementById('vault-dock-bar');")
        code = "\n".join(l for l in blk.split("\n") if not l.strip().startswith(("//", "/*", "*")))
        self.assertIn("dock.setAttribute('data-carried', _carried.length ? '1' : '0');", code,
                      "nothing tells the dock that carried loot stands beside it, so it claims every item has a home")


class L4TheNameAndItsTimeReadWhole(unittest.TestCase):
    """The rendered pixels are the proof (evid_r3_*.png, three sizes); this pins the stylesheet so the ellipsis cannot
    come back unseen. Every rule whose selector names a carried-strip class is read as CSS (comments stripped)."""

    def _rules(self):
        s = _src()
        i = s.index(".vault-carried{display:flex;")
        j = s.index("/* v251: the dock's Auto-Sort widget", i)
        css = re.sub(r"/\*.*?\*/", " ", s[i:j], flags=re.S)
        return re.findall(r"([^{}]+)\{([^{}]*)\}", css)

    def test_no_carried_chip_rule_ellipsises_or_refuses_to_wrap(self):
        rules = self._rules()
        self.assertGreater(len(rules), 8, "BASELINE: the carried strip's stylesheet was not found")
        bad = [(sel.strip(), body) for sel, body in rules
               if "vcar" in sel and ("ellipsis" in body or re.search(r"white-space:\s*nowrap", body))]
        self.assertEqual([], bad, "a carried-strip rule cuts the name or its time again")

    def test_the_name_and_the_time_stack_and_wrap(self):
        rules = {sel.strip(): body for sel, body in self._rules()}
        text = rules.get(".vcar-items > .vault-chip > span.vcar-text", "")
        self.assertIn("flex-direction:column", text, "the name and its last-seen time no longer stack")
        self.assertIn("white-space:normal", text)
        self.assertIn("white-space:normal", rules.get(".vcar-text > .vault-chip-name", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {"why": "H1: the seed cleanse takes a carried (or any receipted) name again — the v677 every-load deletion",
     "file": "bible.html",
     "find": "      if (prov[nm]){\n        var st = _stateOf(nm, prov[nm], amap);\n",
     "replace": "      if (false){\n        var st = _stateOf(nm, prov[nm], amap);\n",
     "matches": 1},
    {"why": "H1: the seed cleanse is not one-time — it runs on every load again",
     "file": "bible.html",
     "find": "    if (done && typeof done === 'object' && done.ver >= _SC_VER && !opts.force) return { ran: false, already: true, receipt: done };\n",
     "replace": "",
     "matches": 1},
    {"why": "H1: the seed cleanse removes outside the removal journal again",
     "file": "bible.html",
     "find": "      try { vr = window.vaultRemove(take, { lane: 'seed-cleanse', quiet: true,\n",
     "replace": "      try { vr = (function(t){ t.forEach(function(n){ owned['delete'](n); }); return { removed: t }; })(take, { lane: 'seed-cleanse', quiet: true,\n",
     "matches": 1},
    {"why": "H1: the seed cleanse deletes while the MAIN ledger is UNKNOWN",
     "file": "bible.html",
     "find": "    if (opts.mainLedger === 'unanswered' || opts.mainLedger === 'UNKNOWN')\n",
     "replace": "    if (false)\n",
     "matches": 1},
    {"why": "H2: carried is a field to fill again — an inventory read re-marks a stashed / worn item carried (the re-mark "
            "is gone since the review of 20c0df1e, M-3: carried is decided once; this puts the fill back where it stood)",
     "file": "bible.html",
     "find": "    if (fresh.carried === true && owned.has(nm)) fresh.carried = null;\n",
     "replace": "    if (fresh.carried === true && cur && cur.kind === 'owned' && cur.carried !== true){ cur.carried = true; }\n",
     "matches": 1},
    {"why": "H2: a same-named floor label takes out an item that is not carried (landed / filed / worn / locked / hand)",
     "file": "bible.html",
     "find": "    if (st.state !== 'carried'){\n      if (st.state == null) return null;\n",
     "replace": "    if (false){\n      if (st.state == null) return null;\n",
     "matches": 1},
    {"why": "H3: the register throws the later sighting away again",
     "file": "control_app.py",
     "find": "        if _placed and (cur.get(\"latestTs\") is None or ts > int(cur.get(\"latestTs\") or 0)):\n",
     "replace": "        if False and (cur.get(\"latestTs\") is None or ts > int(cur.get(\"latestTs\") or 0)):\n",
     "matches": 1},
    {"why": "H3: the board never reads the latest sighting",
     "file": "bible.html",
     "find": "    if (row.latestLoc || row.latestScene)\n      add(",
     "replace": "    if (false)\n      add(",
     "matches": 1},
    {"why": "H3: a drop after the pick-up is ignored (the inventory look owns it)",
     "file": "bible.html",
     "find": "        if (later.length){\n          var drop = later.reduce(",
     "replace": "        if (false){\n          var drop = later.reduce(",
     "matches": 1},
    {"why": "M1: the loot scene overrules the reader's per-name inventory place again",
     "file": "bible.html",
     "find": "    if (l === 'floor' || l === 'ground')\n      return { route: 'not-held', leave: true,",
     "replace": "    if (l === 'floor' || l === 'ground' || s === 'loot')\n      return { route: 'not-held', leave: true,",
     "matches": 1},
    {"why": "M1: the register's leave rule lets the scene overrule the per-name place (the two disagree)",
     "file": "control_app.py",
     "find": "    if l:\n        return l in (\"floor\", \"ground\", \"vendor\", \"trade\")\n    return s in (\"loot\", \"vendor\", \"trade\")\n",
     "replace": "    if s in (\"loot\", \"vendor\", \"trade\"):\n        return True\n    if l:\n        return l in (\"floor\", \"ground\", \"vendor\", \"trade\")\n    return False\n",
     "matches": 1},
    {"why": "M2: the backfill decides each row on its own again — a later floor row of the same item is ignored",
     "file": "bible.html",
     "find": "      var v = window._sightingsRoute(custody, String(head.name).trim());\n",
     "replace": "      var v = window._readRoute(head);\n",
     "matches": 1},
    {"why": "M3: the backfill keys removals and owned names by the exact string again",
     "file": "bible.html",
     "find": "    var _cf = function(n){ return window._vaultCanonName(_regName(n)); };\n",
     "replace": "    var _cf = function(x){ return String(x == null ? '' : x); };\n",
     "matches": 1},
    {"why": "M4: the strip implies it knows the character — the plain UNKNOWN sentence is gone",
     "file": "bible.html",
     "find": "'\">' + E(ch || CARRIED_WHO_UNKNOWN) + '</span>'",
     "replace": "'\">' + E(ch || 'character UNKNOWN') + '</span>'",
     "matches": 1},
    {"why": "L2: the carried strip promises a vendor / trade leave the reader cannot send",
     "file": "bible.html",
     "find": "  var CARRIED_RULE = 'yours right away · lands when seen in a stash tab or on a mule · leaves on a drop (vendor/trade reads are not supported yet)';\n",
     "replace": "  var CARRIED_RULE = 'yours right away · lands when seen in a stash tab or on a mule · leaves on a drop, a vendor or a trade';\n",
     "matches": 1},
    {"why": "L2 sweep: the empty dock claims every owned item has a home while carried loot is still in his hands",
     "file": "bible.html",
     "find": "    try { dock.setAttribute('data-carried', _carried.length ? '1' : '0'); } catch(e){}\n",
     "replace": "",
     "matches": 1},
    {"why": "L4: the carried chip ellipsises its name and its time again",
     "file": "bible.html",
     "find": ".vcar-text > .vault-chip-name{white-space:normal;overflow-wrap:anywhere;line-height:var(--lh-tight)}\n",
     "replace": ".vcar-text > .vault-chip-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:var(--lh-tight)}\n",
     "matches": 1},
]
