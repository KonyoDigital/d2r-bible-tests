# -*- coding: utf-8 -*-
"""REG-2901 (#149.2, GrokBot's GB-L Advanced-drawer pass, ACT 2) - HIS KEEPER DESTINATION IS A HOME THE ROUTER ANSWERS.

GrokBot's audit: "the router never reads it" - no multiKeep in suggestMule or in the war cap / overflow. A keeper's dest
(REG-2900) now routes every copy, and the order is hand > keeper dest > router:

  * Auto      - today's rules, untouched (the Shako's rule home and its war-stash cap of 1);
  * Shared    - the shared stash, every copy he keeps on its pages (the one-big-copy cap is lifted for it);
  * WAR       - the WAR mules: the shared stash's home with a cap of 0, so every copy overflows to WAR1, then WAR2;
  * Mule <id> - that mule by its stable id, ahead of every category rule (a runeword's own rule included);
  * a mule this board does not have is a stated refusal - Unsorted with the reason naming it - never another mule;
  * a filing his HAND made keeps its home: the dest does not re-home it and does not change its cap;
  * a filing the BOARD made is re-homed by the dest - off a mule onto the shared stash with every copy (no extra copy
    returns to the mule it was filed on), and off the shared stash onto the mule he chose;
  * only a keeper has a destination (a stale dest on a want of 1 routes nothing); a set piece is found by its canon;
  * his share switch's default stays the rules' answer, so a switch he sets beside a keeper dest is stored, not dropped.

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

OWNED = ["Harlequin Crest", "Gore Rider", "Grief", "Stormshield", "Skin of the Vipermagi", "Nagelring",
         "Natalya's Totem (helm)"]
SEED = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
        "localStorage.setItem('d2r_owned', %s);\n"
        "localStorage.setItem('d2r_copies', %s);\n"
        "localStorage.setItem('d2r_multiKeep', %s);\n") % (
    json.dumps(json.dumps(OWNED)),
    json.dumps(json.dumps({"Harlequin Crest": 3, "Gore Rider": 2, "Grief": 2, "Skin of the Vipermagi": 2})),
    json.dumps(json.dumps({"Harlequin Crest": 3, "Gore Rider": 2, "Grief": 2, "Stormshield": 2, "Skin of the Vipermagi": 2,
                           "Nagelring": {"want": 1, "dest": "war"}})))

BODY = r"""
(function(){
var W = window, HC = 'Harlequin Crest';
function add(nm){ var t = Date.now(); while (Date.now() === t) {} W.prompt = function(){ return nm; }; W.vaultAddMule(); }
add('WAR1'); add('ALT ONE');
var R = W._vaultRosterNow(), ALT = R.filter(function(m){ return m.name === 'ALT ONE'; })[0].id;
OUT.alt = ALT;
function sg(n){ var s = W.suggestMule(n); return s ? { id: s.id, unsorted: !!s.unsorted, dest: s.keeperDest || null, why: s.why || '' } : null; }
function cap(n){ W._warCapCache = null; var c = W._vaultWarCap(n); return (c === Infinity) ? 'all' : c; }
function homes(n, k){ var o = []; for (var i = 0; i < k; i++){ var h = W._vaultMoveHome(n, i); o.push([h.id, !!h.over]); } return o; }
function dest(n, d){ _mkSetDest(n, d); W._warCapCache = null; W._warOverCache = null; W._movePackCache = null; W._warKeepBag = null; }
var D2S = { source: 'd2s', file: 'fixture.d2s', char: 'Sorc', verify: { ok: true } };
/* Auto */
OUT.auto = sg(HC); OUT.autoCap = cap(HC);
/* Shared, WAR, a mule, a mule this board does not have */
dest(HC, 'shared'); OUT.shared = sg(HC); OUT.sharedCap = cap(HC); OUT.sharedHomes = homes(HC, 3);
dest(HC, 'war'); OUT.war = sg(HC); OUT.warCap = cap(HC); OUT.warHomes = homes(HC, 3);
dest(HC, 'mule:' + ALT); OUT.mule = sg(HC); OUT.muleHome = homes(HC, 1);
dest(HC, 'mule:ghost-mule'); OUT.ghost = sg(HC); OUT.ghostHome = homes(HC, 1);
/* ahead of a category rule */
OUT.griefAuto = sg('Grief'); dest('Grief', 'mule:uni-small'); OUT.grief = sg('Grief');
/* his hand: Stormshield filed by his hand on UNI-ARMOR (its rule home too), then a dest */
var hf = W.vaultFile('Stormshield', { by: 'hand', at: new Date().toISOString(), where: 'a drag onto UNI-ARMOR' }, { mule: 'uni-armor' });
OUT.handFiled = !!(hf && hf.ok) && W._vaultFiledByHand('Stormshield');
OUT.handAutoCap = cap('Stormshield');
dest('Stormshield', 'mule:' + ALT); OUT.handSg = sg('Stormshield'); OUT.handMis = W._vaultMisfiled('Stormshield'); OUT.handHome = homes('Stormshield', 1);
dest('Stormshield', 'war'); OUT.handWarCap = cap('Stormshield');
/* the board's filings: Gore Rider on UNI-ARMOR, the Vipermagi on the shared stash (a save-file witness) */
var b1 = W.vaultFile('Gore Rider', D2S), b2 = W.vaultFile('Skin of the Vipermagi', D2S);
OUT.boardFiled = [b1 && b1.ok && W._vaultFiledOn('Gore Rider'), b2 && b2.ok && W._vaultFiledOn('Skin of the Vipermagi'),
                  W._vaultFiledByHand('Gore Rider'), W._vaultFiledByHand('Skin of the Vipermagi')];
dest('Gore Rider', 'shared'); OUT.boardMis = W._vaultMisfiled('Gore Rider'); OUT.boardHomes = homes('Gore Rider', 2);
/* his share switch keeps its own default (the rules), so a switch he sets beside a keeper dest is stored */
OUT.shareDef = W._shareDefault('Gore Rider'); W._setShareOverride('Gore Rider', 'shared'); OUT.shareSet = W._shareOverride('Gore Rider');
dest('Skin of the Vipermagi', 'mule:' + ALT); OUT.sharedMis = W._vaultMisfiled('Skin of the Vipermagi'); OUT.sharedHome = homes('Skin of the Vipermagi', 1);
/* only a keeper; a set piece by its canon */
OUT.stale = sg('Nagelring');
var NT = W._vfCanon ? W._vfCanon("Natalya's Totem") : "Natalya's Totem"; OUT.ntCanon = NT;
multiKeep[NT] = { want: 2, dest: 'mule:' + ALT }; OUT.nt = sg("Natalya's Totem");
})();
"""

_OUT = {}


def measured():
    if not _OUT:
        out = VPN.run(BODY, prelude=SEED, timeout=300)
        errs = (out.get("__boot") or {}).get("errors") or []
        if errs:
            raise AssertionError("the page did not boot clean in node: %r" % errs[:3])
        _OUT.update(out)
    return _OUT


class AKeeperDestinationRoutesEveryCopy(unittest.TestCase):

    def test_auto_is_todays_rules(self):
        o = measured()
        self.assertIsNone(o["auto"]["dest"], "Auto answered as a keeper setting: %r" % o["auto"])
        self.assertEqual(o["auto"]["id"], "shared")
        self.assertNotIn("keeper setting", o["auto"]["why"])
        self.assertEqual(o["autoCap"], 1, "Auto changed the war stash's one-big-copy cap")

    def test_shared_keeps_every_copy_on_the_shared_stash(self):
        o = measured()
        self.assertEqual((o["shared"]["id"], o["shared"]["dest"]), ("shared", "shared"), o["shared"])
        self.assertIn("your keeper setting", o["shared"]["why"])
        self.assertEqual(o["sharedCap"], "all", "Shared kept the one-big-copy cap, so copies 2 and 3 left the shared stash")
        self.assertEqual(o["sharedHomes"], [["shared", False]] * 3)

    def test_war_sends_every_copy_to_the_war_mules(self):
        o = measured()
        self.assertEqual((o["war"]["id"], o["war"]["dest"]), ("shared", "war"), o["war"])
        self.assertEqual(o["warCap"], 0)
        self.assertEqual(o["warHomes"], [["shared", True]] * 3, "a copy stayed on the shared stash's pages: %r" % o["warHomes"])

    def test_a_mule_he_chose_is_the_home(self):
        o = measured()
        self.assertEqual((o["mule"]["id"], o["mule"]["dest"]), (o["alt"], "mule:" + o["alt"]), o["mule"])
        self.assertIn("ALT ONE", o["mule"]["why"])
        self.assertEqual(o["muleHome"], [[o["alt"], False]])

    def test_a_mule_this_board_does_not_have_is_refused_never_guessed(self):
        o = measured()
        g = o["ghost"]
        self.assertTrue(g["unsorted"] and g["id"] is None, "a missing mule was answered with a home: %r" % g)
        self.assertIn("ghost-mule", g["why"])
        self.assertIn("nothing is guessed", g["why"])
        self.assertEqual(o["ghostHome"], [[None, False]])

    def test_the_destination_beats_a_category_rule(self):
        o = measured()
        self.assertNotEqual(o["griefAuto"]["id"], "uni-small", "the premise needs a rule home other than UNI-SMALL")
        self.assertEqual((o["grief"]["id"], o["grief"]["dest"]), ("uni-small", "mule:uni-small"), o["grief"])

    def test_his_hand_filing_keeps_its_home_and_its_cap(self):
        o = measured()
        self.assertTrue(o["handFiled"], "the setup must start with a filing his hand made")
        self.assertIsNone(o["handSg"]["dest"], "a keeper setting overrode his hand: %r" % o["handSg"])
        self.assertIsNone(o["handMis"], "his hand filing was planned off its mule: %r" % o["handMis"])
        self.assertEqual(o["handHome"], [["uni-armor", False]])
        self.assertEqual(o["handWarCap"], o["handAutoCap"], "WAR changed the cap of an item his hand filed")

    def test_the_boards_filing_is_rehomed_by_the_destination(self):
        o = measured()
        self.assertEqual(o["boardFiled"], ["uni-armor", "shared", False, False], "the setup needs two filings the board made")
        self.assertEqual((o["boardMis"] or {}).get("seam"), {"loc": "shared", "mule": None}, o["boardMis"])
        self.assertEqual(o["boardHomes"], [["shared", False], ["shared", False]],
                         "a copy went back to the mule the board filed it on: %r" % o["boardHomes"])
        self.assertEqual((o["sharedMis"] or {}).get("seam"), {"loc": "filed", "mule": o["alt"]},
                         "a shared-stash filing ignored the mule he chose: %r" % o["sharedMis"])
        self.assertEqual(o["sharedHome"], [[o["alt"], False]])

    def test_the_share_switch_default_is_the_rules_not_the_keeper_dest(self):
        o = measured()
        self.assertEqual(o["shareDef"], "mule", "the share switch's default read the keeper dest (Shared), not the rules")
        self.assertEqual(o["shareSet"], "shared", "a share switch set beside a keeper dest was dropped as 'the default'")

    def test_only_a_keeper_has_a_destination_and_a_set_piece_is_found_by_its_canon(self):
        o = measured()
        self.assertIsNone(o["stale"]["dest"], "a dest on a want of 1 routed: %r" % o["stale"])
        self.assertNotEqual(o["ntCanon"], "Natalya's Totem", "the premise needs a canon other than the bare name")
        self.assertEqual(o["nt"]["id"], o["alt"], "a set piece asked by its bare name missed its keeper's dest: %r" % o["nt"])


RED_PROOF = [
    {"why": "REG-2901 - the router never asks the keeper destination",
     "file": "bible.html",
     "find": "      try { _kdHome = _keeperDestHome(name); } catch (eKd) { _kdHome = null; }\n      if (_kdHome) return _kdHome;\n",
     "replace": "      try { _kdHome = _keeperDestHome(name); } catch (eKd) { _kdHome = null; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - a keeper destination overrides a filing his hand made",
     "file": "bible.html",
     "find": "    if (_vaultFiledByHand(nm)) return null;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - WAR keeps a copy on the shared stash's pages",
     "file": "bible.html",
     "find": "    if (_kdC && _kdC.keeperDest === 'war') return 0;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - Shared keeps the one-big-copy cap, so the copies he asked for leave the shared stash",
     "file": "bible.html",
     "find": "    if (_kdC && _kdC.keeperDest === 'shared') return Infinity;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - a mule the board does not have is guessed",
     "file": "bible.html",
     "find": "    var m = (typeof muleById === 'function') ? muleById(mm[1]) : null;\n    if (!m) return { id: null, unsorted: true, keeperDest: d,\n",
     "replace": "    var m = (typeof muleById === 'function') ? muleById(mm[1]) : null;\n    if (!m) m = muleById('uni-weap');\n    if (!m) return { id: null, unsorted: true, keeperDest: d,\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - a shared-stash filing the board made never moves to the mule he chose",
     "file": "bible.html",
     "find": "    if (_kdMf && _kdMf.id != null && _kdMf.id !== 'shared' && !/^__/.test(String(_kdMf.id))) {\n",
     "replace": "    if (false) {\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - an extra copy returns to the mule the board filed it on, under an explicit destination",
     "file": "bible.html",
     "find": "      if (!_kdX && copyIx != null && copyIx !== _vaultWarKeeper(name)",
     "replace": "      if (copyIx != null && copyIx !== _vaultWarKeeper(name)",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - a stale dest on a want of 1 still routes",
     "file": "bible.html",
     "find": "    if (d === 'auto' || !(_mkWant(key) > 1)) return null;\n",
     "replace": "    if (d === 'auto') return null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - a set piece asked by its bare name misses its keeper's dest",
     "file": "bible.html",
     "find": "        if (c && c !== nm && _mkDest(c) !== 'auto'){ key = c; d = _mkDest(c); }\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2901 - the share switch's default reads the keeper dest, so a switch he sets beside it is dropped",
     "file": "bible.html",
     "find": "    try { var r = suggestMule(name, {ignoreShareOverride:true, ignoreKeeperDest:true}); return",
     "replace": "    try { var r = suggestMule(name, {ignoreShareOverride:true}); return",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
