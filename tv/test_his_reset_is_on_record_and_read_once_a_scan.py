# -*- coding: utf-8 -*-
"""REG-2528 (V1 round 3; the review of REG-2401 / REG-2405, minors) - HIS RESET UNIQUES IS HIS WORD ON RECORD, AND HIS
REMOVALS ARE READ ONCE A SCAN, NEVER ONCE A FILE.

1. RESET UNIQUES (window._uniqueResetDo) is a confirmed destructive act - its dialog says "N also lose their vault
   ownership row" - and it wrote d2r_owned whole with no journal row and no per-name note. REG-2401's verdict then read
   every screenshot that had read one of those uniques as 'gone' ("no removal on record" - false): a folder Scan offered
   it as '♻ Read again', and a dropped / TV-fed screenshot was read without asking - either way the unique came back
   over his reset. Reviewer (r3, the real journal helpers, the reset, the verdict and vaultIntake's filter): verdictBefore
   'seen'; after the reset journal=null, note=null, verdictAfter 'gone', and the drop read crest.jpg again. NOW each name
   the reset takes out of owned is noted per name (window._vaultRemovalNote, lane 'unique-reset'), so the verdict reads
   'removed' and nothing reads it again.
2. Every held name that had left owned asked _removedAfter once PER FILE, and each ask parsed both removal stores and
   folded every name in the ring: files x removed names on the main thread, on the 12 s poll and every Scan (measured on
   the merged tree: 288 ms at 300/300, 1.7 s at 1000/1000, 5.4 s at 2000/2000). NOW _intakeSeenAsk builds one index of
   his removals (window._removedAfterIndex: both stores read once through the one reader, keyed by the fold
   _removedAfter always compared on, the latest per key) on its first ask, and every file's ask reads that index
   (measured after: 8 / 18 / 27 ms, the same verdicts). This law COUNTS the reads, never a clock.

WHAT IS DRIVEN: the page's removal predicate and its helpers (_removalIsHisWord, _rmRead, _vaultRemovalNote,
_removedAfterIndex, _removedAfter), the ⟦INTAKE SEEN VERDICT⟧ block, vaultIntake's seen filter and _uniqueResetDo, cut
from bible.html, in node over a counting store. RED_PROOF below. A missing node is the only skip.
"""
import json
import os
import subprocess
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

JOURNAL = [
    ("  function _iso(ms){ try { return new Date(ms).toISOString(); }", "\n"),
    ("  function _ms(v){\n    if (typeof v === 'number') return (isFinite(v) && v > 0) ? v : null;", "\n  }\n"),
    ("  function _regName(nm){\n", "\n  }\n"),
    ("  function _bfJson(k, dflt){", "catch (e) { return undefined; } }\n"),
    ("  var _RM_NOT_HIS_WORD = ", "\n"),
    ("  window._removalIsHisWord = function(b){", "\n  };\n"),
    ("  var _RM_AT_KEY = ", "\n"),
    ("  function _rmRead(k, shape, dflt){", "\n  }\n"),
    ("  window._vaultRemovalNote = function(b){", "\n  };\n"),
    ("  window._removedAfterIndex = function(){", "\n  };\n"),
    ("  window._removedAfter = function(name, ts, index){", "\n  };\n"),
]
SEEN_LEDGER = ("  function seenLedger(){", "\n")
VERDICT = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")
FILTER = ("    var _seenSkip = 0, _seenGone = 0, _seenRemoved = 0, _seenUnknown = 0;\n    if (!opts.fromFolder){\n",
          "        return false;\n      });\n")
RESET = ("window._uniqueResetDo = function(plan){\n", "\n};\n")


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j + len(end)]


def _run(body):
    if D.NODE is None:
        raise AssertionError("node is absent")
    s = D.src()
    js = r"""
var window = globalThis;
var RAW = {}, READS = {};
window.LSR = { getItem: function(k){ READS[k] = (READS[k] || 0) + 1; return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var LS = window.LSR, SEEN_KEY = 'd2r_intakeSeen';
var _cnV = function(x){ return String(x||'').replace(/[‘’`]/g, "'").toLowerCase().trim().replace(/\s*\([^)]*\)\s*$/,'').trim(); };
%(journal)s
%(seen)s
var owned = new Set(), magicFinds = {};
%(verdict)s
function runFilter(files, opts){
  var report = { hidden: true, innerHTML: '' };
%(filter)s
    }
  return files.map(function(f){ return f.name; });
}
%(reset)s
window._GRAIL_SEED = {}; window._seedsBelongHere = false;
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
""" % {"journal": "\n".join(_cut(s, p) for p in JOURNAL), "seen": _cut(s, SEEN_LEDGER), "verdict": _cut(s, VERDICT),
       "filter": _cut(s, FILTER), "reset": _cut(s, RESET), "body": body}
    r = subprocess.run([D.NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    if r.returncode != 0:
        raise AssertionError("the shipped code would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED journal and verdict; UNMEASURED, not passing")
class HisResetIsOnRecordAndReadOnceAScan(unittest.TestCase):

    def test_his_unique_reset_is_his_word_so_the_screenshot_that_read_it_is_never_read_again(self):
        o = _run(r"""
window._gUniqueRoster = function(){ return ['Harlequin Crest']; };
owned = new Set(['Harlequin Crest', 'Shako']);
RAW['d2r_owned'] = JSON.stringify(Array.from(owned));
RAW['d2r_foundLog'] = JSON.stringify({ 'Harlequin Crest': '2026-10-01' });
var seen = {};
_intakeSeenMark(seen, { name: 'crest.jpg', lastModified: 1 }, { nw: ['Harlequin Crest'], own: [], unr: [], mf: [], err: false }, _intakeSeenAsk());
RAW[SEEN_KEY] = JSON.stringify(seen);
OUT.before = _intakeSeenVerdict(seenLedger(), { name: 'crest.jpg', lastModified: 1 }, _intakeSeenAsk()).state;
var t = Date.now() + 3; while (Date.now() < t) {}
OUT.reset = window._uniqueResetDo({ names: ['Harlequin Crest'] });
owned = new Set(JSON.parse(RAW['d2r_owned']));                     /* the reload reads the store */
OUT.owned = Array.from(owned);
OUT.note = RAW['d2r_vaultRemovedAt'] ? JSON.parse(RAW['d2r_vaultRemovedAt']) : null;
OUT.after = _intakeSeenVerdict(seenLedger(), { name: 'crest.jpg', lastModified: 1 }, _intakeSeenAsk()).state;
OUT.dropReads = runFilter([{ name: 'crest.jpg', lastModified: 1 }], {});
""")
        self.assertEqual(o["before"], "seen", "PREMISE: the screenshot did not read as still his before the reset")
        self.assertTrue(o["reset"]["ok"], o["reset"])
        self.assertEqual(o["owned"], ["Shako"], "PREMISE: the reset no longer takes the unique out of owned")
        self.assertIsNotNone(o["note"], "his reset left no removal on record")
        rec = o["note"].get("harlequin crest")
        self.assertTrue(rec and rec.get("lane") == "unique-reset", "the reset's note is not his word: %r" % o["note"])
        self.assertEqual(o["after"], "removed", "the verdict reads his reset as a silent loss ('%s')" % o["after"])
        self.assertEqual(o["dropReads"], [], "a dropped screenshot was read again over his reset")

    def test_his_removals_are_read_once_a_scan_not_once_a_file(self):
        o = _run(r"""
var T0 = 1790000000000, NF = 300, seen = {}, noted = {}, ring = [];
for (var i = 0; i < NF; i++){ seen['shot_' + i + '.jpg'] = { held: ['Item ' + i + ' A', 'Item ' + i + ' B'], unr: [], at: T0 + i, world: 'main' };
                             owned.add('Item ' + i + ' B');
                             noted[_cnV('Item ' + i + ' A')] = { at: T0 + 10000000 + i, lane: 'card-click', frame: null }; }
for (var b = 0; b < 20; b++){ var names = []; for (var k = 0; k < 150; k++) names.push('Other ' + b + '-' + k);
  ring.push({ ts: T0 + 20000000 + b, names: names, lane: 'clear-unsorted', filed: {}, prov: {} }); }
RAW['d2r_vaultRemovedAt'] = JSON.stringify(noted); RAW['d2r_vaultRemoved'] = JSON.stringify(ring); RAW[SEEN_KEY] = JSON.stringify(seen);
var L = seenLedger(), ask = _intakeSeenAsk(), states = {};
READS = {};
for (var i = 0; i < NF; i++){ var v = _intakeSeenVerdict(L, { name: 'shot_' + i + '.jpg', lastModified: 1 }, ask); states[v.state] = (states[v.state] || 0) + 1; }
OUT.reads = { ring: READS['d2r_vaultRemoved'] || 0, noted: READS['d2r_vaultRemovedAt'] || 0 };
OUT.states = states;
READS = {};
var again = _intakeSeenAsk();                                     /* the next scan reads them afresh */
_intakeSeenVerdict(L, { name: 'shot_0.jpg', lastModified: 1 }, again);
OUT.next = { ring: READS['d2r_vaultRemoved'] || 0, noted: READS['d2r_vaultRemovedAt'] || 0 };
""")
        self.assertEqual(o["states"], {"removed": 300}, "PREMISE: the verdicts changed - %r" % o["states"])
        self.assertLessEqual(o["reads"]["ring"], 1, "the removal journal was read %d times in one scan of 300 files"
                             % o["reads"]["ring"])
        self.assertLessEqual(o["reads"]["noted"], 1, "the per-name removal record was read %d times in one scan"
                             % o["reads"]["noted"])
        self.assertEqual(o["next"], {"ring": 1, "noted": 1}, "the next scan did not read his removals afresh: %r" % o["next"])


RED_PROOF = [
    {"why": "REG-2528 - RESET UNIQUES takes uniques out of owned with no removal on record (the verdict reads 'gone')",
     "file": "bible.html", "matches": 1,
     "find": "    if (_gone.length && _ownW !== false && typeof window._vaultRemovalNote === 'function'){\n",
     "replace": "    if (false){\n"},
    {"why": "REG-2528 - every file's ask reads both removal stores again (files x removed names on the poll)",
     "file": "bible.html", "matches": 1,
     "find": "        if (_rmIdx === null && typeof window._removedAfterIndex === 'function'){\n",
     "replace": "        if (false){\n"},
    {"why": "REG-2528 - _removedAfter ignores the scan's index and builds its own",
     "file": "bible.html", "matches": 1,
     "find": "    var I = (index && (index.idx || index.unknown)) ? index : window._removedAfterIndex();\n",
     "replace": "    var I = window._removedAfterIndex();\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
