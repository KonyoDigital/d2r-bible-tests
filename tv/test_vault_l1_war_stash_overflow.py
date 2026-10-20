# -*- coding: utf-8 -*-
"""Vault L1 - every hand copy is its own item, cell and row; the war stash uses its 5 pages, then WAR1, WAR2.

Elad, live v3774 (2026-10-20): "a 2nd Aldur's Deception I added vanished - no row, no cell, no error". He owns
2-3 Arachnid Mesh, ~4 Andariel's Visage, ~3 Vampire Gaze, all war-stash (SHARED STASH) gear. His rulings:
  - a duplicate hand add is another physical copy: its own copyIx, the next free cell beside the first, its own
    MANUAL -> cell row (the Grief x2 copies[] store; a set piece he types twice is the spare he asked for);
  - the war stash has 5 pages (10x10 each), all used before any overflow;
  - overflow fills the mules named WAR1, then WAR2 ... (case-insensitive), in order;
  - none / all full: the item keeps NO cell and MOVE TASKS says so plainly; a mule is never created (Add mule is
    never pressed - the WAR mules here are seeded into the roster store, the way his saved roster holds them).
Driven on the SHIPPED page through the real door (window.vaultHandAdd), AUTO INTAKE off. RED_PROOF below.
NO CHROME AT ALL = a declared skip, never a pass. [[regression-guard]]
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_vault_l1_a_hand_add_routes_by_type as T  # noqa: E402  (its board, door and reader)
H = T.H

READ = T.READ + r"""
function mv(re){ return recs().filter(function(r){ return re.test(r.name) && r.move; }).map(function(r){ return { n: r.name, c: r.copyIx || 0, to: r.move.to }; }); }
function rows(re){ var h = document.getElementById('vault-move-list'); return h ? Array.prototype.filter.call(h.querySelectorAll('.vtk-list:not([data-sec="done"]) .vmv-row'), function(r){ return re.test(r.getAttribute('data-name') || ''); }).map(function(r){ return r.textContent.replace(/\s+/g, ' '); }) : null; }
"""
ENIGMA_PER_GRID = 15   # a 2x3 on a 10x10 grid: 5 across, 3 down


def tearDownModule():
    T.tearDownModule()


def roster_with(names):
    """the saved roster, plus mules named `names` (seeded like his saved store - never the Add mule button)"""
    T.fresh()
    r = T.board().run("OUT.r = JSON.parse(window.LSR.getItem('d2r_muleRoster') || 'null') || (window._vaultRosterNow && window._vaultRosterNow());")["r"]
    assert isinstance(r, list) and r, "PREMISE: the page saved no roster to extend: %r" % (r,)
    r = [m for m in r if not re.match(r"^war\s*\d*$", str(m.get("name", "")), re.I)]
    for i, n in enumerate(names):
        r.append({"id": "war-law-%d" % i, "name": n})
    T.board().seed({"d2r_muleRoster": r, "d2r_owned": [], "d2r_vaultProv": {}, "d2r_muleAssign": {},
                    "d2r_vaultRecords": None, "d2r_copies": {}, "d2r_multiKeep": {}})


def cells(moves):
    return [(m["to"] or {}).get("holder", None) and ((m["to"]["holder"], m["to"]["cell"])) for m in moves]


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class WarStashOverflow(unittest.TestCase):

    def test_two_hand_copies_of_a_set_piece_are_two_items_two_cells_two_rows(self):
        T.fresh()
        a = T.add_all(["Aldur's Deception", "Aldur's Deception"])["add"]
        o = T.board().run(READ + "OUT.m = mv(/^Aldur's Deception/); OUT.rows = rows(/^Aldur's Deception/);")
        self.assertEqual(len(o["m"]), 2, "the 2nd copy vanished: %r / %r" % (o["m"], a))
        self.assertEqual(sorted(m["c"] for m in o["m"]), [0, 1], o["m"])
        cs = cells(o["m"])
        self.assertTrue(all(c and c[1] for c in cs), "a copy has no cell: %r" % cs)
        self.assertEqual(len(set(cs)), 2, "two copies share one cell: %r" % cs)
        self.assertEqual(len(set(c[0] for c in cs)), 1, "the copies split mules: %r" % cs)
        self.assertEqual(len(o["rows"]), 2, "not two MOVE TASKS rows: %r" % o["rows"])
        for r in o["rows"]:
            self.assertRegex(r, r"MANUAL → SETS-[A-Z\-]+ \(\d+,\d+\)")

    def test_three_and_four_war_copies_each_get_a_cell_and_a_row(self):
        T.fresh()
        T.add_all(["Andariel's Visage"] * 4 + ["Vampire Gaze"] * 3 + ["Arachnid Mesh"] * 3)
        for nm, n in (("Andariel's Visage", 4), ("Vampire Gaze", 3), ("Arachnid Mesh", 3)):
            o = T.board().run(READ + "OUT.m = mv(new RegExp('^' + %s)); OUT.rows = rows(new RegExp('^' + %s));" % (json.dumps(nm), json.dumps(nm)))
            cs = cells(o["m"])
            self.assertEqual(len(cs), n, "%s: %d copies, %d items: %r" % (nm, n, len(cs), cs))
            self.assertEqual(len(set(cs)), n, "%s copies share cells: %r" % (nm, cs))
            self.assertTrue(all(c and c[0] == "SHARED STASH" for c in cs), "%s left the war stash: %r" % (nm, cs))
            self.assertEqual(len(o["rows"]), n, "%s: not %d rows: %r" % (nm, n, o["rows"]))
            for r in o["rows"]:
                self.assertRegex(r, r"MANUAL → SHARED STASH tab [1-5] \(\d+,\d+\)")

    def test_all_five_pages_fill_then_war1_then_war2(self):
        roster_with(["war1", "WAR2"])     # case-insensitive names
        n = 5 * ENIGMA_PER_GRID + ENIGMA_PER_GRID + 1
        T.add_all(["Enigma"] * n)
        o = T.board().run(READ + "OUT.m = mv(/^Enigma$/); OUT.full = window._vaultWarFull || [];")
        cs = cells(o["m"])
        self.assertEqual(len(cs), n, "copies were dropped: %d of %d" % (len(cs), n))
        pages = {}
        for h, c in cs:
            if h == "SHARED STASH":
                y = int(re.match(r"^shared:c\d+r(\d+)$", c).group(1))
                pages[y // 10] = pages.get(y // 10, 0) + 1
        self.assertEqual(pages, {p: ENIGMA_PER_GRID for p in range(5)}, "the 5 war-stash pages were not all filled first: %r" % pages)
        self.assertEqual(sum(1 for h, _ in cs if h == "war1"), ENIGMA_PER_GRID, "WAR1 did not fill next: %r" % cs[-20:])
        self.assertEqual(sum(1 for h, _ in cs if h == "WAR2"), 1, "the spill did not reach WAR2: %r" % cs[-5:])
        self.assertEqual(len(set(cs)), n, "two copies share a cell")
        self.assertEqual(o["full"], [])

    def test_no_war_mule_says_so_and_creates_none(self):
        roster_with([])
        n = 5 * ENIGMA_PER_GRID + 1
        T.add_all(["Enigma"] * n)
        o = T.board().run(READ + "OUT.m = mv(/^Enigma$/); OUT.line = ((document.querySelector('#vault-move-list .vmv-warfull') || {}).textContent || '');"
                          "OUT.roster = JSON.parse(window.LSR.getItem('d2r_muleRoster') || '[]').map(function(m){ return m.name; });")
        placed = [m for m in o["m"] if (m["to"] or {}).get("cell")]
        self.assertEqual(len(placed), 5 * ENIGMA_PER_GRID)
        self.assertIn("no WAR1 mule", o["line"], "the overflow is not said plainly: %r" % o["line"])
        self.assertIn("Enigma", o["line"])
        self.assertFalse(any(re.match(r"^war", str(x), re.I) for x in o["roster"]), "a WAR mule was created: %r" % o["roster"])

    def test_utility_proc_and_charge_gear_routes_to_the_war_stash(self):
        """Elad 2026-10-20: Demon Limb (Enchant charges), Metamorphosis (Mark of Bear/Wolf), Treachery (Fade) -> SHARED STASH"""
        o = T.board().run("OUT.r = {}; ['Demon Limb', 'Metamorphosis', 'Treachery', 'Arachnid Mesh', \"Andariel's Visage\", 'Vampire Gaze']"
                          ".forEach(function(n){ var s = window.suggestMule(n); OUT.r[n] = s && s.id; });")
        for n, mid in o["r"].items():
            self.assertEqual(mid, "shared", "%s routed to %r, not the war stash" % (n, mid))

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import wilson_lower
        import self_arming as SA
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        print("vault L1 war stash: %d distinct attacks, wilson %.4f vs bar %.3f" % (n, w, SA.LOCKS["vault.apply"]["bar"]))
        self.assertGreaterEqual(w, SA.LOCKS["vault.apply"]["bar"])


RED_PROOF = [
    {"why": "A hand add of a name he owns is 'already yours - nothing changed' again: the 2nd copy vanishes.",
     "file": "bible.html", "find": "      if (!(opts && opts.by) && typeof copies !== 'undefined' && copies) {",
     "replace": "      if (false) {", "matches": 1},
    {"why": "The hand copy gets no move row of its own.",
     "file": "bible.html", "find": "if (typeof _vaultMoveNoteAdded === 'function') _cMv = _vaultMoveNoteAdded(pre.name, _cN - 1); } catch (eMc) {} /* L1 hand copy row */",
     "replace": "} catch (eMc) {} /* L1 hand copy row */", "matches": 1},
    {"why": "Every copy's row is written onto copy 0, so copies collapse to one row.",
     "file": "bible.html", "find": "    var wrote = _vaultMoveCommit([{ name: nm, copyIx: copyIx, task: hand }]); /* v3773 manual row */",
     "replace": "    var wrote = _vaultMoveCommit([{ name: nm, copyIx: 0, task: hand }]); /* v3773 manual row */", "matches": 1},
    {"why": "A set piece typed twice stays one presence item: the spare he typed is dropped.",
     "file": "bible.html", "find": "                  && !(multiKeep[pre.name] >= _cN)) multiKeep[pre.name] = _cN; } catch (eMk) {} /* L1 hand set copy */",
     "replace": "                  && false) multiKeep[pre.name] = _cN; } catch (eMk) {} /* L1 hand set copy */", "matches": 1},
    {"why": "The war stash is one page again.",
     "file": "bible.html", "find": "      var left = items, SHARED_TABS = 5; /* L1 the war stash has 5 pages */",
     "replace": "      var left = items, SHARED_TABS = 1; /* L1 the war stash has 5 pages */", "matches": 1},
    {"why": "Every page packs over page 1's cells (the page offset is lost).",
     "file": "bible.html", "find": "cell: 'shared:c' + q.x + 'r' + (q.y + pg * 10) }; });",
     "replace": "cell: 'shared:c' + q.x + 'r' + q.y }; });", "matches": 1},
    {"why": "Overflow never reaches a WAR mule.",
     "file": "bible.html", "find": "      var wars = (typeof _vaultWarMules === 'function') ? _vaultWarMules() : [];",
     "replace": "      var wars = [];", "matches": 1},
    {"why": "WAR mules are matched case-sensitively: 'war1' is not found.",
     "file": "bible.html", "find": "/^war\\s*(\\d*)$/i.exec(String(m.name || '').trim())",
     "replace": "/^WAR\\s*(\\d*)$/.exec(String(m.name || '').trim())", "matches": 1},
    {"why": "WAR mules fill in roster order, not WAR1 then WAR2.",
     "file": "bible.html", "find": "    return r.sort(function(a, b){ return a.n - b.n || (a.name < b.name ? -1 : 1); });",
     "replace": "    return r.reverse();", "matches": 1},
    {"why": "Demon Limb (Enchant charges) goes back to a mule.",
     "file": "bible.html", "find": "    'demon limb': 'enchant charges - utility charge flail',\n",
     "replace": "", "matches": 1},
    {"why": "Metamorphosis (Mark of Bear/Wolf) goes back to the runewords mule.",
     "file": "bible.html", "find": "    'metamorphosis': 'mark of the bear / wolf on striking - utility proc helm',\n",
     "replace": "", "matches": 1},
    {"why": "Treachery (Fade) goes back to the runewords mule.",
     "file": "bible.html", "find": "    'treachery': 'fade on striking - utility proc armour'\n",
     "replace": "    'treachery_x': 'x'\n", "matches": 1},
    {"why": "A full war stash says nothing.",
     "file": "bible.html", "find": "    if (_wf.length) unrHtml += '<p class=\"vmv-warfull\"",
     "replace": "    if (false) unrHtml += '<p class=\"vmv-warfull\"", "matches": 1},
    {"why": "The tab and in-page row are not read off the shared cell.",
     "file": "bible.html", "find": "        return h + ' tab ' + (Math.floor((+m[2]) / 10) + 1) + ' (' + ((+m[1]) + 1) + ',' + ((+m[2]) % 10 + 1) + ')';",
     "replace": "        return h + ' (' + ((+m[1]) + 1) + ',' + ((+m[2]) + 1) + ')';", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
