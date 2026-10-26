# -*- coding: utf-8 -*-
"""Vault v3 layout (Elad t642u/t643u/t659u/t661u, mock approved 2026-10-24) and Save / Load profile (t663u/t664u/t665u).

The layout MOVES doors; it removes none. This law proves, on the shipped page with fixture data only (no real reset is
pressed — every destructive door is driven with its confirm answered NO or replaced), that:

  * every original vault door is still in the page with its original handler, in its new home
    (AUTO INTAKE + folder doors -> Advanced "Auto-intake & screenshots"; lock panel -> a collapsed row at the bottom of the vault;
    Clear & reset -> footer "Reset & restore" / "Vault & mules"; the 3 footer resets unchanged in "Account & chronicle");
  * Advanced stays a collapsed <details> and still opens on Keepers;
  * the reset menu carries no "Danger" word, while the second step (the confirm) does;
  * the two tool cards are equal width and height on one grid;
  * Copy manifests is removed (Elad 14:32 IDT 2026-10-24, the one sanctioned removal);
  * a profile save -> load round-trips byte-identical stores; a corrupt or foreign file is refused and writes nothing.
NO CHROME = a declared skip. [[regression-guard]]
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

class CopyManifestsIsGone(unittest.TestCase):
    """Elad 14:32 IDT 2026-10-24 — the one sanctioned removal: Copy manifests (button + window.vaultExport) is gone, nothing calls it."""
    def test_copy_manifests_is_removed_everywhere(self):
        with open(BIBLE, encoding="utf-8") as fh:
            s = fh.read()
        self.assertNotIn("vaultExport", s)
        self.assertNotIn("Copy manifests", s)


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class VaultV3LayoutKeepsEveryDoor(unittest.TestCase):

    def setUp(self):
        board().seed({"d2r_muleAssign": {}})
        board().run(WORLD + "OUT.ok = 1;")

    def test_every_moved_door_lives_in_its_new_home(self):
        o = board().run(
            "function home(sel){ var e = document.querySelector(sel); if (!e) return null;"
            "  if (e.closest('#vault-locks-fold')) return 'locks:bottom';"
            "  var p = e.closest('.vadv-pane'); if (p) return 'adv:' + p.getAttribute('data-adv');"
            "  if (e.closest('#reset-grp-vault')) return 'reset:vault'; if (e.closest('#reset-grp-account')) return 'reset:account';"
            "  if (e.closest('#vault-profile-grp')) return 'profile'; if (e.closest('.vault-toolbar')) return 'toolbar'; if (e.closest('.vault-deck')) return 'deck'; return 'other'; }"
            "OUT.h = {};"
            "[\"[onclick*='_vaultAutoIntakeToggle']\", '#vault-folder-btn', '#vault-scan-btn', '#vault-clear-scan-btn', '#vault-dir-input', '#vault-watcher',"
            " '#vault-lane-locks', '#vault-danger-tog', \"[onclick*='vaultClearUnsorted']\", \"[onclick*='window.vaultReset()']\","
            " \"[onclick*='vaultClearHistory']\", \"[onclick*='vaultWipeItems']\", '#vault-danger-cancel',"
            " \"[onclick*='_d2rUnseedRestore']\", \"[onclick*='_d2rUnseed()']\", \"[onclick*='vaultAutoSortByHand']\","
            " \"[onclick*='vaultAddMule']\", '#vault-profile-save', '#vault-profile-load',"
            " '#vault-planner-q', '#vault-find-input', '.vault-hand-link', '#vault-lock-chip', '#vault-status']"
            ".forEach(function(s){ OUT.h[s] = home(s); });"
            "OUT.resetBtns = document.querySelectorAll('#reset-grp-account .reset-btn').length;"
            "var adv = document.getElementById('vault-advanced'); OUT.advOpen = adv.open; OUT.advTag = adv.tagName;"
            "OUT.advDefault = (adv.querySelector('.vadv-tab[aria-selected=true]') || {}).getAttribute('data-adv');"
            "OUT.advLast = !adv.nextElementSibling || !adv.parentElement.querySelector('#vault-advanced ~ .vault-tasks-pop');"
            "OUT.locksTab = !!document.querySelector('.vadv-tab[data-adv=locks]');"
            "var fold0 = document.getElementById('vault-locks-fold');"
            "OUT.foldClosed = !!(fold0 && fold0.tagName === 'DETAILS' && !fold0.open);")
        h = o["h"]
        for s in ["[onclick*='_vaultAutoIntakeToggle']", "#vault-folder-btn", "#vault-scan-btn", "#vault-clear-scan-btn",
                  "#vault-dir-input", "#vault-watcher"]:
            self.assertEqual(h[s], "adv:intake", "%s is not in Advanced → Auto-intake: %r" % (s, h))
        self.assertEqual(h["#vault-lane-locks"], "locks:bottom", h)
        self.assertFalse(o["locksTab"], "Locked where they are went back into an Advanced tab: %r" % o)
        self.assertTrue(o["foldClosed"], "the lock row must start collapsed: %r" % o)
        for s in ["#vault-danger-tog", "[onclick*='vaultClearUnsorted']", "[onclick*='window.vaultReset()']",
                  "[onclick*='vaultClearHistory']", "[onclick*='vaultWipeItems']", "#vault-danger-cancel"]:
            self.assertEqual(h[s], "reset:vault", "%s is not in Reset & restore → Vault & mules: %r" % (s, h))
        for s in ["[onclick*='_d2rUnseedRestore']", "[onclick*='_d2rUnseed()']"]:
            self.assertEqual(h[s], "reset:account", h)
        self.assertEqual(o["resetBtns"], 3, "the three account/chronicle resets must all stay: %r" % o)
        for s in ["#vault-profile-save", "#vault-profile-load"]:
            self.assertEqual(h[s], "profile", "%s is not in the 💾 profile row above Add an item: %r" % (s, h))
        for s in ["[onclick*='vaultAutoSortByHand']", "[onclick*='vaultAddMule']", "#vault-lock-chip", "#vault-status"]:
            self.assertEqual(h[s], "toolbar", "%s left the toolbar: %r" % (s, h))
        for s in ["#vault-planner-q", "#vault-find-input", ".vault-hand-link"]:
            self.assertEqual(h[s], "deck", h)
        self.assertEqual(o["advTag"], "DETAILS")
        self.assertFalse(o["advOpen"], "Advanced must start collapsed")
        self.assertEqual(o["advDefault"], "keepers", "Advanced must still open on Keepers")

    def test_chips_open_the_moved_panels(self):
        o = board().run("OUT.chip = document.getElementById('vault-chip-intake');"
                        "var adv = document.getElementById('vault-advanced');"
                        "adv.open = true; window.vaultAdvTab('intake');" + WAIT
                        + "OUT.intake = [adv.open, !document.querySelector('.vadv-pane[data-adv=intake]').hidden];"
                        "var tog = document.getElementById('vault-auto-intake');"
                        "OUT.toggleSeen = !!(tog && tog.getClientRects().length);"
                        "OUT.toggleText = tog ? tog.textContent : '';"
                        "var fold = document.getElementById('vault-locks-fold');"
                        "OUT.fold = [fold.tagName, fold.open];"
                        "window.vaultLocksShow();"
                        "OUT.locks = fold.open && !!document.getElementById('vault-lane-locks');"
                        "fold.open = false;"
                        "window.vaultAdvTab('keepers'); adv.open = false;")
        self.assertIsNone(o["chip"], o)
        self.assertEqual(o["intake"], [True, True], o)
        self.assertTrue(o["toggleSeen"], o)
        self.assertIn("OFF", o["toggleText"], o)
        self.assertTrue(o["locks"], o)

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
        b = board()
        b.t.send("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
        try:
            o = b.run("function r(s){ var b = document.querySelector(s).getBoundingClientRect(); return [Math.round(b.top), Math.round(b.width), Math.round(b.height)]; }"
                        "OUT.a = r('.vault-tool-add'); OUT.f = r('.vault-tool-find');"
                        "var ha = getComputedStyle(document.querySelector('.vault-tool-add .vault-tool-h')),"
                        "    hf = getComputedStyle(document.querySelector('.vault-tool-find .vault-tool-h'));"
                        "OUT.h = [ha.fontSize, hf.fontSize, ha.letterSpacing, hf.letterSpacing];"
                        "OUT.grid = getComputedStyle(document.querySelector('.vault-deck')).gridTemplateColumns;")
        finally:
            b.t.send("Emulation.clearDeviceMetricsOverride")
        self.assertEqual(len(o["grid"].split()), 2, "the deck is not two columns at 1440: %r" % o)
        self.assertGreater(o["a"][1], 300, o)
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
            "OUT.hasChron = /d2r_foundLog|d2r_setPieces|d2r_grailUnfound|d2r_gameFound/.test(file);"
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

    def test_a_held_store_mid_load_rolls_back_and_a_no_writes_nothing(self):
        board().seed({"d2r_muleAssign": {"Fixture Ring": "m1"}, "d2r_runeStash": {"Ber": 2}, "d2r_charBuilds": {"b1": {"name": "A"}}})
        o = board().run(
            "var keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ keys = keys.concat(window._PROFILE_STORES[g]); });"
            "function snap(){ var s = {}; keys.forEach(function(k){ s[k] = window.LSR.getItem(k); }); return JSON.stringify(s); }"
            "var good = JSON.parse(window._vaultProfileBuild());"
            "good.stores.d2r_muleAssign = JSON.stringify({'Other Ring': 'm2'}); good.stores.d2r_runeStash = JSON.stringify({Jah: 1});"
            "good.stores.d2r_charBuilds = JSON.stringify({b2: {name: 'B'}}); var file = JSON.stringify(good);"
            "var before = snap();"
            "OUT.no = await window.vaultProfileLoad(file, { confirm: function(){ return false; }, noReload: true }); OUT.noSame = snap() === before;"
            "var real = window.LSR.setItem;"
            "window.LSR.setItem = function(k, v){ if (k === 'd2r_runeStash' && v.indexOf('Jah') >= 0) return false; return real.apply(this, arguments); };"
            "try { OUT.held = await window.vaultProfileLoad(file, { confirm: function(){ return true; }, noReload: true }); } finally { window.LSR.setItem = real; }"
            "OUT.heldSame = snap() === before;"
            "var bad = JSON.parse(file); bad.stores.d2r_vaultRemovedAt = 'not json';"
            "OUT.removedAt = await window.vaultProfileLoad(JSON.stringify(bad), { confirm: function(){ return true; }, noReload: true });"
            "var proto = JSON.parse(file); proto.stores.constructor = '{}';"
            "OUT.proto = await window.vaultProfileLoad(JSON.stringify(proto), { confirm: function(){ return true; }, noReload: true });"
            "var big = JSON.parse(file); var m = {}; for (var i = 0; i < 400; i++) m['Item ' + i] = Date.now(); big.stores.d2r_vaultRemovedAt = JSON.stringify(m);"
            "OUT.bigOk = window._vaultProfileParse(JSON.stringify(big)).ok;"
            "OUT.allSame = snap() === before;")
        self.assertFalse(o["no"]["ok"], o)
        self.assertTrue(o["noSame"], "answering No still wrote: %r" % o)
        self.assertFalse(o["held"]["ok"], "a held (quarantined) store was read as written: %r" % o)
        self.assertEqual(o["held"].get("stuck"), [], o)
        self.assertTrue(o["heldSame"], "a refused write mid-load left the other stores changed: %r" % o)
        self.assertFalse(o["removedAt"]["ok"], "a damaged removal journal was accepted: %r" % o)
        self.assertFalse(o["proto"]["ok"], "a prototype-named store slipped past the allowlist: %r" % o)
        self.assertTrue(o["bigOk"], "a real-sized removal journal is refused: %r" % o)
        self.assertTrue(o["allSame"], o)

    def test_profile_stores_follow_backups_rule(self):
        """Blueprint audit fix 2: Save profile is a subset of Backup's Export snapshot (same LSR rule) and holds every vault store."""
        keys_js = "var keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ keys = keys.concat(window._PROFILE_STORES[g]); });"
        o = board().run(keys_js +
            "keys.forEach(function(k){ window.LSR.setItem(k, JSON.stringify({probe: k})); });"
            "var snap = _collectProgress(); OUT.missing = keys.filter(function(k){ return !(k in snap); });"
            "OUT.vaultGap = window._VAULT_STORES.filter(function(k){ return window._PROFILE_STORES.vault.indexOf(k) < 0; });"
            "OUT.file = JSON.parse(window._vaultProfileBuild()).stores; OUT.fileMissing = keys.filter(function(k){ return snap[k] !== OUT.file[k]; });")
        self.assertEqual(o["missing"], [], "a profile store is not in Backup's Export snapshot: %r" % o["missing"])
        self.assertEqual(o["vaultGap"], [], "a VAULT_STORES key is missing from the profile: %r" % o["vaultGap"])
        self.assertEqual(o["fileMissing"], [], "the profile file disagrees with Backup's reading: %r" % o["fileMissing"])


if __name__ == "__main__":
    unittest.main()
