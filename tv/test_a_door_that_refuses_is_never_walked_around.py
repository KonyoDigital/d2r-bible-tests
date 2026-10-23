# -*- coding: utf-8 -*-
"""V1 MERGE JOIN (V1a's Magic & Rare toss x V1b's held witness store) - A DOOR THAT SAID NO IS NEVER WALKED AROUND.

Two tracks of the V1 vault batch were each right on their own and wrong together:
  * V1a (REG-2404): the ✕ on a MAGIC & RARE row (window.vaultThrowFind) takes the record out, then takes the owned name
    out through the removal door (vaultRemove: dated, journaled, undoable; the batch carries the record so the undo is
    whole). If the door "is not there or took nothing", a fallback still takes the name out, on record.
  * V1b (REG-2415): while the witness store (d2r_vaultProv) will not read - quarantined at the door - vaultRemove
    REFUSES, in words, any removal that takes a filing, because it can neither carry nor drop the witness rows.
Merged, the refusal looked like "took nothing": the ✕ deleted the Magic & Rare record, the fallback deleted the owned
name with no journal row, and persistOwned wrote that - his keeper gone, with no batch an undo could reach, exactly while
the board says the vault is held. Neither branch alone did it.

NOW the toss waits with the door: the record goes back, the name stays owned, nothing is journaled, and the refusal is
said. With the witness store readable the same toss still goes through the door (the premise case), so this law can
never pass on a harness that does not remove at all.

WHAT IS DRIVEN: the store door window.LSR, the boot loaders and the vault module's head with its whole ⟦#246 VAULTFILE⟧
block (tv/store_door_harness.py vault_page: the witness store is quarantined by the shipped _provAll as the module
loads), the shipped removal journal and window.vaultRemove, and the shipped window.vaultThrowFind - all cut from
bible.html, in node. The per-name removal note is a recorder (it is not what this law asks).
RED_PROOF below. A missing node is the only skip; a node that fails is a failure.
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

import store_door_harness as D  # noqa: E402

#: his witness store cut short mid-write (REG-2415's r1 bytes): it will not parse, so the door quarantines it
CORRUPT_PROV = ('{"Grief":{"mule":"uni-weap","source":"hand","by":"hand","at":"2026-10-01","where":"the vault manager"},'
                '"Shako":{"mule":"uni-armor","source":"stash","looks":[{"id":"s1","frame":"f9","conf":0.93}')
RECORD = '{"q":"rare","base":"Ring","mods":["+1 to All Skills"]}'
OWNED = '["Grief","Death Loop","Harlequin Crest (Shako)"]'


def _seed(prov):
    return {"d2r_owned": OWNED, "d2r_muleAssign": '{"Grief":"uni-weap"}', "d2r_vaultProv": prov,
            "d2r_magicFinds": '{"Death Loop":' + RECORD + '}'}


def _pieces(s):
    extra = ("var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
             + D.between(s, "  function _vrRead(){", "  /* the heart and the console read the journal through here", keep_b=False)
             + D.between(s, "  window.vaultRemove = function(names, opts){", "  /* The reverse of exactly one batch", keep_b=False)
             + D.window_fn(s, "vaultThrowFind") + "\n")
    notes = "var NOTES = []; window._vaultRemovalNote = function(b){ NOTES.push(b); return 1; };\n"
    return notes + D.vault_page(s, extra)


BODY = r"""
OUT.heldBefore = (typeof window._vaultProvHeld === 'function') ? window._vaultProvHeld() : 'NO DOOR';
window.vaultThrowFind('Death Loop');                       /* his ✕ on the MAGIC & RARE row */
OUT.owned = owned.has('Death Loop');
OUT.record = Object.prototype.hasOwnProperty.call(magicFinds, 'Death Loop') ? magicFinds['Death Loop'] : null;
OUT.journal = RAW['d2r_vaultRemoved'] == null ? null : JSON.parse(RAW['d2r_vaultRemoved']);
OUT.notes = NOTES.length;
OUT.storedOwned = JSON.parse(RAW['d2r_owned']);
OUT.prov = RAW['d2r_vaultProv'];
OUT.status = STATUS.slice();
"""


def _run(prov):
    s = D.src()
    return D.page(_pieces(s), BODY, seed=_seed(prov))


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED vault doors; UNMEASURED, not passing")
class ADoorThatRefusesIsNeverWalkedAround(unittest.TestCase):

    def test_the_magic_and_rare_toss_waits_while_the_removal_door_refuses(self):
        o = _run(CORRUPT_PROV)
        self.assertTrue(o["heldBefore"] and "d2r_vaultProv" in o["heldBefore"],
                        "PREMISE: the shipped door did not hold the witness store that will not parse: %r" % o["heldBefore"])
        self.assertTrue(o["owned"], "the ✕ took the keeper out of owned although the removal door refused - no journal, "
                                    "no undo (the fallback walked around the door)")
        self.assertEqual(o["record"], {"q": "rare", "base": "Ring", "mods": ["+1 to All Skills"]},
                         "the ✕ dropped the Magic & Rare record while the removal it belongs to was refused")
        self.assertIsNone(o["journal"], "a refused removal wrote a journal batch: %r" % (o["journal"],))
        self.assertEqual(o["notes"], 0, "a refused removal left a per-name removal note (his word on record for a "
                                        "removal that never happened)")
        self.assertIn("Death Loop", o["storedOwned"], "the stored owned list lost the keeper")
        self.assertEqual(o["prov"], CORRUPT_PROV, "the witness store's bytes were written over")
        said = " | ".join(o["status"])
        self.assertIn("was not thrown out of Magic & Rare", said, "the refusal was not said: %r" % o["status"])
        self.assertIn("d2r_vaultProv", said, "the refusal does not name the store that holds it: %r" % o["status"])

    def test_with_the_witness_store_readable_the_toss_goes_through_the_door(self):
        o = _run("{}")
        self.assertIsNone(o["heldBefore"], "PREMISE: a witness store that reads held the vault: %r" % o["heldBefore"])
        self.assertFalse(o["owned"], "the toss no longer takes the keeper out of owned - the law's premise is gone")
        self.assertIsNone(o["record"])
        self.assertIsNotNone(o["journal"], "the toss did not go through the removal door")
        self.assertEqual([(b.get("lane"), b.get("names"), b.get("magic")) for b in o["journal"]],
                         [("card-click", ["Death Loop"], {"Death Loop": {"q": "rare", "base": "Ring", "mods": ["+1 to All Skills"]}})],
                         "the toss's batch does not carry the keeper whole")
        self.assertNotIn("Death Loop", o["storedOwned"])


RED_PROOF = [
    {"why": "V1 merge join - the toss falls back over the removal door's refusal again (owned name gone, no journal)",
     "file": "bible.html", "matches": 1,
     "find": "    if (nm && r && r.refused){\n",
     "replace": "    if (false){\n"},
    {"why": "V1 merge join - a refused toss keeps the owned name but drops the Magic & Rare record",
     "file": "bible.html", "matches": 1,
     "find": "      try { if (rec != null && !Object.prototype.hasOwnProperty.call(magicFinds, nm)) magicFinds[nm] = rec; } catch(e){}\n",
     "replace": ""},
    {"why": "V1 merge join - a refused toss is silent (no word on the status line)",
     "file": "bible.html", "matches": 1,
     "find": "      status('⚠ \"' + name + '\" was not thrown out of Magic & Rare - ' + (r.why || 'the removal door refused'));\n",
     "replace": ""},
    {"why": "V1 merge join - the removal door no longer refuses while the witness store is held (its REG-2415 wait and the REG-2521 held wait behind it, which asks the witness store as part of the basis), so the toss takes the "
            "keeper and the filing it cannot carry",
     "file": "bible.html", "matches": 1,
     "find": "    if (_whyRm){\n      if (!opts.quiet) status('⚠ nothing removed - ' + _whyRm);\n      return { requested: req.length, removed: [], skipped: [], ts: null, batch: null, refused: 'prov-unreadable', why: _whyRm };\n    }\n    /* REG-2521 — THE REMOVAL DOOR WAITS WHILE A STORE IT WRITES IS UNKNOWN OR HELD: owned, the journal and its per-name\n       record always, and - when it takes a filing - the mule map and what it is judged against (VAULT_BASIS). A journal\n       that will not read is the plainest case: the removal could never be undone. Said even for a quiet caller, because\n       a refusal nobody sees is the silent loss this door exists to prevent. */\n    var _hRm = (typeof window._vaultRemovalHeld === 'function') ? window._vaultRemovalHeld(!opts.keepFiling) : null;\n    var _logRm = _vrRead();\n    if (!_hRm && _logRm === null)\n      _hRm = { keys: [_VR_LOG], why: 'the removal journal (' + _VR_LOG + ') would not read, and nothing is written over it' };\n    if (_hRm){",
     "replace": "    if (false){\n      if (!opts.quiet) status('⚠ nothing removed - ' + _whyRm);\n      return { requested: req.length, removed: [], skipped: [], ts: null, batch: null, refused: 'prov-unreadable', why: _whyRm };\n    }\n    /* REG-2521 — THE REMOVAL DOOR WAITS WHILE A STORE IT WRITES IS UNKNOWN OR HELD: owned, the journal and its per-name\n       record always, and - when it takes a filing - the mule map and what it is judged against (VAULT_BASIS). A journal\n       that will not read is the plainest case: the removal could never be undone. Said even for a quiet caller, because\n       a refusal nobody sees is the silent loss this door exists to prevent. */\n    var _hRm = (typeof window._vaultRemovalHeld === 'function') ? window._vaultRemovalHeld(!opts.keepFiling) : null;\n    var _logRm = _vrRead();\n    if (!_hRm && _logRm === null)\n      _hRm = { keys: [_VR_LOG], why: 'the removal journal (' + _VR_LOG + ') would not read, and nothing is written over it' };\n    if (false){"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
