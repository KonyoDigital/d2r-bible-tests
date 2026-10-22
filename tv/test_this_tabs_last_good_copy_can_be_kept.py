# -*- coding: utf-8 -*-
"""REG-2523 (V1 round 3; the review of REG-2413, r4 - reproduced twice) - WHEN ANOTHER TAB WRITES BAD BYTES, THIS TAB'S
LAST GOOD COPY HAS A WAY OUT.

This tab holds his store in memory - read fine, merged, nothing held it. Another tab writes bytes that will not parse.
_tabSyncMerge quarantined the key, but the copy kept aside is the OTHER tab's bad bytes, and both exits on the notice
dropped this tab's good copy: Start it fresh empties the store, a backup restore loses everything since the backup. The
notice said "Until it is fixed the page runs on a default in its place" - false, this tab runs on his copy. A storage
another tab CLEARED had the same shape: "Reload this tab" was the only exit, and it drops the only copy of everything.
Reviewer (rv4, shipped boot / tab sync / notice): owned [Grief, Enigma, Shako], another tab writes '["Grief","Eni' -> in
memory all three, kept aside only the 13 bad bytes, "runs on a default", persist() refused, Start it fresh removes the
key, and afterwards NO key in storage holds the good list.

NOW the hold carries lastGood (another tab's bad write over a store this tab held fine) or cleared (another tab cleared
the storage), the notice says "This tab still holds your last good copy" and offers KEEP THIS TAB'S COPY
(window._storeKeepThisTab): he is asked; whatever the key holds that is not kept aside yet goes aside first (the bad
bytes are in their quarantine slot; a second bad write, or bytes written after a clear, are copied aside the same way);
only then is this tab's copy written, read back, and the hold lifted. A copy that cannot be kept aside writes nothing.
Start it fresh's question now says the good copy is lost that way, and names the other exit.

WHAT IS DRIVEN: the store door, the boot loaders and persist(), the notice and the tab sync, cut from bible.html
(store_door_harness), in node, firing the storage events another document would. RED_PROOF below. A missing node is the
only skip.
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

GOOD = json.dumps(["Grief", "Enigma", "Harlequin Crest (Shako)"])
BAD = '["Grief","Eni'
BAD2 = '["Grief","Enigma","Harl'


def _pieces(s):
    return (D.stage(s) + D.boot(s) + D.tab_sync(s)
            + "\nvar ASKED = [], SAY_YES = true;\nwindow.uiConfirm = function(q, o){ ASKED.push(String(q)); return Promise.resolve(SAY_YES); };\n"
            + "var location = { reload: function(){ OUT.reloaded = true; } };\n")


def _run(body, seed=None):
    s = D.src()
    prog = ("window.__ASYNC = true;\n"
            "function notice(){ return (document.getElementById('store-quarantine') || {}).innerHTML || ''; }\n"
            "function hasRaw(v){ return Object.keys(RAW).filter(function(k){ return RAW[k] === v; }); }\n"
            "(async function(){\n" + body + "\n})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page(_pieces(s), prog, seed=seed if seed is not None else {"d2r_owned": GOOD})


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED tab sync and notice; UNMEASURED, not passing")
class ThisTabsLastGoodCopyCanBeKept(unittest.TestCase):

    def test_another_tabs_bad_write_offers_this_tabs_copy_and_keeping_it_writes_it_back(self):
        o = _run(r"""
var good = RAW['d2r_owned'];
RAW['d2r_owned'] = %(bad)s; fire('d2r_owned', good, %(bad)s);         /* another tab writes bytes cut short */
var q = window.LSR.quarantined('d2r_owned');
OUT.q = q && { kind: q.kind, lastGood: !!q.lastGood, aside: q.aside ? RAW[q.aside] : null };
OUT.memory = Array.from(owned);
OUT.notice = notice();
persist(); OUT.rawAfterPersist = RAW['d2r_owned'];
var r = await window._storeKeepThisTab('d2r_owned');                  /* his click: Keep this tab's copy */
OUT.r = r; OUT.asked = ASKED.slice();
OUT.raw = RAW['d2r_owned']; OUT.heldAfter = window.LSR.quarantined('d2r_owned');
OUT.badStillAside = hasRaw(%(bad)s).filter(function(k){ return k !== 'd2r_owned'; }).length;
OUT.noticeAfter = notice();
""" % {"bad": json.dumps(BAD)})
        self.assertEqual(o["q"], {"kind": "quarantine", "lastGood": True, "aside": BAD},
                         "another tab's bad write was not held as 'this tab still holds the last good copy': %r" % o["q"])
        self.assertEqual(sorted(o["memory"]), sorted(json.loads(GOOD)), "PREMISE: this tab lost its copy in memory")
        self.assertIn("This tab still holds your last good copy", o["notice"])
        self.assertIn("_storeKeepThisTab", o["notice"], "the notice does not offer Keep this tab's copy")
        self.assertNotIn("runs on a default", o["notice"], "the notice still says the page runs on a default")
        self.assertEqual(o["rawAfterPersist"], BAD, "PREMISE: persist() wrote over a quarantined key")
        self.assertTrue(o["r"]["ok"], "Keep this tab's copy failed: %r" % o["r"])
        self.assertEqual(len(o["asked"]), 1, "he was not asked before his store was written")
        self.assertEqual(sorted(json.loads(o["raw"])), sorted(json.loads(GOOD)), "this tab's copy was not written back")
        self.assertIsNone(o["heldAfter"], "the hold was not lifted after his copy was written")
        self.assertGreaterEqual(o["badStillAside"], 1, "the other tab's bad bytes were not kept aside")
        self.assertEqual(o["noticeAfter"], "", "the notice still shows a store that reads again")

    def test_he_can_leave_it_held_and_nothing_is_written(self):
        o = _run(r"""
var good = RAW['d2r_owned'];
RAW['d2r_owned'] = %(bad)s; fire('d2r_owned', good, %(bad)s);
SAY_YES = false;
OUT.r = await window._storeKeepThisTab('d2r_owned');
OUT.raw = RAW['d2r_owned']; OUT.held = !!window.LSR.quarantined('d2r_owned');
""" % {"bad": json.dumps(BAD)})
        self.assertFalse(o["r"]["ok"])
        self.assertEqual(o["raw"], BAD, "his 'Leave it held' still wrote")
        self.assertTrue(o["held"])

    def test_a_second_bad_write_that_landed_since_is_kept_aside_before_anything_is_written(self):
        o = _run(r"""
var good = RAW['d2r_owned'];
RAW['d2r_owned'] = %(bad)s; fire('d2r_owned', good, %(bad)s);
RAW['d2r_owned'] = %(bad2)s; fire('d2r_owned', %(bad)s, %(bad2)s);   /* the other tab writes again, still cut short */
OUT.r = await window._storeKeepThisTab('d2r_owned', true);
OUT.raw = RAW['d2r_owned'];
OUT.aside1 = hasRaw(%(bad)s).filter(function(k){ return k !== 'd2r_owned'; }).length;
OUT.aside2 = hasRaw(%(bad2)s).filter(function(k){ return k !== 'd2r_owned'; }).length;
""" % {"bad": json.dumps(BAD), "bad2": json.dumps(BAD2)})
        self.assertTrue(o["r"]["ok"], o["r"])
        self.assertEqual(sorted(json.loads(o["raw"])), sorted(json.loads(GOOD)))
        self.assertGreaterEqual(o["aside1"], 1, "the first bad bytes were lost")
        self.assertGreaterEqual(o["aside2"], 1, "the second bad write was written over without being kept aside")

    def test_a_storage_another_tab_cleared_offers_this_tabs_copy_and_keeps_aside_what_was_written_since(self):
        o = _run(r"""
Object.keys(RAW).forEach(function(k){ delete RAW[k]; });              /* another tab clears this browser's storage */
fire(null, null, null);
var q = window.LSR.quarantined('d2r_owned');
OUT.q = q && { kind: q.kind, cleared: !!q.cleared };
OUT.notice = notice();
RAW['d2r_owned'] = '["Shako"]';                                       /* and writes something after the clear */
OUT.r = await window._storeKeepThisTab('d2r_owned', true);
OUT.raw = RAW['d2r_owned'];
OUT.since = hasRaw('["Shako"]').filter(function(k){ return k !== 'd2r_owned'; }).length;
""")
        self.assertEqual(o["q"], {"kind": "stale", "cleared": True}, "a cleared storage is not held as 'this tab still holds the copy'")
        self.assertIn("This tab still holds your last good copy", o["notice"])
        self.assertIn("_storeKeepThisTab", o["notice"])
        self.assertTrue(o["r"]["ok"], o["r"])
        self.assertEqual(sorted(json.loads(o["raw"])), sorted(json.loads(GOOD)), "this tab's copy was not written back")
        self.assertGreaterEqual(o["since"], 1, "what another tab wrote after the clear was written over, not kept aside")

    def test_a_store_this_tab_never_read_well_offers_no_copy(self):
        """the premise: lastGood is a fact about THIS tab - a store quarantined at its own boot has no copy to offer"""
        o = _run(r"""
OUT.q = (function(){ var q = window.LSR.quarantined('d2r_owned'); return q && { lastGood: !!q.lastGood }; })();
OUT.notice = notice();
OUT.r = await window._storeKeepThisTab('d2r_owned', true);
""", seed={"d2r_owned": BAD})
        self.assertEqual(o["q"], {"lastGood": False})
        self.assertNotIn("_storeKeepThisTab", o["notice"], "a copy this tab never had was offered")
        self.assertIn("runs on a default", o["notice"])
        self.assertFalse(o["r"]["ok"])


RED_PROOF = [
    {"why": "REG-2523 - another tab's bad write no longer marks this tab's good copy (the notice says 'runs on a "
            "default' and offers only exits that drop it)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_good){ _qe.lastGood = true;",
     "replace": "    if (false){ _qe.lastGood = true;"},
    {"why": "REG-2523 - the notice never offers Keep this tab's copy",
     "file": "bible.html", "matches": 1,
     "find": "    var tail = q.lastGood\n",
     "replace": "    var tail = false\n"},
    {"why": "REG-2523 - Keep this tab's copy writes over bytes that are not kept aside yet",
     "file": "bible.html", "matches": 1,
     "find": "    if (now != null && now !== '' && now !== bytes && !keptAlready){\n",
     "replace": "    if (false){\n"},
    {"why": "REG-2523 - a storage another tab cleared is not marked as 'this tab holds the copy'",
     "file": "bible.html", "matches": 1,
     "find": "if (!_was && _h && _h.kind === 'stale' && REG[x] && REG[x].kind !== 'store' && typeof REG[x].get === 'function') _h.cleared = true;",
     "replace": ""},
    {"why": "REG-2523 - Keep this tab's copy writes without asking him",
     "file": "bible.html", "matches": 1,
     "find": "  var ask = skipAsk ? Promise.resolve(true)\n    : (typeof window.uiConfirm === 'function'\n        ? window.uiConfirm('Keep this tab",
     "replace": "  var ask = Promise.resolve(true) || (typeof window.uiConfirm === 'function'\n        ? window.uiConfirm('Keep this tab"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
