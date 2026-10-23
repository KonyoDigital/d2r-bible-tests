# -*- coding: utf-8 -*-
"""REG-2529 (V1 round 3; the review of REG-2405 r4 and of REG-2401, minors) - A RE-READ BRINGS BACK HIS FIX, NEVER THE
MISREAD, AND A SCREENSHOT READ BEFORE RECORDS EXISTED IS SAID FOR WHAT IT IS.

1. His socket-count fix (vaultFixSockets) RENAMES a misread label - 'Monarch (Larzuk base)' -> 'Monarch (4os)' - and
   tells the scan ledger (the record holds the new name and keeps the old under `as`). REG-2405's guard stopped a re-read
   from adding the misread label back only WHILE the renamed item is still owned. When the renamed item itself is the
   silent loss the verdict exists to heal, the '♻ Read again' of the same file added the MISREAD label back, his fix was
   lost, and the record it wrote dropped `as` - the board kept the label he corrected, for good. Reviewer (r4, the shipped
   data.items loop): owned ['Monarch (Larzuk base)'], recordAfter with no `as`. NOW the re-read brings back HIS label and
   the record keeps `as`, because the label it maps to is held again.
2. Every mark in his current ledger is a bare 1 written before records existed, and a bare 1 reads 'seen' for ever - yet
   the "Nothing new" card said "A file is read again once what it read has left your vault with no removal on record",
   false for every such file. NOW the card counts them and says they are never read again on their own, and the note says
   which files are read again (a file with a record) and which are not.

WHAT IS DRIVEN: (1) the SHIPPED data.items loop, the per-file line and the verdict block, through
tv/test_a_reread_is_the_same_file.py's own harness (the cut it already proves); (2) vaultIntake's seen filter with its
"Nothing new" card and the verdict block, cut from bible.html, in node. RED_PROOF below. A missing node is the only skip.
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
import test_a_reread_is_the_same_file as RR  # noqa: E402  (its harness runs the shipped data.items loop)

VERDICT = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")
SEEN_LEDGER = ("  function seenLedger(){", "\n")
CARD = ("    var _seenSkip = 0, _seenGone = 0, _seenRemoved = 0, _seenUnknown = 0;\n    if (!opts.fromFolder){\n",
        "    var _seenAt0 = (function(){ try { return seenLedger(); } catch(e){ return {}; } })();\n")


def _cut(s, pair, inclusive_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j + (len(end) if inclusive_end else 0)]


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED intake; UNMEASURED, not passing")
class ARenamedItemComesBackAsHisFix(unittest.TestCase):

    def test_the_reread_of_a_renamed_item_that_left_brings_back_his_label_and_keeps_the_rename(self):
        got = RR._node(r"""
RAW[SEEN_KEY] = JSON.stringify({ 'shot_monarch.jpg': { held: ['Monarch (4os)'], unr: [], at: 10, world: 'main',
                                                       as: { 'Monarch (Larzuk base)': 'Monarch (4os)' } } });
OUT.verdict = _intakeSeenVerdict(seenLedger(), { name: 'shot_monarch.jpg', lastModified: 1 }, _intakeSeenAsk()).state;
var pf = makePerFile([{ name: 'shot_monarch.jpg', lastModified: 1 }]);
fresh(); readItems({ items: ['Monarch (Larzuk base)'] }, pf[0], 'shot_monarch.jpg');
OUT.owned = Array.from(owned); OUT.nw = pf[0].nw;
var seen = seenLedger();
_intakeSeenMark(seen, { name: 'shot_monarch.jpg', lastModified: 1 }, pf[0], _intakeSeenAsk());
OUT.recordAfter = seen['shot_monarch.jpg'];
/* the control: a name that is NOT a rename, silently gone, is still added back as read */
fresh(); var pf2 = makePerFile([{ name: 'shot_grief.jpg', lastModified: 2 }]);
readItems({ items: ['Grief'] }, pf2[0], 'shot_grief.jpg');
OUT.plain = owned.has('Grief');
""")
        self.assertEqual(got["verdict"], "gone", "PREMISE: the renamed item's loss does not read 'gone'")
        self.assertIn("Monarch (4os)", got["owned"], "the re-read did not bring back his corrected label")
        self.assertNotIn("Monarch (Larzuk base)", got["owned"], "the re-read added the MISREAD label back over his fix")
        self.assertEqual(got["nw"], ["Monarch (4os)"])
        self.assertEqual((got["recordAfter"] or {}).get("as"), {"Monarch (Larzuk base)": "Monarch (4os)"},
                         "the record the re-read wrote forgot his rename: %r" % got["recordAfter"])
        self.assertTrue(got["plain"], "PREMISE: the heal no longer adds a silently lost name back")

    def test_the_nothing_new_card_says_which_files_are_never_read_again(self):
        s = D.src()
        js = r"""
var window = globalThis;
var RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var SEEN_KEY = 'd2r_intakeSeen';
function esc(x){ return String(x); }
function _seenUnknownSay(){ return 'UNKNOWN'; }
%(seen)s
var owned = new Set(['Shako']), magicFinds = {};
window._removedAfter = function(){ return null; };
%(verdict)s
function card(files, opts){
  var report = { hidden: true, innerHTML: '' }, _preReg = 1;
  (function(){
%(card)s
  })();
  return report.innerHTML;
}
RAW[SEEN_KEY] = JSON.stringify({ 'old_1.jpg': 1, 'old_2.jpg': 1, 'rec.jpg': { held: ['Shako'], unr: [], at: 10, world: 'main' } });
var OUT = { legacy: card([{ name: 'old_1.jpg', lastModified: 1 }, { name: 'old_2.jpg', lastModified: 2 }], {}),
            recorded: card([{ name: 'rec.jpg', lastModified: 3 }], {}) };
process.stdout.write(JSON.stringify(OUT));
""" % {"seen": _cut(s, SEEN_LEDGER), "verdict": _cut(s, VERDICT), "card": _cut(s, CARD, inclusive_end=False)}
        r = subprocess.run([D.NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped filter would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        o = json.loads(r.stdout)
        self.assertIn("Nothing new to read", o["legacy"], "PREMISE: the card did not show")
        # REG-2529 fix round - a bare mark is also Skip's / Latest N's unread registration: said as what is known
        self.assertIn("<b>2</b> of them were registered without a record of what each read", o["legacy"],
                      "the card does not say the files registered without a record: %r" % o["legacy"][-500:])
        self.assertNotIn("were read before this board kept a record", o["legacy"],
                         "the card still says files Skip registered unread were read")
        self.assertIn("never read again on their own", o["legacy"])
        self.assertIn("a file registered without a record is not", o["legacy"],
                      "the note still claims every file is read again once its item leaves")
        self.assertNotIn("registered without a record of what each read", o["recorded"],
                         "a file with a record was counted as one registered without a record")


RED_PROOF = [
    {"why": "REG-2529 - a re-read of a renamed item that left adds the MISREAD label back over his socket-count fix",
     "file": "bible.html", "matches": 1,
     "find": "          if (_asNow && !owned.has(n) && !owned.has(_asNow)) n = _asNow;\n",
     "replace": ""},
    {"why": "REG-2529 - the Nothing-new card hides the files read before records existed",
     "file": "bible.html", "matches": 1,
     "find": "          + (_seenLegacy ? '<span class=\"vir-rc\"><b>' + _seenLegacy + '</b> of them were registered without a record of what each read (read before records existed, or registered unread by Skip / 🕐 Latest N) — they are never read again on their own</span>' : '')\n",
     "replace": ""},
    {"why": "REG-2529 - the filter no longer counts a legacy mark",
     "file": "bible.html", "matches": 1,
     "find": "        else if (_sv.legacy) _seenLegacy++;\n        return false;\n",
     "replace": "        return false;\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
