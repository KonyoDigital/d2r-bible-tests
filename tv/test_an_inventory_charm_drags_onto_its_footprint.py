# -*- coding: utf-8 -*-
"""Wave 2 — AN INVENTORY CHARM DRAGS ONTO A GREEN FOOTPRINT OF ITS OWN SIZE.

GrokBot ACT 5855237740: the mule window's 10x4 charms must drag-reorder, with a green footprint
of the charm's size (1x1, 1x2, 1x3), and only a valid drop moves the charm. The database tiles
were drawn without data-key, so the mule window's one drag never lifted them.

This law drives that same drag (not a second one) in node, on the shipped mule window: the
pointer listeners the page registered, the inventory writer (_mpInvMove over _mpInvFitWhy), and
the painter the locker drag already uses (vd-drop-ok / vd-drop-no). A 1x1, a 1x2 and a 1x3 each
show a green footprint of their own height and land on an empty cell. A footprint off the 10x4,
over another charm, or on the stash is red and the charm stays. A press that does not move is
still a click (no footprint, no write). A move keeps the placement's time, so the door does not
file the name again.

The stand-in grid only answers the pointer (which cell, which drop element). The fit is the
inventory's own, read from the store.
RED_PROOF below.
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

import test_the_mule_inventory_takes_items_like_the_doll as INV  # noqa: E402

NODE = INV.NODE

#: the painter's cell, the same number the stand-in grid publishes as data-cell.
#: width = n * cell + (n - 1) * 2, which is _mpPreview's (pitch - 2) with pitch = cell + 2.
CELL = 30


def _px(n):
    return n * CELL + (n - 1) * 2


SCENARIO = r"""
setInterval = function(){ return 1; };
clearInterval = function(){};
var beforeBuilds = STORE['d2r_charBuilds'], beforeSel = STORE['d2r_cbSel'];
door();
window.openMuleCard('uni-armor');
out.placed = [place(0, 0, 'b:cm1'), place(1, 0, 'b:cm2'), place(2, 0, 'b:cm3'), place(3, 0, ANNI_ID)];
out.err = st().hostErr || '';
out.filed0 = FILED.length;
out.before = invList();
var DROPS = [], GATTR = { 'data-area': 'inv', 'data-page': '0', 'data-gw': '10', 'data-gh': '4', 'data-cell': '30' };
var GRID = {
  clientLeft: 0, clientTop: 0, children: [],
  classList: { add: function(){}, remove: function(){}, contains: function(){ return false; } },
  getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(GATTR, k) ? String(GATTR[k]) : null; },
  getBoundingClientRect: function(){ return { left: 0, top: 0, width: 340, height: 160, right: 340, bottom: 160 }; },
  appendChild: function(d){ d.parentNode = GRID; GRID.children.push(d);
    if (String(d.className || '').indexOf('vd-drop') >= 0) DROPS.push(d); return d; },
  removeChild: function(d){ d.parentNode = null; GRID.children = GRID.children.filter(function(x){ return x !== d; });
    DROPS = DROPS.filter(function(x){ return x !== d; }); },
  closest: function(sel){ return String(sel).indexOf('vd-grid') >= 0 ? GRID : null; },
  querySelectorAll: function(){ return []; }
};
document.querySelectorAll = function(sel){
  if (String(sel).indexOf('vd-drop') >= 0) return DROPS.filter(function(d){ return d.parentNode; });
  return [];
};
document.elementFromPoint = function(){ return GRID; };
box.contains = function(){ return true; };
function tileFor(rec){
  var attrs = { 'data-dbkey': rec.key, 'data-n': rec.name, 'data-x': String(rec.x), 'data-y': String(rec.y),
                'data-w': String(rec.w), 'data-h': String(rec.h) };
  var tile = { nodeType: 1, innerHTML: '', attrs: attrs,
    classList: { add: function(){}, remove: function(){}, contains: function(){ return false; } },
    getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    getBoundingClientRect: function(){ return { left: 3 + rec.x * 32, top: 3 + rec.y * 32, width: 30,
      height: rec.h * 30, right: 0, bottom: 0 }; },
    closest: function(sel){ sel = String(sel);
      if (sel.indexOf('vd-unlock') >= 0) return null;
      if (sel.indexOf('vd-grid') >= 0 && sel.indexOf('vd-item') < 0) return GRID;
      var hit = false;
      sel.split(',').forEach(function(part){
        if (part.indexOf('vd-item') < 0) return;
        var wantsDb = part.indexOf('data-dbkey') >= 0, wantsKey = part.indexOf('data-key') >= 0 && !wantsDb;
        if (wantsDb && attrs['data-dbkey']) hit = true;
        else if (wantsKey && attrs['data-key']) hit = true;
        else if (!wantsDb && !wantsKey) hit = true;
      });
      return hit ? tile : null; } };
  return tile;
}
function atKey(key){ var hit = null; invList().forEach(function(e){ if (e.key === key) hit = e; }); return hit; }
function dragTo(key, tx, ty, area){
  GATTR['data-area'] = area || 'inv';
  var rec = atKey(key); if (!rec) return { err: 'missing ' + key };
  var tile = tileFor(rec);
  var ax = 3 + rec.x * 32 + 4, ay = 3 + rec.y * 32 + 4, bx = 3 + tx * 32 + 4, by = 3 + ty * 32 + 4;
  var ev = function(x, y){ return { button: 0, pointerId: 1, clientX: x, clientY: y, target: tile, cancelable: true, preventDefault: function(){} }; };
  fire('pointerdown', ev(ax, ay));
  fire('pointermove', ev(bx, by));
  var drop = DROPS.filter(function(d){ return d.parentNode; }).slice(-1)[0] || null;
  var seen = drop ? { cls: String(drop.className || ''), w: String(drop.style.width || ''), h: String(drop.style.height || '') } : null;
  fire('pointerup', ev(bx, by));
  var now = atKey(key);
  return { seen: seen, from: { x: rec.x, y: rec.y, w: rec.w, h: rec.h, name: rec.name },
           now: now ? { x: now.x, y: now.y, w: now.w, h: now.h, at: now.at, name: now.name } : null };
}
function nudge(key){
  var rec = atKey(key); if (!rec) return { err: 'missing' };
  var tile = tileFor(rec), ax = 3 + rec.x * 32 + 4, ay = 3 + rec.y * 32 + 4;
  var ev = function(x, y){ return { button: 0, pointerId: 1, clientX: x, clientY: y, target: tile, cancelable: true, preventDefault: function(){} }; };
  fire('pointerdown', ev(ax, ay));
  fire('pointermove', ev(ax + 2, ay));
  var drop = DROPS.filter(function(d){ return d.parentNode; }).length;
  fire('pointerup', ev(ax + 2, ay));
  var now = atKey(key);
  return { drops: drop, x: now && now.x, y: now && now.y };
}
var k1 = keyOf('Small Charm'), k2 = keyOf('Large Charm'), k3 = keyOf('Grand Charm'), ka = keyOf('Annihilus');
out.keys = [k1, k2, k3, ka];
out.small = dragTo(k1, 9, 3);
out.large = dragTo(k2, 8, 0);
out.grand = dragTo(k3, 7, 0);
out.anni = dragTo(ka, 0, 0);
out.filed1 = FILED.length;
out.off = dragTo(k3, 7, 2);
out.over = dragTo(k3, 0, 0);
out.stash = dragTo(k3, 4, 0, 'personal');
out.nudge = nudge(k1);
out.click = (tileTag(k1) || '').indexOf('_mpInvTile') >= 0;
out.builds = STORE['d2r_charBuilds'] === beforeBuilds;
out.sel = STORE['d2r_cbSel'] === beforeSel;
out.after = invList().map(function(e){ return [e.name, e.x, e.y, e.w, e.h]; });
"""


def _anni():
    return INV._ids(("Annihilus", "u"))["Annihilus"]


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AnInventoryCharmDragsOntoItsFootprint(unittest.TestCase):

    def test_each_size_lands_on_a_green_footprint_and_a_bad_drop_stays(self):
        out = INV._drive(SCENARIO.replace("ANNI_ID", json.dumps(_anni())),
                         store={"d2r_charBuilds": INV.BUILDS, "d2r_cbSel": "b1"})
        self.assertEqual(out["placed"], [True, True, True, True],
                         "a charm was not placed, so the drag has nothing to lift: %r" % out.get("err"))
        self.assertEqual(out["keys"].count(None), 0, "a placed charm has no store key: %r" % out["keys"])
        self.assertGreaterEqual(out["filed0"], 1,
                                "Annihilus was not filed on the way in, so a second filing cannot be seen")
        for label, drag, wh in (("small", out["small"], (1, 1)), ("large", out["large"], (1, 2)),
                                ("grand", out["grand"], (1, 3))):
            self.assertIsNone(drag.get("err"), label)
            self.assertEqual((drag["from"]["w"], drag["from"]["h"]), wh, "%s was not %s" % (label, wh))
            seen = drag["seen"]
            self.assertIsNotNone(seen, "%s drew no footprint" % label)
            self.assertEqual(seen["cls"], "vd-drop vd-drop-ok", "%s footprint was not the green one: %r" % (label, seen))
            self.assertEqual((seen["w"], seen["h"]), ("%dpx" % _px(wh[0]), "%dpx" % _px(wh[1])),
                             "%s green footprint is not its own %sx%s" % (label, wh[0], wh[1]))
        self.assertEqual((out["small"]["now"]["x"], out["small"]["now"]["y"], out["small"]["now"]["w"], out["small"]["now"]["h"]),
                         (9, 3, 1, 1))
        self.assertEqual((out["large"]["now"]["x"], out["large"]["now"]["y"], out["large"]["now"]["h"]), (8, 0, 2))
        self.assertEqual((out["grand"]["now"]["x"], out["grand"]["now"]["y"], out["grand"]["now"]["h"]), (7, 0, 3))
        self.assertEqual((out["anni"]["seen"]["cls"], out["anni"]["seen"]["h"]), ("vd-drop vd-drop-ok", "%dpx" % _px(1)))
        self.assertEqual((out["anni"]["now"]["x"], out["anni"]["now"]["y"], out["anni"]["now"]["name"]), (0, 0, "Annihilus"))
        self.assertEqual(out["filed1"], out["filed0"], "moving a charm filed it again")
        moved = dict((e["name"], e["at"]) for e in out["before"])
        self.assertEqual(out["anni"]["now"]["at"], moved["Annihilus"], "the move minted a new placement time")
        for label, drag in (("off the grid", out["off"]), ("over Annihilus", out["over"]), ("onto the stash", out["stash"])):
            self.assertEqual(drag["seen"]["cls"], "vd-drop vd-drop-no", "%s was not a red footprint: %r" % (label, drag["seen"]))
            self.assertEqual((drag["now"]["x"], drag["now"]["y"]), (drag["from"]["x"], drag["from"]["y"]),
                             "the grand charm moved on a drop that does not fit (%s)" % label)
            self.assertEqual((drag["now"]["w"], drag["now"]["h"]), (1, 3))
        self.assertEqual(out["nudge"], {"drops": 0, "x": 9, "y": 3},
                         "a press that does not move started a drag or wrote a cell")
        self.assertTrue(out["click"], "the charm's click no longer opens it")
        self.assertTrue(out["builds"], "a drag touched d2r_charBuilds")
        self.assertTrue(out["sel"], "a drag touched d2r_cbSel")


RED_PROOF = [
    {
        "why": "a database charm is not lifted, so the drag never starts",
        "file": "bible.html",
        "find": "    var it = e.target.closest('#vault-detail .vd-item[data-key], #vault-detail .vd-item[data-dbkey]'), g = it && it.closest('.vd-grid[data-area]');\n",
        "replace": "    var it = e.target.closest('#vault-detail .vd-item[data-key]'), g = it && it.closest('.vd-grid[data-area]');\n",
        "matches": 1,
    },
    {
        "why": "the footprint shows and the drop does not write",
        "file": "bible.html",
        "find": "    if (d.dbkey) _mpInvCommit(d.dbkey, t);\n",
        "replace": "    if (false) _mpInvCommit(d.dbkey, t);\n",
        "matches": 1,
    },
    {
        "why": "a charm's footprint is one row tall, whatever its size",
        "file": "bible.html",
        "find": "    var r = it.getBoundingClientRect(), p = _mpPitch(g), w = +it.getAttribute('data-w') || 1, h = +it.getAttribute('data-h') || 1;\n",
        "replace": "    var r = it.getBoundingClientRect(), p = _mpPitch(g), w = +it.getAttribute('data-w') || 1, h = 1;\n",
        "matches": 1,
    },
    {
        "why": "the green footprint is no longer the mule drag's painter",
        "file": "bible.html",
        "find": "    d.className = 'vd-drop ' + (ok ? 'vd-drop-ok' : 'vd-drop-no');\n",
        "replace": "    d.className = 'vd-drop vd-drop-no';\n",
        "matches": 1,
    },
    {
        "why": "a footprint off the 10x4 still writes the charm",
        "file": "bible.html",
        "find": "    if (x + w > MULE_INV_W || y + h > MULE_INV_H)\n",
        "replace": "    if (false)\n",
        "matches": 1,
    },
    {
        "why": "a move files the charm again",
        "file": "bible.html",
        "find": "    var entry = { name: rec.name, source: 'manual', at: rec.at, w: rec.w, h: rec.h };\n",
        "replace": "    var entry = { name: rec.name, source: 'manual', at: new Date().toISOString(), w: rec.w, h: rec.h };\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("SKIP — node is not on this machine, so the charm drag was not driven. UNMEASURED.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
