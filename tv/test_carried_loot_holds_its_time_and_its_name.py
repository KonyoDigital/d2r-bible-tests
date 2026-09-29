# -*- coding: utf-8 -*-
"""CARRIED LOOT HOLDS ITS TIME AND ITS NAME — the review of 20c0df1e (round 4 of the vault evidence route), every finding
driven. His rulings, recorded in HANDOFF_GROK.md:
  §31    carried loot is OWNED right away, NOT locked. It LANDS on a stash / mule sighting. It LEAVES ONLY on a drop (vendor /
         trade: a signal the reader cannot send yet). ABSENCE NEVER UN-OWNS IT.
  §29    worn gear and grid standing kit are pinned and LOCKED to the character until his manual unlock.

WHAT THIS LAW HOLDS, one class per finding (each reproduced on 20c0df1e by the round-3 reviewer first):
  H-1  A DROP LEAVES ONLY WHAT IT POSTDATES. The closer loop recloses old reels (every kaiVer bump, incomplete seal and POST
       /api/kai_reclose) and each reclose hands the board that old session's sightings again. An OLDER session's
       pick-up-look-drop, compiled by the SHIPPED register and replayed twice, never un-owns loot a NEWER session carries — it
       is recorded once on the receipt as history. A NEWER drop still leaves with its own frame, and — the mirror, swept —
       stays gone when the older pick-up is replayed after it (his removal outranks every older read; the cleanse's own
       batches are not his word). A drop with no time changes nothing and says UNKNOWN.
  M-2  THE SUFFIX IS PART OF THE NAME WHEN IT SEPARATES TWO ITEMS. The vault's one fold (window._vaultCanonName), driven over
       the board's OWN name lists (ITEMS built by its own builder from BOSSES, RUNEWORDS, ITEM_SETS, WS_SHARDS_HUB), keeps
       Spirit (shield)/(sword), Crescent Moon/(amulet), Aldur's Watchtower (any)/(Druid), Griswold's Legacy (any)/(Pala),
       the Worldstone Shard kinds and Hellmouth/(gloves) apart, and still joins Harlequin Crest with (Shako) and every
       apostrophe / case / slot spelling of one item. The backfill keys removals, owned names and groups through it; the
       register (its real name-resolution slice + the real d2rItemLookup) no longer files the runeword as the amulet.
  M-3  CARRIED IS DECIDED ONCE. For EVERY door the board names (_SRC_SAY), for a name owned before receipts existed, and for
       a door's receipt that outlived its name in `owned` (the merge driven on its own): an owned item is never re-marked
       carried by a later inventory read, so a same-named floor label never un-owns it.
       BASELINE: a fresh inventory pick-up is still carried and still leaves on a later drop.
  L-4  UNKNOWN IS SAID, NEVER []. With d2r_muleAssign unreadable, _carriedNames is null; the strip renders the UNKNOWN row;
       the population line claims neither "0 carried" nor "still loose"; renderVault hands the UNKNOWN to both.
  L-5  THE CORNER TRAY'S COLUMN IS RESERVED. The carried grid (and, swept, the unsorted dock) keeps its magnifier and ✕ out
       of the band the compass and "?" own. The pixels are the proof (evid_r4_*.png, 375 / 901 / 1280: the magnifier ended
       at x 321 under a tray starting at 319 at 375; now 22px short of it, 26px at 901 and 1280, every chip scrolled under
       both tray buttons hit-tests to its own magnifier); this pins the stylesheet so the reserve cannot leave unseen.
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
import test_carried_loot_keeps_its_order as C  # noqa: E402 — its register driver and its lock / MAIN cuts

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")

T = 1790400000000        # a fixture clock (2026-09-26, in the past); every read below carries its own time from it


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _decl(s, head):
    """A top-level `const X = [ ... ];` literal, cut whole by its own head and the first column-0 close after it."""
    assert s.count(head) == 1, "anchor %r matched %d times" % (head, s.count(head))
    i = s.index(head)
    j = s.index("\n];", i)
    return s[i:j + 3]


def _names_js(s):
    """The board's own name lists, installed on the global the region asks (typeof ITEMS / RUNEWORDS / ...)."""
    b = s.index("const BOSSES = ")
    bosses = s[b:s.index("\n", b)]
    builder = P._between(s, "const ITEM_REGISTRY = {};\nBOSSES.forEach(boss => {", "\n});\n", include_b=True)
    return ("globalThis.ITEMS = [];\n(function(){\n" + bosses + "\n" + builder + "\nglobalThis.ITEM_REGISTRY = ITEM_REGISTRY;\n})();\n"
            + "globalThis.RUNEWORDS = (function(){ " + _decl(s, "const RUNEWORDS = [") + " return RUNEWORDS; })();\n"
            + "globalThis.ITEM_SETS = (function(){ " + _decl(s, "const ITEM_SETS = [") + " return ITEM_SETS; })();\n"
            + "globalThis.WS_SHARDS_HUB = (function(){ " + _decl(s, "const WS_SHARDS_HUB = [") + " return WS_SHARDS_HUB; })();\n")


REG_FROM = "        if (typeof ITEMS !== 'undefined' && !ITEMS.some(function(i){ return i.n === name; })){\n"
REG_TO = "        if (typeof window.findSetPiece === 'function'){"
LOOKUP_FROM = "  function d2rItemLookup(name){"
LOOKUP_TO = "  window.d2rItemLookup = d2rItemLookup;"


def _resolver_js(s):
    """tvVaultRegister's own name resolution (its real slice) and the real d2rItemLookup it falls back to."""
    return (P._between(s, LOOKUP_FROM, LOOKUP_TO, include_b=True) + "\n"
            + "function RESOLVE(name){ var _cnV = window._vaultCanonName;\n" + P._between(s, REG_FROM, REG_TO) + "\n  return name; }\n")


def _doors(s):
    m = re.search(r"var _SRC_SAY = \{(.*?)\};", s, re.S)
    assert m, "the board's door list (_SRC_SAY) is gone"
    return re.findall(r"'([a-z0-9-]+)':", m.group(1))


#: H-1 — an OLDER session, as the deep reader journals it: picked up, looked at, dropped
OLD_ROWS = [
    {"lane": "deep", "ts": T + 1000, "frameId": "o1_%d" % (T + 1000), "sessionId": "s_old", "scene": "inventory",
     "names": ["Harlequin Crest"], "names_loc": {"Harlequin Crest": "inventory"}},
    {"lane": "deep", "ts": T + 31000, "frameId": "o2_%d" % (T + 31000), "sessionId": "s_old", "scene": "loot",
     "names": ["Harlequin Crest"], "names_loc": {"Harlequin Crest": "floor"}}]
#: H-1 mirror — a NEWER session's plain pick-up (no drop in it)
PICK_ROWS = [
    {"lane": "deep", "ts": T + 500000, "frameId": "p1_%d" % (T + 500000), "sessionId": "s_pick", "scene": "inventory",
     "names": ["Magefist"], "names_loc": {"Magefist": "inventory"}}]


def _row(name, loc, ts, frame, **kw):
    r = {"name": name, "status": "in-chronicle", "source": "kai-register", "sessionId": "s_bf4", "frameId": frame,
         "firstSeenTs": ts, "loc": loc, "scene": kw.pop("scene", None)}
    r.update(kw)
    return r


#: M-2 — the backfill over rows whose names differ ONLY by the suffix that separates two items
BF_LOG = [
    _row("Spirit (sword)", "stash", T + 1, "m2_sw", scene="stash"),
    _row("Crescent Moon (amulet)", "stash", T + 2, "m2_cm", scene="stash"),
    _row("Griswold's Legacy (any)", "stash", T + 3, "m2_gl", scene="stash"),
    _row("Worldstone Shard (Northern)", "stash", T + 4, "m2_ws", scene="stash"),
    # one group each: (any) picked up and let go, (Druid) held in the stash
    _row("Aldur's Watchtower (any)", "inventory", T + 10, "m2_aw1", heldLoc="inventory", heldFrame="m2_aw1", heldTs=T + 10,
         latestLoc="floor", latestScene="loot", latestFrame="m2_aw2", latestTs=T + 20),
    _row("Aldur's Watchtower (Druid)", "stash", T + 30, "m2_ad", scene="stash")]

PAIRS = [("Spirit (shield)", "Spirit (sword)"), ("Crescent Moon", "Crescent Moon (amulet)"),
         ("Aldur's Watchtower (any)", "Aldur's Watchtower (Druid)"), ("Griswold's Legacy (any)", "Griswold's Legacy (Pala)"),
         ("Worldstone Shard (Northern)", "Worldstone Shard (Eastern)"), ("Worldstone Shard (any)", "Worldstone Shard (Deep)"),
         ("Hellmouth", "Hellmouth (gloves)")]
JOINS = [("Harlequin Crest", "Harlequin Crest (Shako)"), ("harlequin crest", "Harlequin Crest (Shako)"),
         ("Tal Rasha’s Horadric Crest", "Tal Rasha's Horadric Crest"), ("Tal Rasha's Horadric Crest (helm)", "Tal Rasha's Horadric Crest"),
         ("spirit (Shield)", "Spirit (shield)"), ("Crescent moon (AMULET)", "Crescent Moon (amulet)"), ("Atma’s Scarab", "atma's scarab")]

SCRIPT = r"""
OUT.err = {};
function section(k, f){ try { f(); } catch (e) { OUT.err[k] = String(e && e.stack || e).slice(0, 500); } }
function stateOf(n){ return window._ownedState(n).state; }
function strip(){ return (window._carriedNames(function(){ return false; }) || []).map(function(c){ return c.name; }); }
function withSession(it, sid){ return Object.assign({}, it, { sessionId: sid }); }
var OLD = OLD_ITEMS.filter(function(it){ return it.name === 'Harlequin Crest'; })[0];
var PICK = PICK_ITEMS.filter(function(it){ return it.name === 'Magefist'; })[0];
// ══ H-1 — a NEWER carried pick-up, then the OLDER session's pick-up-look-drop replayed by two recloses ══
section('h1old', function(){
  reset({}, []);
  var newer = LIVE({ name: 'Harlequin Crest', loc: 'inventory', scene: 'inventory', frameId: 'n1', sessionId: 's_new', firstSeenTs: TNEW });
  var r1 = LIVE(withSession(OLD, 's_old'));
  var r2 = LIVE(withSession(OLD, 's_old'));
  // and a plain older floor label of the same name (no pick-up in its row at all)
  var r3 = LIVE({ name: 'Harlequin Crest', loc: 'floor', scene: 'loot', frameId: 'o3', sessionId: 's_older', firstSeenTs: T0 + 90000 });
  OUT.h1old = { newer: newer.route, r1: { route: r1.route, left: r1.left || null, dropped: r1.dropped || null },
                r2: { route: r2.route, left: r2.left || null }, r3: { route: r3.route, left: r3.left || null },
                owned: owned.has('Harlequin Crest'), state: stateOf('Harlequin Crest'), strip: strip(),
                removed: REMOVED.map(function(b){ return b.lane; }), past: (prov()['Harlequin Crest'] || {}).pastDrops || null };
});
// ══ H-1 — a NEWER drop still leaves, with its own frame; the older pick-up replayed after it never brings it back ══
section('h1new', function(){
  reset({}, []);
  var pick = LIVE(withSession(PICK, 's_pick'));
  var ownedAfterPick = owned.has('Magefist');
  var drop = LIVE({ name: 'Magefist', loc: 'floor', scene: 'loot', frameId: 'd1', sessionId: 's_drop', firstSeenTs: TPICK + 60000 });
  var ownedAfterDrop = owned.has('Magefist');
  var replay = LIVE(withSession(PICK, 's_pick'));
  var ownedAfterReplay = owned.has('Magefist');
  var again = LIVE({ name: 'Magefist', loc: 'inventory', scene: 'inventory', frameId: 'p9', sessionId: 's_again', firstSeenTs: TPICK + 120000 });
  OUT.h1new = { pick: pick.route, ownedAfterPick: ownedAfterPick, drop: { route: drop.route, left: drop.left || null },
                ownedAfterDrop: ownedAfterDrop, replay: { route: replay.route, why: replay.why, removedAfter: replay.removedAfter || null },
                ownedAfterReplay: ownedAfterReplay, again: again.route, ownedAgain: owned.has('Magefist'), state: stateOf('Magefist'),
                proof: REMOVED.filter(function(b){ return b.lane === 'carried-left'; }).map(function(b){ return b.proof && b.proof.frame; }) };
});
// ══ H-1 — his hand's removal outranks an older read; the cleanse's own batch does not ══
section('h1hand', function(){
  reset({}, []);
  LIVE({ name: 'Shako', loc: 'stash', scene: 'stash', frameId: 'h1', sessionId: 's_h', firstSeenTs: T0 + 5000 });
  // the removal door stamps its batch with the clock: pinned here, AFTER the read, so the order is the fixture's, not today's
  var _dn = Date.now; Date.now = function(){ return T0 + 50000; };
  try { window.vaultRemove(['Shako'], { lane: 'card-click', why: 'not mine' }); } finally { Date.now = _dn; }
  var back = LIVE({ name: 'Shako', loc: 'stash', scene: 'stash', frameId: 'h1', sessionId: 's_h', firstSeenTs: T0 + 5000 });
  var hand = { route: back.route, owned: owned.has('Shako'), removedAfter: back.removedAfter || null };
  reset({}, ['Crown of Ages']);
  Date.now = function(){ return T0 + 50000; };
  try { window.vaultRemove(['Crown of Ages'], { lane: 'seed-cleanse', why: 'residue' }); } finally { Date.now = _dn; }
  var cl = LIVE({ name: 'Crown of Ages', loc: 'stash', scene: 'stash', frameId: 'c1', sessionId: 's_c', firstSeenTs: T0 + 6000 });
  OUT.h1hand = { hand: hand, cleanse: { route: cl.route, owned: owned.has('Crown of Ages') } };
});
// ══ H-1 — a drop with no time cannot be put in order ══
section('h1unk', function(){
  reset({}, []);
  LIVE({ name: 'Nagelring', loc: 'inventory', scene: 'inventory', frameId: 'u1', sessionId: 's_u', firstSeenTs: T0 + 7000 });
  var d = LIVE({ name: 'Nagelring', loc: 'floor', scene: 'loot', frameId: 'u2', sessionId: 's_u2' });
  OUT.h1unk = { route: d.route, why: d.why, left: d.left || null, owned: owned.has('Nagelring'), removed: REMOVED.length };
});
// ══ M-2 — the one fold, over the board's own lists ══
section('m2canon', function(){
  var cn = window._vaultCanonName;
  OUT.m2canon = { pairs: PAIRS.map(function(p){ return [p[0], p[1], cn(p[0]), cn(p[1])]; }),
                  joins: JOINS.map(function(p){ return [p[0], p[1], cn(p[0]), cn(p[1])]; }),
                  known: { items: ITEMS.length, rw: RUNEWORDS.length, sets: ITEM_SETS.length, shards: WS_SHARDS_HUB.length },
                  lists: { spirit: RUNEWORDS.map(function(r){ return r.n; }).filter(function(n){ return /^Spirit/.test(n); }),
                           cmItems: ITEMS.map(function(i){ return i.n; }).filter(function(n){ return /^Crescent Moon/.test(n); }),
                           cmRw: RUNEWORDS.map(function(r){ return r.n; }).filter(function(n){ return /^Crescent Moon/.test(n); }),
                           shards: WS_SHARDS_HUB.map(function(w){ return w.n; }) } };
});
// ══ M-2 — the register's own resolution (the real slice, the real d2rItemLookup) ══
section('m2reg', function(){
  OUT.m2reg = ['Crescent Moon', 'Crescent Moon (amulet)', 'crescent moon (Amulet)', 'Harlequin Crest', 'harlequin crest',
               'Spirit (shield)', 'Spirit (sword)', 'Hellmouth (Gloves)', 'Atma’s Scarab']
    .map(function(n){ return [n, RESOLVE(n)]; });
});
// ══ M-2 — the backfill keys removals, owned names and groups through the one fold ══
section('m2bf', function(){
  reset({}, ['Spirit (shield)', "Griswold's Legacy (Pala)"]);
  STORE['d2r_chronicleInboxLog'] = JSON.stringify(BF_LOG);
  STORE['d2r_vaultRemoved'] = JSON.stringify([{ ts: T0 + 100, names: ['Crescent Moon'], lane: 'card-click' },
                                              { ts: T0 + 100, names: ['Worldstone Shard (Eastern)'], lane: 'card-click' }]);
  var bf = window._ownedProvBackfill();
  OUT.m2bf = { r: bf, owned: Array.from(owned).sort(), prov: prov() };
});
// ══ M-3 — every door the board names, then an inventory read, then a same-named floor label ══
section('m3', function(){
  OUT.m3 = DOORS.map(function(src, i){
    reset({}, []);
    window._ownedAdd('Shako', { source: src, by: 'the round-4 law', ts: T0 + 100 });
    var inv = LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'm3i_' + i, sessionId: 's_m3', firstSeenTs: T0 + 200 });
    var fl = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'm3f_' + i, sessionId: 's_m3', firstSeenTs: T0 + 300 });
    return { door: src, inv: inv.route, floor: fl.route, owned: owned.has('Shako'), carried: (prov()['Shako'] || {}).carried === true,
             state: stateOf('Shako'), strip: strip(), removed: REMOVED.length };
  });
  // a name owned before receipts existed: no receipt at all
  reset({}, ['Shako']);
  LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'lg1', sessionId: 's_lg', firstSeenTs: T0 + 200 });
  var lf = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'lg2', sessionId: 's_lg', firstSeenTs: T0 + 300 });
  OUT.m3legacy = { owned: owned.has('Shako'), carried: (prov()['Shako'] || {}).carried === true, floor: lf.route, removed: REMOVED.length };
  // a door's receipt that outlived its name in `owned` (d2r_owned rewritten by a restore / an un-seed): the read that owns the
  // name again is a PICK-UP (M-1, review of 7cded0c1): `owned` decides, the stale receipt is history, and the later drop leaves
  reset({ Shako: { kind: 'owned', source: 'ledger-restore', by: 'the un-seed undo', ts: T0 + 100, looks: [] } }, []);
  LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'st1', sessionId: 's_st', firstSeenTs: T0 + 200 });
  var stRow = prov()['Shako'] || {};
  var sf = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'st2', sessionId: 's_st', firstSeenTs: T0 + 300 });
  OUT.m3stale = { owned: owned.has('Shako'), carried: stRow.carried === true, source: stRow.source || null,
                  merged: (stRow.looks || []).map(function(k){ return k && k.frame; }), floor: sf.route, removed: REMOVED.length,
                  past: (stRow.pastReceipts || []).map(function(r){ return r && r.source; }) };
  // BASELINE — a fresh pick-up is still carried, and a later drop still leaves
  reset({}, []);
  var fp = LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'b1', sessionId: 's_b', firstSeenTs: T0 + 200 });
  var carriedNow = (prov()['Shako'] || {}).carried === true;
  var fd = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'b2', sessionId: 's_b', firstSeenTs: T0 + 300 });
  OUT.m3base = { pick: fp.route, carried: carriedNow, drop: fd.route, owned: owned.has('Shako') };
});
// ══ L-4 — UNKNOWN is said, never [] ══
section('l4', function(){
  reset({}, []);
  LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'l4', sessionId: 's_l4', firstSeenTs: T0 + 200 });
  var good = strip();
  STORE['d2r_muleAssign'] = '{';
  var names = window._carriedNames(function(){ return false; });
  OUT.l4 = { good: good, names: names, html: window._carriedStripHtml(names), unknown: window.CARRIED_UNKNOWN,
             pop: window._vaultPopHtml({ owned: 5, shared: 0, filed: 2, carried: null, loose: 3, sp: 1 }),
             popKnown: window._vaultPopHtml({ owned: 5, shared: 0, filed: 2, carried: 1, loose: 2, sp: 1 }),
             popNone: window._vaultPopHtml({ owned: 5, shared: 0, filed: 3, carried: 0, loose: 2, sp: 0 }) };
});
"""


def _drive():
    s = _src()
    _o, old = C._register_items(OLD_ROWS)
    _p, pick = C._register_items(PICK_ROWS)
    extra = C.EXTRA % {"locks": P._between(s, C.LOCK_FROM, C.LOCK_TO), "main": P._between(s, C.MAIN_FROM, C.MAIN_TO)}
    head = ("var T0 = %d, TNEW = %d, TPICK = %d;\nvar OLD_ITEMS = %s;\nvar PICK_ITEMS = %s;\nvar BF_LOG = %s;\nvar PAIRS = %s;\n"
            "var JOINS = %s;\nvar DOORS = %s;\n"
            % (T, T + 400000, T + 500000, json.dumps(old), json.dumps(pick), json.dumps(BF_LOG), json.dumps(PAIRS),
               json.dumps(JOINS), json.dumps(_doors(s))))
    # the lists and the resolver sit at the TOP of the program (the region asks `typeof ITEMS` at call time)
    prog = P.HARNESS % {"lanes": P._lanes(s) + "\n" + _names_js(s) + "\n" + _resolver_js(s),
                        "furn": P._between(s, P.FURN_FROM, P.FURN_TO), "region": P.owned_prov_region(s),
                        "evidence": P._marked(s, P.EV_BEGIN, P.EV_END), "rec": P._between(s, P.REC_FROM, P.REC_TO),
                        "script": head + extra + SCRIPT}
    out = P._node(prog, "r4")
    out["_old"] = {r["name"]: r for r in _o}
    return out


_CACHE = {}


def out():
    if "o" not in _CACHE:
        _CACHE["o"] = _drive()
    return _CACHE["o"]


def sec(k):
    """One driven section's result — or a failure naming what threw in it (UNKNOWN, never a pass)."""
    o = out()
    sk = {"m3legacy": "m3", "m3base": "m3", "m3stale": "m3"}.get(k, k)
    if sk in o.get("err", {}):
        raise AssertionError("the %s section threw on this board — UNKNOWN, not passing: %s" % (sk, o["err"][sk]))
    if k not in o:
        raise AssertionError("the %s section produced nothing — UNKNOWN, not passing" % k)
    return o[k]


@unittest.skipIf(NODE is None, "node is absent — the time order was not driven (a declared skip, never a pass)")
class H1ADropLeavesOnlyWhatItPostdates(unittest.TestCase):

    def test_the_older_session_really_is_a_pick_up_look_drop(self):
        """PREMISE: the SHIPPED register hands the board the older session's pick-up AND its later drop, or nothing below
        replays a drop at all."""
        hc = out()["_old"]["Harlequin Crest"]
        self.assertEqual(("inventory", "floor"), (hc.get("heldLoc"), hc.get("latestLoc")), "the register lost a sighting: %r" % hc)
        self.assertLess(hc.get("latestTs"), T + 400000, "PREMISE: the replayed drop must be OLDER than the newer pick-up")

    def test_an_older_sessions_drop_replayed_by_two_recloses_never_takes_newer_carried_loot(self):
        o = sec("h1old")
        self.assertEqual("carried", o["newer"], "BASELINE: the newer pick-up must own it as carried, or this proves nothing")
        self.assertTrue(o["r1"]["dropped"], "BASELINE: the replayed row must still read as a drop (it IS one, in its session)")
        self.assertTrue(o["owned"], "a reclose replayed an OLDER session's drop and un-owned loot a NEWER session carries")
        self.assertEqual([], o["removed"], "an older drop went through the removal door")
        self.assertEqual(["Harlequin Crest"], o["strip"], "the carried item left the strip")
        self.assertEqual("carried", o["state"])
        for k in ("r1", "r2", "r3"):
            self.assertFalse((o[k]["left"] or {}).get("left"), "%s: an older drop was a leave" % k)

    def test_the_older_drop_is_recorded_once_as_history(self):
        o = sec("h1old")
        past = o["past"] or []
        frames = [d.get("frame") for d in past]
        self.assertIn(out()["_old"]["Harlequin Crest"]["latestFrame"], frames, "the older drop was not recorded as history")
        self.assertEqual(len(frames), len(set(frames)), "one drop was recorded twice by two recloses")
        self.assertTrue(o["r1"]["left"].get("history"), "the answer did not say it was history")
        self.assertTrue(all(d.get("ts") for d in past), "a history row carries no time")

    def test_a_newer_drop_still_leaves_with_its_frame(self):
        o = sec("h1new")
        self.assertTrue(o["ownedAfterPick"], "BASELINE: the pick-up must own it")
        self.assertEqual("left", o["drop"]["route"], "a NEWER drop no longer leaves — the guard is a leave that never fires")
        self.assertFalse(o["ownedAfterDrop"])
        self.assertEqual(["d1"], o["proof"], "the leave did not carry the drop's own frame")

    def test_the_older_pick_up_replayed_after_a_newer_drop_never_brings_it_back(self):
        o = sec("h1new")
        self.assertFalse(o["ownedAfterReplay"], "a reclose replayed the older pick-up and re-owned an item that LEFT on a newer drop")
        self.assertEqual("not-held", o["replay"]["route"])
        self.assertEqual("carried-left", (o["replay"]["removedAfter"] or {}).get("lane"))
        self.assertIn("OLDER", o["replay"]["why"])

    def test_baseline_a_newer_pick_up_after_the_drop_is_his_again(self):
        o = sec("h1new")
        self.assertEqual(("carried", True, "carried"), (o["again"], o["ownedAgain"], o["state"]),
                         "a pick-up LATER than the drop must own it again — the removal is not a ban")

    def test_his_hand_outranks_an_older_read_and_the_cleanse_does_not(self):
        o = sec("h1hand")
        self.assertFalse(o["hand"]["owned"], "a read older than his removal brought the item back")
        self.assertEqual("card-click", (o["hand"]["removedAfter"] or {}).get("lane"))
        self.assertTrue(o["cleanse"]["owned"], "the seed cleanse's own batch blocked a holding read — it is not his word")
        self.assertEqual("vault", o["cleanse"]["route"])

    def test_a_drop_with_no_time_changes_nothing_and_says_unknown(self):
        o = sec("h1unk")
        self.assertTrue(o["owned"], "a drop with no time un-owned carried loot")
        self.assertEqual(0, o["removed"])
        self.assertIn("UNKNOWN", o["why"])


@unittest.skipIf(NODE is None, "node is absent — the fold was not driven")
class M2TheSuffixSeparatesTwoItems(unittest.TestCase):

    def test_premise_the_pairs_are_the_boards_own_names(self):
        o = sec("m2canon")
        self.assertEqual(["Spirit (sword)", "Spirit (shield)"], o["lists"]["spirit"])
        self.assertEqual(["Crescent Moon (amulet)"], o["lists"]["cmItems"])
        self.assertEqual(["Crescent Moon"], o["lists"]["cmRw"])
        self.assertEqual(5, len(o["lists"]["shards"]))
        self.assertGreater(o["known"]["items"], 300, "ITEMS was not built from the board's own drop tables")

    def test_the_fold_keeps_every_pair_apart(self):
        bad = [(a, b, ka) for a, b, ka, kb in sec("m2canon")["pairs"] if ka == kb]
        self.assertEqual([], bad, "the fold merged two distinct items into one key (M-2)")

    def test_the_fold_still_joins_every_spelling_of_one_item(self):
        bad = [(a, b, ka, kb) for a, b, ka, kb in sec("m2canon")["joins"] if ka != kb]
        self.assertEqual([], bad, "the fold split one item into two keys (M3 of round 3 would reopen)")

    def test_the_register_keeps_the_runeword_and_still_resolves_its_spellings(self):
        got = dict(sec("m2reg"))
        self.assertEqual("Crescent Moon", got["Crescent Moon"], "the register filed the runeword Crescent Moon as the amulet")
        self.assertEqual("Crescent Moon (amulet)", got["crescent moon (Amulet)"], "a case variant of the amulet no longer resolves")
        self.assertEqual("Harlequin Crest (Shako)", got["Harlequin Crest"], "BASELINE: the bare name must still resolve to (Shako)")
        self.assertEqual("Harlequin Crest (Shako)", got["harlequin crest"])
        self.assertEqual(("Spirit (shield)", "Spirit (sword)"), (got["Spirit (shield)"], got["Spirit (sword)"]))
        self.assertEqual("Hellmouth (gloves)", got["Hellmouth (Gloves)"], "the gloved twin resolved to the other Hellmouth")
        self.assertEqual("Atma's Scarab", got["Atma’s Scarab"])

    def test_the_backfill_keys_removals_owned_names_and_groups_through_it(self):
        o = sec("m2bf")
        rc = o["r"]["receipt"]
        filed = sorted(f["name"] for f in rc["filed"])
        for nm in ("Spirit (sword)", "Crescent Moon (amulet)", "Griswold's Legacy (any)", "Worldstone Shard (Northern)",
                   "Aldur's Watchtower (Druid)"):
            self.assertIn(nm, filed, "%s was folded into another item and never filed on its own" % nm)
        self.assertNotIn("frameId", o["prov"].get("Spirit (shield)") or {}, "the sword's row wrote its receipt onto the shield")
        self.assertNotIn("Griswold's Legacy (Pala)", rc["wrote"], "the (any) row wrote its receipt onto the (Pala) set")
        self.assertEqual(["Aldur's Watchtower (any)"], [d["name"] for d in rc["dropped"]],
                         "(any) and (Druid) were decided as one group")
        self.assertNotIn("removed-by-him", rc["skipped"], "a removal of one item blocked its distinct twin")


@unittest.skipIf(NODE is None, "node is absent — the doors were not driven")
class M3CarriedIsDecidedOnce(unittest.TestCase):

    def test_premise_every_door_the_board_names_is_driven(self):
        self.assertGreaterEqual(len(sec("m3")), 19, "the board's door list shrank or was not read")

    def test_no_door_s_item_is_re_marked_carried_or_un_owned_by_a_floor_label(self):
        bad = [(r["door"], r["state"], r["carried"], r["owned"]) for r in sec("m3")
               if (not r["owned"]) or r["carried"] or r["state"] == "carried" or r["strip"] or r["removed"]]
        self.assertEqual([], bad, "an item a door owns was made carried loot by a later inventory read (M-3)")

    def test_a_name_owned_before_receipts_existed_is_never_made_carried(self):
        o = sec("m3legacy")
        self.assertTrue(o["owned"], "a legacy owned item was un-owned by a floor label after an inventory read")
        self.assertFalse(o["carried"])
        self.assertEqual(0, o["removed"])

    def test_a_pick_up_over_a_receipt_that_outlived_its_name_is_carried(self):
        """M-1 (review of 7cded0c1, reproduced) re-pointed this case: the round-4 cut asserted the defect — a receipt a door
        left behind when the name left `owned` stopped the next real pick-up from being carried, so the later real drop
        never left. `owned` decides; the stale receipt is kept as history; the drop leaves."""
        o = sec("m3stale")
        self.assertEqual(("kai-register", ["st1"], ["ledger-restore"]), (o["source"], o["merged"], o["past"]),
                         "the pick-up did not start a fresh receipt with the stale one as history")
        self.assertTrue(o["carried"], "a receipt that outlived its name stopped a real pick-up from being carried (M-1)")
        self.assertEqual("left", o["floor"], "the later real drop did not leave")
        self.assertFalse(o["owned"])
        self.assertEqual(1, o["removed"])

    def test_baseline_a_fresh_pick_up_is_still_carried_and_still_leaves(self):
        o = sec("m3base")
        self.assertEqual(("carried", True), (o["pick"], o["carried"]), "BASELINE: a fresh pick-up must be carried")
        self.assertEqual("left", o["drop"])
        self.assertFalse(o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the UNKNOWN was not rendered")
class L4UnknownIsSaidNeverEmpty(unittest.TestCase):

    def test_an_unreadable_filing_store_is_null_not_an_empty_strip(self):
        o = sec("l4")
        self.assertEqual(["Shako"], o["good"], "BASELINE: with the stores readable the item is carried")
        self.assertIsNone(o["names"], "an unreadable d2r_muleAssign came back [] — the strip said '0 carried'")

    def test_the_strip_says_it_cannot_tell(self):
        o = sec("l4")
        self.assertIn(o["unknown"], o["html"].replace("&amp;", "&"))
        self.assertIn("UNKNOWN", o["html"])
        self.assertNotIn("vcar-chip", o["html"])

    def test_the_population_line_claims_neither_zero_carried_nor_still_loose(self):
        o = sec("l4")
        self.assertIn("carried <b>UNKNOWN</b>", o["pop"])
        self.assertNotIn("still loose", o["pop"], "the dock counted loot that may be in his hands as still loose")
        self.assertNotIn("<b>0</b> carried", o["pop"])
        self.assertIn("<b>1</b> carried", o["popKnown"], "BASELINE: a known count is still said")
        self.assertIn("still loose", o["popKnown"])
        self.assertNotIn("carried", o["popNone"].replace("carried UNKNOWN", ""), "BASELINE: nothing carried says nothing")

    def test_render_vault_hands_the_unknown_to_the_strip_and_the_line(self):
        s = P._code_only(_src())
        i = s.find("    var _carUnknown = (_carried === null);")
        self.assertGreaterEqual(i, 0, "renderVault keeps no UNKNOWN beside its carried cut — null collapses to [] and is lost")
        j = s.find("dock.innerHTML = unsorted.map(", i)
        self.assertGreater(j, i, "the renderer's strip / dock anchor moved — re-point this law rather than leaving it green")
        code = s[i:j]
        self.assertIn("carried: _carUnknown ? null : _carried.length", code, "the population line is not told the count is UNKNOWN")
        self.assertIn("if (_carUnknown){ _cEl.hidden = false; _cEl.innerHTML = window._carriedStripHtml(null", code,
                      "the strip is hidden instead of saying it cannot tell")


class L5TheCornerTraysColumnIsReserved(unittest.TestCase):
    """The pixels are the proof (evid_r4_after_carried_*.png, evid_r4_before_carried_*.png); this pins the stylesheet. Every
    rule for the exact selector is read in order as CSS (comments stripped) — the LAST padding-right wins, as in the page."""

    def _last(self, sel, prop):
        css = re.sub(r"/\*.*?\*/", " ", _src(), flags=re.S)
        val = None
        for m in re.finditer(r"(?:^|[}\s])" + re.escape(sel) + r"\{([^{}]*)\}", css):
            for d in m.group(1).split(";"):
                k, _, v = d.partition(":")
                if k.strip() == prop:
                    val = v.strip()
                elif k.strip() == "padding" and prop == "padding-right":
                    parts = v.split()
                    val = parts[1] if len(parts) in (2, 3) else (parts[3] if len(parts) == 4 else (parts[0] if parts else None))
        return val

    def test_the_carried_grid_reserves_the_trays_band(self):
        v = self._last(".vcar-items", "padding-right")
        self.assertIsNotNone(v, "the carried grid reserves nothing — its magnifier slides under the compass and the '?'")
        self.assertGreaterEqual(int(re.match(r"(\d+)px", v).group(1)), 20,
                                "the reserve is under the 20px the tray needs at 375 (grid ends 44px from the edge, tray + "
                                "glow own 64px)")

    def test_swept_the_dock_reserves_it_too(self):
        v = self._last(".vault-dock", "padding-right")
        self.assertGreaterEqual(int(re.match(r"(\d+)px", v or "0px").group(1)), 30,
                                "the unsorted dock's ✕ sits under the tray at 375 again")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {"why": "H-1: an older drop un-owns newer carried loot again — the drop's time is not weighed against the owning look",
     "file": "bible.html",
     "find": "    if (dropT <= ownT){\n",
     "replace": "    if (false){\n",
     "matches": 1},
    {"why": "H-1: an older drop is not recorded as history",
     "file": "bible.html",
     "find": "      var hist = _recordPastDrop(nm, all, r, h, fr, row);\n",
     "replace": "      var hist = false;\n",
     "matches": 1},
    {"why": "H-1: a drop with no time is ordered as if it had one (null reads as 0) — no UNKNOWN is said",
     "file": "bible.html",
     "find": "    if (dropT == null || ownT == null)\n      return { left: false, frame: fr, state: 'carried',\n",
     "replace": "    if (false)\n      return { left: false, frame: fr, state: 'carried',\n",
     "matches": 1},
    {"why": "H-1 mirror: a replayed older pick-up brings back an item that left on a newer drop / that he removed",
     "file": "bible.html",
     "find": "      if (rm) return Object.assign({}, v, { route: 'not-held', removedAfter: rm, held: v.sighting, why: rm.why });\n",
     "replace": "",
     "matches": 1},
    {"why": "H-1 mirror: the cleanse's own batch is read as his word and blocks a holding read",
     "file": "bible.html",
     "find": "  var _RM_NOT_HIS_WORD = { 'seed-cleanse': 1, 'backfill-undo': 1 };\n",
     "replace": "  var _RM_NOT_HIS_WORD = {};\n",
     "matches": 1},
    {"why": "M-2: the fold drops every trailing (...) again — Spirit (shield) and Spirit (sword) are one key",
     "file": "bible.html",
     "find": "    return (f !== st && _CN.ambiguous(st)) ? f : st; };\n",
     "replace": "    return st; };\n",
     "matches": 1},
    {"why": "M-2: the register hands a distinct name to the stem lookup again — the runeword Crescent Moon is filed as the amulet",
     "file": "bible.html",
     "find": "          if (!_hitV && !_distinctV && typeof d2rItemLookup === 'function'){\n",
     "replace": "          if (!_hitV && typeof d2rItemLookup === 'function'){\n",
     "matches": 1},
    {"why": "M-3: a receipt with no place is re-marked carried by a later inventory read again (the round-3 rule)",
     "file": "bible.html",
     "find": "    if (fresh.carried === true && owned.has(nm)) fresh.carried = null;\n",
     "replace": "    if (fresh.carried === true && cur && cur.kind === 'owned' && cur.carried !== true && _stateOf(nm, cur).state === null){ cur.carried = true; }\n",
     "matches": 1},
    {"why": "M-3: a name owned before this read (no receipt) is made carried loot by it",
     "file": "bible.html",
     "find": "    if (fresh.carried === true && owned.has(nm)) fresh.carried = null;\n",
     "replace": "    if (fresh.carried === true && cur) fresh.carried = null;\n",
     "matches": 1},
    {"why": "M-1 (round 5): a receipt that outlived its name stops a real pick-up from being carried again",
     "file": "bible.html",
     "find": "    if (fresh.carried === true && owned.has(nm)) fresh.carried = null;\n",
     "replace": "    if (fresh.carried === true && (cur || owned.has(nm))) fresh.carried = null;\n",
     "matches": 1},
    {"why": "L-4: an unreadable d2r_muleAssign reads as an empty strip again",
     "file": "bible.html",
     "find": "    if (amap === undefined) return null;\n",
     "replace": "",
     "matches": 1},
    {"why": "L-4: the strip renders nothing for UNKNOWN",
     "file": "bible.html",
     "find": "    if (carried === null)\n      return '<div class=\"vcar-row vcar-row-unknown\"",
     "replace": "    if (false)\n      return '<div class=\"vcar-row vcar-row-unknown\"",
     "matches": 1},
    {"why": "L-4: the population line says 'still loose' and drops the carried figure when it is UNKNOWN",
     "file": "bible.html",
     "find": "    if (p.carried === null){\n",
     "replace": "    if (false){\n",
     "matches": 1},
    {"why": "L-4: renderVault hands the line a 0 instead of UNKNOWN",
     "file": "bible.html",
     "find": "carried: _carUnknown ? null : _carried.length",
     "replace": "carried: _carried.length",
     "matches": 1},
    {"why": "L-5: the carried grid no longer reserves the corner tray's band",
     "file": "bible.html",
     "find": ".vcar-items{padding-right:24px}\n",
     "replace": "",
     "matches": 1},
    {"why": "L-5 sweep: the unsorted dock no longer reserves it",
     "file": "bible.html",
     "find": ".vault-dock{padding-right:34px}\n",
     "replace": "",
     "matches": 1},
]
