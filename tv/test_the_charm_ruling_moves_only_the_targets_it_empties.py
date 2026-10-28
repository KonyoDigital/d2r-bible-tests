# -*- coding: utf-8 -*-
"""REG-2964 (integration int-4: REG-2896 meets REG-2787) - HIS CHARM RULING IS THE ONE ALLOWANCE TO "A SAVED TARGET NEVER
MOVES UNLESS HE MOVES IT", AND IT TAKES NO MORE THAN IT NAMES.

REG-2787 pins every saved move target in place unless his hand moves it or the mule it names is deleted. REG-2896's one-shot
charm migration re-plans the targets of the charms it re-homes - the ruling's own move - and before this wiring it re-planned
EVERY copy's target of such a name, including a copy already targeted somewhere the ruling never emptied, and said so only in a
`reason` the move row does not draw. Now (_vaultCharmReplan):

  * only a name the one charm rule answers (_charmHome), and of it only a copy whose saved target is still on a locker the
    ruling empties - MAGIC & RARE or UNI-SMALL, by id, or by name on a record older than ids - is planned again;
  * a copy whose saved target is elsewhere keeps it, exactly (REG-2787);
  * the new target says why in REG-2787's own words (retarget), so the move row reads "new target: his 2026-10-28 charm
    ruling re-homed it", and the target stays put afterwards like any other.

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

N, G = "Shimmering Small Charm", "Lion Branded Grand Charm"
STUBS = dict((n, {"rarity": "magic", "base": n, "cat": "TV-vaulted", "val": "tv"}) for n in (N, G))
SEED = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
        "localStorage.setItem('d2r_owned', %s);\n"
        "localStorage.setItem('d2r_tvExtraItems', %s);\n"
        "localStorage.setItem('d2r_copies', %s);\n"
        "localStorage.setItem('d2r_muleAssign', %s);\n") % (
    json.dumps(json.dumps([N, G])), json.dumps(json.dumps(STUBS)), json.dumps(json.dumps({N: 2})),
    json.dumps(json.dumps({N: "magic-rare", G: "magic-rare"})))
BODY = r"""
(function(){
var W = window, N = 'Shimmering Small Charm', G = 'Lion Branded Grand Charm';
/* the load re-homed both; put them back on MAGIC & RARE as they were before the ruling, with saved targets */
H.RAW.delete('d2r_vaultCharmRuling');
[N, G].forEach(function(n){ W.vaultFile(n, null, { move: true, mule: 'magic-rare', by: 'the law' }); });
try { W._vaultRecordsPersist && W._vaultRecordsPersist(); } catch (e) {}
function task(n, to){ return W._vaultMoveTask({ name: n, from: { holder: null, location: null, cell: null }, to: to, status: 'to-move' }); }
W._vaultMoveCommit([
  { name: N, copyIx: 0, task: task(N, { holder: 'MAGIC & RARE', location: 'stash', cell: 'stash:c0r0', id: 'magic-rare' }) },
  { name: N, copyIx: 1, task: task(N, { holder: 'CHARMS', location: 'stash', cell: 'stash:c3r3', id: 'charms' }) },
  { name: G, copyIx: 0, task: task(G, { holder: 'MAGIC & RARE', location: 'stash', cell: 'stash:c1r0' }) }]);
function moves(n){ var raw = JSON.parse(H.RAW.get('d2r_vaultRecords') || 'null');
  var out = {}; ((raw && raw.records) || []).filter(function(x){ return x.name === n; }).forEach(function(r){
    out[r.copyIx || 0] = r.move ? { to: r.move.to, retarget: r.move.retarget || null } : null; }); return out; }
OUT.before = { n: moves(N), g: moves(G) };
OUT.run = W._vaultCharmRulingMigrate();
OUT.after = { n: moves(N), g: moves(G) };
try { W._vaultRecordsPersist && W._vaultRecordsPersist(); } catch (e) {}
OUT.later = { n: moves(N), g: moves(G) };
try { W._vaultMovePaint(); } catch (e) { OUT.paintErr = String(e); }
OUT.rows = String((document.getElementById('vault-move-list') || {}).innerHTML || '');
})();
"""

REASON = "his 2026-10-28 charm ruling re-homed it"


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheCharmRulingMovesOnlyTheTargetsItEmpties(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=SEED, timeout=300)

    def test_the_page_booted_and_the_premise_holds(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        b = self.o["before"]
        self.assertEqual(b["n"]["0"]["to"]["id"], "magic-rare")
        self.assertEqual(b["n"]["1"]["to"]["id"], "charms")
        self.assertIsNone(b["g"]["0"]["to"].get("id"), "PREMISE: the id-less record has an id")
        self.assertEqual(self.o["run"].get("ran"), True, self.o["run"])

    def test_a_target_on_a_locker_the_ruling_empties_moves_and_says_why(self):
        a = self.o["after"]
        self.assertEqual(a["n"]["0"]["to"]["id"], "shared", a)
        self.assertEqual((a["n"]["0"]["retarget"] or {}).get("why"), REASON, "the new target does not say why: %r" % a)
        self.assertEqual(a["g"]["0"]["to"]["id"], "charms", "an id-less target on MAGIC & RARE stayed: %r" % a)
        self.assertEqual((a["g"]["0"]["retarget"] or {}).get("why"), REASON)

    def test_a_target_elsewhere_stands(self):
        b, a = self.o["before"], self.o["after"]
        self.assertEqual(a["n"]["1"], b["n"]["1"], "a target the ruling never emptied was moved: %r -> %r" % (b["n"]["1"], a["n"]["1"]))

    def test_the_new_target_stays_put_and_the_row_says_why(self):
        self.assertEqual(self.o["later"], self.o["after"], "a rebuild moved the ruling's new target")
        self.assertIn("new target: " + REASON, self.o["rows"], "the move row does not say why its target moved")


RED_PROOF = [
    {"why": "REG-2964 - the ruling re-plans a saved target it never emptied",
     "file": "bible.html",
     "find": "      if (sv && sv.to && sv.to.cell && !_oldLk(sv.to)) return;          /* REG-2787 - a target elsewhere stands */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2964 - the ruling's new target does not say why, so its row reads like a drift",
     "file": "bible.html",
     "find": "        retarget: { why: CHARM_RULING_REASON, at: at } }) });   /* REG-2964 - the row says why its target moved */",
     "replace": "        }) });   /* REG-2964 - the row says why its target moved */",
     "matches": 1, "needs": "node"},
    {"why": "REG-2964 - a record older than ids (holder name only) on MAGIC & RARE keeps the target the ruling emptied",
     "file": "bible.html",
     "find": "      return !!(to.holder && ((a && to.holder === a.name) || (u && to.holder === u.name)));\n",
     "replace": "      return false;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
