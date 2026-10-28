# -*- coding: utf-8 -*-
"""REG-2711 (#111, reviewers C2/E/D) - A SPELLING NEVER POISONS THE RUNEWORD CACHE.

_baseRunewords memoises on the LOWERCASED name, and _baseCats looked BASE_CLASS up case-sensitively: 'flail' found no class
(flails are a known gap in the regex fallback), cached [] under 'flail', and every later 'Flail' read that cached nothing.
The exact-name lookup is case-insensitive now, so both spellings resolve to the same base before any memo.

Driven on the whole page in node, in the poisoning order: the lowercase spelling FIRST. RED_PROOF below.
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

BODY = r"""
(function(){
OUT.lower = _baseRunewords('flail').length;
OUT.title = _baseRunewords('Flail').length;
OUT.shout = _baseRunewords('FLAIL').length;
OUT.sup = _baseRunewords('superior flail').length;
OUT.cats = Object.keys(_baseCats('flail')).sort();
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ASpellingNeverPoisonsTheRunewordCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_every_spelling_of_a_base_hosts_the_same_runewords(self):
        o = self.o
        self.assertGreater(o["title"], 0, "PREMISE: a Flail hosts no runeword at all: %r" % o)
        self.assertEqual(o["lower"], o["title"], "'flail' first cached nothing and 'Flail' read it (#111): %r" % o)
        self.assertEqual(o["shout"], o["title"])
        self.assertEqual(o["sup"], o["title"], "a quality prefix in lowercase lost the base")
        self.assertIn("mace", o["cats"], "the lowercase spelling found no class: %r" % o["cats"])


RED_PROOF = [
    {"why": "REG-2711 - the exact-name lookup is case-sensitive again, so 'flail' poisons the cache for 'Flail'",
     "file": "bible.html",
     "find": "  var k = _BASE_CLASS_LC[String(n == null ? '' : n).toLowerCase()];\n",
     "replace": "  var k = null;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
