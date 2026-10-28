# -*- coding: utf-8 -*-
"""#111 (REG-2786) - THE MULE CARD HEADER STOPPED COUNTING AT 3 COPIES. A keeper target was drawn as copies held.

Every copy count on the vault - the locker card's cells and its "N items in M copies" line (REG-2738), the mule card's
"N items total · M copies" header, the records model and the mule packer - asks _vaultPresenceSpan. Once any look names a
cell (v3767) it answered the distinct cells, or the keeper TARGET whenever that was larger, and never read copies[]. The
default targets are 3 for The Stone of Jordan, Mara's Kaleidoscope and Shako. Measured on the whole page in node:

  * Mara's Kaleidoscope seen in one cell, held x1: 3 cells on the card and "3 copies" on the mule card (a want drawn as held);
  * the same item held x3 and typed twice more by hand: still 3 (the door answered "x5 - another copy, its own row and cell");
  * Griswold's Edge seen in 3 cells, typed twice more: 3, and the two typed copies got MANUAL move rows with no cell;
  * a planner pick of a filed Obedience seen in one cell: "copy 2 filed", and the count stayed 1.

Now a target counts only as far as copies[] holds (his v3767 rule: a multi-keep re-read under its target is a real copy; the
target alone is none), and a copy his hand types past what the cells count raises the target at the hand door - the rule L1
already kept for a set piece - so every surface draws it. The planner's undo puts the target back. The move planner counts
through the same span. The v3767 guard stands: a unique whose re-reads of ONE cell climbed copies[] to 4 is still one copy.
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
import vault_page_node as VPN  # noqa: E402


def _look(i, x, session=None):
    return {"id": session or ("s_law_%d" % i), "frame": "%d_100" % i, "conf": None, "at": "2026-10-2%dT08:00:00.000Z" % (i % 8),
            "loc": "stash", "scene": "stash", "holder": "MULE1", "cell": {"x": x, "y": 0, "container": "stash"}}


def _prelude(items):
    """items: {name: (mule, copies, looks)} on a fresh store with the page's default keeper targets."""
    prov = {n: {"mule": m, "source": "tv", "by": "tv", "at": "2026-10-20T08:00:00.000Z", "looks": looks, "kind": "filing"}
            for n, (m, c, looks) in items.items() if looks}
    copies = {n: c for n, (m, c, looks) in items.items() if c > 1}
    return ("localStorage.setItem('d2r_ownerClaim', '*');\n"
            "localStorage.setItem('d2r_owned', %s);\n" % json.dumps(json.dumps(sorted(items)))
            + "localStorage.setItem('d2r_copies', %s);\n" % json.dumps(json.dumps(copies))
            + "localStorage.setItem('d2r_muleAssign', %s);\n" % json.dumps(json.dumps({n: v[0] for n, v in items.items()}))
            + "localStorage.setItem('d2r_vaultProv', %s);\n" % json.dumps(json.dumps(prov)))


HELPERS = r"""
var W = window;
function paint(){ try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); } H.flush(60, 3); }
function card(mule){
  var html = String((document.getElementById('vault-shelf') || {}).innerHTML || '');
  var at = html.indexOf('data-vault-mule="' + mule + '"');
  if (at < 0) return { found: false };
  var next = html.indexOf('data-vault-mule="', at + 10), chunk = html.slice(at, next < 0 ? html.length : next);
  var m = /<div class="vm-copies"[^>]*>([\s\S]*?)<\/div>/.exec(chunk);
  return { found: true, line: m ? m[1].replace(/<[^>]+>/g, '') : null };
}
function header(mule){
  try { W.openMuleCard(mule); } catch (e) { return 'open failed: ' + (e && e.message); }
  H.flush(60, 3);
  var h = String((document.getElementById('vault-detail') || {}).innerHTML || '');
  var m = /<span class="vd-sub">([^<]*total[^<]*)<\/span>/.exec(h);
  return m ? m[1].split(' · pack')[0] : null;
}
function count(n, mule){
  return { have: copyCount(n), span: W._vaultPresenceSpan(n, copyCount(n)), target: multiTarget(n),
           shelf: W._shelfCopyCount(n, mule), records: (W._vaultRecordsForMule(mule) || {})[n] || 0 };
}
function moves(n){
  var raw = null; try { raw = JSON.parse(W.LSR.getItem('d2r_vaultRecords') || 'null'); } catch (e) {}
  return ((raw && raw.records) || []).filter(function(r){ return r.name === n; })
    .map(function(r){ return { ix: r.copyIx, manual: !!(r.move && r.move.manual), cell: (r.move && r.move.to && r.move.to.cell) || null }; });
}
"""

MARA, SOJ, GRIS, GRIF, ANDY, LIGHT, OBED = ("Mara's Kaleidoscope", "The Stone of Jordan", "Griswold's Edge", "Griffon's Eye",
                                           "Andariel's Visage", "Lightsabre", "Obedience")

CASES = {
    # 1 - a target is a want: held x1 in one cell is one copy, not the target's 3
    "want": (_prelude({MARA: ("uni-small", 1, [_look(1, 0)])}),
             HELPERS + "paint(); OUT.c = count(%s, 'uni-small'); OUT.card = card('uni-small'); OUT.head = header('uni-small');"
             % json.dumps(MARA)),
    # 2 - the header that stopped at 3: x3 at its target, two more typed by hand
    "three": (_prelude({SOJ: ("uni-small", 3, [_look(2, 0)])}),
              HELPERS + "paint(); var N = %s; OUT.c0 = count(N, 'uni-small');"
              "OUT.a = [W.vaultHandAdd(N, new Date().toISOString(), {}), W.vaultHandAdd(N, new Date().toISOString(), {})]"
              ".map(function(r){ return r && r.mode + ':' + r.copies; });"
              "paint(); OUT.c = count(N, 'uni-small'); OUT.card = card('uni-small'); OUT.head = header('uni-small'); OUT.mv = moves(N);"
              % json.dumps(SOJ)),
    # 3 - no target: seen in 3 cells, typed twice more; and a name with no cell gains no target from a typed copy
    "cells": (_prelude({GRIS: ("uni-weap", 3, [_look(3, 0), _look(4, 2), _look(5, 4)]), LIGHT: ("wip", 1, [])}),
              HELPERS + "paint(); var N = %s; OUT.c0 = count(N, 'uni-weap');"
              "OUT.a = [W.vaultHandAdd(N, new Date().toISOString(), {}), W.vaultHandAdd(N, new Date().toISOString(), {})]"
              ".map(function(r){ return r && r.mode + ':' + r.copies; });"
              "OUT.l = W.vaultHandAdd(%s, new Date().toISOString(), {}); OUT.l = OUT.l && OUT.l.mode + ':' + OUT.l.copies;"
              "paint(); OUT.c = count(N, 'uni-weap'); OUT.card = card('uni-weap'); OUT.head = header('uni-weap'); OUT.mv = moves(N);"
              "OUT.lt = multiTarget(%s); OUT.lc = count(%s, 'wip');"
              % (json.dumps(GRIS), json.dumps(LIGHT), json.dumps(LIGHT), json.dumps(LIGHT))),
    # 4 - the v3767 guard: one cell re-read into copies[] 4 is one copy; a target above the cells counts what is held under it
    "guard": (_prelude({GRIF: ("uni-armor", 4, [_look(6, 3, "g1"), _look(7, 3, "g2"), _look(8, 3, "g3")]),
                        ANDY: ("wip", 3, [_look(9, 1)])}),
              HELPERS + "paint(); OUT.g = count(%s, 'uni-armor'); OUT.v = count(%s, 'wip');" % (json.dumps(GRIF), json.dumps(ANDY))),
    # 5 - the planner's copy of a filed name seen in one cell, then the pick cleared
    "planner": (_prelude({OBED: ("runewords", 1, [_look(10, 5)])}),
                HELPERS + "paint(); var N = %s, it = W._cbItem('r92'), b = (W._cbBasesOf(it) || [])[0];"
                "var p = W.vaultPlannerFile({ id: 'r92', base: b, affixes: [], sockets: 0 }, 'law-copy');"
                "OUT.p = p && { mode: p.mode, filed: p.filed }; paint(); OUT.c = count(N, 'runewords');"
                "OUT.mkIn = Object.prototype.hasOwnProperty.call(multiKeep, N);"
                "var cl = W.vaultPlannerFile(null, 'law-copy'); OUT.cl = cl && cl.mode; paint(); OUT.c2 = count(N, 'runewords');"
                "OUT.mkGone = !Object.prototype.hasOwnProperty.call(multiKeep, N);"
                "OUT.stored = JSON.parse(W.LSR.getItem('d2r_multiKeep') || '{}')[N] == null;"
                % json.dumps(OBED)),
}


class ACopyPastTheCellsIsCounted(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = {k: VPN.run("(function(){" + body + "\nOUT.errors = H.errors.slice();})();", prelude=pre, timeout=300)
                 for k, (pre, body) in CASES.items()}

    def test_every_case_booted_clean(self):
        for k, o in self.o.items():
            self.assertEqual(o["__boot"]["errors"], [], "%s: %r" % (k, o["__boot"]))
            self.assertNotIn("renderErr", o, "%s: %r" % (k, o.get("renderErr")))
            self.assertEqual(o["errors"], [], k)

    def test_a_keeper_target_is_never_drawn_as_copies_held(self):
        o = self.o["want"]
        self.assertEqual((o["c"]["have"], o["c"]["target"]), (1, 3), "PREMISE: Mara's held x1 under the default target 3: %r" % o)
        self.assertEqual((o["c"]["span"], o["c"]["shelf"], o["c"]["records"]), (1, 1, 1),
                         "one copy held was drawn as the keeper target: %r" % o["c"])
        self.assertTrue(o["card"]["found"], o)
        self.assertIsNone(o["card"]["line"], "the locker card says copies for one item held once: %r" % o["card"])
        self.assertEqual(o["head"], "1 item total", "the mule card header counts copies he does not hold: %r" % o["head"])

    def test_the_mule_card_header_counts_past_three(self):
        o = self.o["three"]
        self.assertEqual((o["c0"]["have"], o["c0"]["target"], o["c0"]["span"]), (3, 3, 3), "PREMISE: %r" % o["c0"])
        self.assertEqual(o["a"], ["copy:4", "copy:5"], "PREMISE: the hand door did not take two more copies: %r" % o["a"])
        c = o["c"]
        self.assertEqual((c["have"], c["span"], c["shelf"], c["records"]), (5, 5, 5, 5), "the count stopped at 3: %r" % c)
        self.assertEqual(c["target"], 5, "his typed copies did not move the target the count reads: %r" % c)
        self.assertEqual(o["card"]["line"], "1 item in 5 copies", o["card"])
        self.assertEqual(o["head"], "1 item total · 5 copies", "the mule card header stopped counting: %r" % o["head"])
        self.assertEqual([m["ix"] for m in o["mv"]], [0, 1, 2, 3, 4], o["mv"])

    def test_copies_typed_past_the_cells_are_drawn_with_their_own_cell(self):
        o = self.o["cells"]
        self.assertEqual((o["c0"]["have"], o["c0"]["span"], o["c0"]["target"]), (3, 3, 1), "PREMISE: %r" % o["c0"])
        self.assertEqual(o["a"], ["copy:4", "copy:5"], o["a"])
        c = o["c"]
        self.assertEqual((c["have"], c["span"], c["shelf"], c["records"]), (5, 5, 5, 5),
                         "two copies he typed past the 3 cells were never drawn: %r" % c)
        self.assertEqual(o["card"]["line"], "1 item in 5 copies", o["card"])
        self.assertEqual(o["head"], "1 item total · 5 copies", o["head"])
        typed = [m for m in o["mv"] if m["ix"] >= 3]
        self.assertEqual([m["ix"] for m in typed], [3, 4], "a typed copy has no record: %r" % o["mv"])
        self.assertTrue(all(m["manual"] for m in typed), o["mv"])
        self.assertTrue(all(m["cell"] for m in typed), "a typed copy's MANUAL row names the mule and no cell: %r" % o["mv"])
        self.assertEqual(len(set(m["cell"] for m in o["mv"])), 5, "two copies share one planned cell: %r" % o["mv"])
        self.assertEqual(o["l"], "copy:2", o)
        self.assertEqual((o["lt"], o["lc"]["span"]), (1, 2), "a name with no cell gained a keeper target from a typed copy: %r" % o)

    def test_one_cell_re_read_into_copies_stays_one_copy(self):
        o = self.o["guard"]
        self.assertEqual((o["g"]["have"], o["g"]["span"], o["g"]["records"]), (4, 1, 1),
                         "re-reads of ONE cell are copies again (the v3767 guard): %r" % o["g"])
        self.assertEqual((o["v"]["have"], o["v"]["target"], o["v"]["span"], o["v"]["records"]), (3, 5, 3, 3),
                         "a target of 5 over 3 held drew the target: %r" % o["v"])

    def test_the_planners_copy_is_counted_and_its_undo_puts_the_target_back(self):
        o = self.o["planner"]
        self.assertEqual(o["p"], {"mode": "copy", "filed": True}, "PREMISE: the planner did not count a copy: %r" % o["p"])
        self.assertEqual((o["c"]["have"], o["c"]["span"], o["c"]["records"]), (2, 2, 2),
                         "the planner's copy 2 was never drawn: %r" % o["c"])
        self.assertTrue(o["mkIn"], o)
        self.assertEqual(o["cl"], "cleared", o)
        self.assertEqual((o["c2"]["have"], o["c2"]["span"], o["c2"]["target"]), (1, 1, 1), o["c2"])
        self.assertTrue(o["mkGone"] and o["stored"], "the cleared pick left the target it raised: %r" % o)


RED_PROOF = [
    {"why": "REG-2786 - the keeper target is drawn as copies held again",
     "file": "bible.html",
     "find": "          return Math.max(_nSg, Math.min((have > 0) ? (have | 0) : 1, _mkWant(name))); /* REG-2786 target is not a copy */\n",
     "replace": "          return _mkWant(name); /* REG-2786 target is not a copy */\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - a copy typed past the cells does not move the target, so it is never drawn",
     "file": "bible.html",
     "find": "                  && window._vaultPresenceSpan(pre.name, _cN) < _cN) _mkSetWant(pre.name, _cN); } catch (eMkC) {} /* REG-2786 hand copy past the cells */\n",
     "replace": "                  && false) _mkSetWant(pre.name, _cN); } catch (eMkC) {} /* REG-2786 hand copy past the cells */\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - every typed copy raises the target, a name with no cell too",
     "file": "bible.html",
     "find": "                  && window._vaultPresenceSpan(pre.name, _cN) < _cN) _mkSetWant(pre.name, _cN); } catch (eMkC) {} /* REG-2786 hand copy past the cells */\n",
     "replace": "                  && true) _mkSetWant(pre.name, _cN); } catch (eMkC) {} /* REG-2786 hand copy past the cells */\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - the planner's copy past the cells is never drawn",
     "file": "bible.html",
     "find": "                    && window._vaultPresenceSpan(nm, copies[nm]) < copies[nm]) { _mkSetWant(nm, copies[nm]); _mkSet = copies[nm]; } } catch (eMkP) {}\n",
     "replace": "                    && false) { _mkSetWant(nm, copies[nm]); _mkSet = copies[nm]; } } catch (eMkP) {}\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - the planner's undo leaves the target its copy raised",
     "file": "bible.html",
     "find": "        if (b.keepHad) multiKeep[b.name] = b.keepWas; else delete multiKeep[b.name];\n",
     "replace": "        if (b.keepHad) multiKeep[b.name] = b.keepWas;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - the move planner counts only the cells, so a typed copy's row has no cell",
     "file": "bible.html",
     "find": "       rows whose target named the mule and no cell. With no keeper target the span answers the cells, exactly as before. */\n    var cc = 1;\n",
     "replace": "       rows whose target named the mule and no cell. With no keeper target the span answers the cells, exactly as before. */\n"
                "    var g0 = (typeof _vaultSightGroups === 'function') ? _vaultSightGroups(name) : null; if (g0 && g0.length) return g0.length;\n"
                "    var cc = 1;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2786 - the count reads copies[] again and the v3767 one-cell guard falls",
     "file": "bible.html",
     "find": "      return _nSg; /* v3767 distinct cells */\n",
     "replace": "      return Math.max(_nSg, (have > 0) ? (have | 0) : 1); /* v3767 distinct cells */\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
