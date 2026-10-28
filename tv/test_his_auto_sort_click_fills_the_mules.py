# -*- coding: utf-8 -*-
"""REG-2019 - HIS AUTO-SORT CLICK FILLS THE MULES, AND WAR GEAR GOES TO THE SHARED STASH BY SLOT. #264, his ask 2026-10-07.

His words, at a vault of 85 loose items and ten empty mules: "the vault all those items when i click auto-assort should be
assembled correctly and organized within the mules" - "items that are rare or war items/like for ubers switching gears and
stuff should stay in the SHARED/MAIN within those 5 pages also organized" - "like dwarf star rings raven frosts..
thundergods.." - "like enigma.. duress.. runewords that are good.. and BOTD, DEATH DOOM".

MEASURED on a copy of his store: the mule map was {} and all 96 owned rows were owned RECEIPTS. vaultAutoAssign files only
a row that already carries a filing witness, and a receipt is never one, so both buttons filed ZERO. Now:
  - the two BUTTONS call vaultAutoSortByHand: his click is the witness, and only for a dock item with a picture whose
    newest placed look is not on his MAIN; discards, keep-on-MAIN and no-picture items stay, counted;
  - vaultAutoAssign (what sweeps and applies call, with nobody at the screen) still files none of them;
  - war / swap gear routes to the shared stash, whose 5 tabs are laid out by slot;
  - an owned item in MAGIC & RARE is filed there: it is not loose, and the audit no longer calls it double-filed (its
    one-click fix deleted it from Magic & Rare, its only home).
Driven on the SHIPPED page in a scratch Chrome. NO CHROME AT ALL = a declared skip, never a pass.
"""
import io
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

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

ROOT = os.path.dirname(HERE)
_B = {}

HIS_WAR_NAMES = ("Enigma", "Duress", "Breath of the Dying", "Death", "Doom", "Raven Frost", "Dwarf Star",
                 "Thundergod's Vigor")


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def _receipt(name, looks):
    return {"kind": "owned", "source": "kai-register", "by": "law", "at": "2026-10-07T08:00:00.000Z",
            "looks": looks, "seen": len(looks)}


def _look(frame, at, loc):
    return {"id": "s_law_1", "frame": frame, "conf": None, "at": at, "loc": loc, "scene": "stash"}


DOCK = {
    "Grief": [_look("1_100", "2026-10-07T08:01:00.000Z", "stash")],
    "Obedience": [_look("2_100", "2026-10-07T08:02:00.000Z", "stash")],
    "Nokozan Relic": [_look("3_100", "2026-10-07T08:03:00.000Z", "stash")],
    "Enigma": [_look("4_100", "2026-10-07T08:04:00.000Z", "stash"), _look("5_100", "2026-10-07T09:04:00.000Z", "equipped")],
    "Insight": [],
    "Isenhart's Case (armor)": [_look("6_100", "2026-10-07T08:06:00.000Z", "stash")],
    "Harpoonist's Grand Charm": [_look("7_100", "2026-10-07T08:07:00.000Z", "stash")],
}


def _seed():
    board().seed({
        "d2r_owned": sorted(DOCK),
        "d2r_vaultProv": {n: _receipt(n, l) for n, l in DOCK.items()},
        "d2r_magicFinds": {"Harpoonist's Grand Charm": {"q": "magic", "base": "Grand Charm",
                                                        "mods": ["+1 to Javelin and Spear Skills (Amazon Only)"]}},
        "d2r_muleAssign": {},
        # his real board keeps a rolled charm through the load-time rebuild of `owned` this way (measured on a copy of
        # his store); without it the charm is dropped at load and the Magic & Rare cases have no subject
        "d2r_tvExtraItems": {"Harpoonist's Grand Charm": {"rarity": "basic", "base": "Harpoonist's Grand Charm",
                                                          "cat": "📺 TV-vaulted", "val": "tv",
                                                          "desc": "registered live by TV DIABLO — physically in your stash"}},
    })


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class HisAutoSortClickFillsTheMules(unittest.TestCase):

    def test_war_gear_routes_to_the_shared_stash_and_the_rest_to_its_mule(self):
        o = board().run("OUT.r = {}; %s.forEach(function(n){ var s = window.suggestMule(n); OUT.r[n] = [s && s.id, s && s.why]; });"
                        % json.dumps(list(HIS_WAR_NAMES) + ["Obedience", "Nokozan Relic"]))["r"]
        for n in HIS_WAR_NAMES:
            self.assertEqual(o[n][0], "shared", "%s - his war gear - did not route to the shared stash: %r" % (n, o[n]))
            self.assertIn("war gear", o[n][1], o[n])
        self.assertEqual(o["Obedience"][0], "runewords", "the control: a runeword not on the war list left its mule %r" % o)
        self.assertEqual(o["Nokozan Relic"][0], "uni-small", o)

    # RETIRED (#144.10 shared half, REG-2801, his ruling 2026-10-28: "the war stash is basically the shared stash with those 5
    # pages + the extra war mules"): REG-2019's case "the five shared tabs are laid out by slot" and its red-proof. The
    # by-slot tabs are gone - the shared stash is drawn on its 5 pages in the order its move tasks fill them, held by
    # tv/test_the_shared_stash_draws_the_plans_pages.py.

    def test_his_click_files_the_dock_and_an_automatic_caller_still_files_nothing(self):
        _seed()
        o = board().run("OUT.auto = window.vaultAutoAssign(); OUT.a0 = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                        "OUT.r = window.vaultAutoSortByHand();"
                        "OUT.a1 = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                        "OUT.pv = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}')['Grief'] || null;"
                        "OUT.dock = window._vaultDockNames();"
                        "OUT.sgIsen = (window.suggestMule(\"Isenhart's Case (armor)\") || {}).id || null;"
                        "OUT.rec = (window._vaultRecords().records || []).map(function(r){ return { name: r.name, kind: r.kind, mule: r.mule }; });")
        self.assertEqual(o["a0"], {}, "an AUTOMATIC caller (vaultAutoAssign) filed a receipt to a mule with nobody's hand: %r" % o["a0"])
        a1 = o["a1"]
        # v3767 — a resolved home leaves the dock through the records seam. The click does not
        # have to write assign, and it must not write it for a name that is no longer loose.
        self.assertEqual(a1, {}, "the click wrote assign for a name the seam already homed: %r" % a1)
        rec = o["rec"]
        def kind(name):
            return [r["kind"] for r in rec if r["name"] == name]
        def mule(name):
            return [r["mule"] for r in rec if r["name"] == name]
        self.assertTrue(kind("Grief") and set(kind("Grief")) == {"sharedStash"}, rec)
        self.assertTrue(kind("Obedience") and set(kind("Obedience")) == {"filed"}, rec)
        self.assertTrue(set(mule("Obedience")) == {"runewords"}, rec)
        self.assertTrue(set(mule("Nokozan Relic")) == {"uni-small"}, rec)
        self.assertTrue(kind("Enigma") and set(kind("Enigma")) == {"keep"}, "a name last seen worn was not kept with MAIN: %r" % rec)
        self.assertNotIn("Enigma", o["dock"])
        self.assertNotIn("Grief", o["dock"])
        # L1 (Elad): a discard route is a THROW OUT task in MOVE TASKS, never a dock chip, and never filed.
        self.assertNotIn("Isenhart's Case (armor)", o["dock"], "a throw-out route sat in the dock: %r" % o["dock"])
        self.assertNotIn("Isenhart's Case (armor)", a1, "a discard suggestion was filed instead of left for him")
        # L1: Auto-Sort reads the dock, and a throw-out is no longer in it - it is a THROW OUT task,
        # left for his Keep / Junk. It is still the planner's discard, so it left the dock for that reason.
        self.assertEqual(o["sgIsen"], "__throwout", "premise: Isenhart's is not a ruled discard %r" % o["sgIsen"])
        self.assertIsNone(o["r"]["left"].get("throwout"), "Auto-Sort still counts a throw-out as left in the dock: %r" % o["r"])
        self.assertTrue(o["pv"] and o["pv"].get("kind") == "owned",
                        "the seam wrote a filing row without his click: %r" % o["pv"])

    def test_a_chronicle_page_is_never_the_picture_a_filing_stands_on(self):
        """REG-2020 (#264) - a Chronicle read proves he found it ONCE (his §28 ruling), never that he holds it."""
        board().seed({"d2r_owned": ["Nokozan Relic", "Obedience"],
                      "d2r_vaultProv": {"Nokozan Relic": _receipt("Nokozan Relic", [_look("8_100", "2026-10-07T08:08:00.000Z", "stash")]),
                                        "Obedience": _receipt("Obedience", [dict(_look("9_100", "2026-10-07T08:09:00.000Z", "chronicle"),
                                                                                    scene="chronicle")])},
                      "d2r_muleAssign": {}})
        o = board().run("OUT.r = window.vaultAutoSortByHand(); OUT.a = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                        "OUT.dock = window._vaultDockNames();"
                        "OUT.rec = (window._vaultRecords().records || []).map(function(r){ return { name: r.name, kind: r.kind, mule: r.mule }; });")
        nok = [r for r in o["rec"] if r["name"] == "Nokozan Relic"]
        self.assertEqual([r["mule"] for r in nok], ["uni-small"], "the stash-seen control was not homed on its mule %r" % o)
        self.assertNotIn("Nokozan Relic", o["a"], "the seam wrote assign: %r" % o["a"])
        self.assertNotIn("Obedience", o["a"], "a Chronicle page was the only picture and his click filed it anyway")
        self.assertIn("Obedience", o["dock"], "a chronicle-only tick left the dock as if he held it %r" % o["dock"])
        self.assertIn("Obedience", o["r"]["noPicture"], o["r"])

    def test_a_magic_and_rare_item_is_not_loose_and_not_double_filed(self):
        _seed()
        o = board().run("OUT.dock = window._vaultDockNames();"
                        "OUT.owned = (typeof owned !== 'undefined') && owned.has(\"Harpoonist's Grand Charm\");"
                        "OUT.magic = window._vaultInMagicRare(\"Harpoonist's Grand Charm\");"
                        "OUT.dupes = window._vaultAudit().findings.filter(function(f){ return f.kind === 'dupe'; })"
                        ".map(function(f){ return f.item; });")
        self.assertTrue(o["owned"] and o["magic"], "premise: the charm is not both owned and in Magic & Rare on this page %r" % o)
        self.assertNotIn("Harpoonist's Grand Charm", o["dock"], "an item filed in MAGIC & RARE was listed as loose")
        self.assertNotIn("Harpoonist's Grand Charm", o["dupes"],
                         "owning a Magic & Rare item read as double-filed - its fix deletes it from its only home")
        self.assertNotIn("Grief", o["dock"], "a resolved war-gear home stayed in the dock %r" % o["dock"])
        # L1: the discard is a THROW OUT task, not loose - the dock stays empty of it.
        self.assertNotIn("Isenhart's Case (armor)", o["dock"], "a throw-out route sat in the dock %r" % o["dock"])

    def test_delete_unsorted_takes_only_what_the_dock_shows(self):
        """REG-2021 (the #231 eye on v3616) - Delete unsorted kept its own copy of "what is loose": it offered and removed
        his Magic & Rare items and his CARRIED loot along with the dock. It asks the one dock list now."""
        board().seed({
            "d2r_owned": ["Grief", "Harpoonist's Grand Charm", "Harlequin Crest", "Isenhart's Case (armor)", "Obedience"],
            "d2r_vaultProv": {
                "Obedience": _receipt("Obedience", [dict(_look("9_100", "2026-10-07T08:09:00.000Z", "chronicle"), scene="chronicle")]),
                "Grief": _receipt("Grief", [_look("1_100", "2026-10-07T08:01:00.000Z", "stash")]),
                "Harpoonist's Grand Charm": _receipt("Harpoonist's Grand Charm", [_look("7_100", "2026-10-07T08:07:00.000Z", "stash")]),
                "Harlequin Crest": dict(_receipt("Harlequin Crest", [_look("c_1", "2026-10-07T08:10:00.000Z", "inventory")]),
                                        loc="inventory", carried=True, frameId="c_1", ts=1791360000000)},
            "d2r_magicFinds": {"Harpoonist's Grand Charm": {"q": "magic", "base": "Grand Charm", "mods": []}},
            "d2r_tvExtraItems": {"Harpoonist's Grand Charm": {"rarity": "basic", "base": "Harpoonist's Grand Charm",
                                                              "cat": "TV-vaulted", "val": "tv", "desc": "registered live"}},
            "d2r_muleAssign": {}})
        o = board().run("OUT.dock = window._vaultDockNames();"
                        "var pr = window.vaultClearUnsorted();"
                        "await new Promise(function(r){ setTimeout(r, 250); });"
                        "var ok = document.querySelector('.ui-confirm-ok'); OUT.msg = (document.querySelector('.ui-confirm-msg') || {}).textContent || '';"
                        "if (ok) ok.click(); await pr; await new Promise(function(r){ setTimeout(r, 250); });"
                        "OUT.owned = (typeof owned !== 'undefined') ? Array.from(owned).sort() : null;")
        # L1: the discard (Isenhart's) is a THROW OUT task, so the only homeless item is the chronicle-only Obedience.
        self.assertEqual(o["dock"], ["Obedience"], "premise: the dock is not exactly the one homeless item %r" % o["dock"])
        self.assertIn("Delete all 1 UNSORTED", o["msg"], "the confirm offered a different count than the dock shows: %r" % o["msg"])
        self.assertNotIn("Obedience", o["owned"] or [], "the control: Delete unsorted did not remove the loose item %r" % o)
        self.assertIn("Isenhart's Case (armor)", o["owned"] or [], "Delete unsorted removed a THROW OUT task - a throw-out is his call, never a sweep")
        self.assertIn("Grief", o["owned"] or [], "Delete unsorted removed a name the seam already homed %r" % o)
        self.assertIn("Harpoonist's Grand Charm", o["owned"] or [], "Delete unsorted removed a Magic & Rare item from owned")
        self.assertIn("Harlequin Crest", o["owned"] or [], "Delete unsorted removed loot he is CARRYING")

    def test_both_buttons_are_his_click(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            code = re.sub(r"/\*.{0,4000}?\*/", "", fh.read(), flags=re.S)
        # Vault v2 (Elad 2026-10-23): the toolbar's Auto-assign and the dock bar's Auto-Sort became ONE "🪄 Sort to mules"
        # button - so exactly one control, and it is his click.
        self.assertEqual(code.count('onclick="window.vaultAutoSortByHand()"'), 1, "the vault sort button is not ONE button that is his click")
        self.assertEqual(code.count('onclick="window.vaultAutoAssign()"'), 0,
                         "a button still calls the automatic sorter, which files nothing a receipt holds")


RED_PROOF = [
    {"why": "REG-2019 - war gear routes to its runeword / unique mule again, a character switch away",
     "file": "bible.html",
     "find": "    if (_war && _ov !== 'mule') return {id:'shared', why:'war gear: ' + _war + ' - in the shared stash, where every character can reach it'};\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2019 - his click files a found-ever receipt nobody ever filmed",
     "file": "bible.html",
     "find": "      if (!_hasPicture(row)){ out.noPicture.push(name); return; }\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2020 - a Chronicle page counts as the picture a filing stands on",
     "file": "bible.html",
     "find": "      return e && e.frame && String(e.loc || '').toLowerCase() !== 'chronicle' && String(e.scene || '').toLowerCase() !== 'chronicle';\n",
     "replace": "      return e && e.frame;\n",
     "matches": 1},
    {"why": "REG-2019 - his click files an item his MAIN is wearing",
     "file": "bible.html",
     "find": "if (onMain) return { loc: 'keep', mule: null }; /* v3767 seam worn */",
     "replace": "if (false && onMain) return { loc: 'keep', mule: null }; /* v3767 seam worn */",
     "matches": 1},
    {"why": "REG-2019 - a Magic & Rare item is listed as loose again",
     "file": "bible.html",
     "find": "        else if (!(assign[n] == null && !isSharedStash(n) && !_inMagicRare(n) && !carSet[n]\n",
     "replace": "        else if (!(assign[n] == null && !isSharedStash(n) && !carSet[n]\n",
     "matches": 1},
    {"why": "REG-2019 - owning a Magic & Rare item reads as double-filed, and its fix deletes it from Magic & Rare",
     "file": "bible.html",
     "find": "        var keepHere = inFiled[n] || (inKeep[n] && !inMagic[n]);\n",
     "replace": "        var keepHere = inKeep[n];\n",
     "matches": 1},
    {"why": "REG-2021 - Delete unsorted keeps its own copy of what is loose, and takes Magic & Rare and carried loot",
     "file": "bible.html",
     "find": "    var unsorted = _dockNames();   /* #264 (REG-2021) — exactly the names the dock shows, never Magic & Rare or carried loot */\n",
     "replace": "    var unsorted = ownedPool().filter(function(name){ return !assign[name] && !isSharedStash(name); });\n",
     "matches": 1},
    {"why": "REG-2019 - the Sort to mules button calls the automatic sorter again and files nothing",
     "file": "bible.html",
     "find": '<button class="vault-btn vault-btn-primary vault-sort-btn" onclick="window.vaultAutoSortByHand()"',
     "replace": '<button class="vault-btn vault-btn-primary vault-sort-btn" onclick="window.vaultAutoAssign()"',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
