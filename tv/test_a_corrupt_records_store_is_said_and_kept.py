# -*- coding: utf-8 -*-
"""#152 item 3 (REG-2412) — A CORRUPT d2r_vaultRecords IS SAID ON THE BOARD AND KEPT, NEVER A SILENTLY EMPTY VAULT.

GrokBot's sweep (#230, 10-21, cov*.py), retested unchanged on v3784: corrupt d2r_vaultRecords "silently empties the
vault forever: no records/tasks, no warning; every hand-add says 'is yours' but writes nothing (store stays not-json)
and is lost on reload; never self-heals". REG-2272 had already made the records persist REFUSE to write over a store it
could not read - and that refusal was the only thing that knew: the move list read the unreadable store as no tasks,
the board said nothing, and nothing offered a way back.

THE FIX, driven here on the SHIPPED records block (_vrRecLoadRaw, _vrRecGuardedSet, _vaultRecordsMigrateUndo,
_vaultMoveHeldHtml, the records tab-sync spec) and the vault module head, cut from bible.html and run in node:
  · every unreadable shape (will not parse, [], {"v":1}, {"records":{}}) is NAMED and KEPT ASIDE at the one door,
    which then refuses every writer - even one that skips the module's own unread mark;
  · the move list says the saved tasks are UNKNOWN, not done, and where their bytes are kept;
  · + Add an item is held while the records store is (its move row could not be saved), but the mule map is not:
    the records are derived FROM it, not the other way round;
  · "Start it fresh" goes through the records' own undo: the door lets go only while the bytes are kept aside, the
    store and its stamp go, and a refused remove is reported partial, never "cleared";
  · another tab that started it fresh lifts the quarantine here. [[unknown-stays-unknown]] [[heart-first]]
RED_PROOF below; prove with `HEART2_PROVE_WORKERS=1 python3 tv/heart2.py --prove test_a_corrupt_records_store_is_said_and_kept`.
"""
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

KEY = "d2r_vaultRecords"
STAMP = "d2r_vaultRecordsMigrate"
BAD = {"{not json": "will not parse", "[]": "is not a records store (wrong shape)",
       '{"v":1}': "is not a records store (wrong shape)", '{"records":{}}': "is not a records store (wrong shape)"}


def _records(pre=""):
    """the door, then `pre` (a fixture switch), then the shipped records pieces and the tab sync."""
    s = D.src()
    spec = D.between(s, "  /* REG-2412 / REG-2413 — the records store is read from storage on every use",
                     "  } catch (eTsR) {}")
    return (D.stage(s) + pre
            + "function esc(t){ return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }\n"
            + "var _VR_STORE_KEY = 'd2r_vaultRecords', _VRM_KEY = 'd2r_vaultRecordsMigrate', _vrRecUnread = {};\n"
            + "\n".join(D.fn(s, n) for n in ("_vrRecQuarantine", "_vrRecLoadRaw", "_vrRecGuardedSet",
                                              "_vaultRecordsMigrateUndo", "_vaultMoveHeldHtml"))
            + "\n" + spec + "\n" + D.tab_sync(s) + "\n")


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED records block; UNMEASURED, not passing")
class ACorruptRecordsStoreIsSaidAndKept(unittest.TestCase):

    def test_each_unreadable_shape_is_named_and_kept_aside(self):
        for raw, why in BAD.items():
            o = D.page(_records(), "OUT.load = (_vrRecLoadRaw() === undefined);"
                       "var q = window.LSR.quarantined(_VR_STORE_KEY); OUT.why = q && q.reason; OUT.aside = q && q.asideOk;"
                       "OUT.set = _vrRecGuardedSet({ v: 1, records: [] }); OUT.raw = RAW[_VR_STORE_KEY]; OUT.kept = aside();",
                       seed={KEY: raw})
            self.assertTrue(o["load"], raw)
            self.assertEqual(o["why"], why, "%s must be NAMED at the door: %r" % (raw, o))
            self.assertTrue(o["aside"], raw)
            self.assertFalse(o["set"], raw)
            self.assertEqual(o["raw"], raw, "%s was written over" % raw)
            self.assertEqual(list(o["kept"].values()), [raw], "%s must be kept aside byte for byte" % raw)

    def test_the_door_refuses_even_a_writer_that_skips_the_module_mark(self):
        o = D.page(_records(), "_vrRecLoadRaw(); delete _vrRecUnread[_VR_STORE_KEY];"
                   "OUT.set = _vrRecGuardedSet({ v: 1, records: [] }); OUT.raw = RAW[_VR_STORE_KEY];"
                   "OUT.direct = window.LSR.setItem(_VR_STORE_KEY, '{}'); OUT.raw2 = RAW[_VR_STORE_KEY];",
                   seed={KEY: "{not json"})
        self.assertFalse(o["set"], "a refused write is not a write: _vrRecGuardedSet must say false")
        self.assertFalse(o["direct"])
        self.assertEqual((o["raw"], o["raw2"]), ("{not json", "{not json"))

    def test_the_move_list_says_unknown_not_done(self):
        o = D.page(_records(), "_vrRecLoadRaw(); OUT.h = _vaultMoveHeldHtml();", seed={KEY: "{not json"})
        self.assertIn("UNKNOWN, not done", o["h"])
        self.assertIn("will not parse", o["h"])
        self.assertIn("d2r_quarantine~d2r_vaultRecords~", o["h"], "the list says where the bytes are kept")
        o = D.page(_records(), "_vrRecLoadRaw(); OUT.h = _vaultMoveHeldHtml();",
                   seed={KEY: '{"v":1,"records":[]}'})
        self.assertEqual(o["h"], "", "a readable store adds nothing to the list")
        s = D.src()
        paint = D.fn(s, "_vaultMovePaint")
        self.assertIn("_vaultMoveHeldHtml() : '') + _vaultMoveHtml(built)", paint,
                      "the move list no longer puts the UNKNOWN line above what it draws")

    def test_start_it_fresh_goes_through_the_undo_and_keeps_the_bytes(self):
        o = D.page(_records(), "_vrRecLoadRaw(); OUT.u = _vaultRecordsMigrateUndo();"
                   "OUT.raw = RAW[_VR_STORE_KEY] || null; OUT.stamp = RAW[_VRM_KEY] || null; OUT.kept = aside();"
                   "OUT.held = !!window.LSR.quarantined(_VR_STORE_KEY); OUT.unread = _vrRecUnread[_VR_STORE_KEY] || null;",
                   seed={KEY: "{not json", STAMP: '{"ver":1}'})
        self.assertTrue(o["u"]["undone"], o)
        self.assertEqual((o["raw"], o["stamp"], o["held"], o["unread"]), (None, None, False, None), o)
        self.assertEqual(list(o["kept"].values()), ["{not json"], "the bytes stay kept aside after the fresh start")
        o = D.page(_records("THROW_ON = /d2r_quarantine~/;\n"),
                   "_vrRecLoadRaw(); OUT.u = _vaultRecordsMigrateUndo(); OUT.raw = RAW[_VR_STORE_KEY] || null;",
                   seed={KEY: "{not json", STAMP: '{"ver":1}'})
        self.assertFalse(o["u"]["undone"], "a store the door would not let go of must not be reported cleared: %r" % o)
        self.assertTrue(o["u"]["partial"])
        self.assertIn("could not be copied aside", o["u"]["why"])
        self.assertEqual(o["raw"], "{not json")

    def test_a_held_records_store_holds_the_hand_door_but_not_the_mule_map(self):
        s = D.src()
        pieces = (D.stage(s) + "var _vaultRecordsRefresh = function(){};\n(function(){\n" + D.vault_head(s) + "\n"
                  + D.fn(s, "saveA") + "\nwindow.__saveA = saveA;\n})();\n")
        o = D.page(pieces, "window.LSR.quarantine('d2r_vaultRecords', 'will not parse');"
                   "OUT.held = window._vaultHeld(); OUT.basis = window._vaultBasisHeld(); OUT.save = window.__saveA();",
                   seed={KEY: "{not json"})
        self.assertEqual(o["held"]["keys"], ["d2r_vaultRecords"], "+ Add an item must be held: its move row has no store")
        self.assertIsNone(o["basis"], "the records are derived from the mule map, so they never hold it")
        self.assertTrue(o["save"], "the mule map still saves while only the records are held")

    def test_another_tab_starting_it_fresh_lifts_the_quarantine_here(self):
        o = D.page(_records(), "_vrRecLoadRaw();"
                   "OUT.r = window._tabSyncMerge(_VR_STORE_KEY, '{not json', '{\"v\":1,\"records\":[]}');"
                   "OUT.held = !!window.LSR.quarantined(_VR_STORE_KEY); OUT.unread = _vrRecUnread[_VR_STORE_KEY] || null;",
                   seed={KEY: "{not json"})
        self.assertTrue(o["r"].get("released"), o)
        self.assertEqual((o["held"], o["unread"]), (False, None), "the lift must clear the module's mark too")
        o = D.page(_records(), "_vrRecLoadRaw();"
                   "OUT.r = window._tabSyncMerge(_VR_STORE_KEY, '{not json', '{\"v\":1}');"
                   "OUT.held = !!window.LSR.quarantined(_VR_STORE_KEY);", seed={KEY: "{not json"})
        self.assertTrue(o["held"], "another tab's write that still does not read lifts nothing")


RED_PROOF = [
    {"why": "REG-2412 - a records store that will not parse is refused but no longer named or kept aside",
     "file": "bible.html", "matches": 1,
     "find": "catch (e) { _vrRecUnread[_VR_STORE_KEY] = 'will not parse'; if (typeof _vrRecQuarantine === 'function') _vrRecQuarantine('will not parse'); return undefined; }",
     "replace": "catch (e) { _vrRecUnread[_VR_STORE_KEY] = 'will not parse'; return undefined; }"},
    {"why": "REG-2412 - a records store of the wrong shape is no longer named or kept aside",
     "file": "bible.html", "matches": 1,
     "find": "        if (typeof _vrRecQuarantine === 'function') _vrRecQuarantine('is not a records store (wrong shape)');\n",
     "replace": ""},
    {"why": "REG-2412 - _vrRecGuardedSet calls a write the door refused a write",
     "file": "bible.html", "matches": 1,
     "find": "    try { return window.LSR.setItem(_VR_STORE_KEY, JSON.stringify(obj)) !== false; } catch (e) { return false; }",
     "replace": "    try { window.LSR.setItem(_VR_STORE_KEY, JSON.stringify(obj)); return true; } catch (e) { return false; }"},
    {"why": "REG-2412 - the move list reads unreadable saved tasks as nothing to move again",
     "file": "bible.html", "matches": 1,
     "find": "    if (!q) return '';\n    return '<p class=\"vault-propose\" data-state=\"unknown\" data-held=\"d2r_vaultRecords\">",
     "replace": "    return '';\n    return '<p class=\"vault-propose\" data-state=\"unknown\" data-held=\"d2r_vaultRecords\">"},
    {"why": "REG-2412 - the undo (Start it fresh) no longer lets go of the quarantine, so the store can never be rebuilt",
     "file": "bible.html", "matches": 1,
     "find": "        var _rl = window.LSR.release(_VR_STORE_KEY);\n",
     "replace": "        var _rl = null;\n"},
    {"why": "REG-2412 - the undo reports a remove the door refused as a cleared store",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR.removeItem(_VR_STORE_KEY) === false) { storeErr = true;",
     "replace": "    try { if (false) { storeErr = true;"},
    {"why": "REG-2412 - + Add an item is not held while the records store is (its move row goes nowhere)",
     "file": "bible.html", "matches": 1,
     "find": "  var VAULT_STORES = VAULT_BASIS.concat(Object.keys({ d2r_vaultRecords: 1 }));\n",
     "replace": "  var VAULT_STORES = VAULT_BASIS.concat([]);\n"},
    {"why": "REG-2412 - another tab's fresh records store never lifts the quarantine here",
     "file": "bible.html", "matches": 1,
     "find": "    if (held && held.kind === 'quarantine'\n        && (theirs.v == null || (typeof spec.readable === 'function' && spec.readable(theirs.v)))){\n",
     "replace": "    if (false){\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
