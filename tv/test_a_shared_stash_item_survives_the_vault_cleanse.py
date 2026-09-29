# -*- coding: utf-8 -*-
"""REG-1280 (#165) — A SHARED-STASH ITEM SURVIVES THE VAULT CLEANSE.

The seed floor's "one-time vault cleanse" (v677) deletes every _GRAIL_SEED / _UNI_EXTRA name that sits in `owned` with
no mule filing - the residue the v659-v676 floors left when they wrote ledger names into the physical vault. A
shared-stash item is never filed to a mule: the shared stash has no mule, and tvVaultRegister('Bone Break') answers
mule:null ("unsorted") by design. Bone Break is also a _GRAIL_SEED name, so the cleanse deleted it on the next load.

MEASURED on a real page (fresh floored board, automation world): registered Bone Break and Black Cleft, reloaded - Bone
Break gone, Black Cleft (no seed name) kept. After the fix both survive. Found because v2208's reload case went red the
moment REG-1275 let the floor run on a fresh board.

⚠ H1 (review of bd976210) MOVED THE CLEANSE. It ran on every load as a bare statement in the grail floor; it is
window._seedCleanse now (the ⟦OWNED PROV⟧ door), armed by the floor and run once per world at load, taking only true
residue and journaling every removal (test_carried_loot_keeps_its_order drives that whole path). This law keeps its own
job on the new door, with the SHIPPED keep pattern handed over exactly as the floor hands it:

  · DRIVEN (node, the shipped door cut from bible.html by its markers, the shipped _SHARED_KEEP): an unfiled
    shared-stash seed name is KEPT; an unfiled plain seed name with no receipt is still STRIPPED (the cleanse keeps its
    job); a filed seed name is kept; a name in no seed is untouched.
RED_PROOF below.
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
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import test_every_owned_door_writes_provenance as P  # noqa: E402 — the ONE harness for the owned door

NODE = shutil.which("node")

PROG = r"""
var window = globalThis, STORE = {}, REMOVED = [];
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
               setItem: function(k, v){ STORE[k] = String(v); }, removeItem: function(k){ delete STORE[k]; } };
window.D2R_BUILD = { id: 'vTEST' }; window.D2R_PROFILE = 'main';
console.info = function(){};
var owned = new Set(%(owned)s);
%(lanes)s
%(furn)s
%(region)s
window._laneLockWhy = function(){ return null; };
window.vaultRemove = function(names, opts){
  var took = []; names.forEach(function(n){ if (owned.has(n)){ owned['delete'](n); took.push(n); } });
  REMOVED.push({ names: took, lane: opts && opts.lane }); return { removed: took, ts: 1 };
};
STORE['d2r_muleAssign'] = JSON.stringify(%(filed)s);
var _GRAIL_SEED = { 'Bone Break': 'Jul 1', 'Harlequin Crest': 'Jul 2', 'Crown of Ages': 'Jul 3' };
var r = window._seedCleanse({ names: Object.keys(_GRAIL_SEED), keep: %(keep)s, seed: _GRAIL_SEED, mainLedger: 'absent' });
process.stdout.write(JSON.stringify({ owned: Array.from(owned).sort(), r: r, removed: REMOVED }));
"""


def _bible():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as f:
        return f.read()


def _keep(src):
    m = re.search(r"var _SHARED_KEEP = (/.+?/i);", src)
    assert m, "the shipped _SHARED_KEEP regex is gone"
    return m.group(1)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ASharedStashItemSurvivesTheVaultCleanse(unittest.TestCase):

    def test_the_floor_hands_the_cleanse_the_shipped_keep_pattern(self):
        """The join: the grail floor arms the door WITH _SHARED_KEEP — a door with the rule, never handed it, keeps
        nothing."""
        s = _bible()
        self.assertEqual(1, s.count("keep: _SHARED_KEEP, seed: _GRAIL_SEED });"),
                         "the grail floor no longer hands the shared-stash pattern to the seed cleanse")

    def _run(self, owned, filed):
        s = _bible()
        out = P._node(PROG % {"owned": json.dumps(owned), "filed": json.dumps(filed), "keep": _keep(s),
                              "lanes": P._lanes(s), "furn": P._between(s, P.FURN_FROM, P.FURN_TO),
                              "region": P.owned_prov_region(s)}, "cleanse")
        self.assertTrue(out["r"].get("ran"), "the cleanse refused to run — UNKNOWN, not passing: %r" % out["r"])
        return out["owned"]

    def test_an_unfiled_shared_stash_seed_name_is_kept(self):
        self.assertIn("Bone Break", self._run(["Bone Break"], {}),
                      "a registered sunder charm (never filed - the shared stash has no mule) was deleted on load")

    def test_floor_residue_is_still_stripped(self):
        self.assertNotIn("Harlequin Crest", self._run(["Harlequin Crest", "Bone Break"], {}),
                         "the cleanse no longer strips an unfiled plain seed name - it stopped doing its job")

    def test_a_filed_seed_name_and_a_name_in_no_seed_are_kept(self):
        got = self._run(["Crown of Ages", "Black Cleft"], {"Crown of Ages": "uni-armor"})
        self.assertEqual(got, ["Black Cleft", "Crown of Ages"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1280 - the cleanse forgets the shared stash again: a registered Bone Break is deleted on the next load",
        "file": "bible.html",
        "find": "      if (keep && keep.test(nm)){ spared[nm] = 'the shared stash (never muled)'; return; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1280 - the grail floor stops handing the shared-stash pattern to the cleanse",
        "file": "bible.html",
        "find": "keep: _SHARED_KEEP, seed: _GRAIL_SEED });",
        "replace": "keep: null, seed: _GRAIL_SEED });",
        "matches": 1,
    },
]
