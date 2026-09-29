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
  L-4  A BARE NAME SEVERAL KNOWN ITEMS SHARE IS NOT A MATCH — Crescent Moon (the runeword beside the amulet), Spirit,
       Hellmouth: window._vaultNameAmbiguity names the candidates, the register refuses it (or settles it by the read's
       kind), and _aicIsGrailName no longer resolves it to whichever one the codex holds.
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
DOOR_MENU = "  window.vaultDropMenuImport = async function(){\n"
DOOR_TV = "  window.tvVaultUnregister = function(name){\n"
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
%(clear)s
%(menu)s
%(tv)s
function journal(){ return JSON.parse(STORE['d2r_vaultRemoved'] || '[]'); }
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
// ══ M-1 — a standing receipt for a name he does NOT own never decides; a pick-up is a pick-up ══
section('m1', function(){
  reset({ Shako: { kind: 'owned', source: 'ledger-restore', by: 'the un-seed undo', ts: T0 + 100, at: new Date(T0 + 100).toISOString(), looks: [] } }, []);
  var pick = LIVE({ name: 'Shako', loc: 'inventory', scene: 'inventory', frameId: 'm1p', sessionId: 's_m1', firstSeenTs: T0 + 100000 });
  var after = row('Shako');
  var drop = LIVE({ name: 'Shako', loc: 'floor', scene: 'loot', frameId: 'm1d', sessionId: 's_m1', firstSeenTs: T0 + 200000 });
  OUT.m1 = { pick: pick.route, carried: after.carried === true, source: after.source || null, mode: (pick.register && pick.register.prov && pick.register.prov.mode) || null,
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
  LIVE(read3);
  var tv = window.tvVaultUnregister('Windforce');
  var j3 = journal();
  var back3 = LIVE(read3);
  OUT.m3tv = { ok: tv && tv.ok, ownedAfter: owned.has('Windforce'), lanes: j3.map(function(b){ return b.lane; }), replay: back3.route,
               removedAfter: back3.removedAfter || null, ownedAfterReplay: owned.has('Windforce') };
  // BASELINE — a pick-up NEWER than the removal is his again
  var again = LIVE({ name: 'Windforce', loc: 'stash', scene: 'stash', frameId: 'm3w2', sessionId: 's_m3b', firstSeenTs: Date.now() + 60000 });
  OUT.m3tv.again = again.route; OUT.m3tv.ownedAgain = owned.has('Windforce');
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
  var drop2 = LIVE({ name: 'Stormshield', loc: 'floor', scene: 'loot', frameId: 'l2e', sessionId: 's_l2b', firstSeenTs: T0 + 200000 });
  OUT.l2later = { look: look.route, lastAt: row('Stormshield').lastAt || null, drop: drop2.route, owned: owned.has('Stormshield') };
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
             spirit: window._vaultNameAmbiguity('Spirit'), hell: window._vaultNameAmbiguity('Hellmouth'), hc: window._vaultNameAmbiguity('Harlequin Crest'),
             shako: window._vaultNameAmbiguity('Shako') };
});
"""


def _drive():
    s = _src()
    extra = C.EXTRA % {"locks": P._between(s, C.LOCK_FROM, C.LOCK_TO), "main": P._between(s, C.MAIN_FROM, C.MAIN_TO)}
    doors = DOORS_JS % {"vr": P._between(s, VR_FROM, VR_TO), "clear": _door(s, DOOR_CLEAR), "menu": _door(s, DOOR_MENU), "tv": _door(s, DOOR_TV)}
    head = "var T0 = %d;\n" % T
    prog = P.HARNESS % {"lanes": P._lanes(s) + "\n" + R4._names_js(s) + "\n" + R4._resolver_js(s),
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
    sk = {"m1owned": "m1", "m2base": "m2", "m3clear": "m3", "m3menu": "m3", "m3tv": "m3", "l1drop": "l1", "l1rm": "l1", "l1bf": "l1",
          "l2later": "l2"}.get(k, k)
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

    def test_the_unique_cards_un_tick_goes_through_the_removal_door(self):
        s = P._code_only(_src())
        blk = P._between(s, UNTICK_FROM, UNTICK_TO)
        self.assertIn("window.vaultRemove([name], { lane: 'un-tick'", blk,
                      "the unique card's un-tick takes the name out of owned beside the removal journal (M-3)")
        self.assertIn("window._ownedProvForget(name)", blk, "the un-tick's fallback leaves the receipt standing (M-1)")


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
        s = P._code_only(_src())
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

    def test_spirit_and_hellmouth_are_ambiguous_too(self):
        o = sec("l4")
        self.assertEqual(["spirit (shield)", "spirit (sword)"], (o["spirit"] or {}).get("among"), "a bare 'Spirit' was registered as a third tile")
        self.assertEqual(["hellmouth", "hellmouth (gloves)"], (o["hell"] or {}).get("among"))

    def test_the_register_and_the_ai_checker_ask_the_same_rule(self):
        s = P._code_only(_src())
        reg = P._between(s, "  window.tvVaultRegister = function(name, witness){\n", "      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(name);")
        self.assertIn("window._vaultNameAmbiguity(name, { kind:", reg, "the register does not ask the ambiguity rule")
        self.assertIn("refused:'ambiguous'", reg)
        self.assertIn("name = window._vaultResolveName(name);", reg, "the register no longer resolves through the ONE published slice")
        i = s.index(GRAIL_FROM)
        j = s.index("\n  function ", i + len(GRAIL_FROM))
        self.assertIn("window._vaultNameAmbiguity(nm)) return null;", s[i:j], "_aicIsGrailName still resolves a bare ambiguous name to the codex's item")


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
    {"why": "M-3: the TV unvault takes the name out beside the removal journal again",
     "file": "bible.html",
     "find": "      if (owned.has(name)){ try { window.vaultRemove([name], { lane: 'tv-unvault', quiet: true, why: 'the TV saw it thrown' }); } catch(e){} }\n",
     "replace": "",
     "matches": 1},
    {"why": "M-3: the unique card's un-tick no longer goes through the removal door",
     "file": "bible.html",
     "find": "          try { if (typeof window.vaultRemove === 'function') _vrUT = window.vaultRemove([name], { lane: 'un-tick', quiet: true, why: 'un-ticked on its item card' }); } catch(e){ _vrUT = null; }\n",
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
]
