# -*- coding: utf-8 -*-
"""#111 (REG-2738, GrokBot close-0915) - A LOCKER THAT DRAWS A CELL PER COPY SAYS HOW MANY COPIES.

GrokBot, on his live board: the mule header read "UNI-ARMOR 2" over 5 copy cells - two items, Nightwing's Veil x3 and
Alma Negra x2. The number is right: REG-2224 made it count ITEMS, because counting copies had it disagree with the
Registered header and the proven chip (GrokBot's own "329 vs 220"). What was missing is the other half: the grid draws a
cell per copy and nothing on the plate said so, so "2" sat over five pictures with no word for the difference. The count
stays items; when the card draws more cells than it has items, a line UNDER the plate says "2 items in 5
copies" (div.vm-copies: never inside .vm-count, whose text two older laws read as a bare number, and never in the plate's
row, where it squeezed the locker name onto two lines on the first cut), and a locker with one copy of everything says nothing extra.

Driven on the whole page in node (vault_page_node: every inline script, a fresh world seeded with one weapon unique x3 in
uni-weap and one helm unique x1 in uni-armor, no network). RED_PROOF below.
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

MULTI, SINGLE = "Griswold's Edge", "Nightwing's Veil"

PRELUDE = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(["Griswold's Edge", "Nightwing's Veil"]));
localStorage.setItem('d2r_copies', JSON.stringify({"Griswold's Edge": 3}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({"Griswold's Edge": 'uni-weap', "Nightwing's Veil": 'uni-armor'}));
"""

BODY = r"""
(function(){
var W = window;
try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); }
H.flush(60, 3);
var all = '';
H.ELS.forEach(function(el){ if (el && typeof el.innerHTML === 'string' && el.innerHTML.indexOf('data-vault-mule=') >= 0 && el.innerHTML.length > all.length) all = el.innerHTML; });
function card(id){
  var i = all.indexOf('data-vault-mule="' + id + '"');
  if (i < 0) return null;
  var j = all.indexOf('data-vault-mule="', i + 10);
  return all.slice(i, j < 0 ? all.length : j);
}
OUT.multi = card('uni-weap'); OUT.single = card('uni-armor');
try { OUT.copiesDrawn = W._shelfDrawNames(["Griswold's Edge"], 'uni-weap').length; } catch (e) { OUT.copiesErr = String(e); }
})();
"""


def _count(html):
    m = re.search(r'<span class="vm-count"[^>]*>(\d+)', html or "")
    return int(m.group(1)) if m else None


def _copies(html):
    return re.findall(r'<div class="vm-copies"[^>]*>(\d+ items? in \d+) copies</div>', html or "")


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ALockerSaysItsCopies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted_and_the_premise_holds(self):
        o = self.o
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertTrue(o.get("multi") and o.get("single"), "PREMISE: a locker card was not drawn: %r" % sorted(o))
        self.assertEqual(o.get("copiesDrawn"), 3, "PREMISE: the grid does not draw 3 cells for the x3 item: %r" % o)

    def test_the_count_stays_items(self):
        self.assertEqual(_count(self.o.get("multi")), 1, "the x3 locker counts copies, not items (REG-2224)")
        self.assertEqual(_count(self.o.get("single")), 1)

    def test_a_locker_with_copies_says_how_many_beside_the_count(self):
        h = self.o.get("multi") or ""
        self.assertEqual(_copies(h), ["1 item in 3"],
                         "a locker drawing 3 cells for 1 item does not say '1 item in 3 copies': %s" % h[:600])
        plate = h.find('<div class="vm-plate"')
        self.assertGreater(h.find('class="vm-copies"'), h.find("</div>", plate),
                           "the copies line sits inside the plate's row, where it squeezes the locker name onto two lines")

    def test_a_locker_with_one_copy_of_everything_says_nothing_extra(self):
        self.assertEqual(_copies(self.o.get("single")), [], "a single-copy locker says copies anyway")


RED_PROOF = [
    {"why": "#111 (REG-2738) - the plate says nothing about copies again",
     "file": "bible.html",
     "find": "        + (_copyN > _itemN && _multiCopy ? '<div class=\"vm-copies\"",
     "replace": "        + (false ? '<div class=\"vm-copies\"",
     "matches": 1, "needs": "node"},
    {"why": "#111 (REG-2738) - the copies are folded into the count instead (REG-2224 undone)",
     "file": "bible.html",
     "find": "          + _itemN + (muleN > 1 ? '<span class=\"vm-mules\"",
     "replace": "          + _copyN + (muleN > 1 ? '<span class=\"vm-mules\"",
     "matches": 1, "needs": "node"},
    {"why": "#111 (REG-2738) - every locker says copies, one copy each or not",
     "file": "bible.html",
     "find": "        + (_copyN > _itemN && _multiCopy ? '<div class=\"vm-copies\"",
     "replace": "        + (true ? '<div class=\"vm-copies\"",
     "matches": 1, "needs": "node"},
    {"why": "#111 (REG-2738) - the copies line moves back into the plate's row, where it squeezes the name",
     "file": "bible.html",
     "find": "        + '</div>'\n        /* #111 (REG-2738) - the copies line sits UNDER the plate",
     "replace": "        /* #111 (REG-2738) - the copies line sits UNDER the plate",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
