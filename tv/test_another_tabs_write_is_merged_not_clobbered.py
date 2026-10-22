# -*- coding: utf-8 -*-
"""#153 item 11 (REG-2413) — ANOTHER TAB'S WRITE IS MERGED INTO THIS ONE, NEVER WRITTEN OVER BY IT.

GrokBot's sweep (#230, 10-21): "two browser tabs overwrite each other — no storage listener for vault keys (only
:11181, :67812 for other features); another tab's owned write is lost on the next hand-add." Every store the page holds
in memory (owned, the mule map, the roster, copies, Magic & Rare, the stashes...) is read ONCE at boot and written back
WHOLE (persist(), persistOwned(), saveA()), so a second tab's next write carried its boot-time copy over the first tab's
item. His console can hold two boards of one origin (the board and its engine frame), so this is not only two tabs.

THE FIX, driven here on the SHIPPED ⟦TAB SYNC⟧ block, the boot loaders and persist(), and the vault module head (which
registers the mule map and the roster), in node, with the page's own storage listener fired as the browser would:
  · a storage event applies THAT write's change - what it added, removed or changed against the value it replaced
    (ev.oldValue) - to this tab's copy in place: what this tab holds that the write did not touch stays, and what the
    write removed does not come back;
  · when both wrote at once, the tab that holds more writes the merged copy back once, and the other side adopts it;
  · nothing is guessed: bytes that will not parse are quarantined here too, a roster both tabs changed and a cleared
    storage HOLD the key (this tab's writes to it are refused and the notice asks for a reload), and a store this tab
    had quarantined lifts when the other tab writes one that reads;
  · only this world's key is merged - another profile's write is not this tab's store.
The real cross-tab delivery is the browser's: tests/v1b_stores_never_bricked.spec.ts drives two pages on CI.
RED_PROOF below; prove with `HEART2_PROVE_WORKERS=1 python3 tv/heart2.py --prove test_another_tabs_write_is_merged_not_clobbered`.
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

import store_door_harness as D  # noqa: E402


def _tab(vault=False):
    s = D.src()
    pieces = D.stage(s) + D.boot(s) + D.tab_sync(s) + "\n"
    if vault:
        pieces += ("var renderVault = function(){};\n(function(){\n" + D.vault_head(s) + "\n" + D.fn(s, "saveA") + "\n"
                   + "window.__V = { saveA: saveA, roster: function(){ return roster; }, assign: function(){ return assign; } };"
                   + "\n})();\n")
    return pieces


#: the other tab writes `new` over `old` (the store moves, then this tab hears of it, as the browser does it)
OTHER = "function other(k, nv){ var ov = RAW[k] == null ? null : RAW[k]; if (nv == null) delete RAW[k]; else RAW[k] = nv; fire(k, ov, nv); }\n"
WRITES = ("var WROTE = []; var _set = window.LSR.setItem; window.LSR.setItem = function(k, v){ WROTE.push(k);"
          " return _set.call(window.LSR, k, v); };\n")


def _run(body, seed, vault=False, **kw):
    return D.page(_tab(vault), OTHER + WRITES + body, seed=seed, **kw)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED tab sync; UNMEASURED, not passing")
class AnotherTabsWriteIsMergedNotClobbered(unittest.TestCase):

    def test_the_other_tabs_add_survives_this_tabs_next_write(self):
        """GrokBot's repro: tab B adds, tab A adds next - and B's item must still be there."""
        o = _run("other('d2r_owned', '[\"A\",\"B\"]'); OUT.mem = Array.from(owned).sort(); OUT.wroteBack = WROTE.slice();"
                 "owned.add('C'); persist(); OUT.raw = JSON.parse(RAW['d2r_owned']).sort();",
                 seed={"d2r_owned": '["A"]'})
        self.assertEqual(o["mem"], ["A", "B"], "this tab never heard of the other tab's add")
        self.assertEqual(o["wroteBack"], [], "a merge that equals the other tab's write writes nothing back")
        self.assertEqual(o["raw"], ["A", "B", "C"], "this tab's next write carried its stale copy over B")

    def test_a_removal_in_the_other_tab_does_not_come_back(self):
        o = _run("other('d2r_owned', '[\"A\"]'); persist(); OUT.raw = JSON.parse(RAW['d2r_owned']).sort();",
                 seed={"d2r_owned": '["A","B"]'})
        self.assertEqual(o["raw"], ["A"], "the other tab removed B and this tab's write brought it back")

    def test_both_wrote_at_once_the_tab_that_holds_more_writes_the_merge_back_once(self):
        # this tab's write landed after the other tab's, which it never saw: the other tab's X is in the event only
        o = _run("owned.add('B'); persist(); WROTE.length = 0;"
                 "fire('d2r_owned', '[\"A\"]', '[\"A\",\"X\"]');"
                 "OUT.mem = Array.from(owned).sort(); OUT.wrote = WROTE.slice();"
                 "OUT.raw = JSON.parse(RAW['d2r_owned']).sort();"
                 "WROTE.length = 0; other('d2r_owned', '[\"A\",\"B\",\"X\",\"Y\"]'); OUT.again = WROTE.slice();",
                 seed={"d2r_owned": '["A"]'})
        self.assertEqual(o["mem"], ["A", "B", "X"])
        self.assertEqual(o["wrote"], ["d2r_owned"], "the tab holding both halves must write the merge back - once")
        self.assertEqual(o["raw"], ["A", "B", "X"], "the merge back healed the store")
        self.assertEqual(o["again"], [], "a write this tab already agrees with is not written back (no ping-pong)")

    def test_a_map_merges_key_by_key(self):
        o = _run("copies.Enigma = 2;"                                           # this tab's own, not yet written
                 "other('d2r_copies', '{\"Grief\":2,\"Shako\":3}'); OUT.a = JSON.parse(JSON.stringify(copies));"
                 "other('d2r_copies', '{\"Grief\":4,\"Shako\":3,\"Enigma\":2}'); OUT.b = JSON.parse(JSON.stringify(copies));"
                 "other('d2r_copies', '{\"Grief\":4,\"Enigma\":2}'); OUT.c = JSON.parse(JSON.stringify(copies));"
                 "OUT.raw = JSON.parse(RAW['d2r_copies']);",
                 seed={"d2r_copies": '{"Grief":2}'})
        self.assertEqual(o["a"], {"Grief": 2, "Shako": 3, "Enigma": 2}, "a key the other tab added must arrive")
        self.assertEqual(o["b"]["Grief"], 4, "a key the other tab changed must change")
        self.assertNotIn("Shako", o["c"], "a key the other tab removed must go")
        self.assertEqual(o["raw"]["Enigma"], 2, "this tab's own key must survive and be written back")

    def test_the_mule_map_and_the_roster_join_the_sync(self):
        o = _run("other('d2r_muleAssign', '{\"Grief\":\"uni-weap\",\"Shako\":\"uni-armor\"}');"
                 "OUT.assign = JSON.parse(JSON.stringify(window.__V.assign()));"
                 "var r = window.__V.roster().map(function(m){ return Object.assign({}, m); });"
                 "RAW['d2r_muleRoster'] = JSON.stringify(r);"
                 "var more = r.concat([{ id: 'war1', name: 'WAR1', icon: 'x', note: '' }]);"
                 "other('d2r_muleRoster', JSON.stringify(more));"
                 "OUT.ids = window.__V.roster().map(function(m){ return m.id; });"
                 "window.__V.roster().push({ id: 'mine', name: 'MINE', icon: 'x', note: '' });"
                 "other('d2r_muleRoster', JSON.stringify(more.concat([{ id: 'theirs', name: 'THEIRS', icon: 'x', note: '' }])));"
                 "OUT.held = window.LSR.quarantined('d2r_muleRoster');"
                 "OUT.save = window.LSR.setItem('d2r_muleRoster', '[]');"
                 "OUT.notice = (document.getElementById('store-quarantine') || {}).innerHTML || '';",
                 seed={"d2r_muleAssign": '{"Grief":"uni-weap"}'}, vault=True)
        self.assertEqual(o["assign"], {"Grief": "uni-weap", "Shako": "uni-armor"}, "the mule map is not in the sync")
        self.assertIn("war1", o["ids"], "a roster this tab had not changed must take the other tab's mule")
        self.assertEqual(o["held"]["kind"], "stale", "a roster both tabs changed must be held, never guessed")
        self.assertFalse(o["save"], "a held roster must refuse this tab's write")
        self.assertIn("Reload this tab", o["notice"])

    def test_a_roster_first_saved_in_the_other_tab_is_taken_not_held(self):
        """Nothing saved yet: this tab runs on the default lockers, so the other tab's first save is a change to that."""
        o = _run("var r = window.__V.roster().map(function(m){ return Object.assign({}, m); });"
                 "other('d2r_muleRoster', JSON.stringify(r.concat([{ id: 'war1', name: 'WAR1', icon: 'x', note: '' }])));"
                 "OUT.ids = window.__V.roster().map(function(m){ return m.id; });"
                 "OUT.held = window.LSR.quarantined('d2r_muleRoster');", seed={}, vault=True)
        self.assertIsNone(o["held"], "a roster nobody had saved here must be taken, not held: %r" % o["held"])
        self.assertIn("war1", o["ids"])

    def test_bytes_that_will_not_parse_are_quarantined_here_too(self):
        o = _run("other('d2r_owned', 'GARB{'); OUT.mem = Array.from(owned);"
                 "OUT.q = window.LSR.quarantined('d2r_owned').reason; persist(); OUT.raw = RAW['d2r_owned'];",
                 seed={"d2r_owned": '["A"]'})
        self.assertEqual(o["mem"], ["A"], "bytes that will not parse must never be read as an empty owned list")
        self.assertIn("will not parse", o["q"])
        self.assertEqual(o["raw"], "GARB{", "this tab must not write over what it could not read")

    def test_a_quarantined_store_here_lifts_when_the_other_tab_writes_one_that_reads(self):
        o = _run("OUT.before = !!window.LSR.quarantined('d2r_owned');"
                 "other('d2r_owned', '[\"S\"]'); OUT.mem = Array.from(owned); OUT.after = !!window.LSR.quarantined('d2r_owned');"
                 "other('d2r_muleAssign', '{\"Grief\":\"uni-weap\"}'); OUT.unread = window._muleStoreUnread('d2r_muleAssign');"
                 "OUT.assign = JSON.parse(JSON.stringify(window.__V.assign())); window.__V.assign().Shako = 'uni-armor';"
                 "OUT.save = window.__V.saveA();"
                 "OUT.notice = !!document.getElementById('store-quarantine') && !document.getElementById('store-quarantine').hidden;",
                 seed={"d2r_owned": '{"a":1}', "d2r_muleAssign": '"text"'}, vault=True)
        self.assertTrue(o["before"])
        self.assertEqual((o["mem"], o["after"]), (["S"], False), o)
        self.assertIsNone(o["unread"], "the mule module's own unread mark must lift with the door's")
        self.assertEqual(o["assign"], {"Grief": "uni-weap"})
        self.assertTrue(o["save"], "once both stores read, the mule map saves again")
        self.assertFalse(o["notice"], "nothing is held any more, so the notice is gone")

    def test_a_cleared_storage_holds_every_store_until_reload(self):
        o = _run("fire(null, null, null); OUT.held = window.LSR.quarantined().map(function(e){ return e.kind; });"
                 "WROTE.length = 0; var before = JSON.stringify(RAW); owned.add('Z'); persist();"
                 "OUT.same = (RAW['d2r_owned'] === '[\"A\"]');"
                 "OUT.notice = (document.getElementById('store-quarantine') || {}).innerHTML || '';",
                 seed={"d2r_owned": '["A"]'})
        self.assertGreaterEqual(len(o["held"]), 15, "every store this tab holds must be held after a clear")
        self.assertEqual(set(o["held"]), {"stale"})
        self.assertTrue(o["same"], "a tab whose storage was cleared elsewhere must not write its old copy back")
        self.assertIn("Reload this tab", o["notice"])

    def test_only_this_worlds_key_is_merged(self):
        o = _run("fire('d2r_owned', '[\"A\"]', '[\"A\",\"MAIN-ONLY\"]'); OUT.a = Array.from(owned).sort();"
                 "fire('L·d2r_owned', '[\"L\"]', '[\"L\",\"LADDER\"]'); OUT.b = Array.from(owned).sort();",
                 seed={"d2r_owned": '["A"]', "L·d2r_owned": '["L"]'}, profile="ladder")
        self.assertEqual(o["a"], ["L"], "another world's write was merged into this one")
        self.assertEqual(o["b"], ["L", "LADDER"])

    def test_the_page_listens_for_storage(self):
        o = _run("OUT.kinds = LISTEN.map(function(l){ return l[0]; });"
                 "OUT.keys = Object.keys(window._TAB_SYNC).sort();", seed={}, vault=True)
        self.assertIn("storage", o["kinds"])
        for k in ("d2r_owned", "d2r_muleAssign", "d2r_muleRoster", "d2r_copies", "d2r_magicFinds", "d2r_multiKeep",
                  "d2r_runeStash", "d2r_setPieces"):
            self.assertIn(k, o["keys"], "%s is held in memory and written back whole, so it must be in the sync" % k)


RED_PROOF = [
    {"why": "REG-2413 - the storage listener hears another tab's write and merges nothing (his item lost on the next add)",
     "file": "bible.html", "matches": 1,
     "find": "        window._tabSyncMerge(k, ev.oldValue, ev.newValue);\n",
     "replace": ""},
    {"why": "REG-2413 - a removal in the other tab comes back with this tab's next write",
     "file": "bible.html", "matches": 1,
     "find": "    bs.forEach(function(x){ if (!ts.has(x) && live.has(x)){ live.delete(x); n++; } });\n",
     "replace": ""},
    {"why": "REG-2413 - both tabs wrote at once and nobody writes the merge back (the race keeps one half)",
     "file": "bible.html", "matches": 1,
     "find": "  if (!same(live, tv))\n",
     "replace": "  if (false)\n"},
    {"why": "REG-2413 - a key the other tab removed from a map stays here",
     "file": "bible.html", "matches": 1,
     "find": "      if (Object.prototype.hasOwnProperty.call(t, x)) live[x] = JSON.parse(tj); else delete live[x];\n",
     "replace": "      if (Object.prototype.hasOwnProperty.call(t, x)) live[x] = JSON.parse(tj);\n"},
    {"why": "REG-2413 - bytes another tab wrote that will not parse are merged as an empty store",
     "file": "bible.html", "matches": 1,
     "find": "  if (!theirs.ok || !shapeOk(theirs.v)){\n",
     "replace": "  if (false){\n"},
    {"why": "REG-2413 - the mule map is left out of the sync",
     "file": "bible.html", "matches": 1,
     "find": "    window._TAB_SYNC[AK] = { kind: 'map', get: function(){ return assign; }, after: _vaultTabAfter,\n",
     "replace": "    window._TAB_SYNC['__off'] = { kind: 'map', get: function(){ return assign; }, after: _vaultTabAfter,\n"},
    {"why": "REG-2413 - a roster both tabs changed is overwritten instead of held",
     "file": "bible.html", "matches": 1,
     "find": "    if (LSR && typeof LSR.hold === 'function') LSR.hold(k, 'it changed here and in another tab at once');\n",
     "replace": ""},
    {"why": "REG-2413 - a roster first saved in another tab is held as a conflict (this tab ran on the default)",
     "file": "bible.html", "matches": 1,
     "find": "    var tl = tv, bl = base.ok ? valOf(base.v) : [];\n",
     "replace": "    var tl = tv, bl = (base.ok && base.v) || [];\n"},
    {"why": "REG-2413 - a storage another tab cleared is ignored and this tab writes its old copy back",
     "file": "bible.html", "matches": 1,
     "find": "              var _h = window.LSR.hold(x, 'another tab cleared this browser\u2019s saved data');\n",
     "replace": "              var _h = null;\n"},
    {"why": "REG-2413 - another world's write is merged into this world's store",
     "file": "bible.html", "matches": 1,
     "find": "        for (var i = 0; i < ks.length; i++){ if (window.LSR.key(ks[i]) === ev.key){ k = ks[i]; break; } }\n",
     "replace": "        for (var i = 0; i < ks.length; i++){ if (String(ev.key).indexOf(ks[i]) >= 0){ k = ks[i]; break; } }\n"},
    {"why": "REG-2413 - a quarantine here never lifts when the other tab writes a store that reads",
     "file": "bible.html", "matches": 1,
     "find": "    replace(live, tv);\n    var rl = LSR.release(k);\n",
     "replace": "    return { ok: false };\n    var rl = LSR.release(k);\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
