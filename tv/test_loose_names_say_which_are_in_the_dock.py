# -*- coding: utf-8 -*-
"""#208 (GrokBot's v3808 sweep) - "13 STILL LOOSE" BESIDE A DOCK OF 8: THE LINE SAYS WHICH ARE IN THE DOCK.

The header's loose count is every owned name whose home is loose - the names in the unsorted dock AND the names off it
because they route to THROW OUT (the dock drops a junk route, "L1 a junk route is a THROW OUT row"). So 13 = 8 in the
dock + 5 marked THROW OUT, and the line's "(5 set pieces · 8 other)" took a dock-only count from the 13.

Driven on the whole page in node: the records count the two apart (looseDock / looseThrow), the header carries them,
the population line names each part from its own list, and with no split the line reads as before.
RED_PROOF below.
"""
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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(["Pelta Lunata", "Lenymo", "The Gnasher"]));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""

BODY = r"""
(function(){
var W = window;
var h = W._vaultRecordsHeader();
OUT.h = h ? { loose: h.loose, looseDock: h.looseDock, looseThrow: h.looseThrow } : null;
OUT.routes = ["Pelta Lunata", "Lenymo", "The Gnasher"].map(function(n){ return (W.suggestMule(n) || {}).id || null; });
OUT.pop = W._vaultPopFromHeader({ owned: 3, loose: 1, sp: 0, carried: 0, orphans: 0 }, h);
function strip(x){ return String(x).replace(/<[^>]+>/g, ''); }
OUT.split = strip(W._vaultPopHtml({ owned: 20, filed: 5, carried: 0, orphans: 0, loose: 13, sp: 2, looseDock: 8, looseThrow: 5 }));
OUT.plain = strip(W._vaultPopHtml({ owned: 20, filed: 5, carried: 0, orphans: 0, loose: 13, sp: 2 }));
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class LooseNamesSayWhichAreInTheDock(unittest.TestCase):

    def test_the_records_count_the_dock_and_the_throw_out_apart(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        h = o["h"]
        self.assertIsNotNone(h, "PREMISE: the records header did not read")
        self.assertEqual(o["routes"], ["__throwout", "__throwout", "uni-weap"], "PREMISE: the routes moved: %r" % o["routes"])
        self.assertEqual(h["looseThrow"], 2, "the THROW OUT names were not counted apart: %r" % h)
        self.assertEqual(h["looseDock"], 0, "a THROW OUT name was counted as in the dock: %r" % h)
        self.assertEqual(h["loose"], h["looseDock"] + h["looseThrow"], h)
        self.assertEqual((o["pop"].get("looseDock"), o["pop"].get("looseThrow")), (h["looseDock"], h["looseThrow"]),
                         "the split did not reach the population line: %r" % o["pop"])

    def test_the_line_names_each_part_from_its_own_list(self):
        o = page()
        self.assertIn("13 still loose", o["split"])
        self.assertIn("8 in the unsorted dock", o["split"], o["split"])
        self.assertIn("2 set pieces · 6 other", o["split"], o["split"])
        self.assertIn("5 marked THROW OUT", o["split"], o["split"])
        self.assertIsNone(re.search(r"11 other", o["split"]), "the set pieces were taken from the whole 13 again")
        self.assertIn("13 still loose (2 set pieces · 11 other)", o["plain"], "with no split the line changed: %r" % o["plain"])


RED_PROOF = [
    {"why": "#208 - a THROW OUT name is counted into the loose total with nothing saying so again",
     "file": "bible.html",
     "find": "            if (_thr) out.looseThrowN = (out.looseThrowN || 0) + 1;\n",
     "replace": "            void _thr;\n", "matches": 1, "needs": "node"},
    {"why": "#208 - the split never reaches the population line",
     "file": "bible.html",
     "find": "    if (typeof header.looseDock === 'number') o.looseDock = header.looseDock;\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#208 - the line takes the dock's set pieces from the whole loose total again",
     "file": "bible.html",
     "find": "    if (lo && _ld !== null) {\n",
     "replace": "    if (false) {\n", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
