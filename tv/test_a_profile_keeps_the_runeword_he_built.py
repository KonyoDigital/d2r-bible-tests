# -*- coding: utf-8 -*-
"""Front-run (REG-2836) - A SAVED PROFILE KEEPS THE RUNEWORD HE BUILT: its base and its rolls.

His plan: hand-add his real items, saving and loading the profile as he goes. The planner keeps each runeword he built in
d2r_plannerMade (the base he chose, the rolls he typed; the vault cell's picture, footprint and hover read it), and the
profile did not carry that store. Measured on the whole page in node: 55 hand adds with 9 runewords, saved with
window._vaultProfileBuild, written into a fresh world the way vaultProfileLoad writes it, then the page reloaded - owned,
every record and target cell, every copy and every Magic & Rare mod came back identical, and d2r_plannerMade came back
with 0 of its 9 records (Grief on his Giant Axe came back as the catalogue's base). Now the profile's vault group
carries it. Driven here: Grief built on a Giant Axe through the planner, the profile saved, a fresh world loaded and
reloaded. RED_PROOF below.
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

PRELUDE = ("Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });\n"
           "localStorage.setItem('d2r_ownerClaim', '*');\n")
DUMP = ("OUT.dump = (function(){ var o = {}; for (var i = 0; i < localStorage.length; i++){ var k = localStorage.key(i);"
        " o[k] = localStorage.getItem(k); } return o; })();")

BUILD = r"""
(function(){
var W = window, DB = W._cbDb();
var gx = Object.keys(DB.b).find(function(c){ return DB.b[c][0] === 'Giant Axe'; });
var grief = DB.it.find(function(x){ return x[1] === 'Grief' && x[2] === 'r'; });
W.vaultPlannerOpen(''); W._cbChoose(grief[0]); W._cbPickBase(gx); W.vaultPlannerClose(); H.flush(60, 3);
OUT.built = { base: W._vpMadeBase('Grief'), rec: W._vpMadeOf('Grief') };
OUT.text = W._vaultProfileBuild();
var P = W._vaultProfileParse(OUT.text);
OUT.carried = !!(P && P.ok && P.stores && Object.prototype.hasOwnProperty.call(P.stores, 'd2r_plannerMade'));
OUT.errors = H.errors.slice();
})();
"""


def _load_body(text):
    return ("(function(){ var P = window._vaultProfileParse(" + json.dumps(text) + "); OUT.ok = !!(P && P.ok);"
            " Object.keys((P && P.stores) || {}).forEach(function(k){ var v = P.stores[k];"
            " if (v === null) window.LSR.removeItem(k); else window.LSR.setItem(k, v); }); })();" + DUMP)


AFTER = r"""
try { window.renderVault(); } catch (e) {} H.flush(60, 3);
OUT.base = window._vpMadeBase('Grief'); OUT.rec = window._vpMadeOf('Grief'); OUT.owned = owned.has('Grief');
"""


class AProfileKeepsTheRunewordHeBuilt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.b = VPN.run(BUILD, prelude=PRELUDE, timeout=300)
        loaded = VPN.run(_load_body(cls.b["text"]), prelude=PRELUDE, timeout=300)
        cls.loaded_ok = loaded.get("ok")
        seed = PRELUDE + "var __D = " + json.dumps(loaded["dump"]) + "; Object.keys(__D).forEach(function(k){ localStorage.setItem(k, __D[k]); });\n"
        cls.a = VPN.run(AFTER, prelude=seed, timeout=300)

    def test_the_build_is_his(self):
        b = self.b
        self.assertEqual(b["__boot"]["errors"], [], b["__boot"])
        self.assertEqual(b["errors"], [])
        self.assertEqual(b["built"]["base"], "Giant Axe", "PREMISE: the planner did not keep the base he chose: %r" % b["built"])
        self.assertTrue(self.loaded_ok, "PREMISE: the profile did not parse")

    def test_the_profile_carries_the_runeword_record(self):
        self.assertTrue(self.b["carried"], "the saved profile leaves d2r_plannerMade out")

    def test_a_fresh_world_loads_it_back(self):
        a = self.a
        self.assertTrue(a["owned"], "PREMISE: Grief did not come back owned: %r" % a)
        self.assertEqual(a["base"], "Giant Axe", "Grief came back on the catalogue's base, not his Giant Axe: %r" % a)
        self.assertEqual((a["rec"] or {}).get("baseName"), "Giant Axe", a)


RED_PROOF = [
    {"why": "REG-2836 - the profile leaves the planner's runewords out again",
     "file": "bible.html",
     "find": "            'd2r_plannerMade',\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
