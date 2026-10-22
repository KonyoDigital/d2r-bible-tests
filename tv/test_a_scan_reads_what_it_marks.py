# -*- coding: utf-8 -*-
"""REG-2403 - A FOLDER SCAN MARKS A SCREENSHOT READ ONLY WHEN IT IS READ (the review of REG-2401, finding 1).

REG-2401 added a '♻ Read again' choice for already-read screenshots whose item left the vault with no removal on record
('gone'), and routed EVERY manual Scan that found one to the pick-a-batch menu. The menu registered every new file the
moment it appeared, before he chose. So with one gone file waiting, his manual Scan of two new screenshots read neither:
a pick of '♻ Read again', Skip, or a menu he simply closed left them marked read (the 12 s poll skips them, the next
Scan says '0 new'). That is v584.1's restart trap exactly: after a browser restart the quiet poll cannot run until he
re-authorises the folder by clicking Scan, and tests/v212_folder_watch.spec.ts' guard for it has no gone file.
Reviewer's measurement (cut from origin/main and from the branch, run in node): origin/main read [new_1, new_2] at once;
the branch read nothing, showed the menu, and the stored ledger already said new_1=1 and new_2=1.

NOW: a manual Scan with 1-12 new files reads them at once whether or not a gone file waits, and SAYS the gone ones; the
menu (a big backlog, or nothing new) marks nothing - a PICK writes what it means: New registers what it reads, Latest N
and Skip register the new files as v224 always did, '♻ Read again' leaves them new. A mark is merged into the ledger as
it is at that moment, never the scan's stale snapshot. The 12 s poll never reads a gone file on its own (v567).

WHAT THIS LAW HOLDS - the SHIPPED scan code cut whole from bible.html (the scan menu, vaultReadBatch, vaultScanFolder,
vaultScanFolderLegacy, seenLedger and the ⟦INTAKE SEEN VERDICT⟧ block) run in node over a stubbed folder handle; the
read itself is a stand-in that records what it was handed and, where a case needs it, writes the record a read writes.
A missing node raises: this law does not skip. Browser half (CI): tests/reg2400_reload_keeps_what_he_owns.spec.ts.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")
VERDICT = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")
SEEN_LEDGER = ("  function seenLedger(){", "\n")
SCAN = ("  var _pendingAll = null, _pendingFresh = null, _pendingGone = null, _pendingWaiting = null;\n",
        "  // v235: toggle the folder UI between")

GONE = "f_1790549355102.jpg"   # one of GrokBot's frames (#162): it read "Death Loop", which then left owned silently


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair, inclusive_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j + (len(end) if inclusive_end else 0)]


def _node(body):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = r"""
var window = globalThis;
var RAW = {}, CALLS = [], OPTS = [], STATUS = [];
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var SEEN_KEY = 'd2r_intakeSeen';
%(seenLedger)s
var REP = { hidden: true, innerHTML: '' };
var document = { getElementById: function(id){ return id === 'vault-intake-report' ? REP : null; } };
function status(m){ STATUS.push(String(m)); }
function idbGet(){ return Promise.resolve(null); } function idbSet(){ return Promise.resolve(); }
function _setFolderConnectedUI(){} function _startAutoWatch(){}
var owned = new Set(['Harlequin Crest']), magicFinds = {};
window._removedAfter = function(){ return null; };       /* nothing on record: the silent loss */
var WRITES = false;                                      /* a case that needs the read's own record turns this on */
window.vaultIntake = function(files, opts){
  CALLS.push(files.map(function(f){ return f.name; })); OPTS.push(opts || {});
  if (WRITES){
    var s = JSON.parse(RAW[SEEN_KEY] || '{}');
    files.forEach(function(f){ owned.add('item of ' + f.name);
      _intakeSeenMark(s, f, { nw: ['item of ' + f.name], own: [], unr: [], mf: [], err: false }, _intakeSeenAsk()); });
    RAW[SEEN_KEY] = JSON.stringify(s);
  }
  return Promise.resolve();
};
%(verdict)s
%(scan)s
var FILES = [];
function folder(names){ FILES = names.map(function(n, i){ return { name: n, lastModified: 1000 + i }; }); }
liveHandle = { queryPermission: function(){ return Promise.resolve('granted'); },
               requestPermission: function(){ return Promise.resolve('granted'); },
               values: async function*(){ for (var f of FILES) yield { kind: 'file', name: f.name,
                 getFile: (function(g){ return function(){ return Promise.resolve(g); }; })(f) }; } };
function ledger(){ return JSON.parse(RAW[SEEN_KEY] || '{}'); }
function menu(){ return { shown: !REP.hidden && /read which/.test(REP.innerHTML),
                          newCount: ((REP.innerHTML.match(/<strong[^>]*>(\d+) new<\/strong>/) || [])[1] || null),
                          readAgain: ((REP.innerHTML.match(/Read again (\d+)/) || [])[1] || null) }; }
function reset(){ CALLS.length = 0; OPTS.length = 0; STATUS.length = 0; REP.hidden = true; REP.innerHTML = ''; }
/* the record GrokBot's frame left: it read "Death Loop", and Death Loop has since left owned with nothing on record */
RAW[SEEN_KEY] = JSON.stringify({ %(gone)s: { held: ['Death Loop'], unr: [], at: 500, world: 'main' } });
var OUT = {};
(async function(){
%(body)s
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String(e && e.stack || e)); process.exit(3); });
""" % {"seenLedger": _cut(s, SEEN_LEDGER), "verdict": _cut(s, VERDICT), "scan": _cut(s, SCAN, inclusive_end=False),
       "gone": json.dumps(GONE), "body": body}
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise AssertionError("the cut scan did not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


class AScanReadsWhatItMarks(unittest.TestCase):

    def test_his_manual_scan_reads_two_new_shots_at_once_while_a_gone_one_waits(self):
        got = _node(r"""
folder([%(gone)s, 'new_1.jpg', 'new_2.jpg']);
var before = RAW[SEEN_KEY];
await window.vaultScanFolder(false);                     /* he clicks 🔄 Scan (the restart case) */
OUT.reads = CALLS.slice(); OUT.opts = OPTS.slice(); OUT.menu = menu(); OUT.status = STATUS.slice();
OUT.ledger = ledger(); OUT.goneUntouched = JSON.stringify(ledger()[%(gone)s]) === JSON.stringify(JSON.parse(before)[%(gone)s]);
reset(); WRITES = true;
await window.vaultScanFolder(true);                      /* the 12 s poll afterwards */
OUT.pollReads = CALLS.slice(); OUT.pollStatus = STATUS.slice();
reset();
var beforeMenu = RAW[SEEN_KEY];
await window.vaultScanFolder(false);                     /* his next Scan: nothing new, the gone one offered */
OUT.next = menu(); OUT.nextReads = CALLS.slice(); OUT.menuWroteNothing = RAW[SEEN_KEY] === beforeMenu;
window.vaultReadBatch('gone');
OUT.readAgain = CALLS.slice();
""" % {"gone": json.dumps(GONE)})
        self.assertEqual(got["reads"], [["new_1.jpg", "new_2.jpg"]],
                         "his manual Scan did not read the two new screenshots at once (v584.1): %r" % got["reads"])
        self.assertFalse(got["menu"]["shown"], "a gone file sent a 1-12 batch to the menu again")
        self.assertTrue(got["opts"][0].get("fromFolder"))
        self.assertEqual(got["opts"][0].get("goneWaiting"), 1, "the read was not told a gone screenshot waits")
        self.assertTrue(any("♻ 1 already-read screenshot" in m for m in got["status"]),
                        "the gone screenshot was not said: %r" % got["status"])
        # REG-2524 - a file handed to a read is marked 'reading' (the read's own end-of-batch mark replaces it), never
        # the bare 1 that read 'seen' for ever when the read never closed
        self.assertEqual(got["ledger"].get("new_1.jpg"), "reading")
        self.assertEqual(got["ledger"].get("new_2.jpg"), "reading")
        self.assertTrue(got["goneUntouched"], "the scan rewrote the gone screenshot's record")
        self.assertEqual(got["pollReads"], [], "the 12 s poll read something on its own: %r" % got["pollReads"])
        self.assertTrue(any("1 already-read screenshot" in m for m in got["pollStatus"]),
                        "the poll did not say the gone screenshot: %r" % got["pollStatus"])
        self.assertEqual(got["nextReads"], [], "a Scan with nothing new read on its own")
        self.assertTrue(got["next"]["shown"])
        self.assertEqual((got["next"]["newCount"], got["next"]["readAgain"]), ("0", "1"),
                         "the next Scan did not offer the gone screenshot as its own choice: %r" % got["next"])
        self.assertTrue(got["menuWroteNothing"], "the menu wrote the ledger before any pick")
        self.assertEqual(got["readAgain"], [[GONE]])

    def test_the_menu_marks_nothing_until_a_pick_names_it(self):
        got = _node(r"""
var pile = [%(gone)s]; for (var i = 1; i <= 13; i++) pile.push('new_' + i + '.jpg');
folder(pile);
var before = RAW[SEEN_KEY];
await window.vaultScanFolder(false);                     /* a backlog of 13: the menu, for the token guard */
OUT.menu = menu(); OUT.reads = CALLS.slice(); OUT.wroteAtMenu = RAW[SEEN_KEY] !== before;
window.vaultReadBatch('gone');                           /* he picks ♻ Read again */
OUT.readAgain = CALLS.slice(); OUT.pickStatus = STATUS.slice();
OUT.marked = Object.keys(ledger()).filter(function(k){ return /^new_/.test(k); });
reset();
await window.vaultScanFolder(true);                      /* the poll: 13 is a backlog, never auto-read */
OUT.pollReads = CALLS.slice(); OUT.pollStatus = STATUS.slice();
reset();
await window.vaultScanFolder(false);                     /* his next Scan: the 13 are still NEW */
OUT.again = menu();
reset();                                                 /* he closes that menu: nothing was picked */
await window.vaultScanFolder(false);
OUT.afterClose = menu(); OUT.markedAfterClose = Object.keys(ledger()).filter(function(k){ return /^new_/.test(k); });
""" % {"gone": json.dumps(GONE)})
        self.assertTrue(got["menu"]["shown"])
        self.assertEqual((got["menu"]["newCount"], got["menu"]["readAgain"]), ("13", "1"))
        self.assertEqual(got["reads"], [])
        self.assertFalse(got["wroteAtMenu"], "the menu registered the new screenshots before he chose")
        self.assertEqual(got["readAgain"], [[GONE]], "'♻ Read again' read more than the gone screenshot")
        self.assertEqual(got["marked"], [], "'♻ Read again' marked new screenshots read without reading them: %r"
                         % got["marked"])
        self.assertTrue(any("stay new" in m for m in got["pickStatus"]), "the pick did not say the new ones stay new")
        self.assertEqual(got["pollReads"], [])
        self.assertTrue(any("13 new screenshots waiting" in m for m in got["pollStatus"]), got["pollStatus"])
        self.assertEqual(got["again"]["newCount"], "13", "the new screenshots were lost to the ♻ pick: %r" % got["again"])
        self.assertEqual(got["afterClose"]["newCount"], "13", "a closed menu marked the new screenshots read")
        self.assertEqual(got["markedAfterClose"], [])

    def test_new_latest_and_skip_register_as_v224_did_and_merge_into_the_ledger_as_it_is(self):
        got = _node(r"""
var pile = []; for (var i = 1; i <= 25; i++) pile.push('s' + (i < 10 ? '0' : '') + i + '.jpg');
folder(pile);
await window.vaultScanFolder(false);
var mid = ledger(); mid['s01.jpg'] = { held: ['Shako'], unr: [], at: 7, world: 'main' };   /* a read landed meanwhile */
mid['other.jpg'] = { held: ['Grief'], unr: [], at: 8, world: 'main' };
RAW[SEEN_KEY] = JSON.stringify(mid);
window.vaultReadBatch(20);                               /* 🕐 Latest 20: reads 20, registers all 25 (v224) */
OUT.latest = CALLS.slice(); var L = ledger();
OUT.latestMarked = pile.filter(function(n){ return L[n] === 1 || L[n] === 'reading'; }).length;
OUT.latestReading = pile.filter(function(n){ return L[n] === 'reading'; }).length;
OUT.kept = [L['s01.jpg'], L['other.jpg']];
reset(); RAW[SEEN_KEY] = JSON.stringify({});
await window.vaultScanFolder(false); window.vaultReadBatch(0);   /* Skip — just register */
OUT.skipReads = CALLS.slice(); OUT.skipMarked = Object.keys(ledger()).length;
reset(); RAW[SEEN_KEY] = JSON.stringify({});
await window.vaultScanFolder(false); window.vaultReadBatch('new');
OUT.newReads = CALLS.slice(); OUT.newMarked = Object.keys(ledger()).length;
""")
        self.assertEqual(len(got["latest"]), 1)
        self.assertEqual(len(got["latest"][0]), 20)
        self.assertEqual(got["latestMarked"], 24, "🕐 Latest N no longer registers the new files (v224): %r" % got)
        self.assertEqual(got["latestReading"], 20, "REG-2524 - the 20 files 🕐 Latest 20 hands to the read are not marked "
                                                   "'reading' (the 4 it registers unread keep the bare 1): %r" % got)
        self.assertEqual(got["kept"][0]["held"], ["Shako"], "a pick wrote a bare mark over a record a read had written")
        self.assertEqual(got["kept"][1]["held"], ["Grief"], "a pick wrote the scan's stale snapshot over the ledger")
        self.assertEqual(got["skipReads"], [], "Skip made a read")
        self.assertEqual(got["skipMarked"], 25, "Skip no longer registers the new files (v224)")
        self.assertEqual(len(got["newReads"][0]), 25)
        self.assertEqual(got["newMarked"], 25)

    def test_the_poll_never_reads_a_gone_shot_and_reads_only_the_new_beside_it(self):
        got = _node(r"""
folder([%(gone)s]);
await window.vaultScanFolder(true);
OUT.alone = CALLS.slice(); OUT.aloneStatus = STATUS.slice();
reset();
folder([%(gone)s, 'new_1.jpg', 'new_2.jpg']);
await window.vaultScanFolder(true);
OUT.beside = CALLS.slice(); OUT.besideOpts = OPTS.slice(); OUT.besideStatus = STATUS.slice();
""" % {"gone": json.dumps(GONE)})
        self.assertEqual(got["alone"], [], "the 12 s poll re-read a gone screenshot on its own (v567's money loop)")
        self.assertTrue(any("hit 🔄 Scan folder to choose" in m for m in got["aloneStatus"]), got["aloneStatus"])
        self.assertEqual(got["beside"], [["new_1.jpg", "new_2.jpg"]], "the poll read the gone screenshot with the new ones")
        self.assertEqual(got["besideOpts"][0].get("goneWaiting"), 1)
        self.assertTrue(any("♻ 1 already-read screenshot" in m for m in got["besideStatus"]), got["besideStatus"])

    def test_the_folder_picker_marks_nothing_until_a_pick(self):
        got = _node(r"""
var F = [{ name: %(gone)s, lastModified: 1 }, { name: 'new_1.jpg', lastModified: 2 }, { name: 'new_2.jpg', lastModified: 3 }];
var before = RAW[SEEN_KEY];
window.vaultScanFolderLegacy(F);
OUT.menu = menu(); OUT.wroteAtMenu = RAW[SEEN_KEY] !== before;
window.vaultReadBatch('gone');
OUT.readAgain = CALLS.slice(); OUT.marked = Object.keys(ledger()).filter(function(k){ return /^new_/.test(k); });
reset();
window.vaultScanFolderLegacy(F);
OUT.again = menu();
""" % {"gone": json.dumps(GONE)})
        self.assertTrue(got["menu"]["shown"])
        self.assertEqual((got["menu"]["newCount"], got["menu"]["readAgain"]), ("2", "1"))
        self.assertFalse(got["wroteAtMenu"], "the picker's menu registered the new files before he chose")
        self.assertEqual(got["readAgain"], [[GONE]])
        self.assertEqual(got["marked"], [])
        self.assertEqual(got["again"]["newCount"], "2", "the picker lost the new files to the ♻ pick")


RED_PROOF = [
    {"why": "REG-2403 - a manual Scan with 1-12 new files goes to the menu again whenever a gone file waits",
     "file": "bible.html",
     "find": "      if (fresh.length > 0 && fresh.length <= 12){\n        if (_seenRegister(fresh, 'reading') < 0)",
     "replace": "      if (fresh.length > 0 && fresh.length <= 12 && !regone.length){\n        if (_seenRegister(fresh, 'reading') < 0)",
     "matches": 1},
    {"why": "REG-2403 - the menu registers the new screenshots the moment it appears, before he chooses",
     "file": "bible.html",
     "find": "    _pendingAll = all; _pendingFresh = fresh; _pendingGone = gone; _pendingWaiting = waiting;\n",
     "replace": "    _pendingAll = all; _pendingFresh = fresh; _pendingGone = gone; _pendingWaiting = waiting; _seenRegister(fresh);\n",
     "matches": 1},
    {"why": "REG-2403 - '♻ Read again' marks the new screenshots read without reading them",
     "file": "bible.html",
     "find": "    if (k !== 'gone' && k !== 'waiting'){\n",
     "replace": "    if (true){\n",
     "matches": 1},
    {"why": "REG-2403 - Skip and Latest N no longer register the new screenshots (v224's token guard)",
     "file": "bible.html",
     "find": "    if (k !== 'gone' && k !== 'waiting'){\n",
     "replace": "    if (k === 'new'){\n",
     "matches": 1},
    {"why": "REG-2403 - a pick writes a bare mark over a record a read wrote since the scan began",
     "file": "bible.html",
     "find": "      if (v && typeof v === 'object') return;      /* a record a read wrote since this scan began outranks a bare mark */\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2401/2403 - the 12 s poll reads a gone screenshot on its own (v567's money loop)",
     "file": "bible.html",
     "find": "        else if (_sv.state === 'gone') regone.push(f);   /* offered for his choice — the poll never reads it */\n",
     "replace": "        else if (_sv.state === 'gone') { seen[f.name] = 1; fresh.push(f); }\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
