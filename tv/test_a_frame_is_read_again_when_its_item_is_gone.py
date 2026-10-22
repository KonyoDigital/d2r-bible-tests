# -*- coding: utf-8 -*-
"""REG-2401 (#162 item 2) - A FRAME IS SKIPPED WHILE WHAT IT READ IS STILL HIS, AND READ AGAIN WHEN IT IS GONE.

GrokBot #230 on v3783 (292 of his real frames, headless): after one reload took 159 of 272 owned names, re-feeding all
292 frames added 0 ("ok 0"). Every frame said "already read", so the loss could never heal. d2r_intakeSeen keyed the skip
on "this file was ever read": the ledger held 1 for a file that read something, which says THAT it read and never WHAT,
so nothing could ask whether the item was still his.

Now a file that read something records what it put in the vault ({held, unr, at}), and the skip asks the vault:
  * every held name still owned (or in MAGIC & RARE)   -> 'seen'     skipped, free, exactly as before
  * a held name is gone and HE removed it afterwards    -> 'removed'  skipped: his removal stands
  * a held name is gone with no removal on record       -> 'gone'     read again - the loss heals
  * what is owned, or whether he removed it, is unknown -> 'unknown'  skipped and said, never guessed
  * a 1 / a number / a name|mtime key from before        -> 'seen'     what it read is UNKNOWN, so nothing is re-billed
  * 'retry' (read nothing)                               -> 'retry'    unchanged (v567)
A file read again is the same file: a name it read last time is never a second copy.

WHAT THIS LAW HOLDS - the SHIPPED ⟦INTAKE SEEN VERDICT⟧ block cut from bible.html and run in node: GrokBot's own frame
(f_1790549355102.jpg read "Death Loop") through mark -> skip -> silent loss -> read again; his removal; UNKNOWN; every
legacy mark; and the four call sites (vaultIntake's filter and its marking, both folder scans) asking this one verdict.
A missing node raises: this law does not skip. The browser half is tests/reg2400_reload_keeps_what_he_owns.spec.ts (CI).
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
BLOCK = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")

#: the call sites - each must ask the one verdict, by its full line [[source-reading-guard]]
SITES = {
    "vaultIntake's filter": "        var _sv = _intakeSeenVerdict(_seenL, f, _seenAsk);   /* REG-2401 — keyed on \"is what it read "
                            "still his\", not \"was it ever read\" */\n",
    "vaultIntake reads a gone file": "        if (_sv.state === 'gone') { _seenGone++; return true; }\n",
    "vaultIntake's marking": "      files.forEach(function(f, i){ _intakeSeenMark(_sNow, f, perFile[i], _sAskM); });\n",
    "the watched folder": "        var _sv = _intakeSeenVerdict(seen, f, _sAsk);\n",
    "the folder picker": "        var _sv = _intakeSeenVerdict(seen, f, _sAsk);   // REG-2401 — the same verdict the watched folder asks\n",
    "the same item, never a 2nd copy": "            if (_intakeSameItem(fRec.prev, n)) { if (dupes.indexOf(n) < 0) dupes.push(n); "
                                       "fRec.own.push(n); return; }\n",
}
#: the old key - "a name ever read" - must not come back
OLD_SKIP = "if (_seenL[f.name] || _seenL[f.name + '|' + f.lastModified])"

FRAME = "f_1790549355102.jpg"   # one of the frames GrokBot names in #162 (reel_s_1790547071068_56270)


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    return s[i:s.index(end, i) + len(end)]


def _node(body):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    js = r"""
var window = globalThis;
var owned = new Set(), magicFinds = {}, REMOVED = {}, REMOVED_UNKNOWN = false;
/* the page's removal rule, as a stand-in: a removal AFTER the read is his word about it */
window._removedAfter = function(n, at){
  if (REMOVED_UNKNOWN) return { unknown: 'the removal journal would not read' };
  var r = REMOVED[n]; if (!r) return null;
  return (at != null && at > r.at) ? null : { at: r.at, lane: 'manual' };
};
%s
var OUT = {};
var F = { name: %s, lastModified: 1790549355102 };
function fr(o){ var b = { nw: [], own: [], unr: [], mf: [], err: false }; for (var k in o) b[k] = o[k]; return b; }
%s
process.stdout.write(JSON.stringify(OUT));
""" % (_cut(_src(), BLOCK), json.dumps(FRAME), body)
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise AssertionError("the cut verdict did not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


class AFrameIsReadAgainWhenItsItemIsGone(unittest.TestCase):

    def test_grokbots_frame_is_skipped_while_owned_and_read_again_once_silently_lost(self):
        got = _node("""
var seen = {}; seen[F.name + '|' + F.lastModified] = 1;     /* a stale name|mtime key from an older read */
owned.add('Death Loop');
_intakeSeenMark(seen, F, fr({ nw: ['Death Loop'] }), _intakeSeenAsk());
OUT.rec = seen[F.name]; OUT.staleKey = (F.name + '|' + F.lastModified) in seen;
OUT.whileOwned = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
owned.delete('Death Loop');                                  /* the reload's silent drop: no removal on record */
var v = _intakeSeenVerdict(seen, F, _intakeSeenAsk());
OUT.afterLoss = v.state; OUT.gone = v.gone; OUT.prev = v.prev;
""")
        self.assertEqual(got["rec"]["held"], ["Death Loop"], "the ledger did not record what the frame put in the vault")
        self.assertIsInstance(got["rec"]["at"], (int, float))
        self.assertFalse(got["staleKey"], "a stale name|mtime key outranks the record")
        self.assertEqual(got["whileOwned"], "seen", "a frame whose item is still his was not skipped")
        self.assertEqual(got["afterLoss"], "gone", "a frame whose item silently left is still 'already read'")
        self.assertEqual(got["gone"], ["Death Loop"])
        self.assertEqual(got["prev"], {"Death Loop": 1})

    def test_his_removal_stands_and_unknown_is_never_a_reread(self):
        got = _node("""
var seen = {}; owned.add('Death Loop');
_intakeSeenMark(seen, F, fr({ nw: ['Death Loop'] }), _intakeSeenAsk());
owned.delete('Death Loop');
REMOVED['Death Loop'] = { at: seen[F.name].at + 1000 };
OUT.removedAfter = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
REMOVED['Death Loop'] = { at: seen[F.name].at - 1000 };      /* removed BEFORE this read: the read is newer, the loss silent */
OUT.removedBefore = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
REMOVED_UNKNOWN = true;
OUT.journalUnreadable = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
REMOVED_UNKNOWN = false;
OUT.ownedUnreadable = _intakeSeenVerdict(seen, F, { held: function(){ return null; }, removedAfter: window._removedAfter }).state;
OUT.heldThrows = _intakeSeenVerdict(seen, F, { held: function(){ throw new Error('x'); }, removedAfter: window._removedAfter }).state;
owned = undefined;
OUT.noOwnedSet = _intakeSeenAsk().held('Death Loop');
""")
        self.assertEqual(got["removedAfter"], "removed", "his removal after the read was overridden by a re-read")
        self.assertEqual(got["removedBefore"], "gone", "a removal older than the read hid a later silent loss")
        self.assertEqual(got["journalUnreadable"], "unknown", "an unreadable removal journal read as 'gone'")
        self.assertEqual(got["ownedUnreadable"], "unknown", "an owned list that cannot answer read as 'gone'")
        self.assertEqual(got["heldThrows"], "unknown")
        self.assertIsNone(got["noOwnedSet"], "no owned set on the page answered false instead of UNKNOWN")

    def test_every_older_mark_keeps_its_old_meaning(self):
        got = _node("""
function v(seen){ return _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state; }
var k = {}; k[F.name + '|' + F.lastModified] = 1;
var o = {}; o[F.name] = 1; var n = {}; n[F.name] = 123; var z = {}; z[F.name] = 0; var r = {}; r[F.name] = 'retry';
OUT.one = v(o); OUT.num = v(n); OUT.zero = v(z); OUT.retry = v(r); OUT.mtimeKey = v(k); OUT.absent = v({});
OUT.oldPrev = _intakePrevOf(o, F);
""")
        self.assertEqual(got["one"], "seen", "a 1 written before records existed is re-billed")
        self.assertEqual(got["num"], "seen")
        self.assertEqual(got["mtimeKey"], "seen", "an old name|mtime key is no longer honoured (v222)")
        self.assertEqual(got["zero"], "fresh")
        self.assertEqual(got["absent"], "fresh")
        self.assertEqual(got["retry"], "retry", "v567's soft retry mark changed meaning")
        self.assertIsNone(got["oldPrev"], "a legacy mark claimed to know what the file read")

    def test_a_record_is_one_worlds_and_ladder_never_rereads_mains_history(self):
        # ladder seeds its ledger ONCE from main's (v636/v684); main's items are not ladder's
        got = _node("""
var seen = {}; owned.add('Death Loop');
_intakeSeenMark(seen, F, fr({ nw: ['Death Loop'] }), _intakeSeenAsk());
OUT.world = seen[F.name].world;
owned.delete('Death Loop');
window.D2R_PROFILE = 'ladder';
OUT.onLadder = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
window.D2R_PROFILE = 'main';
OUT.onMain = _intakeSeenVerdict(seen, F, _intakeSeenAsk()).state;
var noWorld = {}; noWorld[F.name] = { held: ['Death Loop'], unr: [], at: 1 };
OUT.noWorld = _intakeSeenVerdict(noWorld, F, _intakeSeenAsk()).state;
""")
        self.assertEqual(got["world"], "main", "a record does not say which world read it")
        self.assertEqual(got["onLadder"], "seen", "ladder re-reads main's history off the seeded ledger")
        self.assertEqual(got["onMain"], "gone")
        self.assertEqual(got["noWorld"], "gone", "a record with no world is not judged on what it read")

    def test_what_a_read_records(self):
        got = _node("""
var seen = {};
owned.add('Gothic Shield (3os)'); owned.add('Grief'); magicFinds['Jewel of Daring'] = { q: 'magic' };
_intakeSeenMark(seen, { name: 'nothing.jpg', lastModified: 1 }, fr({}), _intakeSeenAsk());
_intakeSeenMark(seen, { name: 'failed.jpg', lastModified: 1 }, fr({ nw: ['Grief'], err: true }), _intakeSeenAsk());
_intakeSeenMark(seen, { name: 'copy.jpg', lastModified: 1 }, fr({ xc: ['Gothic Shield (3os)'] }), _intakeSeenAsk());
_intakeSeenMark(seen, { name: 'magic.jpg', lastModified: 1 }, fr({ mf: ['Jewel of Daring'] }), _intakeSeenAsk());
_intakeSeenMark(seen, { name: 'junk.jpg', lastModified: 1 }, fr({ unr: ['Heavy Belt'] }), _intakeSeenAsk());
_intakeSeenMark(seen, { name: 'mixed.jpg', lastModified: 1 }, fr({ nw: ['Grief'], unr: ['Heavy Belt'], xc: ['Not Owned Base'] }), _intakeSeenAsk());
OUT.seen = seen;
OUT.junkVerdict = _intakeSeenVerdict(seen, { name: 'junk.jpg', lastModified: 1 }, _intakeSeenAsk()).state;
OUT.magicVerdict = _intakeSeenVerdict(seen, { name: 'magic.jpg', lastModified: 1 }, _intakeSeenAsk()).state;
var p = _intakePrevOf(seen, { name: 'mixed.jpg' });
OUT.same = [_intakeSameItem(p, 'Grief'), _intakeSameItem(p, 'Heavy Belt'), _intakeSameItem(p, 'Enigma'), _intakeSameItem(null, 'Grief')];
""")
        s = got["seen"]
        self.assertEqual(s["nothing.jpg"], "retry", "a read of nothing is no longer a soft retry mark (v567)")
        self.assertEqual(s["failed.jpg"], "retry", "a failed read was recorded as read")
        self.assertEqual(s["copy.jpg"]["held"], ["Gothic Shield (3os)"], "an extra copy is not a read")
        self.assertEqual(s["magic.jpg"]["held"], ["Jewel of Daring"], "a MAGIC & RARE keeper is not 'held'")
        self.assertEqual(s["junk.jpg"]["held"], [], "a throw-out was recorded as his item")
        self.assertEqual(s["junk.jpg"]["unr"], ["Heavy Belt"])
        self.assertEqual(s["mixed.jpg"]["held"], ["Grief"], "a name not in the vault was recorded as held")
        self.assertEqual(got["junkVerdict"], "seen", "a frame that read only throw-outs is read again forever")
        self.assertEqual(got["magicVerdict"], "seen", "a keeper held in MAGIC & RARE read as gone")
        self.assertEqual(got["same"], [True, True, False, False], "the same-file rule is wrong: %r" % got["same"])

    def test_every_door_asks_this_verdict_and_the_old_key_is_gone(self):
        s = _src()
        for where, line in SITES.items():
            self.assertEqual(s.count(line), 1, "%s does not ask the one verdict (by its line)" % where)
        self.assertEqual(s.count(OLD_SKIP), 0, "vaultIntake skips by 'a name ever read' again")


RED_PROOF = [
    {"why": "REG-2401 - a frame whose item silently left is never read again (the dedupe keys on 'ever read')",
     "file": "bible.html",
     "find": "      else gone.push(n);\n",
     "replace": "      else removed.push(n);\n",
     "matches": 1},
    {"why": "REG-2401 - a re-read overrides his removal",
     "file": "bible.html",
     "find": "      else if (r) removed.push(n);\n",
     "replace": "      else if (r) gone.push(n);\n",
     "matches": 1},
    {"why": "REG-2401 - a file that read something is marked 1 again: what it read is never recorded",
     "file": "bible.html",
     "find": "    seen[f.name] = some ? _intakeSeenRecord(fr, ask) : 'retry';\n",
     "replace": "    seen[f.name] = some ? 1 : 'retry';\n",
     "matches": 1},
    {"why": "REG-2401 - an owned list that cannot answer reads as 'gone' and re-bills the frame",
     "file": "bible.html",
     "find": "      if (h !== false){ unknown.push(n); return; }\n",
     "replace": "      if (h !== false && h !== null){ unknown.push(n); return; }\n",
     "matches": 1},
    {"why": "REG-2401 - the same file read again counts a second copy",
     "file": "bible.html",
     "find": "  function _intakeSameItem(prev, n){ return !!(prev && typeof n === 'string' && prev[n] === 1); }\n",
     "replace": "  function _intakeSameItem(prev, n){ return false; }\n",
     "matches": 1},
    {"why": "REG-2401 - ladder re-reads main's whole history off the ledger it seeded from main",
     "file": "bible.html",
     "find": "    if (v.world != null && ask && ask.world != null && v.world !== ask.world)\n",
     "replace": "    if (false)\n",
     "matches": 1},
    {"why": "REG-2401 - vaultIntake skips a gone file again",
     "file": "bible.html",
     "find": "        if (_sv.state === 'gone') { _seenGone++; return true; }\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
