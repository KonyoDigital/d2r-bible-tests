# -*- coding: utf-8 -*-
"""#144.9 (REG-2741, GrokBot's eyes-pass 2026-10-21) - FIND NAMES THE CELL OF EVERY COPY, NOT THE FIRST ONE'S.

GrokBot, on the vault FIND: a multi-copy item came back as one row naming one cell. _vaultWhereIs walked the packer's
mules and stopped at the first cell carrying the name, so for an item he holds three of FIND said where ONE of them sits,
and the other two were nowhere on the row - the mule window draws all three. It now keeps every copy's cell (`cells`),
`cell` stays the first so every older reader reads what it always read, and FIND's row says "3 copies: ..." with each.
An item held once reads exactly as before.

Driven on the whole page in node (vault_page_node: every inline script, a fresh world seeded with one weapon unique x3
and one x1, both filed to uni-weap; no network). RED_PROOF below.
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

PRELUDE = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(["Griswold's Edge", "Lightsabre"]));
localStorage.setItem('d2r_copies', JSON.stringify({"Griswold's Edge": 3}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({"Griswold's Edge": 'uni-weap', "Lightsabre": 'uni-weap'}));
"""

BODY = r"""
(function(){
var W = window;
try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); }
H.flush(60, 3);
function where(n){ try { var w = W._vaultWhereIs(n); return w ? { kind: w.kind, cell: w.cell, cells: w.cells || null } : null; } catch (e) { return { err: String(e) }; } }
OUT.multi = where("Griswold's Edge");
OUT.single = where("Lightsabre");
function find(q){
  try { W.vaultFind(q); } catch (e) { return 'ERR ' + String(e && e.message || e); }
  H.flush(400, 3);
  var r = document.getElementById('vault-find-results');
  return r ? String(r.innerHTML || '') : null;
}
OUT.findMulti = find('griswold');
OUT.findSingle = find('lightsabre');
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class FindNamesEveryCopysCell(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted_and_both_items_are_filed(self):
        o = self.o
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual((o.get("multi") or {}).get("kind"), "filed", "PREMISE: the x3 item is not filed: %r" % o.get("multi"))
        self.assertEqual((o.get("single") or {}).get("kind"), "filed", "PREMISE: the x1 item is not filed: %r" % o.get("single"))
        self.assertTrue((o.get("multi") or {}).get("cell"), "PREMISE: the packer placed no copy of the x3 item: %r" % o.get("multi"))

    def test_where_is_keeps_every_copys_cell(self):
        m = self.o.get("multi") or {}
        cells = m.get("cells") or []
        self.assertEqual(len(cells), 3, "where-is kept %d cell(s) for an item held x3: %r" % (len(cells), m))
        self.assertEqual(len(set(cells)), 3, "two copies were given one cell: %r" % cells)
        self.assertEqual(m.get("cell"), cells[0], "`cell` is no longer the first copy's cell - older readers would move")

    def test_find_names_all_three_cells_on_its_row(self):
        h = self.o.get("findMulti") or ""
        cells = (self.o.get("multi") or {}).get("cells") or []
        self.assertIn("3 copies: ", h, "FIND's row does not say how many copies: %s" % h[:800])
        for c in cells:
            self.assertIn(c, h.replace("&middot;", "·"), "FIND's row leaves out a copy's cell %r" % c)

    def test_an_item_held_once_reads_as_before(self):
        s = self.o.get("single") or {}
        self.assertEqual(len(s.get("cells") or []), 1, s)
        h = self.o.get("findSingle") or ""
        self.assertNotIn(" copies: ", h, "an item held once is said as copies")
        self.assertRegex(h, r'<span class="vfr-cell"> · [^<]*col \d+ · row \d+</span>', "the single row lost its one cell: %s" % h[:600])


RED_PROOF = [
    {"why": "#144.9 (REG-2741) - where-is stops at the first copy again",
     "file": "bible.html",
     "find": "      var _put = function(c){ out.cells.push(c); if (!out.cell) out.cell = c; };\n",
     "replace": "      var _put = function(c){ if (!out.cell) { out.cell = c; out.cells.push(c); } };\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.9 (REG-2741) - FIND's row names the first copy's cell alone again",
     "file": "bible.html",
     "find": "          + ((w.cells && w.cells.length > 1)   /* #144.9",
     "replace": "          + ((false)   /* #144.9",
     "matches": 1, "needs": "node"},
    {"why": "#144.9 (REG-2741) - every row is said as copies, held once or not",
     "file": "bible.html",
     "find": "          + ((w.cells && w.cells.length > 1)   /* #144.9",
     "replace": "          + ((w.cells && w.cells.length > 0)   /* #144.9",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
