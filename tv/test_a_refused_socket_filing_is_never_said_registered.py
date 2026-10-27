# -*- coding: utf-8 -*-
"""REG-2571 - THE THROW-OUT REVIEW'S "SET SOCKETS" AND "KEEP AS BASE" NEVER SAY A REFUSED FILING LANDED.

Minor from the focused second eye on the r3a fix round (ede52513c): vaultSetSockets and vaultKeepAsBase asked vaultFile to
file the new label, and a refusal fell through to persistOwned(), saveA(), a status that led with "registered" / "kept"
and {ok:true}. A refusal is now answered {ok:false, refused, why} and said as "not filed".
Driven on the WHOLE page in node (tv/vault_page_node.py); only vaultFile is made to refuse.
RED_PROOF: each door's refusal arm removed.
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
"""

BODY = r"""
(function(){
var W = window, real = W.vaultFile, asked = [];
W.vaultFile = function(label){ asked.push(label); return { ok: false, refused: 'locked', why: 'locked to your MAIN (test)' }; };
function pick(r){ return r ? { ok: r.ok, refused: r.refused || null, why: r.why || '' } : null; }
OUT.set = pick(W.vaultSetSockets('Flail', 4));
OUT.keep = pick(W.vaultKeepAsBase('Champion Axe'));
OUT.asked = asked;
W.vaultFile = real;
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ARefusedSocketFilingIsNeverSaidRegistered(unittest.TestCase):

    def test_0_premise(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], "a page script did not run: %r" % o["__boot"])
        self.assertEqual(len(o["asked"]), 2, "PREMISE: both doors must ask vaultFile to file the label: %r" % o["asked"])

    def test_1_set_sockets_answers_the_refusal(self):
        o = page()
        self.assertIsNotNone(o["set"])
        self.assertFalse(o["set"]["ok"], "set sockets answered ok over a refused filing: %r" % o["set"])
        self.assertEqual(o["set"]["refused"], "locked")

    def test_2_keep_as_base_answers_the_refusal(self):
        o = page()
        self.assertIsNotNone(o["keep"])
        self.assertFalse(o["keep"]["ok"], "keep as base answered ok over a refused filing: %r" % o["keep"])
        self.assertEqual(o["keep"]["refused"], "locked")


BODY_209 = r"""
(function(){
var W = window;
function hand(n){ return W.tvVaultRegister(n, { by: 'hand', where: 'the law (#209)' }); }
function pick(r){ return r ? { ok: r.ok, refused: r.refused || null, why: r.why || '' } : null; }
OUT.npc = pick(hand('Deckard Cain'));
OUT.panel = pick(hand('Stash'));
OUT.real = pick(hand("Tyrael's Might"));
OUT.owned = Array.from(owned);
OUT.words = ['Deckard Cain', 'tyrael', 'Gheed’s Fortune', 'Inventory', 'Shako'].map(function (n) { return W._vaultNotAnItem(n); });
})();
"""


def page_209():
    if "n" not in _RUNS:
        _RUNS["n"] = VPN.run(BODY_209, prelude=SEED, timeout=300)
    return _RUNS["n"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ANameThatIsNotAnItemIsNeverOwned(unittest.TestCase):
    """#209 (GrokBot's v3808 sweep): "Deckard Cain", "Tyrael", "Stash" were registered as owned loose records."""

    def test_an_npc_and_a_panel_word_are_refused_and_never_owned(self):
        o = page_209()
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        for k in ("npc", "panel"):
            self.assertFalse(o[k]["ok"], "%s was registered: %r" % (k, o))
            self.assertEqual(o[k]["refused"], "not-an-item", o)
            self.assertIn("not an item", o[k]["why"], o)
        self.assertNotIn("Deckard Cain", o["owned"], o["owned"])
        self.assertNotIn("Stash", o["owned"], o["owned"])

    def test_a_real_item_that_contains_such_a_word_still_registers(self):
        o = page_209()
        self.assertTrue(o["real"]["ok"], "a real unique was refused: %r" % o["real"])
        self.assertIn("Tyrael's Might", o["owned"], o["owned"])
        self.assertIsNotNone(o["words"][0]); self.assertIsNotNone(o["words"][1]); self.assertIsNotNone(o["words"][3])
        self.assertIsNone(o["words"][2], "an item that contains an NPC's name was called not an item: %r" % o["words"])
        self.assertIsNone(o["words"][4], o["words"])


RED_PROOF = [
    {"why": "REG-2571 - set sockets says 'registered' and ok over a refused filing again",
     "file": "bible.html", "find": "      if (_vfS && !_vfS.ok){\n", "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2571 - keep as base says 'kept' and ok over a refused filing again",
     "file": "bible.html", "find": "      if (_vfK && !_vfK.ok){\n", "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "#209 - an NPC name or a panel word read off a frame is registered as owned again",
     "file": "bible.html", "find": "      if (_notItem) return { ok:false, refused:'not-an-item', registered:false, why:_notItem };\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#209 - the non-item test matches inside a name, so a real item that contains an NPC's name is refused",
     "file": "bible.html", "find": "    var what = Object.prototype.hasOwnProperty.call(_NOT_ITEMS, f) ? _NOT_ITEMS[f] : null;\n",
     "replace": "    var what = null; Object.keys(_NOT_ITEMS).forEach(function(k){ if (f.indexOf(k) >= 0) what = _NOT_ITEMS[k]; });\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
