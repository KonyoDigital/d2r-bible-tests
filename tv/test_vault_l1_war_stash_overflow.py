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
BELT_PER_GRID = 50     # a 2x1 belt on a 10x10 grid (small gear keeps every copy in the war stash)
BELT = "Thundergod's Vigor"


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
        """Elad 2026-10-20: a BIG item keeps ONE copy in the war stash; every extra copy goes to its normal mule,
        each with its own cell and row. Small gear (Arachnid Mesh is a 2x1 belt) keeps every copy there."""
        T.fresh()
        T.add_all(["Andariel's Visage"] * 4 + ["Vampire Gaze"] * 3 + ["Arachnid Mesh"] * 3)
        for nm, n in (("Andariel's Visage", 4), ("Vampire Gaze", 3)):
            o = T.board().run(READ + "OUT.m = mv(new RegExp('^' + %s)); OUT.rows = rows(new RegExp('^' + %s));" % (json.dumps(nm), json.dumps(nm)))
            cs = cells(o["m"])
            self.assertEqual(len(cs), n, "%s: %d copies, %d items: %r" % (nm, n, len(cs), cs))
            self.assertEqual(len(set(cs)), n, "%s copies share cells: %r" % (nm, cs))
            by = {m["c"]: m["to"]["holder"] for m in o["m"]}
            self.assertEqual(by[0], "SHARED STASH", "%s: the first-witnessed copy left the war stash: %r" % (nm, by))
            self.assertEqual([c for c, h in by.items() if h == "SHARED STASH"], [0], "%s: more than one big copy in the war stash: %r" % (nm, by))
            self.assertTrue(all(re.match(r"^UNI-", h) for c, h in by.items() if c), "%s extras not on the normal UNI-* mule: %r" % (nm, by))
            self.assertEqual(len(o["rows"]), n, "%s: not %d rows: %r" % (nm, n, o["rows"]))
        for nm, n in (("Arachnid Mesh", 3),):
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
        n = 5 * BELT_PER_GRID + BELT_PER_GRID + 1
        T.add_all([BELT] * n)
        o = T.board().run(READ + "OUT.m = mv(/^Thundergod's Vigor$/); OUT.full = window._vaultWarFull || [];"
                          "OUT.badge = Array.prototype.map.call(document.querySelectorAll('.vm-warbadge'), function(e){ return e.textContent; });"
                          "OUT.rows = rows(/^Thundergod's Vigor$/).filter(function(t){ return /war1|WAR2/.test(t); });")
        cs = cells(o["m"])
        self.assertEqual(len(cs), n, "copies were dropped: %d of %d" % (len(cs), n))
        pages = {}
        for h, c in cs:
            if h == "SHARED STASH":
                y = int(re.match(r"^shared:c\d+r(\d+)$", c).group(1))
                pages[y // 10] = pages.get(y // 10, 0) + 1
        self.assertEqual(pages, {p: BELT_PER_GRID for p in range(5)}, "the 5 war-stash pages were not all filled first: %r" % pages)
        self.assertEqual(sum(1 for h, _ in cs if h == "war1"), BELT_PER_GRID, "WAR1 did not fill next: %r" % cs[-20:])
        self.assertEqual(sum(1 for h, _ in cs if h == "WAR2"), 1, "the spill did not reach WAR2: %r" % cs[-5:])
        self.assertEqual(len(set(cs)), n, "two copies share a cell")
        self.assertEqual(o["full"], [])
        self.assertTrue(o["rows"] and all("SHARED STASH · overflow" in t for t in o["rows"]),
                        "a WAR row does not say it is the Shared Stash overflow: %r" % o["rows"][:3])

    def test_no_war_mule_says_so_and_creates_none(self):
        roster_with([])
        n = 5 * BELT_PER_GRID + 1
        T.add_all([BELT] * n)
        o = T.board().run(READ + "OUT.m = mv(/^Thundergod's Vigor$/); OUT.line = ((document.querySelector('#vault-move-list .vmv-warfull') || {}).textContent || '');"
                          "OUT.roster = JSON.parse(window.LSR.getItem('d2r_muleRoster') || '[]').map(function(m){ return m.name; });")
        placed = [m for m in o["m"] if (m["to"] or {}).get("cell")]
        self.assertEqual(len(placed), 5 * BELT_PER_GRID)
        self.assertIn("no WAR1 mule", o["line"], "the overflow is not said plainly: %r" % o["line"])
        self.assertIn("Thundergod", o["line"])
        self.assertFalse(any(re.match(r"^war", str(x), re.I) for x in o["roster"]), "a WAR mule was created: %r" % o["roster"])

    def test_utility_proc_and_charge_gear_routes_to_the_war_stash(self):
        """Elad 2026-10-20: Demon Limb (Enchant charges), Metamorphosis (Mark of Bear/Wolf), Treachery (Fade) -> SHARED STASH"""
        o = T.board().run("OUT.r = {}; ['Demon Limb', 'Metamorphosis', 'Treachery', \"Guillaume's Face\", 'Arachnid Mesh', \"Andariel's Visage\", 'Vampire Gaze']"
                          ".forEach(function(n){ var s = window.suggestMule(n); OUT.r[n] = s && s.id; });")
        for n, mid in o["r"].items():
            self.assertEqual(mid, "shared", "%s routed to %r, not the war stash" % (n, mid))

    def test_guillaumes_face_goes_to_the_war_stash_not_sets_rest(self):
        """Elad 2026-10-19: Guillaume's Face -> the war stash (Shared Stash); war gear beats the keep-set rule"""
        o = T.board().run("var s = window.suggestMule(\"Guillaume's Face\"); OUT.id = s && s.id; OUT.why = s && s.why;"
                          "OUT.set = !!(window.findSetPiece && window.findSetPiece(\"Guillaume's Face\"));"
                          "OUT.role = window.vaultWarGearRole(\"Guillaume's Face\");")
        self.assertTrue(o["set"], "PREMISE: Guillaume's Face is a set piece (the keep-set rule would claim it)")
        self.assertEqual(o["id"], "shared", "Guillaume's Face routed to %r (%s), not the war stash" % (o["id"], o["why"]))
        self.assertIn("war gear", o["why"] or "")
        self.assertTrue(o["role"])

    def test_size_is_read_off_the_footprint_not_a_name_list(self):
        o = T.board().run("OUT.r = {}; ['Stone of Jordan', 'Raven Frost', \"Mara's Kaleidoscope\", \"Thundergod's Vigor\", 'Shako', \"Guillaume's Face\", 'Demon Limb', 'Enigma']"
                          ".forEach(function(n){ OUT.r[n] = { small: window._vaultWarSmall(n), cells: window._itemCells ? window._itemCells(n) : null }; });")
        for n in ("Stone of Jordan", "Raven Frost", "Mara's Kaleidoscope", "Thundergod's Vigor"):
            self.assertTrue(o["r"][n]["small"], "%s is small gear: %r" % (n, o["r"][n]))
        for n in ("Shako", "Guillaume's Face", "Demon Limb", "Enigma"):
            self.assertFalse(o["r"][n]["small"], "%s is big gear: %r" % (n, o["r"][n]))

    def test_small_war_gear_keeps_every_copy_grouped_in_the_war_stash(self):
        T.fresh()
        T.add_all(["The Stone of Jordan"] * 5 + ["Raven Frost"] * 5)
        for nm in ("The Stone of Jordan", "Raven Frost"):
            o = T.board().run(READ + "OUT.m = mv(new RegExp('^' + %s + '$'));" % json.dumps(nm))
            cs = cells(o["m"])
            self.assertEqual(len(cs), 5, cs)
            self.assertTrue(all(c[0] == "SHARED STASH" for c in cs), "%s copies left the war stash: %r" % (nm, cs))
            xy = sorted((int(a), int(b)) for a, b in (re.match(r"^shared:c(\d+)r(\d+)$", c[1]).groups() for c in cs))
            self.assertLessEqual(max(x for x, _ in xy) - min(x for x, _ in xy) + max(y for _, y in xy) - min(y for _, y in xy), 5,
                                 "%s copies are not grouped: %r" % (nm, xy))

    def test_big_war_gear_keeper_is_stable_and_copies_never_swap(self):
        roster_with([])
        T.add_all(["Andariel's Visage"] * 3)
        a = T.board().run(READ + "OUT.m = mv(/^Andariel.s Visage$/);")["m"]
        T.add_all(["Andariel's Visage"])
        b = T.board().run(READ + "window._movePackCache = null; window._warKeepBag = null; OUT.m = mv(/^Andariel.s Visage$/);")["m"]
        A = {m["c"]: (m["to"]["holder"], m["to"]["cell"]) for m in a}
        B = {m["c"]: (m["to"]["holder"], m["to"]["cell"]) for m in b}
        self.assertEqual(A[0][0], "SHARED STASH", A)
        self.assertTrue(all(A[c] == B[c] for c in A), "a copy moved or swapped after another add: %r -> %r" % (A, B))
        self.assertEqual(sum(1 for v in B.values() if v[0] == "SHARED STASH"), 1, B)

    def test_renaming_a_war_mule_keeps_its_tasks_colour_and_place(self):
        """Elad 2026-10-20: mule names get renamed to character names later - routing, tasks, colour and place bind to the id"""
        roster_with(["WAR1"])
        n = 5 * BELT_PER_GRID + 2
        T.add_all([BELT] * n)
        q = (READ + "OUT.m = mv(/^Thundergod's Vigor$/).filter(function(m){ return m.to && m.to.holder !== 'SHARED STASH'; })"
             ".map(function(m){ return [m.c, m.to.id, m.to.cell]; });"
             "OUT.rows = rows(/^Thundergod's Vigor$/).filter(function(t){ return /overflow/.test(t); });"
             "var c = document.querySelector('.vault-mule[data-vault-mule=\"war-law-0\"]'); OUT.cls = c ? c.className : null;"
             "OUT.badge = c ? !!c.querySelector('.vm-warbadge') : null; OUT.order = c ? getComputedStyle(c).order : null;"
             "var sh = document.querySelector('.vault-mule.vm-shared'); OUT.sorder = sh ? getComputedStyle(sh).order : null;")
        a = T.board().run(q)
        T.board().run("window.prompt = function(){ return 'DEANSORC'; }; window.vaultRenameMule('war-law-0');"
                      "window._movePackCache = null; window._warKeepBag = null; if (window.renderVault) window.renderVault();")
        b = T.board().run(q)
        self.assertEqual(len(a["m"]), 2, a["m"])
        self.assertEqual(a["m"], b["m"], "a rename moved or dropped WAR1's copies: %r -> %r" % (a["m"], b["m"]))
        self.assertTrue(all(x[1] == "war-law-0" for x in b["m"]), b["m"])
        self.assertEqual(len(b["rows"]), 2, b["rows"])
        self.assertTrue(all("DEANSORC (SHARED STASH · overflow)" in t for t in b["rows"]), b["rows"])
        for o in (a, b):
            self.assertIn("vm-war", o["cls"] or "", "the WAR box lost the shared-stash colour: %r" % o["cls"])
            self.assertTrue(o["badge"])
            self.assertLess(int(o["sorder"]), int(o["order"]), "SHARED STASH is not above its WAR box")
            self.assertLess(int(o["order"]), 0, "the WAR box is not ahead of the other mules: %r" % o["order"])

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
    {"why": "A rename drops the WAR role: the renamed mule stops being the overflow.",
     "file": "bible.html", "find": "    if (m.role === 'war') return +m.warN || 1;",
     "replace": "", "matches": 1},
    {"why": "A target binds to the display name again, so a rename orphans the task.",
     "file": "bible.html", "find": "    if (id != null) pl.id = id; /* L1 a target binds to the mule's stable id */",
     "replace": "", "matches": 1},
    {"why": "The WAR box loses the Shared Stash colour and place.",
     "file": "bible.html", "find": "+((window._vaultWarRole&&window._vaultWarRole(m))?' vm-war':'')",
     "replace": "", "matches": 1},
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
     "file": "bible.html", "find": "    'treachery': 'fade on striking - utility proc armour',\n",
     "replace": "", "matches": 1},
    {"why": "Guillaume's Face falls back to SETS-REST (the keep-set rule wins over war gear).",
     "file": "bible.html", "find": "    \"guillaume's face\": 'crushing blow + deadly strike helm - war set piece'\n",
     "replace": "    \"guillaume_x\": 'x'\n", "matches": 1},
    {"why": "A full war stash says nothing.",
     "file": "bible.html", "find": "    if (_wf.length) unrHtml += '<p class=\"vmv-warfull\"",
     "replace": "    if (false) unrHtml += '<p class=\"vmv-warfull\"", "matches": 1},
    {"why": "The tab and in-page row are not read off the shared cell.",
     "file": "bible.html", "find": "        return h + ' tab ' + (Math.floor((+m[2]) / 10) + 1) + ' (' + ((+m[1]) + 1) + ',' + ((+m[2]) % 10 + 1) + ')';",
     "replace": "        return h + ' (' + ((+m[1]) + 1) + ',' + ((+m[2]) + 1) + ')';", "matches": 1},
    {"why": "Every copy of a big war item stays in the war stash again (the overflow Elad ruled out).",
     "file": "bible.html", "find": "    if (seam && seam.loc === 'shared') { var _xw = _vaultWarExtra(name, copyIx); if (_xw) seam = _xw; } /* L1 one big copy per war item */",
     "replace": "", "matches": 1},
    {"why": "Small war gear (rings, amulets, belts) is cut to one copy too.",
     "file": "bible.html", "find": "    if ((s[0] || 1) * (s[1] || 1) <= 2) return true;",
     "replace": "    if (false) return true;", "matches": 1},
    {"why": "The keeper is not the first-witnessed copy (the last one stays instead).",
     "file": "bible.html", "find": "    return best == null ? 0 : best; /* L1 else the first-witnessed copy */",
     "replace": "    return best == null ? 99 : best; /* L1 else the first-witnessed copy */", "matches": 1},
    {"why": "A WAR mule row does not say it is the Shared Stash overflow.",
     "file": "bible.html", "find": "      if (_pm ? _vaultWarRole(_pm) : /^war\\s*\\d*$/i.test(h.trim())) h = h + ' (SHARED STASH · overflow)'; /* L1 a WAR mule reads as the war stash */",
     "replace": "", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
