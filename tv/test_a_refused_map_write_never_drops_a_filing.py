# -*- coding: utf-8 -*-
"""REG-2570 - A MULE-MAP WRITE THAT DOES NOT STICK NEVER DROPS A FILING, AND ANOTHER TAB'S ROSTER IS HELD BY THE LOAD RULE.

The focused second-eye review of the r3a fix round (ede52513c, REG-2521/2522 fix round), reproduced on the merged V1 tree:
  * vaultUnassign (major): the cell X deleted the filing from the live map, then a refused or THROWING map write (quota)
    left it deleted in memory - the next good saveA() wrote the map without it. The live map now files it again.
  * vaultFile restore (major): it ignored saveA() and answered ok, so vaultFixSockets let the old label go after a
    refile that never landed. A restore the map refuses is undone (filing and witness row) and answered not-written;
    and vaultFixSockets treats a filed label with NO refile as a refusal too.
  * the roster tab sync (major): another tab's roster that drops a mule the map still files to was adopted and the paint
    prune dropped those filings before that tab's map arrived. (Holding it, as the review proposed, would quarantine every
    legit delete from another tab - it writes the roster first.) The prune now waits for the map.
RED_PROOF: the live-map restore removed from vaultUnassign; the restore door's write check removed; _rosterMapWhy taken
the prune's wait for another tab's map removed.
"""
import io
import json
import os
import re
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

import vault_page_node as VPN  # noqa: E402

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Shako']));
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'uni-weap', 'Monarch (4os)': 'bases' }));
localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Shako', 'Monarch (4os)']));
localStorage.setItem('d2r_vaultProv', JSON.stringify({ 'Shako': { kind: 'owned', source: 'hand', by: 'law seed', at: '2026-10-01T00:00:00Z' } }));
"""

BODY = r"""
(function(){
var W = window, AK = 'd2r_muleAssign', mode = null, _set = W.LSR.setItem;
W.LSR.setItem = function(k, v){ if (k === AK && mode === 'throw') throw new Error('QuotaExceededError');
                                 if (k === AK && mode === 'false') return false; return _set.call(W.LSR, k, v); };
function disk(){ try { return JSON.parse(W.LSR.getItem(AK) || '{}'); } catch (e) { return 'UNREADABLE'; } }
mode = 'throw'; var u1 = W.vaultUnassign('Grief'); mode = null;
OUT.u1 = { ok: u1 && u1.ok, refused: (u1 && u1.refused) || null };
var r0 = W.vaultFile('Shako', null, { restore: true, mule: 'uni-armor', prov: null });
OUT.r0 = { ok: r0 && r0.ok, why: (r0 && r0.why) || '' };
OUT.afterNext = disk();
W.vaultUnassign('Shako');
mode = 'false'; var r = W.vaultFile('Shako', null, { restore: true, mule: 'uni-armor', prov: null }); mode = null;
OUT.r = { ok: r && r.ok, refused: (r && r.refused) || null };
mode = 'throw'; var rt = W.vaultFile('Shako', null, { restore: true, mule: 'uni-armor', prov: { source: 'stash', where: 'law' } }); mode = null;
OUT.rt = { ok: rt && rt.ok, refused: (rt && rt.refused) || null };
var pv = JSON.parse(W.LSR.getItem('d2r_vaultProv') || '{}'); OUT.shakoRow = pv['Shako'] || null;
var _vf = W.vaultFile; W.vaultFile = function(){ return undefined; };   /* a refile that answers nothing */
var fx = W.vaultFixSockets('Monarch (4os)', 3); W.vaultFile = _vf;
OUT.fx = fx ? { ok: fx.ok, refused: fx.refused || null } : null;
OUT.flailOwned = JSON.parse(W.LSR.getItem('d2r_owned') || '[]').indexOf('Monarch (4os)') >= 0;
var u3 = W.vaultUnassign('Grief'); OUT.u3 = !!(u3 && u3.ok);
OUT.disk = disk();
})();
"""


# REG-2969 - THE CORE LOCKERS ARE READ FROM THE PAGE, NEVER TYPED HERE. A hand list of them (11 ids) went stale the day
# REG-2895 made CHARMS a core locker: the 'other tab's' roster then lacked it, the board rightly refused it as a store of
# the wrong shape, and the case measured that refusal instead of the map write it is about.
def _core_ids():
    _src = io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html"), encoding="utf-8").read()
    _blk = re.search(r"var DEFAULT_ROSTER=\[(.*?)\n  \];", _src, re.S)
    _ids = re.findall(r"\{id:'([a-z-]+)'", _blk.group(1)) if _blk else []
    assert len(_ids) >= 10, "PREMISE: the page's DEFAULT_ROSTER ids could not be read: %r" % (_ids,)
    return _ids


SYNC_PRELUDE = r"""
var __SL = []; (function(){ var _ael = window.addEventListener;
  window.addEventListener = function(t, f, o){ if (t === 'storage') __SL.push(f); return _ael.apply(this, arguments); }; })();
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Shako']));
var __BASE = __CORE_IDS__
  .map(function(id){ return { id: id, name: id.toUpperCase(), icon: 'x', note: '' }; });
localStorage.setItem('d2r_muleRoster', JSON.stringify(__BASE));
""".replace("__CORE_IDS__", json.dumps(_core_ids()))

SYNC_BODY = r"""
(function(){
var W = window, RK = 'd2r_muleRoster', AK = 'd2r_muleAssign';
function other(k, nv){ var ov = H.RAW.has(k) ? H.RAW.get(k) : null; H.RAW.set(k, nv);
  __SL.forEach(function(f){ try { f.call(W, { key: k, oldValue: ov, newValue: nv, storageArea: W.localStorage }); } catch (e) { OUT.lerr = String(e); } }); }
var base = __BASE;
function save(){ W.vaultUnassign('Shako'); var r = W.vaultFile('Shako', null, { restore: true, mule: 'uni-armor', prov: null });
  return { ok: !!(r && r.ok), why: (r && r.why) || '', disk: JSON.parse(H.RAW.get(AK) || '{}') }; }
var withW = base.concat([{ id: 'war1', name: 'WAR1', icon: 'x', note: '', added: true }]);
other(RK, JSON.stringify(withW));
other(AK, JSON.stringify({ 'Grief': 'war1' }));
OUT.had = { ok: true, disk: JSON.parse(H.RAW.get(AK) || '{}') };
other(RK, JSON.stringify(base));          /* the roster arrives first; its map has not come yet */
try { renderVault(); } catch (e) { OUT.rerr = String(e); }
OUT.after = save();                        /* any good map write from this tab */
OUT.disk = OUT.after.disk;
other(AK, JSON.stringify({ 'Grief': 'war1', 'Shako': 'uni-armor' }));   /* a map that STILL files the missing mule */
try { renderVault(); } catch (e) {}
OUT.stillFiled = save().disk['Grief'] || null;
other(AK, JSON.stringify({}));            /* that tab's map now arrives: the delete is complete */
try { renderVault(); } catch (e) {}
OUT.afterMap = save().disk['Grief'] || null;
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ARefusedMapWriteNeverDropsAFiling(unittest.TestCase):

    def test_0_premise(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run: %r" % o["__boot"])

    def test_1_a_throwing_unassign_keeps_the_live_filing(self):
        o = page()
        self.assertFalse(o["u1"]["ok"], "a map write that threw must not answer ok: %r" % o["u1"])
        self.assertTrue(o["r0"]["ok"], "PREMISE: the next good map write did not happen: %r" % o["r0"])
        self.assertEqual(o["afterNext"].get("Grief"), "uni-weap", "the next good save dropped Grief's filing: %r" % o["afterNext"])

    def test_2_a_refused_restore_is_not_ok(self):
        o = page()
        self.assertFalse(o["r"]["ok"], "a restore the map refused answered ok: %r" % o["r"])
        self.assertEqual(o["r"]["refused"], "not-written")
        self.assertTrue(o["u3"], "PREMISE: the next good map write did not happen")
        self.assertNotIn("Shako", o["disk"], "a refused restore stayed in the live map and the next save wrote it: %r" % o["disk"])

    def test_4_a_throwing_restore_puts_the_old_row_back(self):
        o = page()
        self.assertEqual(o["rt"]["refused"], "not-written", "a restore whose save threw must answer not-written: %r" % o["rt"])
        self.assertEqual((o["shakoRow"] or {}).get("by"), "law seed", "the refused restore left its own witness row: %r" % o["shakoRow"])

    def test_5_a_socket_fix_with_no_refile_is_refused(self):
        o = page()
        self.assertEqual((o["fx"] or {}).get("refused"), "no-home", "a filed label with no refile must be refused: %r" % o["fx"])
        self.assertTrue(o["flailOwned"], "the refused socket fix let the old label go")
        self.assertEqual(o["disk"].get("Monarch (4os)"), "bases", "the refused socket fix dropped the old filing: %r" % o["disk"])

    def test_3_another_tabs_roster_ahead_of_its_map_prunes_nothing(self):
        o = VPN.run(SYNC_BODY, prelude=SYNC_PRELUDE, timeout=300)
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run: %r" % o["__boot"])
        self.assertTrue(o["had"]["ok"] and o["had"]["disk"].get("Grief") == "war1", "PREMISE: the other tab's mule and filing were not taken: %r" % o)
        self.assertIsNone(o.get("lerr"))
        self.assertTrue(o["after"]["ok"], "PREMISE: no good map write after the roster: %r" % o["after"])
        self.assertEqual(o["disk"].get("Grief"), "war1", "this tab's next save wrote the map without the filing: %r" % o["disk"])
        self.assertEqual(o.get("stillFiled"), "war1", "a map that still files the missing mule lifted the wait: %r" % o)
        self.assertIsNone(o.get("afterMap"), "the other tab's map (its delete) must still be taken once it arrives: %r" % o)


RED_PROOF = [
    {"why": "REG-2570 r2 - a socket fix of a filed label with no refile lets the old label go again",
     "file": "bible.html", "find": "      if (_rfNeed && !_rfF) _rfF = { ok: false,", "replace": "      if (false) _rfF = { ok: false,",
     "matches": 1, "needs": "node"},
    {"why": "REG-2570 r2 - any map from another tab lifts the wait, even one still filing the missing mule",
     "file": "bible.html", "find": "after: function(){ try { window._rosterMapPending = !!_rosterMapWhy(roster, assign); } catch (eP) { window._rosterMapPending = true; } return _vaultTabAfter",
     "replace": "after: function(){ window._rosterMapPending = false; return _vaultTabAfter", "matches": 1, "needs": "node"},
    {"why": "REG-2570 r2 - a refused restore leaves its own witness row in place of the old one",
     "file": "bible.html", "find": "        if (rowR && _rowPrevOk){", "replace": "        if (false){", "matches": 1, "needs": "node"},
    {"why": "REG-2570 - a refused map write leaves the filing deleted in the live map, and the next save drops it",
     "file": "bible.html", "find": "      if (_prevU !== undefined) assign[name] = _prevU;",
     "replace": "      /* tamper */", "matches": 1, "needs": "node"},
    {"why": "REG-2570 - the restore door answers ok over a map write that did not stick",
     "file": "bible.html", "find": "      if (!_okR){\n        delete assign[nm];",
     "replace": "      if (false){\n        delete assign[nm];", "matches": 1, "needs": "node"},
    {"why": "REG-2570 - another tab's roster, ahead of its map, lets the paint prune drop the filings",
     "file": "bible.html", "find": "{ if (window._rosterMapPending) return; delete assign[n]; return; }",
     "replace": "{ delete assign[n]; return; }", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
