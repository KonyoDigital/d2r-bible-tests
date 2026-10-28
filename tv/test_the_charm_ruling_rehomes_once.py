# -*- coding: utf-8 -*-
"""REG-2896 (his ruling 2026-10-28) - CHARMS ALREADY FILED ON MAGIC & RARE ARE RE-HOMED ONCE, BY THE RULING, AND SAY SO.

Measured on the whole page in node before the fix: a charm filed on MAGIC & RARE (a TV-registered small charm, a skiller)
kept that filing and its saved move target after the router stopped sending charms there - the board drew a charm where
his ruling says none lives. The one-shot migration (window._vaultCharmRulingMigrate, asked once the page has loaded):

  * re-homes each by the one charm rule: a resist small charm to the SHARED STASH, a skiller to the CHARMS mule, a large
    charm the checker never judged unfiled into Unsorted (its question), Gheed's from UNI-SMALL to CHARMS (his answer:
    a NEW mule only for charms), while a rare jewel stays on MAGIC & RARE and a ring on UNI-SMALL;
  * plans every copy's saved target again on its new home, carrying the reason word for word (the one exception
    REG-2787's stability law must allow);
  * is stamped (d2r_vaultCharmRuling, holding the log), so a second ask does nothing;
  * never runs in a shadow (read only), and never with the affix table unread (it would unfile every rolled charm) -
    a first cut ran at script time, before the table loaded, and unfiled all three charms.

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
"""
import json
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

NAMES = ["Shimmering Small Charm", "Lion Branded Grand Charm", "Bronze Large Charm", "Viper Eye"]
STUBS = dict((n, {"rarity": "magic", "base": n, "cat": "TV-vaulted", "val": "tv"}) for n in NAMES)
SMALL = ["Gheed's Fortune", "Nagelring"]   # on UNI-SMALL before the ruling: Gheed's moves to CHARMS, a ring stays
SEED = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
        "localStorage.setItem('d2r_owned', %s);\n"
        "localStorage.setItem('d2r_tvExtraItems', %s);\n"
        "localStorage.setItem('d2r_muleAssign', %s);\n") % (
    json.dumps(json.dumps(NAMES + SMALL)), json.dumps(json.dumps(STUBS)),
    json.dumps(json.dumps(dict([(n, "magic-rare") for n in NAMES] + [(n, "uni-small") for n in SMALL]))))
BODY = r"""
(function(){
var W = window;
OUT.boot = W._vaultCharmRuling || null;
OUT.assign = JSON.parse(H.RAW.get('d2r_muleAssign') || '{}');
OUT.stamp = H.RAW.get('d2r_vaultCharmRuling') ? JSON.parse(H.RAW.get('d2r_vaultCharmRuling')) : null;
OUT.again = W._vaultCharmRulingMigrate();
/* a saved target on MAGIC & RARE is planned again on the new home, with the reason */
var N = 'Shimmering Small Charm';
H.RAW.delete('d2r_vaultCharmRuling');
W.vaultFile(N, null, { move: true, mule: 'magic-rare', by: 'the law' });
try { W._vaultRecordsPersist && W._vaultRecordsPersist(); } catch (e) {}
/* the target the router planned before the ruling: a cell on MAGIC & RARE, saved */
W._vaultMoveCommit([{ name: N, copyIx: 0, task: W._vaultMoveTask({ name: N, from: { holder: null, location: null, cell: null },
  to: { holder: 'MAGIC & RARE', location: 'stash', cell: 'stash:c0r0', id: 'magic-rare' }, status: 'to-move' }) }]);
function moveOf(n){ var raw = JSON.parse(H.RAW.get('d2r_vaultRecords') || 'null');
  var r = raw ? (raw.records || []).filter(function(x){ return x.name === n; })[0] : null; return r ? (r.move || null) : null; }
OUT.before = moveOf(N);
OUT.run2 = W._vaultCharmRulingMigrate();
OUT.after = moveOf(N);
/* a shadow is read only */
H.RAW.delete('d2r_vaultCharmRuling');
W._tvdShadow = { owner: 'law' };
OUT.shadow = W._vaultCharmRulingMigrate();
delete W._tvdShadow;
OUT.shadowStamp = H.RAW.get('d2r_vaultCharmRuling') || null;
/* the affix table unread: it refuses, unstamped, and moves nothing */
var M = 'Fine Small Charm of Vita';
W._tvExtraRemember(M, { rarity: 'magic', base: M, cat: 'TV-vaulted', val: 'tv' }); owned.add(M);
W.vaultFile(M, { by: 'hand', at: new Date().toISOString(), where: 'the law' }, { mule: 'magic-rare' });
var keepDb = W._cbDb; _CHARM_AF = null; W._cbDb = function(){ return null; };
OUT.unread = W._vaultCharmRulingMigrate();
W._cbDb = keepDb; _CHARM_AF = null;
OUT.unreadAssign = JSON.parse(H.RAW.get('d2r_muleAssign') || '{}')[M] || null;
OUT.unreadStamp = H.RAW.get('d2r_vaultCharmRuling') || null;
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheCharmRulingRehomesOnce(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_the_load_rehomed_each_charm_by_the_rule(self):
        a = self.o["assign"]
        self.assertEqual(a.get("Shimmering Small Charm"), "shared", a)
        self.assertEqual(a.get("Lion Branded Grand Charm"), "charms", a)
        self.assertNotIn("Bronze Large Charm", a, "an unjudged large charm stayed filed: %r" % a)
        self.assertEqual(a.get("Viper Eye"), "magic-rare", "a rare jewel was moved: %r" % a)
        self.assertEqual(a.get("Gheed's Fortune"), "charms", "Gheed's stayed on UNI-SMALL: %r" % a)
        self.assertEqual(a.get("Nagelring"), "uni-small", "a ring left UNI-SMALL: %r" % a)
        moved = dict((m["name"], [m["from"], m["to"]]) for m in (self.o["boot"] or {}).get("moved", []))
        self.assertEqual(moved, {"Shimmering Small Charm": ["magic-rare", "shared"], "Lion Branded Grand Charm": ["magic-rare", "charms"],
                                 "Bronze Large Charm": ["magic-rare", None], "Gheed's Fortune": ["uni-small", "charms"]}, moved)

    def test_it_is_stamped_and_runs_once(self):
        self.assertIsNotNone(self.o["stamp"], "the migration left no stamp")
        self.assertEqual(len(self.o["stamp"]["moved"]), 4, self.o["stamp"])
        self.assertEqual(self.o["again"].get("done"), True, self.o["again"])

    def test_a_saved_target_is_planned_again_with_the_reason(self):
        b, a = self.o["before"], self.o["after"]
        self.assertEqual((b or {}).get("to", {}).get("id"), "magic-rare", "PREMISE: no saved target on MAGIC & RARE: %r" % b)
        self.assertEqual(self.o["run2"].get("tasks"), 1, self.o["run2"])
        self.assertEqual((a or {}).get("to", {}).get("id"), "shared", "the saved target did not move with the ruling: %r" % a)
        self.assertEqual((a or {}).get("reason"), "his 2026-10-28 charm ruling re-homed it", a)

    def test_an_unread_affix_table_moves_nothing(self):
        self.assertEqual(self.o["unread"].get("ran"), False, self.o["unread"])
        self.assertEqual(self.o["unreadAssign"], "magic-rare", "an unread table moved a charm: %r" % self.o["unreadAssign"])
        self.assertIsNone(self.o["unreadStamp"], "an unread table stamped the migration")

    def test_a_shadow_never_runs_it(self):
        self.assertEqual(self.o["shadow"], {"ran": False, "why": "a shadow is read only"})
        self.assertIsNone(self.o["shadowStamp"], "a shadow wrote the stamp")


RED_PROOF = [
    {"why": "REG-2896 - the migration is asked at script time, before the affix table loads, and re-homes nothing",
     "file": "bible.html",
     "find": ("    var go = function(){ try { _vaultCharmRulingMigrate(); } catch (eCM) {} };\n"
              "    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();\n"),
     "replace": "    var go = function(){ try { _vaultCharmRulingMigrate(); } catch (eCM) {} };\n    go();\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2896 - Gheed's (and every charm UNI-SMALL held) stays on UNI-SMALL",
     "file": "bible.html",
     "find": "      if (from !== 'magic-rare' && from !== 'uni-small') return;\n",
     "replace": "      if (from !== 'magic-rare') return;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2896 - it leaves no stamp, so it is not one-shot",
     "file": "bible.html",
     "find": "    try { window.LSR.setItem(CHARM_RULING_DONE, JSON.stringify(log)); } catch (eS) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2896 - the saved targets keep pointing at MAGIC & RARE",
     "file": "bible.html",
     "find": "    var tasks = moved.length ? _vaultCharmReplan(moved.map(function(m){ return m.name; })) : 0;\n",
     "replace": "    var tasks = 0;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2896 - a shadow runs it",
     "file": "bible.html",
     "find": "    if (window._tvdShadow) return { ran: false, why: 'a shadow is read only' };\n    var stamp = null;\n",
     "replace": "    var stamp = null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2896 - it runs with the affix table unread",
     "file": "bible.html",
     "find": "    if (typeof _charmAffixes !== 'function' || !_charmAffixes()) return { ran: false, why: 'the game\\u2019s affix table is not on this page yet' };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
