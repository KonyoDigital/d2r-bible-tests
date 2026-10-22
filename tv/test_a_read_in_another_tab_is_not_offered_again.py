# -*- coding: utf-8 -*-
"""REG-2524 FIX ROUND (V1 round 3; the review of REG-2524, minor b) - A READ ANOTHER TAB IS RUNNING IS NOT "A READ THAT
NEVER FINISHED", SO NO OTHER TAB OFFERS IT AGAIN (OR RE-BILLS IT).

REG-2524 marked a file handed to a read 'reading' and offered a 'reading' file as "⏯ Finish N" once no read was in flight
- asked of window._vIntakeBusy, which is THIS tab's alone. While tab A's read was in flight, tab B's 12 s poll said "⏯ N
screenshots were handed to a read that never finished (the page closed or reloaded)" and B's manual Scan offered ⏯
Finish, which re-read and re-billed the files A was still reading (a re-read of a low base can bump d2r_copies).

NOW the mark carries when and which tab handed the file over - 'reading@<ms>@<tab>', the tab being this browser tab's own
id (sessionStorage, so a reload of the SAME tab knows its old marks): this tab's mark is in flight while this tab reads;
another tab's mark is in flight while it is younger than 15 minutes, and is counted and SAID ("being read in another tab
right now"), never offered; an older one never finished and is offered. ⏯ Finish re-stamps what it hands to the read.

WHAT IS DRIVEN, cut whole from bible.html, in node over a stubbed folder: the store door (store_door_harness), seenLedger,
the AUTO INTAKE switch and gate, the head of window.vaultIntake with a stand-in for the read, the ⟦INTAKE SEEN VERDICT⟧
block and the whole scan region (⟦SCAN MARKS⟧, the menu, vaultReadBatch, vaultScanFolder). RED_PROOF below. A missing
node is the only skip.
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

SEEN_LEDGER = ("  function seenLedger(){", "\n")
GATE = ("  var VAULT_AUTO_INTAKE_KEY = 'd2r_vaultAutoIntake';", "  try { window._vaultIntakeGate = _vaultIntakeGate; } catch (eAg) {}\n")
VI_HEAD = ("  window.vaultIntake = async function(files, opts){\n", "    if (_stopped) return _stopped; /* v3767 intake stop */\n")
VERDICT = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")
SCAN = ("  var _pendingAll = null, _pendingFresh = null, _pendingGone = null, _pendingWaiting = null;\n",
        "  // v235: toggle the folder UI between")
MARK = re.compile(r"^reading@(\d+)@(.+)$")


def _cut(s, pair, inclusive_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j + (len(end) if inclusive_end else 0)]


def _pieces(s):
    return (D.stage(s) + r"""
var SEEN_KEY = 'd2r_intakeSeen';
var READ = [], STATUS = [];
function status(m){ STATUS.push(String(m)); }
function idbGet(){ return Promise.resolve(null); } function idbSet(){ return Promise.resolve(); }
function _setFolderConnectedUI(){} function _startAutoWatch(){}
var owned = new Set(['Harlequin Crest']), magicFinds = {};
window._removedAfter = function(){ return null; };
var REP = new El('vault-intake-report'); ELS['vault-intake-report'] = REP;
""" + _cut(s, SEEN_LEDGER) + _cut(s, GATE) + _cut(s, VI_HEAD) + r"""
    /* ── the read itself, a stand-in that never closes: it records what it was handed and writes nothing ── */
    READ.push(files.map(function(f){ return f.name; }));
    return { ok: true };
  };
""" + _cut(s, VERDICT) + _cut(s, SCAN, inclusive_end=False) + r"""
var FILES = [];
function folder(names){ FILES = names.map(function(n, i){ return { name: n, lastModified: 1000 + i }; }); }
liveHandle = { queryPermission: function(){ return Promise.resolve('granted'); },
               requestPermission: function(){ return Promise.resolve('granted'); },
               values: async function*(){ for (var f of FILES) yield { kind: 'file', name: f.name,
                 getFile: (function(g){ return function(){ return Promise.resolve(g); }; })(f) }; } };
function ledger(){ return RAW[SEEN_KEY] == null ? null : JSON.parse(RAW[SEEN_KEY]); }
function menuText(){ return REP.hidden ? '' : String(REP.innerHTML || ''); }
function reset(){ READ.length = 0; STATUS.length = 0; REP.hidden = true; REP.innerHTML = ''; }
var RECORD = { held: ['Harlequin Crest'], unr: [], at: 10, world: 'main' };
""")


def _run(body):
    s = D.src()
    prog = ("window.__ASYNC = true;\n(async function(){\nRAW['d2r_vaultAutoIntake'] = 'on';\n" + body
            + "\n})().then(done).catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page(_pieces(s), prog, seed={})


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED scan; UNMEASURED, not passing")
class AReadInAnotherTabIsNotOfferedAgain(unittest.TestCase):

    def test_another_tabs_read_in_flight_is_said_never_offered_or_read(self):
        o = _run(r"""
RAW[SEEN_KEY] = JSON.stringify({ 'old.jpg': RECORD, 'mid.jpg': 'reading@' + (Date.now() - 60000) + '@tabA' });
folder(['old.jpg', 'mid.jpg']);
await window.vaultScanFolder(true);                           /* tab B's 12 s poll, a minute into tab A's read */
OUT.poll = { read: READ.slice(), status: STATUS.slice() };
reset();
await window.vaultScanFolder(false);                          /* tab B's manual Scan */
OUT.manual = { read: READ.slice(), menu: menuText(), status: STATUS.slice() };
""")
        self.assertEqual(o["poll"]["read"], [], "the poll read a file another tab is reading")
        said = " | ".join(o["poll"]["status"])
        self.assertNotIn("never finished", said, "a read another tab is running was said as one that never finished: %r" % said)
        self.assertIn("1 screenshot is being read in another tab right now", said, "the read in flight was not said: %r" % said)
        self.assertEqual(o["manual"]["read"], [], "the manual Scan re-read a file another tab is reading")
        self.assertNotIn("Finish", o["manual"]["menu"] + " ".join(o["manual"]["status"]),
                         "the manual Scan offered ⏯ Finish for a read another tab is running")

    def test_an_old_mark_from_another_tab_never_finished_and_finish_re_stamps_it(self):
        o = _run(r"""
RAW[SEEN_KEY] = JSON.stringify({ 'old.jpg': RECORD, 'mid.jpg': 'reading@' + (Date.now() - 20 * 60000) + '@tabA' });
folder(['old.jpg', 'mid.jpg']);
await window.vaultScanFolder(true);
OUT.poll = { read: READ.slice(), status: STATUS.slice() };
reset();
await window.vaultScanFolder(false);
OUT.menu = menuText();
window.vaultReadBatch('waiting');                             /* ⏯ Finish 1 */
OUT.finish = READ.slice(); OUT.mark = ledger()['mid.jpg'];
""")
        self.assertEqual(o["poll"]["read"], [], "the poll read an unfinished file on its own")
        self.assertTrue(any("handed to a read that never finished" in m for m in o["poll"]["status"]), o["poll"]["status"])
        self.assertIn("Finish 1", o["menu"], "a read that never finished (20 minutes old) is not offered: %r" % o["menu"])
        self.assertEqual(o["finish"], [["mid.jpg"]], "⏯ Finish did not read it")
        m = MARK.match(o["mark"] or "")
        self.assertTrue(m, "⏯ Finish left no stamped mark: %r" % o["mark"])
        self.assertNotEqual(m.group(2), "tabA", "⏯ Finish did not re-stamp the file as this tab's - another tab would offer it again")

    def test_this_tabs_own_mark_is_in_flight_only_while_this_tab_reads(self):
        o = _run(r"""
folder(['new_1.jpg']);
await window.vaultScanFolder(false);                          /* reads it now: the read stand-in never closes */
OUT.mark = ledger()['new_1.jpg'];
reset(); window._vIntakeBusy = true;
await window.vaultScanFolder(false);
OUT.busy = { read: READ.slice(), menu: menuText() };
reset(); window._vIntakeBusy = false;
await window.vaultScanFolder(false);
OUT.idle = { read: READ.slice(), menu: menuText() };
""")
        self.assertTrue(MARK.match(o["mark"] or ""), "the hand-off mark carries no time and tab: %r" % o["mark"])
        self.assertNotIn("Finish", o["busy"]["menu"], "this tab's own read in flight was offered again")
        self.assertEqual(o["busy"]["read"], [])
        self.assertIn("Finish 1", o["idle"]["menu"], "this tab's read that never closed is not offered: %r" % o["idle"]["menu"])


RED_PROOF = [
    {"why": "REG-2524 fix round - another tab's read in flight is offered as one that never finished (re-read, re-billed)",
     "file": "bible.html", "matches": 1,
     "find": "    return (typeof sv.at === 'number' && isFinite(sv.at)) ? (Date.now() - sv.at) < _READING_FRESH_MS : false;\n",
     "replace": "    return false;\n"},
    {"why": "REG-2524 fix round - the hand-off mark carries no time and no tab again",
     "file": "bible.html", "matches": 1,
     "find": "  function _readingMark(){ return 'reading@' + Date.now() + '@' + _SCAN_TAB; }\n",
     "replace": "  function _readingMark(){ return 'reading'; }\n"},
    {"why": "REG-2524 fix round - ⏯ Finish does not re-stamp what it reads, so another tab offers it again",
     "file": "bible.html", "matches": 1,
     "find": "      _marked = (_seenRegister(pick, 'reading') < 0) ? -1 : 0;\n",
     "replace": "      _marked = 0;\n"},
    {"why": "REG-2524 fix round - the verdict reads a stamped mark as a legacy 'seen' (never offered, never said)",
     "file": "bible.html", "matches": 1,
     "find": "    var _rdV = _readingOf(v);\n",
     "replace": "    var _rdV = (v === 'reading') ? { at: null, tab: null } : null;\n"},
    {"why": "REG-2524 fix round - a read in flight in another tab is skipped in silence",
     "file": "bible.html", "matches": 1,
     "find": "    if (r) out += ' · ' + r + ' screenshot' + (r===1?' is':'s are') + ' being read in another tab right now — not read here';\n",
     "replace": ""},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
