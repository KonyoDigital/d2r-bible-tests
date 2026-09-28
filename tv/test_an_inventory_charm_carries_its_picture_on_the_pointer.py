# -*- coding: utf-8 -*-
"""Wave 2 — A LIFTED CHARM CARRIES ITS OWN PICTURE ON THE POINTER.

GrokBot ACT 5855265931: picking a charm up shows that charm's graphic on the cursor, not a text
name and not one stub for every size. The mule window already has that painter (vd-ghost). This
law does not add a second one. It drives the same drag as the footprint law.

The ghost's HTML is the art the tile drew (the d2art the page put in the cell). Off the grid the
ghost sits on the pointer, at the size it was lifted. Over a cell it sits on that footprint at
the charm's own width and height. A press that does not move paints no picture. Letting go takes
the picture off the pointer. A Fine Small Charm of Balance still carries the Small Charm picture:
the store's composed name is not the cursor.

The stand-in grid only answers the pointer. The picture and the fit are the page's own.
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

#: the painter's cell. pitch = cell + 2, the same step _mpPitch reads off data-cell.
CELL = 30
PITCH = CELL + 2
GRAB = 4


def _px(n):
    return n * CELL + (n - 1) * 2


SCENARIO = r"""
setInterval = function(){ return 1; };
clearInterval = function(){};
door();
window.openMuleCard('uni-armor');
out.placed = [place(0, 0, 'b:cm1')];
var k1 = keyOf('Small Charm');
out.addFine = window._cbAddMod('p256');
out.addBal = window._cbAddMod('s267');
out.placed.push(place(1, 0, 'b:cm2'), place(2, 0, 'b:cm3'), place(4, 0, ANNI_ID));
var GHOSTS = [];
body.appendChild = function(el){
  el.parentNode = body; el.parentElement = body;
  if (el && el.id) MADE[el.id] = el;
  if (el && String(el.className || '').indexOf('vd-ghost') >= 0) GHOSTS.push(el);
  return el;
};
body.removeChild = function(el){ el.parentNode = null; el.parentElement = null; };
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
var AIR = { closest: function(){ return null; } };
var MODE = 'grid';
document.querySelectorAll = function(sel){
  if (String(sel).indexOf('vd-drop') >= 0) return DROPS.filter(function(d){ return d.parentNode; });
  return [];
};
document.elementFromPoint = function(){ return MODE === 'air' ? AIR : GRID; };
box.contains = function(){ return true; };
function artHtml(key){
  var h = invHtml(), i = h.indexOf('data-dbkey="' + key + '"'); if (i < 0) return '';
  var gt = h.indexOf('>', i), end = h.indexOf('</div>', gt);
  return h.slice(gt + 1, end);
}
function atKey(key){ var hit = null; invList().forEach(function(e){ if (e.key === key) hit = e; }); return hit; }
function tileFor(key){
  var rec = atKey(key); if (!rec) return null;
  var drawn = dbTiles().filter(function(t){ return t.key === key; })[0] || null;
  var html = artHtml(key);
  var attrs = { 'data-dbkey': key, 'data-n': drawn ? drawn.n : rec.name,
                'data-x': String(rec.x), 'data-y': String(rec.y),
                'data-w': String(rec.w), 'data-h': String(rec.h) };
  var tile = { nodeType: 1, innerHTML: html,
    classList: { add: function(){}, remove: function(){}, contains: function(){ return false; } },
    getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    getBoundingClientRect: function(){
      return { left: 3 + rec.x * 32, top: 3 + rec.y * 32,
               width: rec.w * 30 + (rec.w - 1) * 2, height: rec.h * 30 + (rec.h - 1) * 2, right: 0, bottom: 0 }; },
    closest: function(sel){ sel = String(sel);
      if (sel.indexOf('vd-unlock') >= 0) return null;
      if (sel.indexOf('vd-grid') >= 0 && sel.indexOf('vd-item') < 0) return GRID;
      if (sel.indexOf('vd-item') >= 0 || sel.indexOf('data-dbkey') >= 0) return tile;
      return null; } };
  return tile;
}
function dragTo(key, tx, ty, mode){
  MODE = mode || 'grid';
  var rec = atKey(key); if (!rec) return { err: 'missing ' + key };
  var tile = tileFor(key);
  var ax = 3 + rec.x * 32 + 4, ay = 3 + rec.y * 32 + 4;
  var bx = MODE === 'air' ? 220 : (3 + tx * 32 + 4), by = MODE === 'air' ? 160 : (3 + ty * 32 + 4);
  var ev = function(x, y){ return { button: 0, pointerId: 1, clientX: x, clientY: y, target: tile, cancelable: true, preventDefault: function(){} }; };
  var n0 = GHOSTS.length;
  fire('pointerdown', ev(ax, ay));
  fire('pointermove', ev(bx, by));
  var g = GHOSTS.slice(-1)[0] || null;
  var drop = DROPS.filter(function(d){ return d.parentNode; }).slice(-1)[0] || null;
  var seen = g ? { html: String(g.innerHTML || ''), left: String(g.style.left || ''), top: String(g.style.top || ''),
                   w: String(g.style.width || ''), h: String(g.style.height || '') } : null;
  fire('pointerup', ev(bx, by));
  var now = atKey(key);
  return { seen: seen, foot: drop ? String(drop.className || '') : '',
           from: { x: rec.x, y: rec.y, w: rec.w, h: rec.h },
           now: now ? { x: now.x, y: now.y, w: now.w, h: now.h } : null,
           gone: !g || !g.parentNode, grew: GHOSTS.length > n0,
           ax: ax, ay: ay, bx: bx, by: by };
}
function nudge(key){
  var rec = atKey(key); if (!rec) return { err: 'missing' };
  var tile = tileFor(key), ax = 3 + rec.x * 32 + 4, ay = 3 + rec.y * 32 + 4;
  var ev = function(x, y){ return { button: 0, pointerId: 1, clientX: x, clientY: y, target: tile, cancelable: true, preventDefault: function(){} }; };
  var n0 = GHOSTS.length;
  fire('pointerdown', ev(ax, ay));
  fire('pointermove', ev(ax + 2, ay));
  fire('pointerup', ev(ax + 2, ay));
  var now = atKey(key);
  return { ghosts: GHOSTS.length - n0, x: now && now.x, y: now && now.y };
}
var k2 = keyOf('Large Charm'), k3 = keyOf('Grand Charm'), ka = keyOf('Annihilus');
out.keys = [k1, k2, k3, ka];
out.art = { small: artHtml(k1), large: artHtml(k2), grand: artHtml(k3), anni: artHtml(ka) };
out.names = { small: (dbTiles().filter(function(t){ return t.key === k1; })[0] || {}).n };
out.nudge = nudge(k1);
out.air = dragTo(k1, 0, 0, 'air');
out.large = dragTo(k2, 9, 0, 'grid');
out.grand = dragTo(k3, 7, 0, 'grid');
out.anni = dragTo(ka, 0, 3, 'grid');
out.hostErr = st().hostErr || '';
"""


def _anni():
    return INV._ids(("Annihilus", "u"))["Annihilus"]


def _air(drag):
    return ("%dpx" % (drag["bx"] - GRAB), "%dpx" % (drag["by"] - GRAB))


def _snap(x, y, w, h):
    return ("%dpx" % (3 + x * PITCH), "%dpx" % (3 + y * PITCH), "%dpx" % _px(w), "%dpx" % _px(h))


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class AnInventoryCharmCarriesItsPictureOnThePointer(unittest.TestCase):

    def test_the_lifted_picture_is_that_charms_art_and_it_follows_the_pointer(self):
        out = INV._drive(SCENARIO.replace("ANNI_ID", json.dumps(_anni())),
                         store={"d2r_charBuilds": INV.BUILDS, "d2r_cbSel": "b1"})
        self.assertEqual(out["placed"], [True, True, True, True],
                         "a charm was not placed, so there is no picture to lift: %r" % out.get("hostErr"))
        self.assertIs(out["addFine"], True, "Fine was not added, so the composed name is not there to refuse")
        self.assertIs(out["addBal"], True, "of Balance was not added")
        self.assertEqual(out["keys"].count(None), 0, "a placed charm has no store key: %r" % out["keys"])
        self.assertEqual(out["names"]["small"], "Fine Small Charm of Balance",
                         "the composed name is not on the tile, so the cursor cannot be told from it")
        for label in ("small", "large", "grand", "anni"):
            self.assertIn("d2art-wrap", out["art"][label], "%s was drawn with no picture" % label)
        self.assertIn('aria-label="Small Charm"', out["art"]["small"],
                      "the modded charm's picture is no longer the Small Charm: %r" % out["art"]["small"][:180])
        self.assertNotIn("Fine", out["art"]["small"], "the picture carries the composed name")
        self.assertEqual(out["nudge"], {"ghosts": 0, "x": 0, "y": 0},
                         "a press that does not move put a picture on the pointer or wrote a cell")
        air = out["air"]
        self.assertIsNone(air.get("err"), air)
        self.assertTrue(air["grew"], "lifting the charm painted no picture")
        self.assertEqual(air["seen"]["html"], out["art"]["small"],
                         "the picture on the pointer is not the charm's art: %r" % air["seen"])
        self.assertEqual((air["seen"]["left"], air["seen"]["top"]), _air(air),
                         "off the grid the picture did not sit on the pointer: %r" % air["seen"])
        self.assertEqual((air["seen"]["w"], air["seen"]["h"]), ("%dpx" % _px(1), "%dpx" % _px(1)))
        self.assertTrue(air["gone"], "letting go left the picture on the pointer")
        self.assertEqual((air["now"]["x"], air["now"]["y"]), (air["from"]["x"], air["from"]["y"]),
                         "an air drop moved the charm")
        for label, drag, wh, cell in (("large", out["large"], (1, 2), (9, 0)),
                                      ("grand", out["grand"], (1, 3), (7, 0)),
                                      ("anni", out["anni"], (1, 1), (0, 3))):
            self.assertIsNone(drag.get("err"), drag)
            self.assertEqual(drag["foot"], "vd-drop vd-drop-ok", "%s had no green footprint" % label)
            self.assertEqual(drag["seen"]["html"], out["art"][label],
                             "%s's pointer picture is not its own art" % label)
            self.assertEqual((drag["seen"]["left"], drag["seen"]["top"], drag["seen"]["w"], drag["seen"]["h"]),
                             _snap(cell[0], cell[1], wh[0], wh[1]),
                             "%s's picture is not its own footprint" % label)
            self.assertTrue(drag["gone"], "%s left its picture on the pointer" % label)
            self.assertEqual((drag["now"]["x"], drag["now"]["y"], drag["now"]["w"], drag["now"]["h"]),
                             (cell[0], cell[1], wh[0], wh[1]))


RED_PROOF = [
    {
        "why": "the cursor carries the charm's text name, not its picture",
        "file": "bible.html",
        "find": "      gh.innerHTML = d.el.innerHTML;\n",
        "replace": "      gh.innerHTML = d.el.getAttribute('data-n') || '';\n",
        "matches": 1,
    },
    {
        "why": "off the grid the picture stays at the corner instead of the pointer",
        "file": "bible.html",
        "find": "    if (d.ghost){ d.ghost.style.left = (cx - d.ox) + 'px'; d.ghost.style.top = (cy - d.oy) + 'px'; d.ghost.style.width = d.gw0 + 'px'; d.ghost.style.height = d.gh0 + 'px'; }\n",
        "replace": "    if (d.ghost){ d.ghost.style.left = '0px'; d.ghost.style.top = '0px'; d.ghost.style.width = d.gw0 + 'px'; d.ghost.style.height = d.gh0 + 'px'; }\n",
        "matches": 1,
    },
    {
        "why": "every charm's picture is one row tall once it is over a cell",
        "file": "bible.html",
        "find": "        d.ghost.style.width = (d.w * (p - 2) + (d.w - 1) * 2) + 'px'; d.ghost.style.height = (d.h * (p - 2) + (d.h - 1) * 2) + 'px';\n",
        "replace": "        d.ghost.style.width = (d.w * (p - 2) + (d.w - 1) * 2) + 'px'; d.ghost.style.height = '30px';\n",
        "matches": 1,
    },
    {
        "why": "letting go leaves the picture on the pointer",
        "file": "bible.html",
        "find": "    try { if (d.ghost && d.ghost.parentNode) d.ghost.parentNode.removeChild(d.ghost); } catch (e) {}\n",
        "replace": "    try { if (false && d.ghost && d.ghost.parentNode) d.ghost.parentNode.removeChild(d.ghost); } catch (e) {}\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("SKIP — node is not on this machine, so the charm's picture was not driven. UNMEASURED.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
