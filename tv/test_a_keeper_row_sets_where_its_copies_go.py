# -*- coding: utf-8 -*-
"""REG-2902 (#149.2, GrokBot's GB-L Advanced-drawer pass, ACT 2) - EACH KEEPER ROW SAYS WHERE EVERY COPY GOES.

GrokBot: the Keepers tab was "HAVE/WANT ± and × only". Each keeper row in the ⚙ Advanced drawer's Keepers tab now
carries Destination [Auto | Shared stash | WAR mules | Mule <name>] beside its want:

  * the select lists Auto, Shared stash, WAR mules and every mule on the board but the shared stash (by its stable id,
    named as it is now), with the keeper's dest selected; a row with no target draws no select;
  * a choice is written to d2r_multiKeep as {want, dest} and the router answers it at once (the joined end, REG-2901);
  * refused in words, nothing changed: a mule the board does not have, the shared stash as a "mule", a name that is not
    a keeper, a word that is not a destination, and a shadow (read only);
  * a dest that names a mule since deleted stays selected and says so under the row - nothing moves, nothing guessed;
  * a keeper his hand filed says his filing stands over the setting (hand > keeper dest > router);
  * a change is his hand: the stable-target door (REG-2787's _vaultMoveRetargetByHand, where it is on the page) is
    asked to re-plan the copies it re-homes, once, with the reason; the same choice again asks nothing.

Driven on the whole page in node (vault_page_node), fixtures only. The pixels of the row are GrokBot's to judge (NEEDS
LIVE). RED_PROOF below.
"""
import json
import os
import re
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

SEED = ("localStorage.setItem('d2r_ownerClaim', '*');\n"
        "localStorage.setItem('d2r_owned', %s);\n"
        "localStorage.setItem('d2r_copies', %s);\n"
        "localStorage.setItem('d2r_multiKeep', %s);\n") % (
    json.dumps(json.dumps(["Harlequin Crest", "Stormshield", "Natalya's Totem (helm)"])),
    json.dumps(json.dumps({"Harlequin Crest": 3, "Natalya's Totem (helm)": 3})),
    json.dumps(json.dumps({"Harlequin Crest": 3, "Stormshield": 2})))

BODY = r"""
(function(){
var W = window, HC = 'Harlequin Crest', SS = 'Stormshield';
function add(nm){ var t = Date.now(); while (Date.now() === t) {} W.prompt = function(){ return nm; }; W.vaultAddMule(); }
add('ALT ONE');
var ALT = W._vaultRosterNow().filter(function(m){ return m.name === 'ALT ONE'; })[0].id; OUT.alt = ALT;
function disk(){ var k = Array.from(H.RAW.keys()).filter(function(x){ return /(^|[^A-Za-z])d2r_multiKeep$/.test(x); })[0];
  return k ? JSON.parse(H.RAW.get(k)) : null; }
function row(n){
  W.renderMultiKeep(); var el = document.getElementById('vault-multikeep'), h = el ? String(el.innerHTML) : '';
  var key = 'data-mk="' + n.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') + '"', i = h.indexOf(key);
  if (i < 0) return null; var j = h.indexOf('class="vmk-row"', i + 1); return h.slice(i, j < 0 ? h.length : j);
}
var CALLS = []; W._vaultMoveRetargetByHand = function(n, why){ CALLS.push([n, why]); return 2; };
OUT.row0 = row(HC); OUT.rowNoTarget = row("Natalya's Totem (helm)");
OUT.war = W.vaultKeeperDest(HC, 'war'); OUT.diskWar = disk()[HC]; OUT.routeWar = (W.suggestMule(HC) || {}).keeperDest || null;
OUT.rowWar = row(HC);
OUT.mule = W.vaultKeeperDest(HC, 'mule:' + ALT); OUT.calls = CALLS.slice();
OUT.again = W.vaultKeeperDest(HC, 'mule:' + ALT); OUT.callsAgain = CALLS.length;
OUT.noMule = W.vaultKeeperDest(HC, 'mule:nobody-here'); OUT.sharedMule = W.vaultKeeperDest(HC, 'mule:shared');
OUT.notKeeper = W.vaultKeeperDest("Natalya's Totem (helm)", 'war'); OUT.word = W.vaultKeeperDest(HC, 'the moon');
W._tvdShadow = { owner: 'the other PC' }; OUT.shadow = W.vaultKeeperDest(HC, 'auto'); W._tvdShadow = null;
OUT.afterRefusals = JSON.parse(JSON.stringify(multiKeep[HC])); OUT.diskAfter = disk()[HC];
_mkSetDest(HC, 'mule:gone-mule'); OUT.rowGone = row(HC);
var hf = W.vaultFile(SS, { by: 'hand', at: new Date().toISOString(), where: 'a drag onto UNI-ARMOR' }, { mule: 'uni-armor' });
OUT.handFiled = !!(hf && hf.ok); W.vaultKeeperDest(SS, 'shared'); OUT.rowHand = row(SS);
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


def _options(row):
    return re.findall(r'<option value="([^"]*)"( selected)?>([^<]*)</option>', row or "")


class AKeeperRowSetsWhereItsCopiesGo(unittest.TestCase):

    def test_a_keeper_row_carries_its_destination(self):
        o = measured()
        self.assertIn('class="vmk-dest-sel"', o["row0"] or "", "a keeper row draws no Destination select")
        opts = _options(o["row0"])
        vals = [v for v, _s, _t in opts]
        self.assertEqual(vals[:3], ["auto", "shared", "war"])
        self.assertIn("mule:uni-armor", vals)
        self.assertIn("mule:" + o["alt"], vals, "a mule he added is not offered")
        self.assertNotIn("mule:shared", vals, "the shared stash is offered as a mule")
        self.assertEqual([v for v, s, _t in opts if s], ["auto"], "the keeper's dest is not the selected option")
        self.assertIn("Mule · ALT ONE", [t for _v, _s, t in opts])
        self.assertNotIn("vmk-dest-sel", o["rowNoTarget"] or "", "a row with no target draws a Destination select")

    def test_a_choice_is_stored_and_routed(self):
        o = measured()
        self.assertTrue(o["war"]["ok"], o["war"])
        self.assertEqual(o["diskWar"], {"want": 3, "dest": "war"}, "the choice was not written to d2r_multiKeep")
        self.assertEqual(o["routeWar"], "war", "the router does not answer the row's choice")
        self.assertEqual([v for v, s, _t in _options(o["rowWar"]) if s], ["war"])

    def test_a_change_asks_the_stable_target_door_once(self):
        o = measured()
        self.assertTrue(o["mule"]["ok"])
        self.assertEqual(o["mule"]["retargeted"], 2)
        self.assertEqual(o["calls"], [["Harlequin Crest", "your keeper setting sends it to the WAR mules"],
                                      ["Harlequin Crest", "your keeper setting sends it to ALT ONE"]])
        self.assertTrue(o["again"]["ok"] and o["again"].get("same"), o["again"])
        self.assertEqual(o["callsAgain"], 2, "the same choice again re-planned the copies")

    def test_refusals_change_nothing_and_say_why(self):
        o = measured()
        for k, code in (("noMule", "no-mule"), ("sharedMule", "no-mule"), ("notKeeper", "not-a-keeper"),
                        ("word", "not-a-destination"), ("shadow", "shadow")):
            self.assertFalse(o[k]["ok"], "%s was accepted: %r" % (k, o[k]))
            self.assertEqual(o[k].get("refused"), code, "%s: %r" % (k, o[k]))
            self.assertTrue(o[k].get("why"), "%s refused without words" % k)
        self.assertIn("nobody-here", o["noMule"]["why"])
        want = {"want": 3, "dest": "mule:" + o["alt"]}
        self.assertEqual(o["afterRefusals"], want, "a refused choice changed the keeper")
        self.assertEqual(o["diskAfter"], want)

    def test_a_dest_naming_a_deleted_mule_says_so(self):
        o = measured()
        opts = _options(o["rowGone"])
        self.assertEqual([v for v, s, _t in opts if s], ["mule:gone-mule"], "the missing mule's choice was dropped or guessed")
        self.assertIn('class="vmk-dest-miss"', o["rowGone"])
        self.assertIn("gone-mule", o["rowGone"])
        self.assertIn("nothing is guessed", o["rowGone"])

    def test_his_hand_filing_is_said_to_stand(self):
        o = measured()
        self.assertTrue(o["handFiled"], "the setup must start with a filing his hand made")
        self.assertIn('class="vmk-dest-hand"', o["rowHand"] or "")
        self.assertIn("your hand filed it on UNI-ARMOR", o["rowHand"])


RED_PROOF = [
    {"why": "REG-2902 - a keeper row draws no Destination select",
     "file": "bible.html",
     "find": "        +dst.sel\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - a choice is kept in memory and never written to d2r_multiKeep",
     "file": "bible.html",
     "find": "    try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){}\n    var say = _vmkDestSay(d), rt = 0;\n",
     "replace": "    var say = _vmkDestSay(d), rt = 0;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - a mule the board does not have is accepted",
     "file": "bible.html",
     "find": "    if (/^mule:/.test(d) && (d.slice(5) === 'shared' || !muleById(d.slice(5)))) return no('no-mule',",
     "replace": "    if (false) return no('no-mule',",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - a shadow writes a keeper's destination",
     "file": "bible.html",
     "find": "    if (window._tvdShadow) return no('shadow', 'a shadow is read only - nothing was changed');\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - a dest naming a deleted mule is not said",
     "file": "bible.html",
     "find": "    if (miss != null) tail = '<span class=\"vmk-dest-miss\"",
     "replace": "    if (false) tail = '<span class=\"vmk-dest-miss\"",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - his hand filing is not said to stand over the setting",
     "file": "bible.html",
     "find": "    else if (d !== 'auto' && typeof _vaultFiledByHand === 'function' && _vaultFiledByHand(n)){\n",
     "replace": "    else if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2902 - a change never asks the stable-target door, so the saved targets keep the old home",
     "file": "bible.html",
     "find": "rt = window._vaultMoveRetargetByHand(n, 'your keeper setting sends it to ' + say) || 0;",
     "replace": "rt = 0;",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
