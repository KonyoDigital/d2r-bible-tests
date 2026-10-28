# -*- coding: utf-8 -*-
"""#154.17 (REG-2830, REG-2831) - A READ HE KEEPS, AND A READ HE DISMISSES, CAN COME BACK FROM THE BOARD.

GrokBot's vault sweep: a reader-kept unknown (vaultKeepUnknown -> Magic & Rare) got no record, and removing it
(vaultThrowFind) or dismissing a read (vaultDismissUnknown) deleted with no confirm and no undo. Measured at HEAD on the
whole page in node (tv/vault_page_node.py):
  * the keep wrote the Magic & Rare record and nothing else - not in owned, no receipt row - while the AI Item Checker's
    keep (aicMule) owns the name beside its record with a hand receipt. No Magic & Rare item gets a vault record or a move
    task (both doors alike: Magic & Rare has its own locker), so "no record" was the missing receipt;
  * its X then went through no door: 0 journal batches, nothing vaultRestoreLast could put back (the checker-kept control:
    1 batch, restored whole);
  * Dismiss deleted the read from d2r_unknownReads at once: no journal, no undo;
  * no confirm in any of them, and the board draws no "Recently removed" list - the journal's undo is vaultRestoreLast(), a
    console call. The board's undo surface for a hand change is the toolbar's Undo chip (#145).
Now the keep owns the name with his hand as its receipt (REG-2830), so its X is journaled like every Magic & Rare X; the X
and Dismiss arm the toolbar's Undo with the board as it was just before (REG-2831), and the profile it restores carries the
review's reads (d2r_unknownReads). Like the other one-item removals here (vaultUnown), they take an undo, not a confirm.
RED_PROOF below.
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

A, J = "Havoc Eye Ring", "Zzq Junk Read"
PRELUDE = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
           "localStorage.setItem('d2r_unknownReads', %s);\n" % json.dumps(json.dumps([A, J])))

BODY = r"""
(function(){
var W = window, CONFIRMS = [], A = %s, J = %s;
W.uiConfirm = function(m){ CONFIRMS.push(String(m).slice(0, 80)); return Promise.resolve(true); };
W.confirm = function(m){ CONFIRMS.push('native'); return true; };
try { W.renderVault(); } catch (e) {} H.flush(60, 3);
function log(){ var l = W.vaultRemovalLog(); return Array.isArray(l) ? l.length : l; }
function prov(n){ try { return JSON.parse(W.LSR.getItem('d2r_vaultProv') || '{}')[n] || null; } catch (e) { return 'UNREADABLE'; } }
/* what the toolbar's Undo would write: its own parse of the snapshot, and its own diff against the page now */
function undoWould(store, name){
  var u = W._vaultUndo; if (!u) return { armed: false };
  var P = W._vaultProfileParse(u.text); if (!P || !P.ok) return { armed: true, parsed: false };
  var v = P.stores[store], has = false;
  try { var x = JSON.parse(v); has = Array.isArray(x) ? x.indexOf(name) >= 0 : !!(x && Object.prototype.hasOwnProperty.call(x, name)); } catch (e) {}
  var d = (W._vaultProfileDiff(P.stores) || []).filter(function(r){ return r.store === store; })[0] || null;
  return { armed: true, parsed: true, what: u.what, has: has, changed: !!(d && d.changed) };
}
OUT.log0 = log();
W.vaultKeepUnknown(A); H.flush(60, 3);
var pv = prov(A);
OUT.keep = { mf: !!magicFinds[A], owned: owned.has(A), unknown: unknownReads.has(A), prov: pv && { by: pv.by || (pv.ownedBy && pv.ownedBy.by) || null, source: pv.source || null } };
var l1 = log();
W.vaultThrowFind(A); H.flush(60, 3);
OUT.toss = { journal: log() - l1, mf: !!magicFinds[A], owned: owned.has(A), undoMf: undoWould('d2r_magicFinds', A), undoOwned: undoWould('d2r_owned', A) };
var r = W.vaultRestoreLast(); H.flush(60, 3);
OUT.restore = { restored: r && r.restored, mf: !!magicFinds[A], owned: owned.has(A) };
W.vaultDismissUnknown(J); H.flush(60, 3);
OUT.dismiss = { gone: !unknownReads.has(J), stored: JSON.parse(W.LSR.getItem('d2r_unknownReads') || '[]'), undo: undoWould('d2r_unknownReads', J),
                chip: !(document.getElementById('vault-chip-undo') || {}).hidden };
OUT.confirms = CONFIRMS.slice();
OUT.errors = H.errors.slice();
})();
""" % (json.dumps(A), json.dumps(J))


class AKeptOrDismissedReadCanComeBack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])

    def test_a_kept_read_is_owned_with_his_hand_as_its_receipt(self):
        k = self.o["keep"]
        self.assertTrue(k["mf"] and not k["unknown"], "PREMISE: the keep did not move the read to Magic & Rare: %r" % k)
        self.assertTrue(k["owned"], "a kept read is not owned, so its X can be undone by nothing: %r" % k)
        self.assertEqual(k["prov"], {"by": "the throw-out review", "source": "hand"}, "no receipt says who kept it: %r" % k)

    def test_its_x_is_journaled_and_put_back_whole(self):
        t, r = self.o["toss"], self.o["restore"]
        self.assertFalse(t["mf"] or t["owned"], "PREMISE: the X did not take it out: %r" % t)
        self.assertEqual(t["journal"], 1, "the X of a kept read wrote no journal batch: %r" % t)
        self.assertEqual((r["restored"], r["mf"], r["owned"]), (1, True, True), "the journal's undo did not put it back: %r" % r)

    def test_its_x_arms_the_toolbar_undo_with_the_read_in_it(self):
        t = self.o["toss"]
        self.assertEqual((t["undoMf"].get("armed"), t["undoMf"].get("has"), t["undoMf"].get("changed")), (True, True, True),
                         "the toolbar's Undo would not put the Magic & Rare record back: %r" % t["undoMf"])
        self.assertEqual(t["undoMf"]["what"], "the removal of " + A)
        self.assertTrue(t["undoOwned"].get("has") and t["undoOwned"].get("changed"), t["undoOwned"])

    def test_a_dismissed_read_can_come_back_from_the_toolbar(self):
        d = self.o["dismiss"]
        self.assertTrue(d["gone"] and J not in d["stored"], "PREMISE: the dismiss did not take the read: %r" % d)
        self.assertEqual((d["undo"].get("armed"), d["undo"].get("has"), d["undo"].get("changed")), (True, True, True),
                         "a dismissed read cannot come back: %r" % d["undo"])
        self.assertEqual(d["undo"]["what"], "the dismissal of " + J)
        self.assertTrue(d["chip"], "the toolbar's Undo chip is not shown")

    def test_a_one_item_removal_takes_an_undo_not_a_confirm(self):
        self.assertEqual(self.o["confirms"], [], "a confirm was asked: %r" % self.o["confirms"])


RED_PROOF = [
    {"why": "REG-2830 - a kept read is not owned again, so its X is journaled nowhere",
     "file": "bible.html",
     "find": "        window._ownedAdd(name, { source: 'hand', by: 'the throw-out review', where: 'the throw-out review (kept to Magic & Rare)' });\n",
     "replace": "        void 0;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2831 - the Magic & Rare X arms no undo on the board",
     "file": "bible.html",
     "find": "    var _undoTook = !!(_undoTF && typeof window._vaultUndoTake === 'function' && window._vaultUndoTake('the removal of ' + nm, '', _undoTF));\n",
     "replace": "    var _undoTook = false;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2831 - Dismiss arms no undo",
     "file": "bible.html",
     "find": "    var _undoTookD = !!(_undoDU && typeof window._vaultUndoTake === 'function' && window._vaultUndoTake('the dismissal of ' + name, '', _undoDU));\n",
     "replace": "    var _undoTookD = false;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2831 - the profile the undo restores leaves the review's reads out",
     "file": "bible.html",
     "find": "            'd2r_unknownReads',\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
