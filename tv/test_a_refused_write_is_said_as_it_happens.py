# -*- coding: utf-8 -*-
"""REG-2526 (V1 round 3; the review of REG-2410, r5 and the storage-full minor) - A WRITE THE DOOR REFUSES IS SAID ON THE
BOARD AS IT HAPPENS, AND A STORE WITH NO WAY OUT SAYS SO.

r5: the store door counted every refused write of a quarantined store, but only into its registry and the console: the
notice was painted when the store was quarantined and never again. A rune, gem or material count he edited looked
accepted all session and was gone on the reload, and the board never said a write was refused. Reviewer (rv5): with
d2r_runeStash cut short, persist() ran 3 times - refused=3, the notice HTML identical to before, {Ber:2, Jah:1} never saved.
Storage full: when the bytes cannot be copied aside, Start it fresh is not offered and a backup restore refuses that key
(rightly - both would lose the bytes), yet the footer still said "A backup restore (Backup & Share) puts a good copy back":
a store the vault stands on in that state held the vault with no way out in the page, and the board said there was one.

NOW the first refusal of a store repaints the notice at once and the rest are gathered into one repaint per 250 ms, so
the count he reads is never behind by more than that; a store whose bytes could not be copied aside says there is no way
out in the page, what to do (download its bytes, or free space and reload), offers "Download its bytes", and the
restore footer is shown only for stores whose bytes ARE kept aside.

WHAT IS DRIVEN: the store door window.LSR, the boot loaders, persist() and the notice (store_door_harness), in node; the
storage-full case makes the door's own aside write throw, the way a full browser storage does. RED_PROOF below.
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

RUNES_CUT = '{"Ber":0,"Ja'


def _plain(body, seed):
    s = D.src()
    prog = ("window.__ASYNC = true;\n"
            "function notice(){ return (document.getElementById('store-quarantine') || {}).innerHTML || ''; }\n"
            "function later(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }\n"
            "(async function(){\n" + body + "\n})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page(D.stage(s) + D.boot(s), prog, seed=seed)


def _full(body, seed):
    s = D.src()
    prog = ("window.__ASYNC = true;\n"
            "function notice(){ return (document.getElementById('store-quarantine') || {}).innerHTML || ''; }\n"
            "(async function(){\n" + body + "\n})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page("THROW_ON = /d2r_quarantine~/;\n" + D.stage(s) + D.boot(s), prog, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED door and notice; UNMEASURED, not passing")
class ARefusedWriteIsSaidAsItHappens(unittest.TestCase):

    def test_the_count_of_refused_writes_reaches_the_board_while_he_works(self):
        o = _plain(r"""
OUT.before = notice();
runeStash['Ber'] = 2; runeStash['Jah'] = 1;
persist();
OUT.first = notice();                                  /* at once, on the first refusal */
persist(); persist();
OUT.refused = window.LSR.quarantined('d2r_runeStash').refused;
await later(400);
OUT.later = notice();                                  /* every refusal since, within the repaint window */
OUT.raw = RAW['d2r_runeStash'];
""", {"d2r_runeStash": RUNES_CUT})
        self.assertNotIn("refused", o["before"], "PREMISE: a refusal was counted before any write")
        self.assertIn("1 write was refused", o["first"], "the first refused write was not said at once: %r" % o["first"][-300:])
        self.assertEqual(o["refused"], 3)
        self.assertIn("3 writes were refused", o["later"], "later refusals never reached the board: %r" % o["later"][-300:])
        self.assertEqual(o["raw"], RUNES_CUT, "PREMISE: a quarantined store was written")

    def test_a_store_whose_bytes_could_not_be_kept_aside_says_there_is_no_way_out_in_the_page(self):
        o = _full(r"""
var q = window.LSR.quarantined('d2r_runeStash');
OUT.asideOk = q && q.asideOk;
OUT.notice = notice();
""", {"d2r_runeStash": RUNES_CUT})
        self.assertIs(o["asideOk"], False, "PREMISE: the aside write did not fail")
        n = o["notice"]
        self.assertIn('data-aside="none"', n)
        self.assertIn("could not be copied aside", n)
        self.assertIn("nothing on this page can start it fresh or restore a backup over them", n,
                      "a store with no way out in the page does not say so")
        self.assertIn("_storeDownloadBytes", n, "the one way out (download its bytes) is not offered")
        self.assertNotIn("_storeStartFresh", n, "Start it fresh is offered for bytes that cannot be kept aside")
        self.assertNotIn("puts a good copy back", n, "the footer still promises a restore that refuses this store")

    def test_a_store_kept_aside_still_offers_its_two_ways_out(self):
        o = _plain("OUT.notice = notice();", {"d2r_runeStash": RUNES_CUT})
        self.assertIn("_storeStartFresh", o["notice"])
        self.assertIn("puts a good copy back", o["notice"], "PREMISE: the restore footer is gone for a store kept aside")


RED_PROOF = [
    {"why": "REG-2526 - the first refused write is not said until something else repaints the notice",
     "file": "bible.html", "matches": 1,
     "find": "    if (ent.refused === 1) _qSay();\n",
     "replace": ""},
    {"why": "REG-2526 - refusals after the first never reach the board (the notice keeps the old count)",
     "file": "bible.html", "matches": 1,
     "find": "      try { _qPaintT = setTimeout(function(){ _qPaintT = null; _qSay(); }, 250); } catch(eT){ _qPaintT = null; _qSay(); }\n",
     "replace": ""},
    {"why": "REG-2526 - the footer promises a restore for a store whose bytes could not be kept aside",
     "file": "bible.html", "matches": 1,
     "find": "    + (nAside ? '<div class=\"sq-foot\">'",
     "replace": "    + (nq ? '<div class=\"sq-foot\">'"},
    {"why": "REG-2526 - a store with no way out in the page offers no way to save its bytes",
     "file": "bible.html", "matches": 1,
     "find": "                   : ' <button type=\"button\" class=\"sq-btn\" onclick=\"window._storeDownloadBytes(\\'' + k + '\\')\">Download its bytes</button>')\n",
     "replace": "                   : '')\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
