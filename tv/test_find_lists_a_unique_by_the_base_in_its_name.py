# -*- coding: utf-8 -*-
"""REG-2958 (#154.16 follow-up) - FIND "shako" LISTS HARLEQUIN CREST (SHAKO) BESIDE THE SHAKO BASES.

A unique's vault name carries its base in brackets ("Harlequin Crest (Shako)", the register's one name, v792 / REG-2897).
FIND matches on that name, so "shako" lists the unique beside a white Shako base he typed, the base first (an exact
match ranks ahead of a whole-word one). A name he owns under a bare spelling written before the one name ("Harlequin
Crest") is matched by its vault name too. Measured before the fix on the whole page in node: FIND "shako" over a bare
"Harlequin Crest" and a hand-added Shako listed the base only.

It is a SEARCH match, never a resolution: the row shows the name he owns, nothing is owned or filed by a search, and the
hand door's question for a bare "Shako" (REG-2858: the unique or the base?) is exactly as it was.

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


def _seed(owned):
    return ("localStorage.setItem('d2r_ownerClaim', '*');\n"
            "localStorage.setItem('d2r_owned', %s);\n") % json.dumps(json.dumps(owned))


BODY = r"""
(function(){
var W = window;
OUT.base = (function(r){ return r && [r.ok, r.mode || r.refused || '', r.name || '']; })(W.vaultHandAdd('Shako', null, { kind: 'base' }));
var pool = Array.from(owned);
(W._vaultHandBasePool ? W._vaultHandBasePool() : []).forEach(function(n){ if (pool.indexOf(n) < 0) pool.push(n); });
OUT.pool = pool.slice().sort();
OUT.m = {};
['shako', 'SHAKO', 'crest', 'jordan'].forEach(function(q){ OUT.m[q] = W._vaultFindMatches(pool, q); });
var before = Array.from(owned).sort().join('|');
var res = document.getElementById('vault-find-results');
W.vaultFind('shako');
OUT.shown = res ? String(res.textContent || '') : null;
OUT.ownedSame = Array.from(owned).sort().join('|') === before;
var bare = W.vaultHandAdd('Shako', null, {});
OUT.ask = bare ? [bare.ok, bare.refused || bare.mode || '', String(bare.why || '')] : null;
})();
"""


def _run(owned):
    out = VPN.run(BODY, prelude=_seed(owned), timeout=300)
    errs = (out.get("__boot") or {}).get("errors") or []
    if errs:
        raise AssertionError("the page did not boot clean in node: %r" % errs[:3])
    return out


_OUT = {}


def measured(which):
    if which not in _OUT:
        _OUT[which] = _run({"vault": ["Harlequin Crest (Shako)", "The Stone of Jordan"],
                            "bare": ["Harlequin Crest", "The Stone of Jordan"]}[which])
    return _OUT[which]


class FindListsAUniqueByTheBaseInItsName(unittest.TestCase):

    def test_shako_lists_the_unique_beside_the_base_base_first(self):
        o = measured("vault")
        self.assertEqual(o["base"][:2], [True, "added"], "the setup needs a white Shako he typed: %r" % o["base"])
        self.assertEqual(o["m"]["shako"], ["Shako", "Harlequin Crest (Shako)"], o["m"])
        self.assertEqual(o["m"]["SHAKO"], o["m"]["shako"])
        self.assertIn("2 matches", o["shown"] or "", "the FIND panel does not list both: %r" % o["shown"])
        self.assertIn("Harlequin Crest (Shako)", o["shown"])

    def test_a_bare_spelling_he_owns_is_matched_by_its_vault_name(self):
        o = measured("bare")
        self.assertIn("Harlequin Crest", o["pool"], "the setup needs the bare spelling in the pool: %r" % o["pool"])
        self.assertEqual(o["m"]["shako"], ["Shako", "Harlequin Crest"],
                         "FIND 'shako' missed the unique owned under its bare spelling: %r" % o["m"])
        self.assertEqual(o["m"]["crest"], ["Harlequin Crest"])

    def test_it_matches_and_never_resolves(self):
        for which in ("vault", "bare"):
            o = measured(which)
            self.assertEqual(o["m"]["jordan"], ["The Stone of Jordan"], "%s: an unrelated name moved: %r" % (which, o["m"]))
            self.assertNotIn("The Stone of Jordan", o["m"]["shako"])
            self.assertTrue(o["ownedSame"], "%s: a search changed what he owns" % which)
            self.assertFalse(o["ask"][0], "%s: the hand door took a bare Shako without asking: %r" % (which, o["ask"]))
            self.assertEqual(o["ask"][1], "ambiguous", "%s: the hand door's question for a bare Shako changed: %r" % (which, o["ask"]))
            self.assertIn("Harlequin Crest", o["ask"][2])


RED_PROOF = [
    {"why": "REG-2958 - FIND reads only the name he owns, so a bare spelling is never matched by its vault name",
     "file": "bible.html",
     "find": "    function keys(n){ var a = _vfKey(n), b = _vfVaultKey(n); return b ? [a, b] : [a]; }\n",
     "replace": "    function keys(n){ return [_vfKey(n)]; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2958 - the match stops at a name's beginning, so the base in a unique's brackets lists nothing",
     "file": "bible.html",
     "find": "    return pool.filter(function(n){ return keys(n).some(function(k){ return k.indexOf(qa) !== -1; }); })\n",
     "replace": "    return pool.filter(function(n){ return keys(n).some(function(k){ return k.indexOf(qa) === 0; }); })\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2958 - the rank is lost, so the unique sorts ahead of the base he typed",
     "file": "bible.html",
     "find": "    function score(n){ return Math.min.apply(null, keys(n).map(rank)); }\n",
     "replace": "    function score(n){ return 3; }\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
