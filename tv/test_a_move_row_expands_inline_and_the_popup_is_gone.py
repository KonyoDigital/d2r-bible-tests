# -*- coding: utf-8 -*-
"""#144.14 (REG-2780, found landing v3783) - THE DEAD BEFORE | AFTER POPUP IS GONE, AND THE MOVE ROW STILL DRAWS ITS FROM -> TO.

A move row first opened a BEFORE | AFTER popup (REG-2304, Elad ruling 12): two whole-container grids, a ring on each
cell, a close button. Elad's 2026-10-20 22:35 ruling ("one grid per task") replaced it with the row's own inline expand
(_vaultTaskExpandHtml), and from then on nothing on the page opened the popup - but _vaultMoveCompareHtml / Open / Close,
the model's whole-container `before` / `after` lists and the 12 .vault-move-compare / .vmc-* card rules stayed, exported,
and laws kept driving them: three red-proofs were retired as false coverage of it landing v3783, and two Chrome laws still
photographed the popup as if it were the vault. It is removed; _vaultMoveCompareModel stays, because the inline expand
reads it.

Driven on the whole page in node (vault_page_node: every inline script, a fresh world; AUTO INTAKE off; three uniques
hand-added that file to one mule, so the second and third get cells that are not the first; one of them then sighted on a
mule). The popup's doors are asked at runtime AND as declarations in the source (a door left declared but unexported is
still dead code). RED_PROOF below.
"""
import io
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

ROOT = os.path.dirname(HERE)
CLAIM = "localStorage.setItem('d2r_ownerClaim', '*');\n"
HAND = ["Gull (dagger)", "The Grandfather", "Lightsabre"]   # three weapon uniques: UNI-WEAPONS, distinct cells
SEEN = "Lightsabre"

BODY = r"""
(function(){
var W = window;
OUT.doors = { open: typeof W._vaultMoveCompareOpen, close: typeof W._vaultMoveCompareClose, html: typeof W._vaultMoveCompareHtml,
              model: typeof W._vaultMoveCompareModel, expand: typeof W._vaultTaskExpandHtml };
W._vaultAutoIntakeSet(false);
OUT.add = %(hand)s.map(function(n){ var a = W.vaultHandAdd(n); return !!(a && a.ok); });
W.renderVault(); H.flush(60, 3);
function tiles(part){
  var out = [], re = /<div class="vd-item[^"]*"[^>]*?data-key="([^"]*)" data-x="(\d+)" data-y="(\d+)"/g, m;
  while ((m = re.exec(part))) out.push({ key: m[1].replace(/&#39;/g, "'"), x: +m[2], y: +m[3] });
  return out;
}
function look(n){
  var t = (W._vaultMoveEnsure(n, 0) || {}).task || {}, h = '';
  try { h = W._vaultTaskExpandHtml(n, 0); } catch (e) { return { err: String(e && e.message || e) }; }
  var i = h.indexOf('class="vtx-to"');
  var fm = /class="vtx-from" data-from="(\w+)"/.exec(h), tm = /class="vtx-to" data-to="([^"]*)"/.exec(h);
  return { cell: (t.to && t.to.cell) || null, from: fm ? fm[1] : null, to: tm ? tm[1] : null,
           manual: h.indexOf('vmv-manual-badge') >= 0, arrow: h.indexOf('class="vtx-arrow"') >= 0,
           wrap: h.indexOf('<div class="vtk-expand" ') === 0,
           fromTiles: tiles(i >= 0 ? h.slice(0, i) : h), toTiles: tiles(i >= 0 ? h.slice(i) : '') };
}
OUT.hand = {};
%(hand)s.forEach(function(n){ OUT.hand[n] = look(n); });
var mdl = W._vaultMoveCompareModel(%(seen)s, 0);
OUT.modelKeys = Object.keys(mdl || {}).sort();
W._vaultAutoIntakeSet(true);
W._vaultMoveApplySight(%(seen)s, { holder: 'MULE-2', location: 'stash', cell: 'stash:c3r1', frame: 'f_1' });
OUT.seen = look(%(seen)s);
})();
""" % {"hand": repr(HAND).replace("'", '"'), "seen": '"' + SEEN + '"'}


def _xy(cell):
    m = re.match(r"^\w+:c(\d+)r(\d+)$", cell or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AMoveRowExpandsInline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=CLAIM, timeout=300)

    def test_the_page_booted_and_the_hand_adds_landed(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o.get("add"), [True] * len(HAND), "PREMISE: a hand add did not land: %r" % self.o.get("add"))
        cells = [(self.o["hand"][n] or {}).get("cell") for n in HAND]
        self.assertTrue(all(cells), "PREMISE: a hand add has no target cell: %r" % cells)
        self.assertEqual(len(set(cells)), len(HAND), "PREMISE: two hand adds share a cell: %r" % cells)
        self.assertTrue(any(_xy(c) != (0, 0) for c in cells), "PREMISE: every target is the first cell: %r" % cells)

    def test_the_popup_doors_are_gone_and_the_model_and_the_expand_stay(self):
        d = self.o.get("doors") or {}
        self.assertEqual((d.get("open"), d.get("close"), d.get("html")), ("undefined",) * 3,
                         "a BEFORE | AFTER popup door is still on the page: %r" % d)
        self.assertEqual((d.get("model"), d.get("expand")), ("function", "function"),
                         "the expand or the model it reads went with the popup: %r" % d)

    def test_the_model_carries_no_whole_container_list(self):
        keys = self.o.get("modelKeys") or []
        self.assertIn("to", keys, "PREMISE: the model did not build: %r" % keys)
        for dead in ("after", "before", "say"):
            self.assertNotIn(dead, keys, "the model still builds the popup's %r: %r" % (dead, keys))

    def test_each_hand_row_expands_to_manual_and_its_own_cell_alone(self):
        for n in HAND:
            e = self.o["hand"][n] or {}
            self.assertNotIn("err", e, e)
            self.assertTrue(e.get("wrap") and e.get("arrow"), "%s: the expand is not FROM -> TO: %r" % (n, e))
            self.assertEqual((e.get("from"), e.get("manual")), ("manual", True), "%s: a hand row is not MANUAL: %r" % (n, e))
            self.assertEqual(e.get("to"), e.get("cell"), "%s: TO names another cell than its task: %r" % (n, e))
            self.assertEqual([t["key"] for t in e.get("toTiles") or []], [n + "#0"],
                             "%s: the TO grid does not hold this copy alone: %r" % (n, e.get("toTiles")))
            t = (e.get("toTiles") or [{}])[0]
            self.assertEqual((t.get("x"), t.get("y")), _xy(e.get("cell")), "%s is not drawn at its task's cell: %r" % (n, e))

    def test_a_sighted_row_draws_the_cell_it_was_seen_in(self):
        e = self.o.get("seen") or {}
        self.assertEqual(e.get("from"), "seen", "a sighted row's FROM is not the cell it was seen in: %r" % e)
        self.assertEqual([(t["key"], t["x"], t["y"]) for t in e.get("fromTiles") or []], [(SEEN + "#0", 3, 1)], e)
        self.assertEqual(e.get("to"), self.o["hand"][SEEN]["cell"], "the sighting moved the target: %r" % e)


class ThePopupIsNotDeclared(unittest.TestCase):
    """The runtime case cannot see a door left DECLARED but no longer exported. The declaration shapes are counted (a
    sentence about the popup - this file's own, or bible.html's - never carries `function _vault...(` or `{`)."""

    def test_no_popup_declaration_or_rule_is_left(self):
        for f in ("bible.html", os.path.join("tv", "control_ui.html")):
            src = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
            for shape in ("function _vaultMoveCompareHtml(", "function _vaultMoveCompareOpen(", "function _vaultMoveCompareClose(",
                          ".vault-move-compare{", ".vault-move-compare[hidden]{", ".vmc-card{", ".vmc-ring{", ".vmc-close{",
                          "getElementById('vault-move-compare')"):
                self.assertEqual(src.count(shape), 0, "%s still carries %r" % (f, shape))

    def test_the_expand_still_reads_the_model(self):
        src = io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()
        self.assertEqual(src.count("  function _vaultMoveCompareModel(name, copyIx){\n"), 1)
        self.assertEqual(src.count("    var m = _vaultMoveCompareModel(name, copyIx || 0), cell = 26, sz = m.size;\n"), 1,
                         "the inline expand no longer reads the model")


RED_PROOF = [
    {"why": "#144.14 (REG-2780) - a popup door is exported again",
     "file": "bible.html",
     "find": "  try { window._vaultMoveCompareModel = _vaultMoveCompareModel; } catch (eCm) {}\n",
     "replace": "  try { window._vaultMoveCompareModel = _vaultMoveCompareModel; } catch (eCm) {}\n"
                "  try { window._vaultMoveCompareOpen = function(){ return null; }; } catch (eCo) {}\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 (REG-2780) - a popup builder is declared again, unexported",
     "file": "bible.html",
     "find": "  function _vaultMoveCompareModel(name, copyIx){\n",
     "replace": "  function _vaultMoveCompareHtml(name, copyIx){ return ''; }\n  function _vaultMoveCompareModel(name, copyIx){\n",
     "matches": 1},
    {"why": "#144.14 (REG-2780) - the popup's card rules come back",
     "file": "bible.html",
     "find": ".vtk-donebox summary{cursor:pointer}\n",
     "replace": ".vtk-donebox summary{cursor:pointer}\n.vault-move-compare{position:fixed;inset:0}\n",
     "matches": 1},
    {"why": "#144.14 (REG-2780) - the model builds the whole-container list again",
     "file": "bible.html",
     "find": "    return { name: name, copyIx: copyIx, task: t, manual: !from, from: from, to: to,\n",
     "replace": "    return { name: name, copyIx: copyIx, task: t, manual: !from, from: from, to: to, after: [],\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 - the TO grid draws every task bound for that mule (the merged grid the popup drew)",
     "file": "bible.html",
     "find": "      var it = [{ n: m.name, key: m.name + '#' + m.copyIx, x: c.x, y: c.y, w: sz[0], h: sz[1] }];",
     "replace": "      var it = (label === 'To' ? (function(){ var bag = _vaultMoveBag(), all = []; Object.keys(bag.map || {}).forEach(function(k){ var mv = bag.map[k], cm = mv && mv.to && String(mv.to.cell || '').match(/^(\\w+):c(\\d+)r(\\d+)$/); if (cm && String(mv.to.holder || '') === String(m.task.to.holder || '')) all.push({ n: k.split(String.fromCharCode(0))[0], key: k.split(String.fromCharCode(0)).join('#'), x: +cm[2], y: +cm[3], w: 1, h: 1 }); }); return all; })() : [{ n: m.name, key: m.name + '#' + m.copyIx, x: c.x, y: c.y, w: sz[0], h: sz[1] }]);",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 - the TO grid draws the item at the mule's first cell, not its task's",
     "file": "bible.html",
     "find": "one(m.to, m.dims.to, 'To', 'task-to')",
     "replace": "one({ x: 0, y: 0 }, m.dims.to, 'To', 'task-to')",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 - the expand draws no TO grid at all",
     "file": "bible.html",
     "find": "one(m.to, m.dims.to, 'To', 'task-to')",
     "replace": "''",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 - a hand-typed row's FROM is a grid instead of MANUAL",
     "file": "bible.html",
     "find": "    if (m.manual && m.task && m.task.manual) from = ",
     "replace": "    if (false) from = ",
     "matches": 1, "needs": "node"},
    {"why": "#144.14 - a sighted row's FROM is not the cell it was seen in",
     "file": "bible.html",
     "find": "    else if (m.from) from = ",
     "replace": "    else if (false) from = ",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
