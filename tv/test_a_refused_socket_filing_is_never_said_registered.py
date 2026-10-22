# -*- coding: utf-8 -*-
"""REG-2565 - THE THROW-OUT REVIEW'S "SET SOCKETS" AND "KEEP AS BASE" NEVER SAY A REFUSED FILING LANDED.

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


RED_PROOF = [
    {"why": "REG-2565 - set sockets says 'registered' and ok over a refused filing again",
     "file": "bible.html", "find": "      if (_vfS && !_vfS.ok){\n", "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2565 - keep as base says 'kept' and ok over a refused filing again",
     "file": "bible.html", "find": "      if (_vfK && !_vfK.ok){\n", "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
