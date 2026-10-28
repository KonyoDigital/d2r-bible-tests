# -*- coding: utf-8 -*-
"""#144.11 (REG-2781, GrokBot's eyes-pass A2, seeds 1012 / 1017 / 1021) - A WAR MULE DRAWS THE COPIES THE PLAN SENDS TO IT.

GrokBot: "the open WAR1 card says 0 items total while its preview tile shows 8 items and 8 tasks target WAR1". Measured
here before the fix (node, whole page): Shako x3 and Arachnid Mesh x6 hand-added with a WAR1 mule - four copies are over
the war stash's cap (big gear keeps 1, a belt 4) and their move tasks go to WAR1 (stash:c0r0, c2r0, c4r0, c6r0), yet the
WAR1 window drew nothing and said "Items 0 · 0 items total", its locker census said 0, and the shelf tile said "0 items
in 2 copies". Those copies stay homed on the shared stash in the records, so the window's name list, the packer's records
span and the census never saw them; only the tile's own badge asked the plan (_vaultWarOverOn).
Now the census, the name list and the packer ask the same plan: WAR1 says 2 items, 4 copies, and draws two of each.

Swept with it: an item he FILED on WAR1 by hand (REG-2761's case) was counted twice on the shelf tile - its own copies
plus the over-cap ones, 8 cells for 6 owned belts - while the window drew 6. Both now follow one rule: filed there, its own
copies; else the over-cap copies planned there.

Driven on the whole page in node (vault_page_node - never a browser on his Mac), the WAR mule seeded into the roster store
beside the page's own default lockers (the shape of test_a_war_item_on_a_war_mule_says_why_it_waits). RED_PROOF below.
"""
import json
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

CLAIM = "localStorage.setItem('d2r_ownerClaim', '*');\n"
SHAKO, BELT, WAR = "Harlequin Crest (Shako)", "Arachnid Mesh", "war-law-0"
ADDS = [SHAKO] * 3 + [BELT] * 6     # big gear keeps 1 in the war stash, a belt 4: two of each are over the cap

BODY = r"""
(function(){
var W = window, WAR = %(war)s, NAMES = [%(shako)s, %(belt)s];
W._vaultAutoIntakeSet(false);
OUT.add = %(adds)s.map(function(n){ var a = W.vaultHandAdd(n); return !!(a && a.ok); });
if (%(file)s) W.vaultAssign(%(belt)s, WAR);
W.renderVault(); H.flush(60, 3);
OUT.tasks = 0;
NAMES.forEach(function(n){
  var cc = (typeof copyCount === 'function') ? copyCount(n) : 1;
  for (var ci = 0; ci < cc; ci++) { var t = (W._vaultMoveEnsure(n, ci) || {}).task; if (t && t.to && t.to.id === WAR && t.to.cell) OUT.tasks++; }
});
OUT.names = W._muleNamesFor(WAR);
var L = W._muleLoad(OUT.names, {}, WAR), drawn = {};
(L.mules || []).forEach(function(m){
  (m.stash || []).concat(m.inv || []).forEach(function(p){ drawn[p.n] = (drawn[p.n] || 0) + 1; });
  Object.keys(m.tabs || {}).forEach(function(k){ (m.tabs[k] || []).forEach(function(p){ drawn[p.n] = (drawn[p.n] || 0) + 1; }); });
});
OUT.drawn = drawn; OUT.phys = L.phys;
OUT.census = W._vaultLockerItems(WAR);
OUT.armor = W._muleNamesFor('uni-armor');
var shelf = (document.getElementById('vault-shelf') || {}).innerHTML || '';
var at = shelf.indexOf('data-vault-mule="' + WAR + '"'), nx = at < 0 ? -1 : shelf.indexOf('data-vault-mule="', at + 10);
var card = at < 0 ? '' : shelf.slice(at, nx < 0 ? shelf.length : nx);
OUT.tile = {};
NAMES.forEach(function(n){ OUT.tile[n] = card.split('data-vault-item="' + n.replace(/'/g, '&#39;') + '"').length - 1; });
var cm = /(\d+) items? in (\d+) cop/.exec(card.replace(/<[^>]+>/g, ' '));
OUT.tileSay = cm ? [+cm[1], +cm[2]] : null;
W.openMuleCard(WAR);
var head = ((document.getElementById('vault-detail') || {}).innerHTML || '').replace(/<[^>]+>/g, ' ');
var hm = /(\d+) items? total(?: · (\d+) copies)?/.exec(head);
OUT.head = hm ? [+hm[1], hm[2] ? +hm[2] : +hm[1]] : null;
})();
"""


def _body(filed):
    return BODY % {"war": json.dumps(WAR), "shako": json.dumps(SHAKO), "belt": json.dumps(BELT),
                   "adds": json.dumps(ADDS), "file": "true" if filed else "false"}


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AWarMuleDrawsTheCopiesPlannedOnIt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base = VPN.run("OUT.r = JSON.parse(window.LSR.getItem('d2r_muleRoster') || 'null') || "
                       "(window._vaultRosterNow && window._vaultRosterNow());", prelude=CLAIM, timeout=300).get("r")
        if not isinstance(base, list) or not base:
            raise AssertionError("PREMISE: the page has no default roster to extend: %r" % (base,))
        roster = [m for m in base if not str(m.get("id", "")).startswith("war-law-")] + [{"id": WAR, "name": "WAR1"}]
        pre = CLAIM + "localStorage.setItem('d2r_muleRoster', %s);\n" % json.dumps(json.dumps(roster))
        cls.o = VPN.run(_body(False), prelude=pre, timeout=300)
        cls.f = VPN.run(_body(True), prelude=pre, timeout=300)

    def test_the_premise_four_tasks_go_to_war1(self):
        for o in (self.o, self.f):
            self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
            self.assertEqual(o.get("add"), [True] * len(ADDS), "PREMISE: a hand add did not land: %r" % o.get("add"))
            self.assertEqual(o.get("tasks"), 4, "PREMISE: not four over-cap copies bound for WAR1: %r" % o.get("tasks"))

    def test_the_war1_window_draws_two_of_each(self):
        o = self.o
        self.assertEqual(sorted(o.get("names") or []), sorted([SHAKO, BELT]), "WAR1's name list leaves out its planned copies")
        self.assertEqual(o.get("drawn"), {SHAKO: 2, BELT: 2}, "WAR1 does not draw the four copies its tasks send it: %r" % o)
        self.assertEqual(o.get("phys"), 4, o)

    def test_the_window_the_census_and_the_tile_say_two_items_four_copies(self):
        o = self.o
        self.assertEqual(o.get("census"), 2, "the locker census says %r items on WAR1" % o.get("census"))
        self.assertEqual(o.get("head"), [2, 4], "the WAR1 window head says %r, not 2 items / 4 copies" % o.get("head"))
        self.assertEqual(o.get("tileSay"), [2, 4], "the WAR1 shelf tile says %r, not 2 items in 4 copies" % o.get("tileSay"))
        self.assertEqual(o.get("tile"), {SHAKO: 2, BELT: 2}, "the WAR1 shelf tile draws %r" % o.get("tile"))

    def test_no_normal_mule_takes_them(self):
        self.assertNotIn(SHAKO, self.o.get("armor") or [], "an over-cap Shako was put on UNI-ARMOR's list too")

    def test_a_belt_he_filed_on_war1_is_counted_once(self):
        f = self.f
        self.assertEqual((f.get("drawn") or {}).get(BELT), 6, "6 owned belts filed on WAR1 draw %r in its window" % f.get("drawn"))
        self.assertEqual((f.get("tile") or {}).get(BELT), 6, "6 owned belts filed on WAR1 draw %r on its tile" % f.get("tile"))
        self.assertEqual(f.get("head"), [2, 8], "filed belts 6 + over-cap Shakos 2: the window says %r" % f.get("head"))
        self.assertEqual(f.get("tileSay"), [2, 8], "the tile says %r" % f.get("tileSay"))


RED_PROOF = [
    {"why": "#144.11 (REG-2781) - the packer skips the over-cap copies again (the window draws an empty WAR1)",
     "file": "bible.html",
     "find": "      if (_woN && !(typeof window._vaultFiledOn === 'function' && window._vaultFiledOn(n) === muleId)) {\n",
     "replace": "      if (false) {\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 (REG-2781) - WAR1's name list leaves its planned copies out again",
     "file": "bible.html",
     "find": "          if (_wo11) Object.keys(_wo11).sort().forEach(function(n){ if (names.indexOf(n) < 0) names.push(n); }); } catch (eWo) {}",
     "replace": "          } catch (eWo) {}",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 (REG-2781) - the locker census says 0 items on WAR1 again",
     "file": "bible.html",
     "find": "          if (_wo11) Object.keys(_wo11).forEach(function(n){ if (n) names[n] = 1; }); } catch (e4) {}",
     "replace": "          } catch (e4) {}",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 (REG-2781) - the window draws every copy of an over-cap name, not the ones planned there",
     "file": "bible.html",
     "find": "        for (var _wi = 0; _wi < _woN - _ww; _wi++)\n",
     "replace": "        for (var _wi = 0; _wi < ((typeof copyCount === 'function' ? copyCount(n) : 1) || 1) - _ww; _wi++)\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 sweep (REG-2781) - the tile counts a belt filed on WAR1 twice again (8 cells for 6)",
     "file": "bible.html",
     "find": "      if (_wo && _wo[n]) c = (window._vaultFiledOn && window._vaultFiledOn(n) === muleId) ? c : _wo[n];",
     "replace": "      if (_wo && _wo[n]) c = (window._vaultFiledOn && window._vaultFiledOn(n) === muleId ? c : 0) + _wo[n];",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 sweep (REG-2781) - the window adds the over-cap copies to a name filed there too",
     "file": "bible.html",
     "find": "      var _w = Math.min(cc, Math.max(0, (worn && worn[n]) | 0));\n",
     "replace": "      if (_woN) cc += _woN;\n      var _w = Math.min(cc, Math.max(0, (worn && worn[n]) | 0));\n",
     "matches": 1, "needs": "node"},
    {"why": "#144.11 sweep (REG-2781) - a filed belt takes the over-cap branch and draws 2 of its 6",
     "file": "bible.html",
     "find": "      if (_woN && !(typeof window._vaultFiledOn === 'function' && window._vaultFiledOn(n) === muleId)) {\n",
     "replace": "      if (_woN) {\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
