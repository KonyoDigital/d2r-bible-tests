# -*- coding: utf-8 -*-
"""REG-2401 / REG-2405 - A FILE READ AGAIN IS THE SAME FILE: IT READS ONLY WHAT IT MAY, AND NEVER COUNTS A SECOND COPY
(the review of REG-2401, finding 4: what the REG-2401 laws promised with nothing that could fail).

REG-2401 lets a frame be read again once what it read has left the vault with no removal on record, and promised four
things about that read that only call-site TEXT pinned. The reviewer's sabotages, each left every REG-2401 node law green:
  M2  vaultIntake's filter also reads a file whose verdict is 'unknown' (owned or the journal would not read);
  M4  the base-copy branch counts a second copy off the same file (its `!_intakeSameItem(fRec.prev, n)` dropped);
  M5  the per-file line hands the read prev: null - the same-item guard is still THERE, and dead;
  M1  the 12 s poll reads a gone file on its own - held by tv/test_a_scan_reads_what_it_marks.py.
And REG-2405 adds one more promise: a label he RENAMED (his socket-count fix) and that a re-read reads again under its old
name is the renamed item, never a new one beside it.

WHAT THIS LAW HOLDS - the SHIPPED code cut whole from vaultIntake (its seen filter, its per-file line, the data.items
loop that adds / counts / collapses each read name, and the base-copy branch of the unrecognised loop) plus the
⟦INTAKE SEEN VERDICT⟧ block, run in node:
  * the filter reads exactly the 'fresh' and 'gone' files - never 'removed', 'unknown', 'retry', 'seen' or a legacy
    mark - and counts each; a folder batch is not re-filtered;
  * every file's perFile entry carries exactly _intakePrevOf(the ledger at the batch's start, that file);
  * a name the same file read last time never bumps a copy - a multi-keep staple under its target, a socketed base under
    the mule cap, or a base-like unrecognised read - while the SAME name off a DIFFERENT file still does (so the guard is
    not passing by never counting);
  * the old label of a renamed item, read again off the same file, is the renamed item; a name that silently left is
    still added back (the heal is not blocked); and the record a re-read writes keeps the rename;
  * the Last-scan card SAYS a file was read again (review M7, which only the CI spec caught) and says the gone
    screenshots a folder read left waiting for his choice (REG-2403).
A missing node raises: this law does not skip.
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
FILTER = ("    var _seenSkip = 0, _seenGone = 0, _seenRemoved = 0, _seenUnknown = 0;\n    if (!opts.fromFolder){\n",
          "        return false;\n      });\n")
PERFILE = ("    var _seenAt0 = (function(){ try { return seenLedger(); } catch(e){ return {}; } })();\n",
           "    try { _vPruneShots(100); }")
ITEMS_LOOP = ("        (data.items || []).forEach(function(n){\n", "        (data.unrecognized || []).forEach(function(n){\n")
NOTE = ("(function(){ var _it = logged.length + magicNew.length + unrec.length + cappedOut.length;\n",
        "          return parts.join(' · ') + ' — one shot can hold several items; duplicates never double-count.';\n"
        "        })()")
BASE_COPY = ("          var _cln = (typeof _throwClean==='function') ? _throwClean(n) : n;\n",
             "            return;   // 2nd copy counted (×N); already shown in the throw-out list\n          }\n")


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
var RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var SEEN_KEY = 'd2r_intakeSeen';
%(seenLedger)s
var owned = new Set(), magicFinds = {}, assign = {}, copies = {}, unknownReads = new Set();
var REMOVED = {}, UNREADABLE = {};
/* REG-2969 - REG-2890's per-file capture-time map, which the cut per-file and items code now writes and reads; no clock
   is no time (null), the shipped rule */
var _capAt = {};
function _capOf(fname){ return Object.prototype.hasOwnProperty.call(_capAt, fname) ? _capAt[fname] : null; }
window._vaultShotTime = function(){ return null; };
window._removedAfter = function(n, at){
  if (UNREADABLE[n]) return { unknown: 'the removal journal would not read' };
  return REMOVED[n] ? { at: at + 1, lane: 'card-click' } : null;
};
%(verdict)s
/* vaultIntake's seen filter, as it ships */
function runFilter(files, opts){
%(filter)s
    }
  return { files: files.map(function(f){ return f.name; }), skip: _seenSkip, gone: _seenGone, removed: _seenRemoved,
           unknown: _seenUnknown };
}
/* vaultIntake's per-file line, as it ships */
function makePerFile(files){
%(perfile)s
  return perFile;
}
/* the data.items loop, as it ships, over the board it touches */
var logged, dupes, unrec, extraCopies, cappedOut, witnessed, _ownedAtStart, _QTY_CAP = 3, MULTI = {};
function multiTarget(n){ return MULTI[n] || 1; }
window.EXTRA_ITEMS = { 'Monarch (4os)': { cat: 'Socketed bases' }, 'Monarch (Larzuk base)': { cat: 'Socketed bases' } };
window._ownedAdd = function(n){ var had = owned.has(n); owned.add(n); return { added: !had }; };
function _intakeRec(fname){ return { source: 'folder-photo', where: 'photo ' + fname }; }
function _intakeWitness(){ return { by: 'folder-photo' }; }
function suggestMule(){ return null; }
function muleById(){ return null; }
window.vaultFile = function(){ return { ok: true }; };
function fresh(){ logged = []; dupes = []; unrec = []; extraCopies = []; cappedOut = []; witnessed = [];
                  _ownedAtStart = new Set(Array.from(owned)); }
function readItems(data, fRec, fname){
%(items)s
}
/* the unrecognised loop's base-copy branch, as it ships */
function _baseCats(c){ return /monarch|thresher/i.test(c) ? { shield: 1 } : {}; }
function baseCopy(n, fRec){
%(basecopy)s
  return 'fell through';
}
function rec(o){ var b = { file: 'x', nw: [], own: [], unr: [], mf: [], err: false, prev: null }; for (var k in o) b[k] = o[k]; return b; }
/* the Last-scan card's note, as it ships, over the counters vaultIntake hands it */
function scanNote(c, opts){
  var files = c.files || [], magicNew = [], _emptyShots = [], _preReg = 1, _seenSkip = c.skip || 0, _seenGone = c.gone || 0;
  fresh();
  return %(note)s;
}
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
""" % {"seenLedger": _cut(s, SEEN_LEDGER), "verdict": _cut(s, VERDICT), "filter": _cut(s, FILTER),
       "perfile": _cut(s, PERFILE, inclusive_end=False), "items": _cut(s, ITEMS_LOOP, inclusive_end=False), "basecopy": _cut(s, BASE_COPY), "note": _cut(s, NOTE),
       "body": body}
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise AssertionError("the cut intake did not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


class AReReadIsTheSameFile(unittest.TestCase):

    def test_the_filter_reads_only_new_and_gone_files_and_counts_the_rest(self):
        got = _node(r"""
owned.add('Shako');
REMOVED['Grief'] = 1; UNREADABLE['Enigma'] = 1;
RAW[SEEN_KEY] = JSON.stringify({
  'gone.jpg':    { held: ['Death Loop'], unr: [], at: 10, world: 'main' },     /* left with nothing on record */
  'removed.jpg': { held: ['Grief'],      unr: [], at: 10, world: 'main' },     /* he removed it after the read */
  'unknown.jpg': { held: ['Enigma'],     unr: [], at: 10, world: 'main' },     /* whether he did is UNKNOWN */
  'seen.jpg':    { held: ['Shako'],      unr: [], at: 10, world: 'main' },     /* still his */
  'retry.jpg':   'retry', 'legacy.jpg': 1 });
var all = ['fresh.jpg', 'gone.jpg', 'removed.jpg', 'unknown.jpg', 'seen.jpg', 'retry.jpg', 'legacy.jpg']
  .map(function(n, i){ return { name: n, lastModified: i + 1 }; });
OUT.manual = runFilter(all.slice(), {});
OUT.folder = runFilter(all.slice(), { fromFolder: true });
""")
        m = got["manual"]
        self.assertEqual(m["files"], ["fresh.jpg", "gone.jpg"],
                         "vaultIntake read a file it must skip (or skipped one it must read): %r" % m["files"])
        self.assertEqual((m["skip"], m["gone"], m["removed"], m["unknown"]), (5, 1, 1, 1), "the counts it says are wrong: %r" % m)
        self.assertEqual(len(got["folder"]["files"]), 7, "a folder batch (already picked by his menu) was re-filtered")

    def test_every_file_carries_what_it_read_last_time(self):
        got = _node(r"""
RAW[SEEN_KEY] = JSON.stringify({
  'rec.jpg': { held: ['Monarch (4os)'], unr: ['Heavy Belt'], at: 10, world: 'main', as: { 'Monarch (Larzuk base)': 'Monarch (4os)' } },
  'legacy.jpg': 1 });
var files = [{ name: 'rec.jpg', lastModified: 1 }, { name: 'new.jpg', lastModified: 2 }, { name: 'legacy.jpg', lastModified: 3 }];
var pf = makePerFile(files), L = seenLedger();
OUT.prev = pf.map(function(p){ return p.prev; });
OUT.expected = files.map(function(f){ return _intakePrevOf(L, f); });
""")
        self.assertEqual(got["prev"], got["expected"], "a re-read is not handed what its file read last time")
        self.assertEqual(got["prev"][0], {"Monarch (4os)": 1, "Heavy Belt": 1, "Monarch (Larzuk base)": "Monarch (4os)"})
        self.assertIsNone(got["prev"][1])
        self.assertIsNone(got["prev"][2], "a legacy mark claimed to know what its file read")

    def test_a_reread_of_the_same_file_never_counts_a_second_copy(self):
        got = _node(r"""
owned.add('Arachnid Mesh'); MULTI['Arachnid Mesh'] = 3; copies['Arachnid Mesh'] = 1;   /* a multi-keep under target */
owned.add('Monarch (4os)'); copies['Monarch (4os)'] = 1;                               /* a socketed base, under the cap */
fresh(); var same = rec({ prev: { 'Arachnid Mesh': 1, 'Monarch (4os)': 1 } });
readItems({ items: ['Arachnid Mesh', 'Monarch (4os)'] }, same, 'shot_a.jpg');
OUT.same = { copies: JSON.parse(JSON.stringify(copies)), own: same.own, xc: same.xc || [] };
fresh(); var other = rec({ prev: null });                                                /* a DIFFERENT screenshot */
readItems({ items: ['Arachnid Mesh', 'Monarch (4os)'] }, other, 'shot_b.jpg');
OUT.other = { copies: JSON.parse(JSON.stringify(copies)), xc: other.xc || [] };
""")
        self.assertEqual(got["same"]["copies"], {"Arachnid Mesh": 1, "Monarch (4os)": 1},
                         "the same file read again counted a second copy: %r" % got["same"])
        self.assertEqual(sorted(got["same"]["own"]), ["Arachnid Mesh", "Monarch (4os)"])
        self.assertEqual(got["same"]["xc"], [])
        self.assertEqual(got["other"]["copies"], {"Arachnid Mesh": 2, "Monarch (4os)": 2},
                         "PREMISE: a different screenshot of the same name no longer counts a copy - the guard is vacuous")

    def test_a_base_read_off_the_same_file_is_never_a_second_copy(self):
        got = _node(r"""
fresh(); unknownReads.add('Thresher (4os)');
var r1 = baseCopy('Thresher (4os)', rec({ prev: { 'Thresher (4os)': 1 }, xc: [] }));
OUT.same = (r1 === undefined) ? 'counted' : r1; OUT.sameCopies = copies['Thresher (4os)'] || null;
var r2 = baseCopy('Thresher (4os)', rec({ prev: null, xc: [] }));
OUT.other = (r2 === undefined) ? 'counted' : r2; OUT.otherCopies = copies['Thresher (4os)'] || null;
""")
        self.assertEqual(got["same"], "fell through", "a base read off the same file counted a second copy")
        self.assertIsNone(got["sameCopies"])
        self.assertEqual(got["other"], "counted", "PREMISE: a base off a different file no longer counts - the guard is vacuous")
        self.assertEqual(got["otherCopies"], 2)

    def test_a_reread_of_a_label_he_renamed_is_the_renamed_item_and_a_loss_still_heals(self):
        got = _node(r"""
owned.add('Monarch (4os)');
fresh(); var f1 = rec({ prev: { 'Monarch (4os)': 1, 'Monarch (Larzuk base)': 'Monarch (4os)', 'Death Loop': 1 } });
readItems({ items: ['Monarch (Larzuk base)', 'Death Loop'] }, f1, 'shot_monarch.jpg');
OUT.renamed = { misreadBack: owned.has('Monarch (Larzuk base)'), own: f1.own, nw: f1.nw, healed: owned.has('Death Loop') };
fresh(); var f2 = rec({ prev: null });                                                 /* no record: a new screenshot */
readItems({ items: ['Monarch (Larzuk base)'] }, f2, 'shot_new.jpg');
OUT.unrelated = { added: owned.has('Monarch (Larzuk base)'), nw: f2.nw };
var seen = {};
owned.delete('Monarch (Larzuk base)');
_intakeSeenMark(seen, { name: 'shot_monarch.jpg', lastModified: 1 }, f1, _intakeSeenAsk());
OUT.record = seen['shot_monarch.jpg'];
owned.delete('Monarch (4os)');
var seen2 = {}; _intakeSeenMark(seen2, { name: 'shot_monarch.jpg', lastModified: 1 }, rec({ own: ['Shako'], prev: f1.prev }), _intakeSeenAsk());
OUT.dropped = seen2['shot_monarch.jpg'];
""")
        r = got["renamed"]
        self.assertFalse(r["misreadBack"], "a re-read put the misread label back beside the one he fixed")
        self.assertEqual(r["own"], ["Monarch (4os)"])
        self.assertEqual(r["nw"], ["Death Loop"], "the rename guard blocked a silent loss from healing: %r" % r)
        self.assertTrue(r["healed"])
        self.assertTrue(got["unrelated"]["added"], "PREMISE: a label read off another screenshot is no longer added")
        rec = got["record"]
        self.assertEqual(rec["held"], ["Death Loop", "Monarch (4os)"])
        self.assertEqual(rec.get("as"), {"Monarch (Larzuk base)": "Monarch (4os)"}, "a re-read forgot his rename: %r" % rec)
        self.assertNotIn("as", got["dropped"], "a rename was kept for a name the record no longer holds")

    def test_the_last_scan_card_says_what_it_read_again_and_what_still_waits(self):
        got = _node(r"""
OUT.again = scanNote({ files: [{}, {}], skip: 1, gone: 1 }, {});
OUT.waits = scanNote({ files: [{}] }, { fromFolder: true, goneWaiting: 2 });
OUT.quiet = scanNote({ files: [{}] }, { fromFolder: true });
""")
        self.assertIn("1 file read again", got["again"], "a file read again is not said: %r" % got["again"])
        self.assertIn("no removal on record", got["again"])
        self.assertIn("1 already-read file skipped", got["again"])
        self.assertIn("♻ 2 already-read screenshots wait in the folder for your choice", got["waits"],
                      "the gone screenshots a folder read left waiting are not said: %r" % got["waits"])
        self.assertNotIn("read again", got["quiet"])
        self.assertNotIn("wait", got["quiet"])


RED_PROOF = [
    {"why": "REG-2401 (review M7) - the Last-scan card no longer says a file was read again",
     "file": "bible.html",
     "find": "          if (_seenGone) parts.push(",
     "replace": "          if (false) parts.push(",
     "matches": 1},
    {"why": "REG-2403 - the Last-scan card no longer says the gone screenshots a folder read left waiting",
     "file": "bible.html",
     "find": "          if (opts.goneWaiting > 0) parts.push(",
     "replace": "          if (false) parts.push(",
     "matches": 1},
    {"why": "REG-2401 (review M2) - vaultIntake reads a file whose verdict is UNKNOWN (re-billed on a guess)",
     "file": "bible.html",
     "find": "        if (_sv.state === 'fresh' || _sv.state === 'reading') return true;",
     "replace": "        if (_sv.state === 'fresh' || _sv.state === 'reading' || _sv.state === 'unknown') return true;",
     "matches": 1},
    {"why": "REG-2401 - vaultIntake reads a file whose item HE removed, over his removal",
     "file": "bible.html",
     "find": "        if (_sv.state === 'fresh' || _sv.state === 'reading') return true;",
     "replace": "        if (_sv.state === 'fresh' || _sv.state === 'reading' || _sv.state === 'removed') return true;",
     "matches": 1},
    {"why": "v567 - vaultIntake reads a 'retry' file (the TV's fixed-name feed would re-bill every frame)",
     "file": "bible.html",
     "find": "        if (_sv.state === 'fresh' || _sv.state === 'reading') return true;",
     "replace": "        if (_sv.state === 'fresh' || _sv.state === 'reading' || _sv.state === 'retry') return true;",
     "matches": 1},
    {"why": "REG-2401 (review M5) - the per-file line hands a re-read prev: null, so the same-item guard is dead",
     "file": "bible.html",
     "find": "err: false, prev: _intakePrevOf(_seenAt0, f) }; });\n",
     "replace": "err: false, prev: null }; });\n",
     "matches": 1},
    {"why": "REG-2401 (review M4) - the base-copy branch counts a second copy off the same file",
     "file": "bible.html",
     "find": " && !owned.has(n) && !_intakeSameItem(fRec.prev, n)){",
     "replace": " && !owned.has(n)){",
     "matches": 1},
    {"why": "REG-2401 - an owned name the same file read last time bumps a copy (multi-keep / socketed base)",
     "file": "bible.html",
     "find": ("            if (_intakeSameItem(fRec.prev, n)) { if (dupes.indexOf(n) < 0) dupes.push(n); fRec.own.push(n); "
              "return; }\n"),
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - a re-read adds the misread label back beside the one he renamed",
     "file": "bible.html",
     "find": ("          if (_asNow && !owned.has(n) && owned.has(_asNow)) { if (dupes.indexOf(_asNow) < 0) dupes.push(_asNow); "
              "fRec.own.push(_asNow); return; }\n"),
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - the record a re-read writes forgets his rename",
     "file": "bible.html",
     "find": "    if (as) rec.as = as;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - what a file read last time leaves out the label he renamed",
     "file": "bible.html",
     "find": ("      Object.keys(v.as).forEach(function(o){ var t = v.as[o]; if (o && typeof t === 'string' && t && m[o] !== 1) "
              "m[o] = t; });\n"),
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
