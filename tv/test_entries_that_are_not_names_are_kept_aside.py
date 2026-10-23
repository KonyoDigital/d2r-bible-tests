# -*- coding: utf-8 -*-
"""REG-2527 (V1 round 3; the review of REG-2400, minor) - AN OWNED ENTRY THAT IS NOT A NAME IS KEPT ASIDE, NEVER DELETED.

REG-2400's owned-load doctor keeps every name the load-time prune would drop, and "sets aside" an entry that is not a
name (a number, null, an empty string - what a broken writer or GrokBot's fuzz sweep leaves in d2r_owned). But "set
aside" was a delete: persist() wrote d2r_owned without them, nothing kept them anywhere, and the next load said nothing,
while the Vault's line said they "were set aside on this load". The builder's own case asserted the stored list holds
none of [5, null, ""] after one load - the delete, pinned.

NOW the entries are copied aside BEFORE persist() runs - content-addressed beside the store's own quarantine slots
(<world>d2r_quarantine~d2r_owned~not-names~<hash>, so a reload never writes a second copy), read back to prove it - and
the Vault says where they are. When the copy cannot be made (a full browser storage), they stay in the SAVED list: the
door quarantines d2r_owned (every write refused, said on the board) while the page runs on the names, so memory never
holds a non-name the code after the load reads as a name.

WHAT IS DRIVEN: the store door window.LSR (store_door_harness.stage) and the whole load-time prune with its owned-load
doctor and the Vault's line (_vaultOwnedKeptPaint), cut from bible.html, in node; the full-storage case makes the
door's raw writes of an aside slot throw. RED_PROOF below. A missing node is the only skip.
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

import store_door_harness as D  # noqa: E402

OWNED = json.dumps(["Grief", 5, None, "", "Harlequin Crest"])
NOT_NAMES = [5, None, ""]


def _pieces(s, full=False):
    norm = D.between(s, "function _norm(s){", "\n")
    safe = D.between(s, "const _safeJsonParse = (raw, fallback) => {", "\n};\n")
    rws = D.between(s, "const RUNEWORDS = [", "\n];\n")
    prune = D.between(s, "(function _v42_sanitizeWishlistOwned() {", "\n  // v659 — GRAIL FOUND-SEED floor", keep_b=False)
    return (("THROW_ON = /d2r_quarantine~/;\n" if full else "") + D.stage(s) + "var LS = window.LSR;\n" + norm + "\n" + safe
            + "\n" + rws + r"""
var SUNDER_CHARMS = [], BASE_CLASS = {};
var ITEM_REGISTRY = { "Harlequin Crest": { n: "Harlequin Crest" }, "Grief": { n: "Grief" } };
var _UNI_EXTRA = {}, _GRAIL_SEED = {}, _EXTRA_ITEM_SET = new Set();
window._gUniqueRoster = function(){ return ["Harlequin Crest"]; };
function findSetPiece(){ return null; }
var SLOT = new El('vault-owned-kept'); ELS['vault-owned-kept'] = SLOT;
var wishlist, owned, magicFinds;
function persist(){ LS.setItem('d2r_owned', JSON.stringify(Array.from(owned))); }
function pageLoad(){
  wishlist = new Set(); magicFinds = {};
  owned = new Set(JSON.parse(RAW['d2r_owned']));
""" + prune + "\n})();\n}\n")


BODY = r"""
pageLoad();
var R = window._ownedLoadReceipt;
OUT.receipt = { notNames: R.notNames, asideAt: R.asideAt };
OUT.aside = R.asideAt ? RAW[R.asideAt] : null;
OUT.memory = Array.from(owned);
OUT.stored = RAW['d2r_owned'];
var q = window.LSR.quarantined('d2r_owned'); OUT.q = q ? { reason: q.reason } : null;
window._vaultOwnedKeptPaint(); OUT.line = SLOT.innerHTML;
OUT.slots = Object.keys(RAW).filter(function(k){ return k.indexOf('not-names') >= 0; }).length;
pageLoad();                                                    /* a second load over the same bytes */
OUT.slotsAfterReload = Object.keys(RAW).filter(function(k){ return k.indexOf('not-names') >= 0; }).length;
"""


def _run(full=False):
    s = D.src()
    return D.page(_pieces(s, full), BODY, seed={"d2r_owned": OWNED})


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED load; UNMEASURED, not passing")
class EntriesThatAreNotNamesAreKeptAside(unittest.TestCase):

    def test_they_are_copied_aside_before_the_load_writes_owned_and_the_vault_says_where(self):
        o = _run()
        self.assertEqual(o["receipt"]["notNames"], NOT_NAMES)
        self.assertTrue(o["receipt"]["asideAt"] and "d2r_quarantine~d2r_owned~not-names~" in o["receipt"]["asideAt"],
                        "the entries were not kept aside anywhere: %r" % o["receipt"])
        self.assertEqual(json.loads(o["aside"]), NOT_NAMES, "the slot aside does not hold the exact entries")
        self.assertEqual(json.loads(o["stored"]), ["Grief", "Harlequin Crest"], "PREMISE: the saved list still holds non-names")
        self.assertIn(o["receipt"]["asideAt"], o["line"], "the Vault does not say where they are kept")
        self.assertIn("set aside on this load, kept as", o["line"])
        self.assertIsNone(o["q"], "a load that kept them aside held the store")
        self.assertEqual(o["slots"], 1)
        self.assertEqual(o["slotsAfterReload"], 1, "a reload wrote a second copy of the same entries")

    def test_when_they_cannot_be_copied_aside_they_stay_in_the_saved_list_and_nothing_writes_over_it(self):
        o = _run(full=True)
        self.assertIsNone(o["receipt"]["asideAt"], "PREMISE: the full storage let the aside write through")
        self.assertEqual(o["stored"], OWNED, "the entries were deleted from the saved list with no copy anywhere")
        self.assertEqual(sorted(o["memory"]), ["Grief", "Harlequin Crest"], "memory holds a non-name the page reads as a name")
        self.assertIsNotNone(o["q"], "the saved list is not protected - the next persist() drops the entries")
        self.assertIn("not item names", o["q"]["reason"])
        self.assertIn("could not be copied aside", o["line"], "the Vault overclaims 'set aside' for entries it could not keep")
        self.assertNotIn("kept as", o["line"])


RED_PROOF = [
    {"why": "REG-2527 - 'set aside' is a delete again: the entries are never copied anywhere before persist() drops them",
     "file": "bible.html", "matches": 1,
     "find": "      if (_naDoor.getItem(_naKey) !== _naRaw) _naDoor.setItem(_naKey, _naRaw);\n",
     "replace": ""},
    {"why": "REG-2527 - entries that could not be copied aside are dropped from the saved list by the next persist()",
     "file": "bible.html", "matches": 1,
     "find": "      try { if (typeof LS.quarantine === 'function')\n              LS.quarantine('d2r_owned', 'holds '",
     "replace": "      try { if (false)\n              LS.quarantine('d2r_owned', 'holds '"},
    {"why": "REG-2527 - the Vault says 'set aside' for entries it could not keep",
     "file": "bible.html", "matches": 1,
     "find": "         + ((R && R.asideAt) ? ' and '",
     "replace": "         + (true ? ' and '"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
