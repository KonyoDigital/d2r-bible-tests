# -*- coding: utf-8 -*-
"""REG-2523 FIX ROUND (V1 round 3; the review of REG-2523, minor) - WHEN ANOTHER TAB CLEARS THE STORAGE, THE NOTICE SAYS
THIS TAB HOLDS THE ONLY COPY, OFFERS NO UNASKED RELOAD, AND KEEPS EVERY COPY ON ONE ANSWER.

After another tab cleared this browser's storage every row said "This tab still holds your last good copy" and offered
Keep this tab's copy - but the HEADLINE still said "Another tab changed what this tab holds — reload before you change
anything here", and every row also said "This tab writes nothing to it until it reloads" beside an unasked "Reload this
tab" (location.reload()): the one click that drops the only remaining copy of every store, recommended by the headline.
Keep worked one store at a time - about 20 rows, each with its own question. Reviewer (p6, the REG-2523 law's harness,
fire(null) after clearing RAW): '⚠ Another tab changed what this tab holds — reload before you change anything here |
d2r_owned ... This tab still holds your last good copy. | Keep this tab’s copy | Reload this tab | d2r_copies ...'.

NOW the headline says this tab holds the only copy of N stores and to keep them before reloading; a cleared row offers
Keep this tab's copy and no reload; and "Keep all of this tab's copies (N)" asks ONCE, then keeps each store the one
store's way (window._storeKeepThisTab). A store another tab only CHANGED still offers Reload this tab (its bytes are
there to read).

WHAT IS DRIVEN: the store door, the boot loaders and persist(), the notice and the tab sync, cut from bible.html
(store_door_harness), in node, firing the storage events another document would. RED_PROOF below. A missing node is the
only skip.
"""
import json
import os
import re
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
COPIES = json.dumps({"Grief": 2})


def _pieces(s):
    return (D.stage(s) + D.boot(s) + D.tab_sync(s)
            + "\nvar ASKED = [], SAY_YES = true;\nwindow.uiConfirm = function(q, o){ ASKED.push(String(q)); return Promise.resolve(SAY_YES); };\n"
            + "var location = { reload: function(){ OUT.reloaded = true; } };\n")


def _run(body):
    s = D.src()
    prog = ("window.__ASYNC = true;\n"
            "function notice(){ return (document.getElementById('store-quarantine') || {}).innerHTML || ''; }\n"
            "function rows(){ return notice().split('<li ').slice(1); }\n"
            "function head(){ var m = /<div class=\"sq-head\">([\\s\\S]*?)<\\/div>/.exec(notice()); return m ? m[1] : ''; }\n"
            "(async function(){\n" + body + "\n})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page(_pieces(s), prog, seed={"d2r_owned": GOOD, "d2r_copies": COPIES})


CLEAR = "Object.keys(RAW).forEach(function(k){ delete RAW[k]; });\nfire(null, null, null);\n"


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED tab sync and notice; UNMEASURED, not passing")
class AClearedStorageKeepsThisTabsOnlyCopy(unittest.TestCase):

    def test_the_notice_says_this_tab_holds_the_only_copy_and_offers_no_unasked_reload(self):
        o = _run(CLEAR + "OUT.head = head(); OUT.rows = rows(); OUT.n = window.LSR.quarantined().filter(function(q){ return q.cleared; }).length;")
        n = o["n"]
        self.assertGreater(n, 1, "PREMISE: a clear held fewer than two stores this tab holds")
        self.assertIn("this tab now holds the only copy of %d stores" % n, o["head"], "the headline: %r" % o["head"])
        self.assertIn("before you reload", o["head"])
        self.assertNotIn("reload before you change anything here", o["head"], "the headline still recommends the reload")
        self.assertIn("Keep all of this tab’s copies (%d)" % n, o["head"], "no one action keeps them all: %r" % o["head"])
        kept_rows = [r for r in o["rows"] if 'data-last-good="1"' in r]
        self.assertEqual(len(kept_rows), n, "a store this tab holds is not offered back")
        for r in kept_rows:
            self.assertIn("This tab still holds your last good copy", r)
            self.assertIn("_storeKeepThisTab", r)
        for r in o["rows"]:
            # a reload is the whole page: while any row holds the only copy, no row may offer one
            self.assertNotIn("location.reload()", r, "a row offers an unasked reload over the only copy: %r" % r[:200])

    def test_keep_all_asks_once_and_writes_every_copy_back(self):
        o = _run(CLEAR + r"""
RAW['d2r_owned'] = '["Shako"]';                                       /* another tab wrote after the clear */
var held = window.LSR.quarantined().filter(function(q){ return q.cleared; }).map(function(q){ return q.key; });
var r = await window._storeKeepAllThisTab();
OUT.held = held; OUT.r = r; OUT.asked = ASKED.slice();
OUT.owned = RAW['d2r_owned']; OUT.copies = RAW['d2r_copies'];
OUT.still = window.LSR.quarantined().filter(function(q){ return q.cleared; }).length;
OUT.lastGoodRows = (notice().match(/data-last-good="1"/g) || []).length;
OUT.since = Object.keys(RAW).filter(function(k){ return k !== 'd2r_owned' && RAW[k] === '["Shako"]'; }).length;
""")
        self.assertEqual(len(o["asked"]), 1, "Keep all asked %d times, not once: %r" % (len(o["asked"]), o["asked"]))
        self.assertTrue(o["r"]["ok"], o["r"])
        self.assertEqual(sorted(o["r"]["kept"]), sorted(o["held"]), "a held store was not kept")
        self.assertEqual(sorted(json.loads(o["owned"])), sorted(json.loads(GOOD)), "this tab's owned copy was not written back")
        self.assertEqual(json.loads(o["copies"]), json.loads(COPIES), "this tab's copy counts were not written back")
        self.assertEqual(o["still"], 0, "a store this tab holds stayed held after Keep all")
        self.assertEqual(o["lastGoodRows"], 0, "the notice still offers a copy that was kept")
        self.assertGreaterEqual(o["since"], 1, "what another tab wrote after the clear was written over, not kept aside")

    def test_leave_them_held_writes_nothing(self):
        o = _run(CLEAR + "SAY_YES = false; OUT.r = await window._storeKeepAllThisTab(); OUT.raw = Object.keys(RAW).length;"
                 " OUT.held = window.LSR.quarantined().length;")
        self.assertFalse(o["r"]["ok"])
        self.assertEqual(o["raw"], 0, "his 'Leave them held' still wrote")
        self.assertGreater(o["held"], 1)

    def test_a_store_another_tab_only_changed_still_offers_its_reload(self):
        """the premise: a stale (not cleared) row's bytes are there to read - its reload is the right exit"""
        o = _run("window.LSR.hold('d2r_copies', 'another tab wrote it while this one was busy'); OUT.notice = notice();")
        self.assertIn("location.reload()", o["notice"])
        self.assertIn("reload before you change anything here", o["notice"])
        self.assertNotIn("only copy", o["notice"])


RED_PROOF = [
    {"why": "REG-2523 fix round - after a clear the headline recommends the reload that drops the only copy again",
     "file": "bible.html", "matches": 1,
     "find": "    : (nc ? '⚠ ' + clearedSay : '⚠ Another tab changed what this tab holds — reload before you change anything here');\n",
     "replace": "    : '⚠ Another tab changed what this tab holds — reload before you change anything here';\n"},
    {"why": "REG-2523 fix round - a cleared row offers an unasked 'Reload this tab' again",
     "file": "bible.html", "matches": 1,
     "find": "    if (q.kind === 'stale' && q.cleared)\n      return",
     "replace": "    if (false)\n      return"},
    {"why": "REG-2523 fix round - a row this tab holds no copy of offers the whole-page reload over the copies it holds",
     "file": "bible.html", "matches": 1,
     "find": "        + (nc ? ' Keep this tab’s copies first - a reload drops them.'\n",
     "replace": "        + (false ? ' Keep this tab’s copies first - a reload drops them.'\n"},
    {"why": "REG-2523 fix round - no one action keeps every copy (one question per store)",
     "file": "bible.html", "matches": 1,
     "find": "  if (nKeep > 1)\n    head += ",
     "replace": "  if (false)\n    head += "},
    {"why": "REG-2523 fix round - Keep all writes without asking him",
     "file": "bible.html", "matches": 1,
     "find": "  var ask = skipAsk ? Promise.resolve(true)\n    : (typeof window.uiConfirm === 'function'\n        ? window.uiConfirm('Keep all of this tab’s copies - '",
     "replace": "  var ask = Promise.resolve(true) || (typeof window.uiConfirm === 'function'\n        ? window.uiConfirm('Keep all of this tab’s copies - '"},
    {"why": "REG-2523 fix round - Keep all keeps nothing",
     "file": "bible.html", "matches": 1,
     "find": "        return Promise.resolve(window._storeKeepThisTab(k, true)).then(function(r){\n",
     "replace": "        return Promise.resolve({ ok: false, why: 'not kept' }).then(function(r){\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
