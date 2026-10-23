# -*- coding: utf-8 -*-
"""Vault v2 - every door the old Vault had is still reached from a control he can SEE.

Elad, 2026-10-23, approving the Vault v2 design, his hard rule: nothing is dropped. The toolbar lost three red buttons
and "+ Add an item", the dock bar lost its two buttons, MOVE TASKS became a FAB and the panels below the mules went into
one ⚙ Advanced drawer. This law walks the design's mapping table on the SHIPPED page in Chrome: for every handler it
presses only the visible controls a person would (the ⚠ Clear & reset toggle, the 📦 FAB, the Advanced summary and its
tab), and then asks the page whether the control that calls the handler is RENDERED (a box on screen, not display:none,
not visibility:hidden, not inside a closed menu or drawer). It never presses a destructive door itself.
NO CHROME = a declared skip. RED_PROOF below. [[regression-guard]]
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

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402

_B = {}
SHAKO = "Harlequin Crest (Shako)"


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


# what "a control he can see" means, asked of the page itself
SEEN = r"""
function seen(el){
  if (!el || !el.isConnected) return false;
  for (var a = el; a; a = a.parentElement){
    if (a.hidden) return false;
    var cs = getComputedStyle(a);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (a.tagName === 'DETAILS' && a !== el && !a.open && !(el.closest('summary') && el.closest('details') === a)) return false;
  }
  var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0;
}
function by(sel){ return document.querySelector(sel); }
function door(fn){ return document.querySelector('[onclick^="window.' + fn + '("]'); }
function doors(fn){ return [].slice.call(document.querySelectorAll('[onclick^="window.' + fn + '("]')); }
function closeAll(){ window.vaultDangerMenuTog(false); window.vaultTasksTog(false, true); var a = by('#vault-advanced'); if (a) a.open = false; }
"""

WORLD = ("window._vaultAutoIntakeSet(false); window.switchTab('vault');"
         "var c = document.getElementById('mule-vault-card');"
         "if (c && c.classList.contains('collapsed')) window.toggleCardCollapse('mule-vault-card');"
         "var owned = window.eval('owned'); owned.add('Obedience');"
         "window._ownedProvWrite('Obedience', { source: 'intake-read', by: 'law', holder: 'Chronicle', loc: 'chronicle', scene: 'chronicle', sessionId: 's1', frameId: 'f1', ts: Date.now() });"
         "renderVault(); window._vaultMovePaint();")

# the design's mapping table: handler -> how a person reaches it (the controls pressed first, all visible + harmless)
TOOLBAR = ["vaultAutoSortByHand", "vaultAddMule", "vaultExport", "_vaultAutoIntakeToggle"]
DANGER = ["vaultClearUnsorted", "vaultReset", "vaultClearHistory", "vaultWipeItems"]
ADVANCED = [("keepers", "#vault-multikeep"), ("registered", "#vault-registered"), ("registered", "#vault-intake-report"),
            ("registered", "#vault-journal"), ("stash", "#vault-share-settings"), ("ledger", "#routing-ledger"),
            ("keep", "#vault-keep"), ("reviews", "#vault-socketed"), ("reviews", "#vault-throwout"),
            ("reviews", "#vault-suggested"), ("help", ".vault-shot-guide > summary"), ("help", ".vd-howto > summary")]


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class EveryVaultDoorIsReachable(unittest.TestCase):

    def setUp(self):
        board().seed({"d2r_owned": [SHAKO], "d2r_muleAssign": {}, "d2r_vaultRecords": None,
                      "d2r_vaultProv": {SHAKO: {"kind": "owned", "source": "tv", "seen": 2, "looks": [
                          {"session": "w%d" % i, "frame": "f%d" % i, "holder": "MAIN", "loc": "stash", "cell": "c4r0"} for i in range(2)]}}})
        board().run(WORLD + "OUT.ok = 1;")

    def test_the_toolbar_doors_are_on_screen_and_sort_is_one_button(self):
        o = board().run(SEEN + "closeAll(); OUT.r = {};"
                        "%s.forEach(function(f){ OUT.r[f] = doors(f).filter(seen).length; });"
                        "OUT.sortInDock = !!by('#vault-dock-bar [onclick*=\"vaultAutoSortByHand\"]');"
                        "OUT.sortN = (by('#vault-sort-n') || {}).textContent || ''; OUT.sortNSeen = seen(by('#vault-sort-n'));"
                        "OUT.label = (door('vaultAutoSortByHand') || {}).textContent || '';" % json.dumps(TOOLBAR))
        for f in TOOLBAR:
            self.assertGreaterEqual(o["r"][f], 1, "%s has no visible control any more: %r" % (f, o))
        self.assertEqual(o["r"]["vaultAutoSortByHand"], 1, "sorting is not ONE button (Auto-assign + Auto-Sort merged): %r" % o)
        self.assertFalse(o["sortInDock"], "the dock bar grew its own Auto-Sort button back")
        self.assertIn("Sort to mules", o["label"])
        self.assertTrue(o["sortNSeen"] and o["sortN"].endswith("loose"), "the sort button does not carry the loose count: %r" % o)

    def test_the_danger_doors_are_reached_through_the_one_menu(self):
        o = board().run(SEEN + "closeAll(); OUT.before = {}; OUT.after = {};"
                        "var D = %s; D.forEach(function(f){ OUT.before[f] = doors(f).filter(seen).length; });"
                        "OUT.tog = seen(by('#vault-danger-tog')); by('#vault-danger-tog').click();"
                        "D.forEach(function(f){ var d = doors(f); OUT.after[f] = [d.length, d.filter(seen).length,"
                        "  d.every(function(e){ return !!e.closest('#vault-danger-menu'); })]; });"
                        "var _f = window._menuAscendingFraction, _n = window._menuRunNames;"
                        "window._menuAscendingFraction = function(){ return { frac: 1, up: 9, steps: 9, matched: 10 }; };"
                        "window._menuRunNames = function(){ return ['Obedience']; }; renderVault();"
                        "OUT.menuImport = seen(door('vaultDropMenuImport')) && !!door('vaultDropMenuImport').closest('#vault-danger-menu');"
                        "window._menuAscendingFraction = _f; window._menuRunNames = _n; renderVault(); OUT.menuImportGone = !seen(door('vaultDropMenuImport'));"
                        "closeAll();" % json.dumps(DANGER))
        self.assertTrue(o["tog"], "the ⚠ Clear & reset toggle is not on screen")
        for f in DANGER:
            self.assertEqual(o["before"][f], 0, "%s is on screen without opening the danger menu: %r" % (f, o))
            self.assertEqual(o["after"][f], [1, 1, True], "%s is not exactly one visible row of the danger menu: %r" % (f, o))
        self.assertTrue(o["menuImport"], "the chronicle-page cleanup is not reachable when the verdict says menu")
        self.assertTrue(o["menuImportGone"], "the chronicle-page row shows without a menu verdict")

    def test_hand_add_planner_and_find_are_on_screen(self):
        o = board().run(SEEN + "closeAll(); var h = doors('vaultHandOpen'); OUT.hand = [h.length, h.filter(seen).length, h.length ? h[0].tagName : ''];"
                        "OUT.planner = seen(by('#vault-planner-q')); OUT.find = seen(by('#vault-find-input'));"
                        "OUT.handText = h.length ? h[0].textContent : '';"
                        "OUT.handAfterPlanner = !!(h.length && by('.vault-find-row').compareDocumentPosition(h[0]) & Node.DOCUMENT_POSITION_FOLLOWING);"
                        "h[0].click(); await new Promise(function(r){ setTimeout(r, 300); });"
                        "OUT.box = [].slice.call(document.querySelectorAll('#vault-hand-box, .vault-hand-box, #vault-hand')).some(seen);"
                        "try { window.vaultHandClose(); } catch (e) {}")
        self.assertEqual(o["hand"], [1, 1, "BUTTON"], "add-by-name is not ONE visible button: %r" % o)
        self.assertIn("add by name only", o["handText"])
        self.assertTrue(o["handAfterPlanner"], "the add-by-name link is not under the planner bar")
        self.assertTrue(o["planner"] and o["find"], "the planner bar or Find on a mule left the screen: %r" % o)
        self.assertTrue(o["box"], "pressing add by name only did not open the hand-add box")

    def test_the_folder_doors_are_in_the_intake_strip_in_both_states(self):
        o = board().run(SEEN + "closeAll(); window._setFolderConnectedUI(false);"
                        "OUT.off = { connect: seen(door('vaultConnectFolder')), scan: seen(door('vaultScanFolder')), clear: seen(door('vaultClearScanHistory')) };"
                        "window._setFolderConnectedUI(true);"
                        "OUT.on = { connect: seen(door('vaultConnectFolder')), scan: seen(door('vaultScanFolder')), clear: seen(door('vaultClearScanHistory')) };"
                        "OUT.inStrip = ['vaultConnectFolder', 'vaultScanFolder', 'vaultClearScanHistory', '_vaultAutoIntakeToggle'].map(function(f){"
                        "  var d = door(f); return !!(d && d.closest('#vault-intake-strip')); });"
                        "OUT.clearNotDanger = !door('vaultClearScanHistory').closest('#vault-danger');"
                        "window._setFolderConnectedUI(false);")
        self.assertTrue(o["off"]["connect"], "no visible Connect folder door before a folder is linked: %r" % o)
        self.assertTrue(o["on"]["scan"] and o["on"]["clear"], "Scan / Clear scan history not visible once linked: %r" % o)
        self.assertTrue(all(o["inStrip"]), "a folder door left the intake strip: %r" % o)
        self.assertTrue(o["clearNotDanger"], "Clear scan history moved into the danger menu (his answer: it stays in the strip)")

    def test_move_tasks_tick_and_untick_are_reached_from_the_fab(self):
        o = board().run(SEEN + "closeAll(); var f = by('#vault-tasks-fab'); OUT.fab = seen(f); OUT.listBefore = seen(by('#vault-move-list'));"
                        "f.click(); OUT.listAfter = seen(by('#vault-move-list'));"
                        "var tick = [].slice.call(document.querySelectorAll('#vault-move-list .vtk-list:not([data-sec=done]) [onclick*=\"_vaultTaskTick\"]')).filter(seen);"
                        "OUT.ticks = tick.length; if (tick.length) tick[0].click();"
                        "var dn = by('#vault-move-list .vtk-donebox'); if (dn) dn.open = true;"
                        "OUT.untick = [].slice.call(document.querySelectorAll('#vault-move-list [onclick*=\"_vaultTaskUntick\"]')).filter(seen).length;"
                        "closeAll();")
        self.assertTrue(o["fab"], "the 📦 MOVE TASKS FAB is not on screen")
        self.assertFalse(o["listBefore"], "premise: the overlay starts closed")
        self.assertTrue(o["listAfter"], "the FAB does not open the MOVE TASKS list")
        self.assertGreaterEqual(o["ticks"], 1, "no visible tick box on an open task: %r" % o)
        self.assertGreaterEqual(o["untick"], 1, "his tick cannot be taken back from a visible control: %r" % o)

    def test_every_advanced_panel_is_one_tab_away(self):
        o = board().run(SEEN + "closeAll(); var adv = by('#vault-advanced'); OUT.sum = seen(adv.querySelector('summary'));"
                        "var A = %s; OUT.closed = A.map(function(a){ return seen(by(a[1])) || !!(by(a[1]) && seen(by(a[1]).closest('.vadv-pane'))); });"
                        "adv.querySelector('summary').click(); await new Promise(function(r){ setTimeout(r, 100); });"
                        "OUT.r = A.map(function(a){ var t = adv.querySelector('.vadv-tab[data-adv=\"' + a[0] + '\"]'); var ts = seen(t); if (t) t.click();"
                        "  var el = by(a[1]); var pane = el ? el.closest('.vadv-pane') : null;"
                        "  return [a[1], ts, !!pane && pane.getAttribute('data-adv') === a[0], !!pane && seen(pane), !!el && !!el.closest('#vault-advanced')]; });"
                        "OUT.detailOutside = !by('#vault-detail').closest('#vault-advanced');"
                        "closeAll();" % json.dumps(ADVANCED))
        self.assertTrue(o["sum"], "the ⚙ Advanced summary is not on screen")
        self.assertFalse(any(o["closed"]), "an Advanced panel shows while the drawer is closed: %r" % o)
        for row in o["r"]:
            self.assertEqual(row[1:], [True, True, True, True], "%s is not reached by its visible Advanced tab: %r" % (row[0], row))
        self.assertTrue(o["detailOutside"], "the mule window (#vault-detail) went into the drawer - it must open from the mules")


RED_PROOF = [
    {"why": "Add mule drops off the toolbar.",
     "file": "bible.html",
     "find": "        <button class=\"vault-btn\" onclick=\"window.vaultAddMule()\">➕ Add mule</button>\n",
     "replace": "",
     "matches": 1},
    {"why": "The dock bar's Auto-Sort comes back beside the toolbar's (two sort buttons again).",
     "file": "bible.html",
     "find": "          +'<span class=\"vdb-hint\">sort them with",
     "replace": "          +'<button class=\"vault-resort-btn\" onclick=\"window.vaultAutoSortByHand()\">Auto-Sort</button><span class=\"vdb-hint\">sort them with",
     "matches": 1},
    {"why": "The sort button loses its loose count.",
     "file": "bible.html",
     "find": "      if (_sn){ _sn.hidden = !unsorted.length;",
     "replace": "      if (_sn){ _sn.hidden = true;",
     "matches": 1},
    {"why": "Reset assignments is dropped from the danger menu.",
     "file": "bible.html",
     "find": "<button class=\"vault-btn vault-btn-danger vdm-go\" role=\"menuitem\" onclick=\"window.vaultReset()\"",
     "replace": "<button class=\"vault-btn vault-btn-danger vdm-go\" role=\"menuitem\" hidden onclick=\"window.vaultReset()\"",
     "matches": 1},
    {"why": "Wipe items sits on the toolbar again, outside the menu.",
     "file": "bible.html",
     "find": "        <span class=\"vault-lock-chip\" id=\"vault-lock-chip\" hidden></span>\n",
     "replace": "        <button class=\"vault-btn vault-btn-danger\" onclick=\"window.vaultWipeItems()\">Wipe</button>\n        <span class=\"vault-lock-chip\" id=\"vault-lock-chip\" hidden></span>\n",
     "matches": 1},
    {"why": "The danger toggle never opens the menu.",
     "file": "bible.html",
     "find": "    var want = (typeof open === 'boolean') ? open : !!m.hidden;\n    m.hidden = !want;",
     "replace": "    var want = false;\n    m.hidden = !want;",
     "matches": 1},
    {"why": "The chronicle-page cleanup row is never painted into the menu.",
     "file": "bible.html",
     "find": "        _mi.hidden = !_isMenu;",
     "replace": "        _mi.hidden = true;",
     "matches": 1},
    {"why": "The add-by-name link under the planner is dropped (vaultHandOpen has no door).",
     "file": "bible.html",
     "find": "<button class=\"vault-hand-link\" type=\"button\" onclick=\"window.vaultHandOpen()\"",
     "replace": "<button class=\"vault-hand-link\" type=\"button\" hidden onclick=\"window.vaultHandOpen()\"",
     "matches": 1},
    {"why": "Clear scan history no longer shows in the intake strip once a folder is linked.",
     "file": "bible.html",
     "find": "<button class=\"vault-btn\" id=\"vault-clear-scan-btn\" style=\"display:none;",
     "replace": "<button class=\"vault-btn\" hidden id=\"vault-clear-scan-btn\" style=\"display:none;",
     "matches": 1},
    {"why": "The MOVE TASKS FAB does not open the overlay.",
     "file": "bible.html",
     "find": "    var want = (typeof open === 'boolean') ? open : !!p.hidden;\n    if (want) { var adv",
     "replace": "    var want = (typeof open === 'boolean') ? open : false;\n    if (want) { var adv",
     "matches": 1},
    {"why": "A hand tick can no longer be unticked (no undo snapshot is kept).",
     "file": "bible.html",
     "find": "    if (ens.task && ens.task.status !== 'moved-manual') t.undo = {",
     "replace": "    if (false) t.undo = {",
     "matches": 1},
    {"why": "The Advanced tabs never switch panes.",
     "file": "bible.html",
     "find": "function(p){ var on = p.getAttribute('data-adv') === name; p.hidden = !on; if (on) hit = true; }",
     "replace": "function(p){ var on = p.getAttribute('data-adv') === name; if (on) hit = true; }",
     "matches": 1},
    {"why": "The routing ledger loses its Advanced tab (only the tab is gone; the pane is still there).",
     "file": "bible.html",
     "find": "data-adv=\"ledger\" aria-selected=\"false\" onclick=\"window.vaultAdvTab('ledger')\">Routing ledger</button>",
     "replace": "data-adv=\"ledger-x\" aria-selected=\"false\" hidden>Routing ledger</button>",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
