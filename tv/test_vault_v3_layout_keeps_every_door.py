# -*- coding: utf-8 -*-
"""Vault v3 layout (Elad t642u/t643u/t659u/t661u, mock approved 2026-10-24) and Save / Load profile (t663u/t664u/t665u).

The layout MOVES doors; it removes none. This law proves, on the shipped page with fixture data only (no real reset is
pressed — every destructive door is driven with its confirm answered NO or replaced), that:

  * every original vault door is still in the page with its original handler, in its new home
    (AUTO INTAKE + folder doors -> Advanced "Auto-intake & screenshots"; lock panel -> Advanced "Locked on MAIN";
    Clear & reset -> footer "Reset & restore" / "Vault & mules"; the 3 footer resets unchanged in "Account & chronicle");
  * Advanced stays a collapsed <details> and still opens on Keepers;
  * the reset menu carries no "Danger" word, while the second step (the confirm) does;
  * the two tool cards are equal width and height on one grid;
  * Copy manifests is byte-for-byte the v3795 function and button;
  * a profile save -> load round-trips byte-identical stores; a corrupt or foreign file is refused and writes nothing.
NO CHROME = a declared skip. [[regression-guard]]
"""
import hashlib
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

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


WORLD = ("window._vaultAutoIntakeSet(false); window.switchTab('vault');"
         "var c = document.getElementById('mule-vault-card');"
         "if (c && c.classList.contains('collapsed')) window.toggleCardCollapse('mule-vault-card');"
         "renderVault();")
WAIT = "await new Promise(function(r){ setTimeout(r, 250); });"

# the v3795 vaultExport, hashed from 27b9a028 — Copy manifests must not change by one byte
EXPORT_SHA = "143bc7ee2f9551c746efb208b1e6e993d6f907620648596819f9288b779437e5"
EXPORT_BTN = '<button class="vault-btn" onclick="window.vaultExport()">📋 Copy manifests</button>'


class CopyManifestsUnchanged(unittest.TestCase):
    def test_copy_manifests_is_the_v3795_door(self):
        with open(BIBLE, encoding="utf-8") as fh:
            s = fh.read()
        i = s.index("  window.vaultExport = function(){")
        j = s.index("\n  };\n", i) + 6
        self.assertEqual(hashlib.sha256(s[i:j].encode()).hexdigest(), EXPORT_SHA, "vaultExport (Copy manifests) changed")
        self.assertEqual(s.count(EXPORT_BTN), 1, "the Copy manifests button changed or moved out of the toolbar")


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class VaultV3LayoutKeepsEveryDoor(unittest.TestCase):

    def setUp(self):
        board().seed({"d2r_muleAssign": {}})
        board().run(WORLD + "OUT.ok = 1;")

    def test_every_moved_door_lives_in_its_new_home(self):
        o = board().run(
            "function home(sel){ var e = document.querySelector(sel); if (!e) return null;"
            "  var p = e.closest('.vadv-pane'); if (p) return 'adv:' + p.getAttribute('data-adv');"
            "  if (e.closest('#reset-grp-vault')) return 'reset:vault'; if (e.closest('#reset-grp-account')) return 'reset:account';"
            "  if (e.closest('.vault-toolbar')) return 'toolbar'; if (e.closest('.vault-deck')) return 'deck'; return 'other'; }"
            "OUT.h = {};"
            "[\"[onclick*='_vaultAutoIntakeToggle']\", '#vault-folder-btn', '#vault-scan-btn', '#vault-clear-scan-btn', '#vault-dir-input', '#vault-watcher',"
            " '#vault-lane-locks', '#vault-danger-tog', \"[onclick*='vaultClearUnsorted']\", \"[onclick*='window.vaultReset()']\","
            " \"[onclick*='vaultClearHistory']\", \"[onclick*='vaultWipeItems']\", '#vault-danger-cancel',"
            " \"[onclick*='_d2rUnseedRestore']\", \"[onclick*='_d2rUnseed()']\", \"[onclick*='vaultAutoSortByHand']\","
            " \"[onclick*='vaultAddMule']\", \"[onclick*='vaultExport']\", '#vault-profile-save', '#vault-profile-load',"
            " '#vault-planner-q', '#vault-find-input', '.vault-hand-link', '#vault-lock-chip', '#vault-status']"
            ".forEach(function(s){ OUT.h[s] = home(s); });"
            "OUT.resetBtns = document.querySelectorAll('#reset-grp-account .reset-btn').length;"
            "var adv = document.getElementById('vault-advanced'); OUT.advOpen = adv.open; OUT.advTag = adv.tagName;"
            "OUT.advDefault = (adv.querySelector('.vadv-tab[aria-selected=true]') || {}).getAttribute('data-adv');"
            "OUT.advLast = !adv.nextElementSibling || !adv.parentElement.querySelector('#vault-advanced ~ .vault-tasks-pop');")
        h = o["h"]
        for s in ["[onclick*='_vaultAutoIntakeToggle']", "#vault-folder-btn", "#vault-scan-btn", "#vault-clear-scan-btn",
                  "#vault-dir-input", "#vault-watcher"]:
            self.assertEqual(h[s], "adv:intake", "%s is not in Advanced → Auto-intake: %r" % (s, h))
        self.assertEqual(h["#vault-lane-locks"], "adv:locks", h)
        for s in ["#vault-danger-tog", "[onclick*='vaultClearUnsorted']", "[onclick*='window.vaultReset()']",
                  "[onclick*='vaultClearHistory']", "[onclick*='vaultWipeItems']", "#vault-danger-cancel"]:
            self.assertEqual(h[s], "reset:vault", "%s is not in Reset & restore → Vault & mules: %r" % (s, h))
        for s in ["[onclick*='_d2rUnseedRestore']", "[onclick*='_d2rUnseed()']"]:
            self.assertEqual(h[s], "reset:account", h)
        self.assertEqual(o["resetBtns"], 3, "the three account/chronicle resets must all stay: %r" % o)
        for s in ["[onclick*='vaultAutoSortByHand']", "[onclick*='vaultAddMule']", "[onclick*='vaultExport']",
                  "#vault-profile-save", "#vault-profile-load", "#vault-lock-chip", "#vault-status"]:
            self.assertEqual(h[s], "toolbar", "%s left the toolbar: %r" % (s, h))
        for s in ["#vault-planner-q", "#vault-find-input", ".vault-hand-link"]:
            self.assertEqual(h[s], "deck", h)
        self.assertEqual(o["advTag"], "DETAILS")
        self.assertFalse(o["advOpen"], "Advanced must start collapsed")
        self.assertEqual(o["advDefault"], "keepers", "Advanced must still open on Keepers")

    def test_chips_open_the_moved_panels(self):
        o = board().run("document.getElementById('vault-chip-intake').click();" + WAIT
                        + "var adv = document.getElementById('vault-advanced');"
                        "OUT.intake = [adv.open, !document.querySelector('.vadv-pane[data-adv=intake]').hidden];"
                        "window.vaultAdvTab('locks');"
                        "OUT.locks = !document.querySelector('.vadv-pane[data-adv=locks]').hidden;"
                        "OUT.chipSays = document.getElementById('vault-chip-intake').textContent;"
                        "window.vaultAdvTab('keepers'); adv.open = false;")
        self.assertEqual(o["intake"], [True, True], o)
        self.assertTrue(o["locks"], o)
        self.assertIn("off", o["chipSays"].lower(), o)

    def test_menu_says_no_danger_but_the_second_step_does(self):
        o = board().run(
            "var z = document.querySelector('details.danger-zone'); z.open = true;"
            "OUT.summary = z.querySelector('summary').textContent;"
            "OUT.menu = document.getElementById('vault-danger').textContent;"
            "var seen = []; var real = window.uiConfirm;"
            "window.uiConfirm = function(m, o){ seen.push((o && o.title) || ''); return Promise.resolve(false); };"
            "try { await window.vaultReset(); await window.vaultWipeItems(); await window.vaultClearHistory(); } finally { window.uiConfirm = real; }"
            "OUT.titles = seen;"
            "var p = real('fixture question', { cancelFirst: true, title: '⚠ Danger — Reset vault' });"
            "await new Promise(function(r){ setTimeout(r, 120); });"
            "var t = document.querySelector('.ui-confirm-title'); OUT.drawn = t ? t.textContent : null;"
            "var cbtn = [].slice.call(document.querySelectorAll('.ui-confirm button')).filter(function(b){ return /cancel/i.test(b.textContent); })[0];"
            "if (cbtn) cbtn.click(); OUT.answer = await p; z.open = false;")
        self.assertIn("Reset & restore", o["summary"])
        self.assertNotIn("danger", o["summary"].lower())
        self.assertNotIn("danger", o["menu"].lower(), "the reset menu still shouts DANGER: %r" % o["menu"][:200])
        self.assertEqual(len(o["titles"]), 3, o)
        for t in o["titles"]:
            self.assertTrue(t.startswith("⚠ Danger — "), "a second step lost its Danger heading: %r" % o)
        self.assertEqual(o["drawn"], "⚠ Danger — Reset vault", o)
        self.assertFalse(o["answer"], "the fixture confirm was not cancelled: %r" % o)

    def test_the_two_cards_are_twins_on_one_grid(self):
        board().run("document.documentElement.style.width = '1440px';")
        o = board().run("function r(s){ var b = document.querySelector(s).getBoundingClientRect(); return [Math.round(b.top), Math.round(b.width), Math.round(b.height)]; }"
                        "OUT.a = r('.vault-tool-add'); OUT.f = r('.vault-tool-find');"
                        "var ha = getComputedStyle(document.querySelector('.vault-tool-add .vault-tool-h')),"
                        "    hf = getComputedStyle(document.querySelector('.vault-tool-find .vault-tool-h'));"
                        "OUT.h = [ha.fontSize, hf.fontSize, ha.letterSpacing, hf.letterSpacing];"
                        "OUT.grid = getComputedStyle(document.querySelector('.vault-deck')).display;")
        self.assertEqual(o["grid"], "grid")
        if o["a"][1] > 0:
            self.assertEqual(o["a"], o["f"], "the ADD and FIND cards are not twins: %r" % o)
        self.assertEqual(o["h"][0], o["h"][1], o)
        self.assertEqual(o["h"][2], o["h"][3], o)

    def test_profile_round_trip_is_byte_identical(self):
        stores = {"d2r_muleRoster": [{"id": "m1", "name": "Fixture Mule"}], "d2r_muleAssign": {"Fixture Ring": "m1"},
                  "d2r_mulePos": {"Fixture Ring": {"tab": 1, "cell": "c2r3"}}, "d2r_laneLock": {"Fixture Ring": "MAIN"},
                  "d2r_runeStash": {"Ber": 2}, "d2r_charBuilds": {"b1": {"name": "Fixture Sorc", "gear": {"helm": "Shako"}, "inv": ["Torch"]}}}
        board().seed(stores)
        o = board().run(
            "var keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ keys = keys.concat(window._PROFILE_STORES[g]); });"
            "function snap(){ var s = {}; keys.forEach(function(k){ s[k] = window.LSR.getItem(k); }); return s; }"
            "var before = snap(); var file = window._vaultProfileBuild();"
            "OUT.hasChron = /d2r_foundLog|d2r_setPieces|d2r_owned\"/.test(file);"
            "keys.forEach(function(k){ window.LSR.setItem(k, JSON.stringify({scribbled: k})); });"
            "var r = await window.vaultProfileLoad(file, { confirm: function(){ return true; }, noReload: true });"
            "var after = snap(); OUT.r = r;"
            "OUT.diff = keys.filter(function(k){ return before[k] !== after[k]; });"
            "OUT.ring = after['d2r_muleAssign'];")
        self.assertTrue(o["r"]["ok"], o)
        self.assertEqual(o["diff"], [], "a save→load did not put the stores back byte-identical: %r" % o)
        self.assertEqual(json.loads(o["ring"]), {"Fixture Ring": "m1"})
        self.assertFalse(o["hasChron"], "the profile file carries the chronicle, which has its own backups")

    def test_a_corrupt_or_foreign_file_is_refused_and_writes_nothing(self):
        board().seed({"d2r_muleAssign": {"Fixture Ring": "m1"}, "d2r_runeStash": {"Ber": 2}})
        o = board().run(
            "var keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ keys = keys.concat(window._PROFILE_STORES[g]); });"
            "function snap(){ var s = {}; keys.forEach(function(k){ s[k] = window.LSR.getItem(k); }); s.c = window.LSR.getItem('d2r_foundLog'); return s; }"
            "var before = JSON.stringify(snap()); var asked = 0;"
            "var good = JSON.parse(window._vaultProfileBuild());"
            "var bad = ['{not json', JSON.stringify({kind: 'grail-progress', version: 1, stores: {}}),"
            "  JSON.stringify(Object.assign({}, good, {version: 99})),"
            "  JSON.stringify(Object.assign({}, good, {stores: Object.assign({}, good.stores, {d2r_foundLog: '{}'})})),"
            "  JSON.stringify(Object.assign({}, good, {stores: Object.assign({}, good.stores, {d2r_muleAssign: '{broken'})}))];"
            "OUT.res = [];"
            "for (var i = 0; i < bad.length; i++){ OUT.res.push(await window.vaultProfileLoad(bad[i], { confirm: function(){ asked++; return true; }, noReload: true })); }"
            "OUT.asked = asked; OUT.same = JSON.stringify(snap()) === before;"
            "OUT.say = document.getElementById('vault-status').textContent;")
        for r in o["res"]:
            self.assertFalse(r["ok"], o)
            self.assertTrue(r.get("why"), o)
        self.assertEqual(o["asked"], 0, "a bad file reached the confirm: %r" % o)
        self.assertTrue(o["same"], "a refused file wrote something: %r" % o)
        self.assertIn("Nothing was changed", o["say"])


if __name__ == "__main__":
    unittest.main()
