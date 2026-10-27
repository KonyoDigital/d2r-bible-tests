# -*- coding: utf-8 -*-
"""THE VAULT'S DOORS TAKE ONLY WHAT IS HIS, UNDER ONE NAME (GrokBot's vault sweeps, board #144 #148 #152 #154).

Each item below was reproduced on the whole page in node at v3812 (a read-only agent's probes) and is driven here the
same way, through the real doors on a fresh board:
  - #152.1 the Shared-stash switch never moved an item: its witness said at: Date.now() and the check reads Date.parse,
    so every tick was refused "is not a date"; a refused filing also kept the override.
  - #144.1+8 ghost items: Minor Healing Potion, Jewel, Grand Charm, Khalim's Eye, Ber Rune, Diablo's Horn each added as
    owned through + Add an item (every catalogue row was a "base"). Monarch / Ethereal Monarch / Eth Thresher still add.
  - #148.2 case variants: Grief + GRIEF + grief were three owned names; SHAKO + Shako two.
  - #144.12 "Nightwings Veil" (no apostrophe) was refused.
  - #148.4 assigning a name he does not own filed it AND made it owned.
  - #154.14 a blank mule name and a second mule with an existing name were accepted.
  - #148.3 "Spirit" in Multi-copy Keepers added Spirit Forge (the first name that began that way).
  - #154.16 FIND: "tal rashas" found nothing; a hand-added Shako was not in FIND's pool.
RED_PROOF below.
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
localStorage.setItem('d2r_owned', JSON.stringify([]));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""

BODY = r"""
(function(){
var W = window;
function add(n){ var r = W.vaultHandAdd(n); return r ? { ok: !!r.ok, name: r.name || null, refused: r.refused || null } : null; }
OUT.ghost = ['Minor Healing Potion', 'Jewel', 'Grand Charm', "Khalim's Eye", 'Ber Rune', "Diablo's Horn"].map(add);
OUT.bases = ['Monarch', 'Ethereal Monarch', 'eth thresher'].map(add);
OUT.cases = ['Grief', 'GRIEF', 'grief', 'SHAKO', 'Shako'].map(add);
OUT.apos = ['Nightwings Veil', 'Halaberds Reign'].map(add);
OUT.owned = Array.from(owned).sort();
OUT.assign = W.vaultAssign('Never Owned Thing', 'runewords') || null;
OUT.ownedAfterAssign = owned.has('Never Owned Thing');
function amap(){ try { return JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}') || {}; } catch (e) { return {}; } }
OUT.assignMap = !!amap()['Never Owned Thing'];
var _ros = W._vaultRosterNow() || [];
var taken = _ros[0] ? _ros[0].name : null;
OUT.taken = taken;
OUT.mules = ['   ', taken ? taken.toLowerCase() : 'x', 'NEWMULE'].map(function(n){ var v = W._vmNameOk(n, null); return { ok: v.ok, why: v.why || '' }; });
OUT.spirit = W._resolveGrailName('Spirit');
OUT.exact = W._resolveGrailName('Spirit Forge');
OUT.find = W._vaultFindMatches(["Tal Rasha's Horadric Crest", 'Harlequin Crest'], 'tal rashas');
OUT.handPool = (typeof _vaultHandBasePool === 'function') ? _vaultHandBasePool() : null;
/* #152.1 - the Shared switch on an item he owns */
add('The Stone of Jordan');
var errs = [];
var st = document.getElementById('vault-status');
W.vaultShareToggle('The Stone of Jordan', true);
OUT.shared = amap()['The Stone of Jordan'] || null;
OUT.sharedSay = st ? String(st.textContent || '') : null;
/* a refused filing puts the old override back */
var realFile = W.vaultFile;
W.vaultFile = function(){ return { ok: false, refused: 'locked', why: 'locked to your MAIN (the law)' }; };
var before = JSON.stringify(W._shareOverride('The Stone of Jordan'));
W.vaultShareToggle('The Stone of Jordan', false);
OUT.ovKept = JSON.stringify(W._shareOverride('The Stone of Jordan')) === before;
W.vaultFile = realFile;
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheVaultDoorsTakeOnlyWhatIsHis(unittest.TestCase):

    def test_the_page_booted(self):
        self.assertEqual(page()["__boot"]["errors"], [], page()["__boot"])

    def test_a_ghost_item_is_not_a_base(self):
        o = page()
        for r in o["ghost"]:
            self.assertFalse(r["ok"], "a ghost item was added as owned (#144.1+8): %r" % r)
            self.assertEqual(r["refused"], "not-drawn", r)
        self.assertEqual([r["name"] for r in o["bases"]], ["Monarch", "Ethereal Monarch", "Eth Thresher"], o["bases"])
        self.assertTrue(all(r["ok"] for r in o["bases"]), "PREMISE: a real base no longer adds: %r" % o["bases"])
        for g in ("Minor Healing Potion", "Jewel", "Grand Charm", "Ber Rune"):
            self.assertNotIn(g, o["owned"])

    def test_one_item_is_one_owned_name(self):
        o = page()
        self.assertEqual([r["name"] for r in o["cases"]], ["Grief", "Grief", "Grief", "Shako", "Shako"], o["cases"])
        for v in ("GRIEF", "grief", "SHAKO"):
            self.assertNotIn(v, o["owned"], "a case variant became its own owned name (#148.2): %r" % o["owned"])

    def test_a_name_typed_without_its_apostrophe_is_found(self):
        o = page()
        self.assertEqual([r["name"] for r in o["apos"]], ["Nightwing's Veil", "Halaberd's Reign"], o["apos"])

    def test_assigning_a_name_he_does_not_own_writes_nothing(self):
        o = page()
        self.assertEqual(o["assign"], {"ok": False, "refused": "not-owned"}, o)
        self.assertFalse(o["ownedAfterAssign"], "assigning made an item he never had owned (#148.4)")
        self.assertFalse(o["assignMap"], "assigning filed an item he does not own")

    def test_a_mule_name_is_never_blank_or_taken(self):
        o = page()
        self.assertIsNotNone(o["taken"], "PREMISE: the board has no mule")
        self.assertFalse(o["mules"][0]["ok"], "a blank mule name was accepted (#154.14)")
        self.assertFalse(o["mules"][1]["ok"], "a second mule named %s was accepted (#154.14)" % o["taken"])
        self.assertIn("already", o["mules"][1]["why"])
        self.assertTrue(o["mules"][2]["ok"])

    def test_a_beginning_names_an_item_only_when_one_item_begins_that_way(self):
        o = page()
        self.assertIsNone(o["spirit"], "'Spirit' was resolved to %r (#148.3)" % o["spirit"])
        self.assertEqual(o["exact"], "Spirit Forge", "PREMISE: an exact name no longer resolves")

    def test_find_without_apostrophes_and_finds_a_hand_added_base(self):
        o = page()
        self.assertEqual(o["find"], ["Tal Rasha's Horadric Crest"], "'tal rashas' found %r (#154.16)" % o["find"])
        self.assertIn("Shako", o["handPool"] or [], "PREMISE: the hand-added Shako is not in the hand-base pool")

    def test_the_shared_switch_moves_the_item_and_a_refusal_keeps_the_old_choice(self):
        o = page()
        self.assertEqual(o["shared"], "shared", "the Shared switch did not move the item (#152.1): %r" % o.get("sharedSay"))
        self.assertNotIn("not a date", o["sharedSay"] or "")
        self.assertTrue(o["ovKept"], "a refused filing kept the new override (#152.1)")


RED_PROOF = [
    {"why": "#144.1+8 - every catalogue row is a hand-add base again (potions, jewels, runes, quest items)",
     "file": "bible.html", "find": "  function _vaultHandGear(r){ return r[21] !== 'm' && r[1] !== 'tpot' && r[20] !== 0; }\n",
     "replace": "  function _vaultHandGear(r){ return true; }\n", "matches": 1, "needs": "node"},
    {"why": "#148.2 - a typed base keeps its own case, so SHAKO and Shako are two owned names again",
     "file": "bible.html",
     "find": "    if (!_vaultKeeps(r.name)) { var _hb = _vaultHandBase(r.name); if (_hb) r = { ok: true, name: _vaultHandBaseName(r.name, _hb) }; }\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#148.2 - a runeword keeps its typed case, so GRIEF and Grief are two owned names again",
     "file": "bible.html",
     "find": "          if (_rw && String(_rw).toLowerCase() === String(r.name).toLowerCase()) r = { ok: true, name: String(_rw) }; } catch (eRw) {}\n",
     "replace": "          void _rw; } catch (eRw) {}\n", "matches": 1, "needs": "node"},
    {"why": "#144.12 - a name typed without its apostrophe is refused again",
     "file": "bible.html",
     "find": "    function k(x){ return String(x == null ? '' : x).trim().toLowerCase().replace(/[\\u2018\\u2019`']/g, '').replace(/^the\\s+/, ''); }\n",
     "replace": "    function k(x){ return String(x == null ? '' : x).trim().toLowerCase().replace(/[\\u2018\\u2019`]/g, \"'\").replace(/^the\\s+/, ''); }\n",
     "matches": 1, "needs": "node"},
    {"why": "#148.4 - assigning a name he does not own files it and owns it again",
     "file": "bible.html", "find": "    if (!(typeof owned !== 'undefined' && owned && owned.has(name))){\n      try { _vaultLockSay(name,",
     "replace": "    if (false){\n      try { _vaultLockSay(name,", "matches": 1, "needs": "node"},
    {"why": "#154.14 - a second mule may take a name another mule has again",
     "file": "bible.html", "find": "    if (clash) return { ok: false, why: 'another mule is already called ' + v + ' - nothing was changed' };\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#148.3 - the first item that begins with the text wins again ('Spirit' -> Spirit Forge)",
     "file": "bible.html", "find": "    return pref.length === 1 ? pref[0] : null;\n  }\n  try { window._resolveGrailName",
     "replace": "    return pref[0] || null;\n  }\n  try { window._resolveGrailName", "matches": 1, "needs": "node"},
    {"why": "#154.16 - FIND keeps the apostrophe again, so 'tal rashas' finds nothing",
     "file": "bible.html", "find": "  function _vfKey(x){ return _vfNorm(x).replace(/'/g, ''); }\n",
     "replace": "  function _vfKey(x){ return _vfNorm(x); }\n", "matches": 1, "needs": "node"},
    {"why": "#152.1 - the Shared switch's witness is a number again and every tick is refused 'is not a date'",
     "file": "bible.html", "find": "        var w = { by:'hand', at: new Date().toISOString(), where:'Shared-stash switch — your click' };\n",
     "replace": "        var w = { by:'hand', at: Date.now(), where:'Shared-stash switch — your click' };\n", "matches": 1, "needs": "node"},
    {"why": "#152.1 - a refused Shared filing keeps the new override again",
     "file": "bible.html", "find": "        if (r && !r.ok){ _setShareOverride(name, _ov0); var st",
     "replace": "        if (r && !r.ok){ var st", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
