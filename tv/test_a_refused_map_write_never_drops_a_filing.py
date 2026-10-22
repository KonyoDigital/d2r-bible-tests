# -*- coding: utf-8 -*-
"""REG-2564 - A MULE-MAP WRITE THAT DOES NOT STICK NEVER DROPS A FILING, AND ANOTHER TAB'S ROSTER IS HELD BY THE LOAD RULE.

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
import os
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
localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'uni-weap' }));
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
var u3 = W.vaultUnassign('Grief'); OUT.u3 = !!(u3 && u3.ok);
OUT.disk = disk();
})();
"""


SYNC_PRELUDE = r"""
var __SL = []; (function(){ var _ael = window.addEventListener;
  window.addEventListener = function(t, f, o){ if (t === 'storage') __SL.push(f); return _ael.apply(this, arguments); }; })();
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Shako']));
var __BASE = ['sets-major','sets-rest','uni-weap','uni-armor','uni-small','runewords','bases','magic-rare','shared','dupes','wip']
  .map(function(id){ return { id: id, name: id.toUpperCase(), icon: 'x', note: '' }; });
localStorage.setItem('d2r_muleRoster', JSON.stringify(__BASE));
"""

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

    def test_3_another_tabs_roster_ahead_of_its_map_prunes_nothing(self):
        o = VPN.run(SYNC_BODY, prelude=SYNC_PRELUDE, timeout=300)
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run: %r" % o["__boot"])
        self.assertTrue(o["had"]["ok"] and o["had"]["disk"].get("Grief") == "war1", "PREMISE: the other tab's mule and filing were not taken: %r" % o)
        self.assertIsNone(o.get("lerr"))
        self.assertTrue(o["after"]["ok"], "PREMISE: no good map write after the roster: %r" % o["after"])
        self.assertEqual(o["disk"].get("Grief"), "war1", "this tab's next save wrote the map without the filing: %r" % o["disk"])
        self.assertIsNone(o.get("afterMap"), "the other tab's map (its delete) must still be taken once it arrives: %r" % o)


RED_PROOF = [
    {"why": "REG-2564 - a refused map write leaves the filing deleted in the live map, and the next save drops it",
     "file": "bible.html", "find": "      if (_prevU !== undefined) assign[name] = _prevU;",
     "replace": "      /* tamper */", "matches": 1, "needs": "node"},
    {"why": "REG-2564 - the restore door answers ok over a map write that did not stick",
     "file": "bible.html", "find": "      if (!_okR){\n        delete assign[nm];",
     "replace": "      if (false){\n        delete assign[nm];", "matches": 1, "needs": "node"},
    {"why": "REG-2564 - another tab's roster, ahead of its map, lets the paint prune drop the filings",
     "file": "bible.html", "find": "{ if (_rosterMapPending) return; delete assign[n]; return; }",
     "replace": "{ delete assign[n]; return; }", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
