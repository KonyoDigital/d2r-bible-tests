# -*- coding: utf-8 -*-
"""REG-2524 (V1 round 3; the review of REG-2403, r1) - A FOLDER SCAN ASKS THE GATE BEFORE IT MARKS A SCREENSHOT, AND MARKS
ONLY WHAT A READ WILL TAKE.

REG-2403 said "a scan marks only what it reads". But _seenRegister ran BEFORE window.vaultIntake, whose first statement
is the v3767 AUTO INTAKE gate - and AUTO INTAKE is off by default (an absent d2r_vaultAutoIntake reads off). So his
manual Scan, the 12 s poll, the menu with no report element and the ✨ New / 🕐 Latest picks all marked new screenshots
as a bare 1 and the read was refused; the status line said "📂 2 new screenshots — reading…" over a silent refusal, and
under REG-2401's verdict a bare 1 reads 'seen' for ever: after he turned AUTO INTAKE on the folder said "0 new" and
those screenshots were never read. A page reloaded or closed mid-read left the same bare marks (v584.1's restart trap).
Reviewer, on the real gate and the shipped scan (identical on origin/main and on the merged V1 tree): read=[], ledger
{new_1.jpg:1, new_2.jpg:1}, and after AUTO INTAKE on: read=[], menu '0 new', every verdict 'seen'.

NOW (⟦SCAN MARKS⟧ in bible.html):
  * the gate (window._vaultIntakeGate: AUTO INTAKE and the vault hold) is asked BEFORE anything is marked - by the
    manual Scan, the poll, the folder picker and every pick; refused, nothing is marked or read, and the scan SAYS how
    many screenshots wait and why;
  * a file handed to a read is marked 'reading', never 1: the read's own end-of-batch mark replaces it, and a read that
    never closed leaves it 'reading' - offered by a manual Scan as ⏯ Finish N, never read by the poll on its own;
  * a scan ledger that will not read is UNKNOWN (the one reader quarantines it): nothing is read or marked, and that is
    said;
  * a file whose items' status could not be read ('unknown') is counted and said on the poll's line and in the menu,
    never skipped in silence (the review's S8 sabotage left every V1a law green).

WHAT IS DRIVEN: the store door window.LSR (store_door_harness), and cut whole from bible.html: seenLedger, the AUTO INTAKE
switch and gate, the head of window.vaultIntake (its gate) with a stand-in for the read itself, the ⟦INTAKE SEEN VERDICT⟧
block and the whole scan region (the ⟦SCAN MARKS⟧ helpers, the menu, vaultReadBatch, vaultScanFolder,
vaultScanFolderLegacy), in node over a stubbed folder. RED_PROOF below. A missing node is the only skip.
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

#: the scan ledger cut short mid-write (the review's r2 bytes)
CUT_LEDGER = ('{"old_1.jpg":{"held":["Shako"],"unr":[],"at":10,"world":"main"},'
              '"old_2.jpg":{"held":["Grief"],"unr":[],"at":10,"world":"main"},"old_3.')


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
var READ = [], HANDED = [], STATUS = [], WRITES = false;
function status(m){ STATUS.push(String(m)); }
function idbGet(){ return Promise.resolve(null); } function idbSet(){ return Promise.resolve(); }
function _setFolderConnectedUI(){} function _startAutoWatch(){}
var owned = new Set(['Harlequin Crest']), magicFinds = {};
window._removedAfter = function(){ return null; };              /* nothing on record: a silent loss reads 'gone' */
var REP = new El('vault-intake-report'); ELS['vault-intake-report'] = REP;
""" + _cut(s, SEEN_LEDGER) + _cut(s, GATE) + _cut(s, VI_HEAD) + r"""
    /* ── the read itself, a stand-in: what it was handed, and how the ledger stood at the hand-off ── */
    READ.push(files.map(function(f){ return f.name; }));
    var atHand = (function(){ try { return JSON.parse(RAW[SEEN_KEY] || '{}'); } catch (e) { return null; } })();
    HANDED.push(files.map(function(f){ return atHand ? atHand[f.name] : 'UNREADABLE'; }));
    if (WRITES){
      var sNow = seenLedger();
      files.forEach(function(f){ owned.add('item of ' + f.name);
        _intakeSeenMark(sNow, f, { nw: ['item of ' + f.name], own: [], unr: [], mf: [], err: false }, _intakeSeenAsk()); });
      window.LSR.setItem(SEEN_KEY, JSON.stringify(sNow));
    }
    return { ok: true };
  };
""" + _cut(s, VERDICT) + _cut(s, SCAN, inclusive_end=False) + r"""
var FILES = [];
function folder(names){ FILES = names.map(function(n, i){ return { name: n, lastModified: 1000 + i }; }); }
liveHandle = { queryPermission: function(){ return Promise.resolve('granted'); },
               requestPermission: function(){ return Promise.resolve('granted'); },
               values: async function*(){ for (var f of FILES) yield { kind: 'file', name: f.name,
                 getFile: (function(g){ return function(){ return Promise.resolve(g); }; })(f) }; } };
function ledger(){ return RAW[SEEN_KEY] == null ? null : RAW[SEEN_KEY]; }
function menuText(){ return REP.hidden ? '' : String(REP.innerHTML || ''); }
function reset(){ READ.length = 0; HANDED.length = 0; STATUS.length = 0; REP.hidden = true; REP.innerHTML = ''; }
""")


def _run(body, seed=None):
    s = D.src()
    prog = ("window.__ASYNC = true;\n(async function(){\n" + body + "\n})().then(done).catch(function(e){ "
            "process.stderr.write(String(e && e.stack || e)); process.exit(3); });")
    return D.page(_pieces(s), prog, seed=seed or {})


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED scan and gate; UNMEASURED, not passing")
class AScanAsksTheGateBeforeItMarks(unittest.TestCase):

    def test_auto_intake_off_marks_nothing_reads_nothing_and_says_how_many_wait(self):
        o = _run(r"""
folder(['new_1.jpg', 'new_2.jpg']);
await window.vaultScanFolder(false);                          /* his manual 🔄 Scan, AUTO INTAKE never set (off) */
OUT.manual = { read: READ.slice(), ledger: ledger(), status: STATUS.slice(), menu: menuText() };
reset(); folder(['new_1.jpg', 'new_2.jpg', 'new_3.jpg']);
await window.vaultScanFolder(true);                           /* the 12 s poll */
OUT.poll = { read: READ.slice(), ledger: ledger(), status: STATUS.slice() };
reset();
window.vaultScanFolderLegacy(FILES.map(function(f){ return { name: f.name, lastModified: f.lastModified }; }));
OUT.picker = { read: READ.slice(), ledger: ledger(), status: STATUS.slice(), menu: menuText() };
reset(); RAW['d2r_vaultAutoIntake'] = 'on';                   /* he turns AUTO INTAKE on: the three are still NEW */
await window.vaultScanFolder(false);
OUT.on = { read: READ.slice(), handed: HANDED.slice(), ledger: JSON.parse(ledger() || '{}') };
""")
        for k, n in (("manual", 2), ("poll", 3), ("picker", 3)):
            got = o[k]
            self.assertEqual(got["read"], [], "%s: a read ran while AUTO INTAKE is off" % k)
            self.assertIsNone(got["ledger"], "%s: screenshots were MARKED while the gate refuses their read (the trap): %r"
                              % (k, got["ledger"]))
            said = " | ".join(got["status"])
            self.assertIn("AUTO INTAKE is off", said, "%s: the refusal was not said: %r" % (k, got["status"]))
            self.assertIn("%d screenshots wait" % n, said, "%s: how many wait was not said: %r" % (k, got["status"]))
            self.assertIn("nothing was read or marked", said)
        self.assertNotIn("read which", o["picker"]["menu"], "the picker offered picks the gate would refuse")
        self.assertEqual(o["on"]["read"], [["new_1.jpg", "new_2.jpg", "new_3.jpg"]],
                         "after AUTO INTAKE is on the screenshots were never read: %r" % o["on"]["read"])
        # REG-2524 fix round - the hand-off mark carries when and which tab: 'reading@<ms>@<tab>'
        self.assertEqual(len(o["on"]["handed"]), 1)
        self.assertTrue(all(isinstance(m, str) and re.match(r"^reading@\d+@.+$", m) for m in o["on"]["handed"][0]),
                        "a file handed to a read must be marked 'reading@<ms>@<tab>', never the bare 1 that reads 'seen' "
                        "for ever: %r" % o["on"]["handed"])

    def test_a_read_that_never_closed_is_offered_as_its_own_choice_and_never_read_by_the_poll(self):
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'on';
RAW[SEEN_KEY] = JSON.stringify({ 'old.jpg': { held: ['Harlequin Crest'], unr: [], at: 10, world: 'main' }, 'mid.jpg': 'reading' });
folder(['old.jpg', 'mid.jpg']);
await window.vaultScanFolder(true);                           /* the poll after a reload that cut a read short */
OUT.poll = { read: READ.slice(), status: STATUS.slice() };
reset(); window._vIntakeBusy = true;                          /* a read in flight in THIS tab is taking it now */
await window.vaultScanFolder(false);
OUT.busy = { read: READ.slice(), menu: menuText() };
reset(); window._vIntakeBusy = false;
await window.vaultScanFolder(false);                          /* his manual Scan */
OUT.menu = menuText(); OUT.menuRead = READ.slice();
window.vaultReadBatch('waiting');                             /* ⏯ Finish 1 */
OUT.finish = READ.slice(); OUT.ledger = JSON.parse(ledger());
""")
        self.assertEqual(o["poll"]["read"], [], "the 12 s poll read a file whose read never closed, on its own")
        self.assertTrue(any("handed to a read that never finished" in m for m in o["poll"]["status"]),
                        "the poll did not say the unfinished read: %r" % o["poll"]["status"])
        self.assertNotIn("Finish", o["busy"]["menu"], "a file a read in this tab is taking was offered again")
        self.assertIn("Finish 1", o["menu"], "the manual Scan did not offer the unfinished read as its own choice: %r" % o["menu"])
        self.assertEqual(o["menuRead"], [], "the manual Scan read the unfinished file without his choice")
        self.assertEqual(o["finish"], [["mid.jpg"]], "⏯ Finish did not read the unfinished file")
        self.assertEqual(o["ledger"]["old.jpg"]["held"], ["Harlequin Crest"], "a record was written over")

    def test_a_file_whose_status_could_not_be_read_is_said_never_skipped_in_silence(self):
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'on';
window._removedAfter = function(){ return { unknown: 'the removal journal would not read' }; };
RAW[SEEN_KEY] = JSON.stringify({ 'u.jpg': { held: ['Death Loop'], unr: [], at: 500, world: 'main' } });
folder(['u.jpg']);
await window.vaultScanFolder(true);
OUT.poll = { read: READ.slice(), status: STATUS.slice() };
reset();
await window.vaultScanFolder(false);
OUT.manual = { read: READ.slice(), menu: menuText() };
""")
        self.assertEqual(o["poll"]["read"], [], "an UNKNOWN file was read on a guess")
        self.assertTrue(any("status could not be read" in m for m in o["poll"]["status"]),
                        "the poll skipped an UNKNOWN file in silence: %r" % o["poll"]["status"])
        self.assertEqual(o["manual"]["read"], [])
        self.assertIn("status could not be read", o["manual"]["menu"], "the Scan menu hid the UNKNOWN file")

    def test_a_screenshot_read_before_records_existed_is_said_in_the_scan_menu(self):
        """REG-2529 (review of REG-2401, minor) - a bare mark reads 'seen' for ever; the menu says so instead of hiding it"""
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'on';
RAW[SEEN_KEY] = JSON.stringify({ 'old.jpg': 1, 'rec.jpg': { held: ['Harlequin Crest'], unr: [], at: 10, world: 'main' } });
folder(['old.jpg', 'rec.jpg']);
await window.vaultScanFolder(false);
OUT.menu = menuText(); OUT.read = READ.slice();
""")
        self.assertEqual(o["read"], [])
        # REG-2529 fix round - a bare mark is said as what is known: registered without a record of what it read
        self.assertIn("<strong>1</strong> screenshot was registered without a record of what it read", o["menu"],
                      "the menu hides the screenshots registered without a record: %r" % o["menu"])
        self.assertNotIn("read before this board kept a record", o["menu"])

    def test_a_ledger_that_will_not_read_is_unknown_and_nothing_is_read_or_marked_over_it(self):
        o = _run(r"""
folder(['old_1.jpg', 'old_2.jpg', 'new_1.jpg']);
await window.vaultScanFolder(true);
OUT.poll = { read: READ.slice(), status: STATUS.slice(), raw: ledger() };
reset();
await window.vaultScanFolder(false);
OUT.manual = { read: READ.slice(), status: STATUS.slice(), raw: ledger() };
reset();
window.vaultScanFolderLegacy(FILES.slice());
OUT.picker = { read: READ.slice(), status: STATUS.slice(), raw: ledger(), menu: menuText() };
var q = window.LSR.quarantined(SEEN_KEY);
OUT.q = q ? { kind: q.kind, reason: q.reason, aside: q.aside ? RAW[q.aside] : null } : null;
""", seed={"d2r_intakeSeen": CUT_LEDGER, "d2r_vaultAutoIntake": "on"})
        for k in ("poll", "manual", "picker"):
            self.assertEqual(o[k]["read"], [], "%s: an unreadable ledger was read as empty - old screenshots re-billed" % k)
            self.assertEqual(o[k]["raw"], CUT_LEDGER, "%s: marks were written over the unreadable ledger" % k)
            self.assertTrue(any("d2r_intakeSeen" in m and "nothing was read or marked" in m for m in o[k]["status"]),
                            "%s: the UNKNOWN ledger was not said: %r" % (k, o[k]["status"]))
        self.assertNotIn("read which", o["picker"]["menu"])
        self.assertEqual(o["q"], {"kind": "quarantine", "reason": "will not parse", "aside": CUT_LEDGER},
                         "the ledger was not quarantined with its bytes kept aside")

    def test_a_switch_that_will_not_read_is_said_as_unknown_never_as_off(self):
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'maybe';                         /* the switch's own bytes, unreadable */
folder(['new_1.jpg']);
await window.vaultScanFolder(false);
OUT.read = READ.slice(); OUT.ledger = ledger(); OUT.status = STATUS.slice();
""")
        self.assertEqual(o["read"], [])
        self.assertIsNone(o["ledger"], "a refused read left the screenshot marked")
        said = " | ".join(o["status"])
        self.assertIn("AUTO INTAKE would not read", said, "an unreadable switch was not said: %r" % o["status"])
        self.assertNotIn("AUTO INTAKE is off", said, "an unreadable switch was said as 'off' - a guess")

    def test_a_held_vault_refuses_before_anything_is_marked(self):
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'on';
window._vaultHeld = function(){ return { keys: ['d2r_owned'], why: 'the vault is held - d2r_owned will not parse' }; };
folder(['new_1.jpg']);
await window.vaultScanFolder(false);
OUT.read = READ.slice(); OUT.ledger = ledger(); OUT.status = STATUS.slice();
""")
        self.assertEqual(o["read"], [])
        self.assertIsNone(o["ledger"], "a held vault's refusal left the screenshot marked")
        self.assertTrue(any("the vault is held" in m and "nothing was read or marked" in m for m in o["status"]), o["status"])

    def test_a_pick_asks_the_gate_first(self):
        o = _run(r"""
RAW['d2r_vaultAutoIntake'] = 'on';
var pile = []; for (var i = 1; i <= 13; i++) pile.push('new_' + i + '.jpg');
folder(pile);
await window.vaultScanFolder(false);                          /* a backlog: the menu */
OUT.menu = menuText();
RAW['d2r_vaultAutoIntake'] = 'off';                           /* he turns AUTO INTAKE off before he picks */
window.vaultReadBatch('new');
OUT.read = READ.slice(); OUT.ledger = ledger(); OUT.status = STATUS.slice();
""")
        self.assertIn("13 new", o["menu"], "PREMISE: the backlog menu did not show")
        self.assertEqual(o["read"], [], "a pick read while the gate refuses")
        self.assertIsNone(o["ledger"], "a pick marked screenshots the gate then refused to read")
        self.assertTrue(any("AUTO INTAKE is off" in m and "13 screenshots wait" in m for m in o["status"]), o["status"])


RED_PROOF = [
    {"why": "REG-2524 - the folder scan marks new screenshots before it asks the gate (marked 'read', never read)",
     "file": "bible.html", "matches": 1,
     "find": "      var _gS = (fresh.length || regone.length || waiting.length) ? _scanGate() : null;\n",
     "replace": "      var _gS = null;\n"},
    {"why": "REG-2524 - a file handed to a read is marked with the bare 1 again ('seen' for ever if the read never closes)",
     "file": "bible.html", "matches": 1,
     "find": "    var s = seenLedger(), n = 0, m = (mark === 'reading') ? _readingMark() : 1;\n",
     "replace": "    var s = seenLedger(), n = 0, m = 1;\n"},
    {"why": "REG-2524 - the 12 s poll reads a file whose read never closed, on its own",
     "file": "bible.html", "matches": 1,
     "find": "        else if (_sv.state === 'reading'){ if (_readingInFlight(_sv)) inFlightN++; else waiting.push(f); }\n",
     "replace": "        else if (_sv.state === 'reading'){ seen[f.name] = 1; fresh.push(f); }\n"},
    {"why": "REG-2524 (review S8) - a file whose status could not be read is skipped in silence on the poll",
     "file": "bible.html", "matches": 1,
     "find": "    if (u) out += ' · ' + u + ' screenshot' + (u===1?'':'s') + ' read items whose status could not be read — not read again';\n",
     "replace": ""},
    {"why": "REG-2524 - a switch that will not read is said as 'AUTO INTAKE is off' (a guess)",
     "file": "bible.html", "matches": 1,
     "find": "    if (g && g.refused === 'auto-intake-off' && /^AUTO INTAKE is off/.test(String(g.why || '')))\n",
     "replace": "    if (g && g.refused === 'auto-intake-off')\n"},
    {"why": "REG-2524 - a pick marks and reads without asking the gate",
     "file": "bible.html", "matches": 1,
     "find": "    if (pick.length){\n      var _g = _scanGate();\n",
     "replace": "    if (false){\n      var _g = _scanGate();\n"},
    {"why": "REG-2529 - the scan menu hides the screenshots read before records existed",
     "file": "bible.html", "matches": 1,
     "find": "    if (more.legacy) html += ",
     "replace": "    if (false) html += "},
    {"why": "REG-2524 - the verdict reads an unfinished read as 'seen' (never offered again)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_rdV) return { state: 'reading', gone: [], prev: null, at: _rdV.at, tab: _rdV.tab };   /* REG-2524 — handed to a read that has not closed */\n",
     "replace": ""},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
