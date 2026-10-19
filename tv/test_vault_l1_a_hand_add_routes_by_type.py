# -*- coding: utf-8 -*-
"""Vault L1 — a hand add routes by its type, reads MANUAL to its target cell, and opens BEFORE | AFTER.

Elad, 2026-10-19: "the manual version of it is me adding item by item and just making sure all items are
properly being routed to the right mules/stashed/throwout" - "jewels too" - "the demonstration there from manual on
the left and the right side should still be like the visual rendering ... with the cross reference".

Driven on the SHIPPED page through the real door (window.vaultHandAdd) with AUTO INTAKE off:
  - a set piece, a unique, a runeword, a grand charm, a jewel and an amulet each get ONE auto move row,
    FROM = MANUAL (no cell), TO = the mule its type routes to, at a real cell;
  - each footprint is the game's (2x3 armor, 2x2 helm, 2x4 polearm, 1x3 grand charm, 1x1 jewel / amulet, 2x1 belt);
  - placement is append-only: a later, larger add never lands on a cell already given (ruling 1);
  - a first real sighting upgrades the SAME row to a real FROM cell (ruling 4);
  - an item seen on the equipment is locked: no move row; seen off the character again, it is routed (ruling 8);
  - clicking the row opens BEFORE (MANUAL badge, or the real grid once seen) and AFTER (the organized grid with the
    item at its target), real art in real cells, the same ring on both, one instruction line, and it closes cleanly.
NO CHROME AT ALL = a declared skip, never a pass. RED_PROOF below. [[regression-guard]] [[heart-first]]
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}

# typed name -> (type, the name the vault files it under, expected mule holder, footprint w x h)
BY_TYPE = [
    ("set", "Tal Rasha's Guardianship", "Tal Rasha's Guardianship (armor)", "SETS-TAL-IK", (2, 3)),
    ("unique", "Harlequin Crest", "Harlequin Crest (Shako)", "SHARED STASH", (2, 2)),
    ("runeword", "Insight", "Insight", "RUNEWORDS", (2, 4)),
    ("charm", "Gheed's Fortune", "Gheed's Fortune", "UNI-SMALL", (1, 3)),
    ("jewel", "Rainbow Facet", "Rainbow Facet", "SHARED STASH", (1, 1)),
    ("amulet", "Nokozan Relic", "Nokozan Relic", "UNI-SMALL", (1, 1)),
    ("belt", "Arachnid Mesh", "Arachnid Mesh", "SHARED STASH", (2, 1)),
    ("war runeword", "Enigma", "Enigma", "SHARED STASH", (2, 3)),
]

READ = r"""
function recs(){ try { return (JSON.parse(LSR.getItem('d2r_vaultRecords') || '{}').records || []); } catch (e) { return []; } }
function moveOf(nm){ return recs().filter(function(r){ return r.name === nm && r.move; }).map(function(r){ return r.move; }); }
"""


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def fresh():
    board().seed({"d2r_owned": [], "d2r_vaultProv": {}, "d2r_muleAssign": {}, "d2r_vaultRecords": None})


def add_all(names):
    return board().run(READ + "window._vaultAutoIntakeSet(false); OUT.add = {};"
                       "%s.forEach(function(n){ var a = window.vaultHandAdd(n); OUT.add[n] = { ok: a && a.ok, name: a && a.name, why: a && a.why }; });"
                       % json.dumps(names))


def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class AHandAddRoutesByType(unittest.TestCase):

    def test_each_type_gets_one_manual_row_to_its_mule_at_a_real_cell(self):
        fresh()
        typed = [t[1] for t in BY_TYPE]
        add_all(typed)
        o = board().run(READ + "OUT.m = {}; %s.forEach(function(n){ OUT.m[n] = moveOf(n); });"
                        "var host = document.getElementById('vault-move-list');"
                        "OUT.rows = host ? Array.prototype.map.call(host.querySelectorAll('.vmv-row'), function(r){"
                        "  return { name: r.getAttribute('data-name'), manual: !!r.querySelector('.vmv-manual-badge'), text: r.textContent }; }) : [];"
                        % json.dumps([t[2] for t in BY_TYPE]))
        for kind, _typed, nm, holder, _fp in BY_TYPE:
            mv = o["m"][nm]
            self.assertEqual(len(mv), 1, "%s (%s) has %d move rows, not one: %r" % (nm, kind, len(mv), mv))
            mv = mv[0]
            self.assertTrue(mv["manual"], "%s (%s) is not a MANUAL row: %r" % (nm, kind, mv))
            self.assertIsNone(mv["from"]["cell"], "%s (%s) invented a FROM cell: %r" % (nm, kind, mv))
            self.assertEqual(mv["to"]["holder"], holder, "%s (%s) routed to the wrong mule: %r" % (nm, kind, mv))
            self.assertRegex(mv["to"]["cell"] or "", r"^(stash|shared|inventory):c\d+r\d+$", "%s (%s) has no target cell" % (nm, kind))
            row = [r for r in o["rows"] if r["name"] == nm]
            self.assertEqual(len(row), 1, "%s does not paint exactly one row: %r" % (nm, row))
            self.assertTrue(row[0]["manual"], "%s row does not wear the MANUAL badge: %r" % (nm, row))
            self.assertIn(holder, row[0]["text"])

    def test_each_type_packs_at_the_game_footprint(self):
        o = board().run("OUT.c = {}; %s.forEach(function(n){ OUT.c[n] = window._itemCells(n); });" % json.dumps([t[2] for t in BY_TYPE]))
        for kind, _t, nm, _h, fp in BY_TYPE:
            c = o["c"][nm]
            self.assertEqual((c["w"], c["h"]), fp, "%s (%s) footprint %r, the game's is %r" % (nm, kind, c, fp))
            self.assertFalse(c.get("approx"), "%s (%s) footprint is a guess: %r" % (nm, kind, c))

    def test_placement_is_append_only_and_no_two_targets_overlap(self):
        fresh()
        add_all(["Harlequin Crest"])
        first = board().run(READ + "OUT.c = moveOf('Harlequin Crest (Shako)')[0].to.cell;")["c"]
        add_all(["Annihilus"])
        nxt = board().run(READ + "OUT.c = moveOf('Annihilus')[0].to.cell;")["c"]
        self.assertEqual(nxt, "shared:c2r0", "the next add did not take the next free cell beside Shako: %r" % nxt)
        add_all(["Enigma", "Rainbow Facet", "Arachnid Mesh", "Insight", "Spirit"])
        o = board().run(READ + "OUT.r = recs().filter(function(r){ return r.move && r.move.to && r.move.to.cell; }).map(function(r){"
                        " var s = window.vaultSize(r.name); return [r.name, r.move.to.holder, r.move.to.cell, s[0], s[1]]; });")
        shako = [r for r in o["r"] if r[0] == "Harlequin Crest (Shako)"]
        self.assertEqual(shako[0][2], first, "a later add moved the cell Shako was already given: %r -> %r" % (first, shako))
        import re
        rects = []
        for nm, holder, cell, w, h in o["r"]:
            m = re.match(r"^(\w+):c(\d+)r(\d+)$", cell)
            rects.append((nm, holder, m.group(1), (int(m.group(2)), int(m.group(3)), w, h)))
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                if a[1] == b[1] and a[2] == b[2]:
                    self.assertFalse(overlap(a[3], b[3]), "%s and %s were sent to overlapping cells: %r %r" % (a[0], b[0], a, b))

    def test_a_first_sighting_upgrades_the_same_row_to_a_real_from_cell(self):
        fresh()
        add_all(["Insight"])
        o = board().run(READ + "var before = moveOf('Insight')[0]; window._vaultAutoIntakeSet(true);"
                        "OUT.ap = window._vaultMoveApplySight('Insight', { holder: 'MULE-3', location: 'stash', cell: 'stash:c4r2', frame: 'f_1' });"
                        "OUT.mv = moveOf('Insight'); OUT.before = before;"
                        "var row = document.querySelector('#vault-move-list .vmv-row[data-name=\"Insight\"]');"
                        "OUT.badge = !!(row && row.querySelector('.vmv-manual-badge')); OUT.text = row ? row.textContent : null;"
                        "OUT.nrows = document.querySelectorAll('#vault-move-list .vmv-row[data-name=\"Insight\"]').length;")
        self.assertTrue(o["ap"]["applied"], o)
        self.assertEqual(len(o["mv"]), 1, "the sighting made a second row: %r" % o["mv"])
        mv = o["mv"][0]
        self.assertEqual(mv["from"]["cell"], "stash:c4r2", "the row did not take the real FROM cell: %r" % mv)
        self.assertEqual(mv["from"]["holder"], "MULE-3")
        self.assertEqual(mv["to"], o["before"]["to"], "the sighting changed the target: %r" % mv)
        self.assertEqual(mv["status"], "to-move", mv)
        self.assertIn("f_1", mv["evidence"], mv)
        self.assertEqual(o["nrows"], 1)
        self.assertFalse(o["badge"], "the upgraded row still wears MANUAL")
        self.assertIn("MULE-3", o["text"])

    def test_an_equipped_item_gets_no_row_and_is_routed_once_seen_off_the_character(self):
        fresh()
        add_all(["Insight"])
        o = board().run(READ + "window._vaultAutoIntakeSet(true);"
                        "window._vaultMoveApplySight('Insight', { holder: 'MAIN', location: 'equipment', cell: 'equipment:c0r0', frame: 'e_1' });"
                        "OUT.worn = document.querySelectorAll('#vault-move-list .vmv-row[data-name=\"Insight\"]').length;"
                        "OUT.wornMv = moveOf('Insight')[0];"
                        "window._vaultMoveApplySight('Insight', { holder: 'MAIN', location: 'stash', cell: 'stash:c1r1', frame: 'e_2' });"
                        "OUT.off = document.querySelectorAll('#vault-move-list .vmv-row[data-name=\"Insight\"]').length;"
                        "OUT.offMv = moveOf('Insight')[0];")
        self.assertEqual(o["worn"], 0, "an equipped item got a move row: %r" % o["wornMv"])
        self.assertEqual(o["off"], 1, "seen off the character, it was not routed: %r" % o["offMv"])
        self.assertEqual(o["offMv"]["from"]["cell"], "stash:c1r1", o["offMv"])
        self.assertEqual(o["offMv"]["status"], "to-move", o["offMv"])

    def test_clicking_a_row_opens_before_and_after_with_real_art_and_closes(self):
        fresh()
        add_all(["Gheed's Fortune", "Nokozan Relic"])
        o = board().run(READ + "var row = document.querySelector('#vault-move-list .vmv-row[data-name=\"Nokozan Relic\"]'); row.click();"
                        "var h = document.getElementById('vault-move-compare'); OUT.open = !!(h && !h.hidden);"
                        "OUT.say = (h.querySelector('.vmc-say') || {}).textContent;"
                        "OUT.manualLeft = !!h.querySelector('.vmc-before .vmv-manual-badge');"
                        "OUT.leftGrid = !!h.querySelector('.vmc-before .vd-grid');"
                        "OUT.afterItems = Array.prototype.map.call(h.querySelectorAll('.vmc-after .vd-item'), function(e){ return e.getAttribute('title') || e.textContent; });"
                        "OUT.afterArt = h.querySelectorAll('.vmc-after .vd-item img, .vmc-after .vd-item .d2art, .vmc-after .vd-item [class*=art]').length;"
                        "OUT.ring = (h.querySelector('.vmc-after .vmc-ring') || {getAttribute:function(){return null;}}).getAttribute('data-ring');"
                        "OUT.to = moveOf('Nokozan Relic')[0].to.cell;"
                        "h.querySelector('.vmc-close').click(); OUT.closed = h.hidden === true && h.innerHTML === '';"
                        "window._vaultAutoIntakeSet(true);"
                        "window._vaultMoveApplySight('Nokozan Relic', { holder: 'MULE-2', location: 'stash', cell: 'stash:c3r1', frame: 'n_1' });"
                        "document.querySelector('#vault-move-list .vmv-row[data-name=\"Nokozan Relic\"]').click();"
                        "OUT.seenLeftGrid = !!h.querySelector('.vmc-before .vd-grid');"
                        "OUT.seenLeftRing = (h.querySelector('.vmc-before .vmc-ring') || {getAttribute:function(){return null;}}).getAttribute('data-ring');"
                        "OUT.seenManual = !!h.querySelector('.vmc-before .vmv-manual-badge');"
                        "OUT.seenSay = (h.querySelector('.vmc-say') || {}).textContent;"
                        "h.click(); OUT.backdrop = h.hidden === true;")
        self.assertTrue(o["open"], o)
        self.assertTrue(o["manualLeft"] and not o["leftGrid"], "BEFORE of a hand-typed row is not the MANUAL badge: %r" % o)
        self.assertTrue(any("Nokozan Relic" in (x or "") for x in o["afterItems"]), "AFTER does not draw the item: %r" % o)
        self.assertTrue(any("Gheed" in (x or "") for x in o["afterItems"]), "AFTER is not the organized container: %r" % o)
        self.assertGreaterEqual(o["afterArt"], 1, "AFTER tiles carry no item art")
        import re
        m = re.match(r"^stash:c(\d+)r(\d+)$", o["to"])
        self.assertEqual(o["ring"], "%s,%s" % (m.group(1), m.group(2)), "AFTER rings a cell that is not the target")
        self.assertIn("Move Nokozan Relic from MANUAL to UNI-SMALL", o["say"])
        self.assertTrue(o["closed"], "close left the view up")
        self.assertTrue(o["seenLeftGrid"] and not o["seenManual"], "once seen, BEFORE is not the real grid: %r" % o)
        self.assertEqual(o["seenLeftRing"], "3,1", o)
        self.assertIn("from MULE-2 private stash (4,2)", o["seenSay"])
        self.assertTrue(o["backdrop"], "a backdrop click did not close the view")

    def test_a_hand_typed_base_routes_to_the_bases_mule_at_its_footprint(self):
        fresh()
        bases = [("Monarch", (2, 3)), ("Archon Plate", (2, 3)), ("Eth Thresher", (2, 4)), ("Ethereal Archon Plate", (2, 3))]
        a = add_all([b for b, _ in bases])["add"]
        o = board().run(READ + "OUT.m = {}; OUT.c = {}; %s.forEach(function(n){ OUT.m[n] = moveOf(n); OUT.c[n] = window.vaultSize(n); });"
                        "OUT.rows = document.querySelectorAll('#vault-move-list .vmv-row .vmv-manual-badge').length;"
                        % json.dumps([b for b, _ in bases]))
        import re
        rects = []
        for nm, fp in bases:
            self.assertTrue(a[nm]["ok"], "the hand door refused the base %s: %r" % (nm, a[nm]))
            mv = o["m"][nm]
            self.assertEqual(len(mv), 1, "%s has %d rows: %r" % (nm, len(mv), mv))
            self.assertTrue(mv[0]["manual"] and mv[0]["from"]["cell"] is None, mv)
            self.assertEqual(mv[0]["to"]["holder"], "SOCKETED", "%s did not route to the bases mule: %r" % (nm, mv))
            self.assertEqual(tuple(o["c"][nm]), fp, "%s footprint %r" % (nm, o["c"][nm]))
            m = re.match(r"^stash:c(\d+)r(\d+)$", mv[0]["to"]["cell"])
            rects.append((nm, (int(m.group(1)), int(m.group(2)), fp[0], fp[1])))
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                self.assertFalse(overlap(rects[i][1], rects[j][1]), "bases overlap: %r" % rects)
        self.assertEqual(o["rows"], len(bases))

    def test_a_hand_typed_base_changes_no_other_list(self):
        # a base owned through any OTHER door (no hand receipt) stays exactly where it was: not in records, not in the pool
        board().seed({"d2r_owned": ["Monarch", "Insight"], "d2r_vaultProv": {}, "d2r_muleAssign": {}, "d2r_vaultRecords": None})
        o = board().run("var rn = function(){ return (window._vaultRecords().records || []).map(function(r){ return r.name; }).sort(); };"
                        "OUT.pool0 = ownedPool(); OUT.dock0 = window._vaultDockNames(); OUT.rec0 = rn(); OUT.hb0 = window._vaultHandBasePool();"
                        "window._vaultAutoIntakeSet(false); OUT.add = window.vaultHandAdd('Archon Plate');"
                        "OUT.pool1 = ownedPool(); OUT.dock1 = window._vaultDockNames(); OUT.rec1 = rn(); OUT.hb1 = window._vaultHandBasePool();")
        self.assertTrue(o["add"]["ok"], o["add"])
        self.assertEqual(o["hb0"], [], "a base he never typed counted as hand-typed: %r" % o["hb0"])
        self.assertNotIn("Monarch", o["rec0"], "a non-hand base entered the records: %r" % o["rec0"])
        self.assertEqual(o["pool0"], o["pool1"], "ownedPool changed")
        self.assertEqual(o["dock0"], o["dock1"], "the dock changed")
        self.assertEqual(o["hb1"], ["Archon Plate"], o["hb1"])
        self.assertEqual(sorted(set(o["rec1"]) - set(o["rec0"])), ["Archon Plate"], "records changed beyond the typed base: %r -> %r" % (o["rec0"], o["rec1"]))
        self.assertTrue(set(o["rec0"]) <= set(o["rec1"]))

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("vault L1 hand add: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar, msg)


RED_PROOF = [
    {"why": "The hand door refuses a catalogue base again.",
     "file": "bible.html",
     "find": "if (!_vaultKeeps(r.name) && !_vaultHandBase(r.name)) /* L1 a catalogue base passes the hand door */",
     "replace": "if (!_vaultKeeps(r.name)) /* L1 a catalogue base passes the hand door */",
     "matches": 1},
    {"why": "An ethereal base is not recognised as its catalogue base.",
     "file": "bible.html",
     "find": ".replace(/^(eth|ethereal)\\s+/i, '').toLowerCase();",
     "replace": ".toLowerCase();",
     "matches": 1},
    {"why": "The packer leaves hand-typed bases out, so they get no target cell.",
     "file": "bible.html",
     "find": "try { if (typeof window._vaultHandBasePool === 'function') pool = pool.concat(window._vaultHandBasePool()); } catch (eHb) {} /* L1 hand bases pack */",
     "replace": "/* L1 hand bases pack */",
     "matches": 1},
    {"why": "The records leave hand-typed bases out, so the row is never saved.",
     "file": "bible.html",
     "find": "try { if (typeof window._vaultHandBasePool === 'function') poolAll = poolAll.concat(window._vaultHandBasePool()); } catch (eHb) {} /* L1 hand bases record */",
     "replace": "/* L1 hand bases record */",
     "matches": 1},
    {"why": "Any owned base counts as hand-typed, so a base from another door enters the records.",
     "file": "bible.html",
     "find": "if (p && p.source === 'hand' && /Add an item/.test(String(p.where || p.by || ''))) out.push(n); /* L1 hand-typed base */",
     "replace": "out.push(n); /* L1 hand-typed base */",
     "matches": 1},
    {"why": "Saved targets are not reserved, so a later bigger add is packed onto the cell Shako was given.",
     "file": "bible.html",
     "find": "    }); /* L1 append-only occ */",
     "replace": "    }); kept = {}; occBy = {}; /* L1 append-only occ */",
     "matches": 1},
    {"why": "The saved cell is dropped from the pack, so the item is re-packed.",
     "file": "bible.html",
     "find": "if (kept[n + '\\u0000' + i]) continue; /* L1 saved cell stays */",
     "replace": "/* L1 saved cell stays */",
     "matches": 1},
    {"why": "The stash grid ignores the taken rectangles.",
     "file": "bible.html",
     "find": "var st = packGrid(items, 10, 10, occBy.stash);",
     "replace": "var st = packGrid(items, 10, 10);",
     "matches": 1},
    {"why": "The shared grid ignores the taken rectangles.",
     "file": "bible.html",
     "find": "lay(packGrid(items, 10, 10, occBy.shared).placed, 'shared');",
     "replace": "lay(packGrid(items, 10, 10).placed, 'shared');",
     "matches": 1},
    {"why": "A sighting no longer upgrades the MANUAL row, so it reads moved-elsewhere with no FROM cell.",
     "file": "bible.html",
     "find": "if (t.manual && t.status === 'to-move' && !atTo && (t.from == null",
     "replace": "if (false && t.manual && t.status === 'to-move' && !atTo && (t.from == null",
     "matches": 1},
    {"why": "The upgrade writes a fresh target, so the sighting moves where he was sent.",
     "file": "bible.html",
     "find": "var up = _vaultMoveTask({ name: name, from: place, to: t.to, status: 'to-move', evidence: ev0, manual: true }); /* L1 sighting upgrades the manual row */",
     "replace": "var up = _vaultMoveTask({ name: name, from: place, to: place, status: 'to-move', evidence: ev0, manual: true }); /* L1 sighting upgrades the manual row */",
     "matches": 1},
    {"why": "The sighting frame is not kept as the upgrade's proof.",
     "file": "bible.html",
     "find": "if (sighting.frame != null && sighting.frame !== '' && ev0.indexOf(String(sighting.frame)) < 0) ev0.push(String(sighting.frame));",
     "replace": "void ev0;",
     "matches": 1},
    {"why": "An equipped item gets a move row.",
     "file": "bible.html",
     "find": "if (_vaultMoveWorn(t.from)) return false; /* L1 equipped is locked, no move row */",
     "replace": "/* L1 equipped is locked, no move row */",
     "matches": 1},
    {"why": "An item seen worn stays locked after it is seen off the character.",
     "file": "bible.html",
     "find": "(t.from == null || t.from.cell == null || _vaultMoveWorn(t.from))",
     "replace": "(t.from == null || t.from.cell == null)",
     "matches": 1},
    {"why": "Clicking a row opens the evidence panel, not BEFORE | AFTER.",
     "file": "bible.html",
     "find": "          + ' onclick=\"' + esc(compare) + '\">'",
     "replace": "          + ' onclick=\"' + esc(opener) + '\">'",
     "matches": 1},
    {"why": "BEFORE of a seen row stays the MANUAL badge.",
     "file": "bible.html",
     "find": "    var left = m.manual\n",
     "replace": "    var left = true\n",
     "matches": 1},
    {"why": "AFTER draws only the item, not the organized container.",
     "file": "bible.html",
     "find": "      if (!c || !to || String(mv.to.holder || '') !== String(t.to.holder || '') || c.loc !== to.loc) return;",
     "replace": "      if (!c || !to || k.split('\\u0000')[0] !== name) return;",
     "matches": 1},
    {"why": "The ring is drawn at the origin instead of the target cell.",
     "file": "bible.html",
     "find": "return '<div class=\"vmc-ring\" data-ring=\"' + c.x + ',' + c.y + '\"",
     "replace": "c = { x: 0, y: 0 }; return '<div class=\"vmc-ring\" data-ring=\"' + c.x + ',' + c.y + '\"",
     "matches": 1},
    {"why": "Close leaves the view up.",
     "file": "bible.html",
     "find": "    if (host){ host.hidden = true; host.innerHTML = ''; }\n  }\n  function _vaultMoveHtml",
     "replace": "    void host;\n  }\n  function _vaultMoveHtml",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
