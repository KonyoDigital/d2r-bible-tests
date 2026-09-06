# -*- coding: utf-8 -*-
"""v2699 — THE UN-SEED IS DESTRUCTIVE, IRREVERSIBLE-IF-WRONG, AND HAD NO TEST AT ALL.

`window._d2rUnseed` deletes seeded entries out of a person's chronicle. Until v2699 a code review
found four separate ways it did not do what its own dialog said, and `grep -rn '_d2rUnseed'
tests/ tv/` returned nothing. The previous version of this same control shipped COMPLETELY INERT —
an apostrophe in "Gloom's Trap" terminated its `onclick="…"` attribute, so `onclick` was an object
rather than a function, the button rendered, looked right, and did nothing. That was caught by
luck, not by a gate.

=== THE FOUR DEFECTS THIS PINS, each one measured before it was fixed ===

1. THE PROMISED UNDO DID NOT EXIST. The confirm said "a full backup is saved first so this can be
   undone". `d2r_unseedBackup` was written in exactly ONE place and read in NONE. Measured:
   `grep -rn d2r_unseedBackup .` -> a single hit, the write itself.

2. IT WAS IRREVERSIBLE ON KONYO'S OWN BOARD, which is where it is most dangerous. His
   `d2r_ledgerName` is unset, so `_D2R_LEDGER` falls through to the has-a-chronicle heuristic and
   answers 'KonyoEndgame' — that is why his floors restore. The un-seed's write of
   `d2r_ledgerName` lands in the resolver's FIRST branch (`if (n) return n`), so one click made
   `_seedsBelongHere` false forever and the 245 grail entries it had just deleted could never come
   back. The dialog said "press Cancel"; the code comment told the next reader it was self-healing.

3. THE NAME WAS WRITTEN LAST, after every destructive step. Any throw in between — a quota
   rejection on one of the JSON.stringify writes — left a store that was stripped AND unnamed,
   which re-seeds on the next load, with the v1692 one-shot flag already deleted so that migration
   re-fired too.

4. TWO STORES WERE BACKED UP AND NEVER STRIPPED. `d2r_rwVerify` kept the owner's seeded
   Mania/Hysteria "fail" verdicts (and because the seed only writes when the key is NULL, renaming
   the ledger could not clear them either). `d2r_owned` matters because `_ownedNames()` is
   `new Set(d2r_owned)` UNIONED with the foundLog keys, so inherited names there still counted as
   found and the board could not reach the number the button promises.

=== WHAT THIS FILE CAN AND CANNOT SETTLE ===
These are SOURCE laws — order, presence, wiring. The behavioural half needs a browser and lives on
CI, never on his Mac. A source gate cannot prove the strip removes the right rows; it CAN prove the
undo has a reader, that the name is written before the destruction, and that every store the
snapshot carries is one the restore puts back. Those are exactly the four things that were wrong,
and every one of them is decidable from the file. [[the-unjoined-end]]
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")

# every store the snapshot carries must be one the restore can put back
BACKED_UP = ["d2r_foundLog", "d2r_setPieces", "d2r_rwMade", "d2r_owned",
             "d2r_rwVerify", "d2r_v1692FleshrenderApplied"]


def _src():
    return io.open(BIBLE, encoding="utf-8").read()


def _node():
    """-> a usable node binary, or FAIL. A skip here would be recorded as a PASS.

    ⚠⚠ v2704 — THIS RAISED SkipTest AND THAT MADE THE GATE A LIAR. Measured: a SkipTest raised
    from setUpClass yields "Ran 0 tests ... OK (skipped=1)" and EXIT STATUS 0, which run_gates
    records as green. So on any machine without node on PATH, the most consequential logic in
    bible.html was guarded by a gate that graded nothing and said OK — and the anti-vacuity
    assertion that would catch it lives inside the skipped class, where it can never fire.
    A SKIP IS NOT A PASS. That is carved, and this file walked into it anyway. If node is
    missing the honest verdict is that the gate could not run, which must be RED.
    """
    for exe in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            if subprocess.run([exe, "-v"], capture_output=True).returncode == 0:
                return exe
        except Exception:
            continue
    raise AssertionError(
        "GATE CANNOT RUN: node is not available, so nothing here was graded. This is a FAILURE, "
        "not a skip -- a skipped gate exits 0 and is recorded as a pass, which would leave this "
        "logic unguarded while reporting green."
    )


def _script_fragment():
    """The <script> block that defines both controls, bound at both ends."""
    s = _src()
    i = s.find("window._d2rUnseed = function")
    if i < 0:
        raise AssertionError("GUARD CANNOT GRADE: the un-seed is not in bible.html")
    st = s.rfind("<script>", 0, i) + len("<script>")
    en = s.index("</script>", i)
    return s[st:en]


#: the mock store the round trip is run against: two seeded grail finds, one seeded ruling find,
#: two of HIS OWN, a seeded name inside d2r_owned, and the seeded rwVerify verdicts.
_ROUND_TRIP_JS = r"""
const vm = require('vm');
const FRAG = %s;
const ORIGINAL = {
  d2r_foundLog: JSON.stringify({'Shaftstop':'Jan 1, 2026 - 00:00','Wormskull':'Jan 2, 2026 - 00:00',
                                'The Diggler':'Jan 3, 2026 - 00:00','HIS FIND A':'Jun 9, 2026 - 12:00',
                                'HIS FIND B':'Jun 9, 2026 - 13:00'}),
  d2r_owned:     JSON.stringify(['Shaftstop','HIS FIND A']),
  d2r_rwMade:    JSON.stringify({}),
  d2r_setPieces: JSON.stringify([]),
  d2r_rwVerify:  JSON.stringify({'Mania':'fail','Hysteria':'fail'})
};
const store = Object.assign({}, ORIGINAL);
const sandbox = {
  console:{log:()=>{},warn:()=>{}}, location:{reload:()=>{}},
  uiConfirm:()=>Promise.resolve(true), setTimeout:(f)=>f(),
  Date:Date, JSON:JSON, Object:Object, String:String, Array:Array,
};
sandbox.window = {
  localStorage:{ getItem:k=>(k in store?store[k]:null), setItem:(k,v)=>{store[k]=v;}, removeItem:k=>{delete store[k];} },
  _D2R_INSTALL:'INST1234',
  _GRAIL_SEED:{'Shaftstop':'Jan 1, 2026 - 00:00','Wormskull':'Jan 2, 2026 - 00:00'},
  _SET_SEED:{}, _RWC_SEED:{}, _RULING_SEED:{'The Diggler':'Jan 3, 2026 - 00:00'},
  _RWV_SEED:{'Mania':'fail','Hysteria':'fail'}
};
sandbox.window.LSR = sandbox.window.localStorage;
vm.createContext(sandbox); vm.runInContext(FRAG, sandbox);
sandbox.window._d2rUnseed();
setTimeout(()=>{
  const fl = JSON.parse(store.d2r_foundLog);
  if (Object.keys(fl).length !== 2) { console.log('THE UN-SEED DID NOT STRIP: ' + JSON.stringify(fl)); console.log('NOT SYMMETRIC'); return; }
  sandbox.window._d2rUnseedRestore();
  setTimeout(()=>{
    let bad = [];
    Object.keys(ORIGINAL).forEach(k=>{ if (store[k] !== ORIGINAL[k]) bad.push(k); });
    if (store.d2r_ledgerName) bad.push('d2r_ledgerName still set to ' + store.d2r_ledgerName);
    console.log(bad.length ? ('NOT SYMMETRIC: ' + bad.join(', ')) : 'SYMMETRIC');
  }, 20);
}, 20);
"""



#: un-seed -> Undo -> work -> un-seed -> Undo. The week must survive.
_TWICE_JS = r"""
const vm=require('vm'); const FRAG=%s;
const store={ d2r_foundLog: JSON.stringify({'Shaftstop':'Jan 1, 2026 - 00:00','HIS FIND A':'Jun 9, 2026 - 12:00'}),
              d2r_owned:'[]', d2r_rwMade:'{}', d2r_setPieces:'[]', d2r_rwVerify:'{}' };
const sb={console:{log:()=>{},warn:()=>{}},location:{reload:()=>{}},
  uiConfirm:()=>Promise.resolve(true),setTimeout:f=>f(),Date:Date,JSON:JSON,Object:Object,String:String,Array:Array};
sb.window={localStorage:{getItem:k=>(k in store?store[k]:null),setItem:(k,v)=>{store[k]=v;},removeItem:k=>{delete store[k];}},
  _D2R_INSTALL:'I1',_GRAIL_SEED:{'Shaftstop':'Jan 1, 2026 - 00:00'},_SET_SEED:{},_RWC_SEED:{},_RULING_SEED:{},
  _RWV_SEED:{"Mania":"fail","Hysteria":"fail"}};
sb.window.LSR=sb.window.localStorage;
vm.createContext(sb); vm.runInContext(FRAG,sb);
sb.window._d2rUnseed();
setTimeout(()=>{ sb.window._d2rUnseedRestore(); setTimeout(()=>{
  console.log('snapshot after restore: ' + (store.d2r_unseedBackup ? 'STILL THERE' : 'cleared'));
  const fl=JSON.parse(store.d2r_foundLog); fl['A WEEK OF WORK']='Jun 16, 2026 - 09:00';
  store.d2r_foundLog=JSON.stringify(fl);
  sb.window._d2rUnseed();
  setTimeout(()=>{ sb.window._d2rUnseedRestore(); setTimeout(()=>{
    const back=Object.keys(JSON.parse(store.d2r_foundLog));
    console.log(back.indexOf('A WEEK OF WORK')>=0 ? 'THE WEEK SURVIVED' : 'THE WEEK WAS ROLLED BACK');
  },20); },20);
},20); },20);
"""

class UnseedIsReversible(unittest.TestCase):

    def setUp(self):
        self.src = _src()
        self.unseed = self._fn("window._d2rUnseed = function")

    @property
    def restore(self):
        """Resolved LAZILY, on purpose.

        ⚠ The first cut fetched this in setUp, and running the suite against the shipped v2697
        bytes reported 8 FAILURES — every one of them the same setUp error about the missing
        restore function. Eight red lines, ONE fact. That is the count-inflation this repo has
        been bitten by before (spec filenames counted instead of failure anchors, 4x), and a gate
        whose redness cannot be attributed is barely better than a green one. Resolving it here
        means the ordering test fails on ORDERING, the rwVerify test fails on rwVerify, and the
        eight lines are eight independent findings.
        """
        return self._fn("window._d2rUnseedRestore = function")

    def _fn(self, marker):
        """The named function's source, bound at BOTH ends by brace matching.

        A fixed-size window past the region reads as absent and would grade a truncated body —
        [[source-window-shortcut]], which cost this repo four separate false readings in one day.
        """
        i = self.src.find(marker)
        if i < 0:
            raise AssertionError(
                "GUARD CANNOT GRADE: `%s` is not in bible.html. The control was renamed or "
                "removed -- fix this test before trusting any verdict it prints." % marker
            )
        st = self.src.index("{", i)
        depth = 0
        for j in range(st, len(self.src)):
            if self.src[j] == "{":
                depth += 1
            elif self.src[j] == "}":
                depth -= 1
                if depth == 0:
                    return self.src[i:j + 1]
        raise AssertionError("GUARD CANNOT GRADE: `%s` is never closed" % marker)

    # ---- 1. the undo exists at all -------------------------------------------------------

    def test_the_backup_key_is_read_somewhere_not_only_written(self):
        """The defect verbatim: one write, zero reads, and a dialog promising an undo."""
        writes = len(re.findall(r"setItem\(\s*['\"]d2r_unseedBackup['\"]", self.src))
        reads = len(re.findall(r"getItem\(\s*['\"]d2r_unseedBackup['\"]", self.src))
        self.assertGreater(
            reads, 0,
            "d2r_unseedBackup is written %d time(s) and READ %d times. The confirm dialog "
            "promises the un-seed 'can be undone'; a snapshot nothing ever reads is not an undo, "
            "it is a sentence. This is the exact defect v2699 fixed." % (writes, reads)
        )

    def test_a_restore_entry_point_exists_and_is_wired_to_a_control(self):
        # assertTrue, NOT assertIn: the haystack is a 6MB file and assertIn prints it on
        # failure, so the verdict drowns in the very document it is grading. Measured: the first
        # run of this against the shipped bytes emitted 6.1MB of output.
        self.assertTrue("window._d2rUnseedRestore = function" in self.src,
                        "there is no restore function -- the dialog's promise of an undo has "
                        "nothing behind it")
        self.assertTrue("_d2rUnseedRestore()" in self.src,
                        "nothing CALLS the restore -- a function with no door is the unjoined "
                        "end this repo keeps shipping")

    # ---- 2 & 3. the ledger name, which is the half that turns the floors off --------------

    def test_the_ledger_is_named_before_anything_is_destroyed(self):
        """A throw after a strip but before the name leaves a stripped store that RE-SEEDS."""
        i_name = self.unseed.find("setItem('d2r_ledgerName'")
        i_strip = self.unseed.find("strip('d2r_foundLog'")
        self.assertGreater(i_name, -1, "the un-seed never names the ledger")
        self.assertGreater(i_strip, -1, "the un-seed never strips the found log")
        self.assertLess(
            i_name, i_strip,
            "the ledger name is written at offset %d, AFTER the first strip at %d. A quota "
            "rejection or any throw between them leaves a store that is stripped and unnamed, "
            "which re-seeds on the next load -- with the v1692 one-shot flag already deleted, so "
            "that migration re-fires too." % (i_name, i_strip)
        )

    def test_the_restore_puts_the_ledger_name_back(self):
        """Without this the undo restores the data and leaves the floors switched off."""
        self.assertIn("d2r_ledgerName", self.restore,
                      "the restore never touches d2r_ledgerName -- it would put the entries back "
                      "while _seedsBelongHere stays false, so the floors remain off")
        self.assertIn("removeItem('d2r_ledgerName')", self.restore,
                      "the restore must REMOVE the ledger name when the snapshot had none. "
                      "Writing '' instead would leave the key present, and the resolver's first "
                      "branch is `if (n) return n` on a trimmed string -- only absence re-arms "
                      "the has-a-chronicle heuristic that Konyo's own board depends on")

    # ---- 4. every store the snapshot carries is one the restore can put back ---------------

    def test_every_backed_up_store_is_restorable(self):
        missing = [k for k in BACKED_UP if k not in self.restore]
        self.assertEqual(
            missing, [],
            "these stores are captured in the snapshot but the restore never puts them back: %s. "
            "A backup that cannot be restored is a promise with no door." % ", ".join(missing)
        )

    def test_the_two_stores_that_were_silently_kept_are_stripped(self):
        for key, why in (
            ("d2r_rwVerify", "the cousin keeps the owner's seeded Mania/Hysteria 'fail' verdicts, "
                             "and because the seed only writes when the key is NULL, renaming the "
                             "ledger cannot clear them either"),
            ("d2r_owned",    "_ownedNames() unions d2r_owned with the foundLog keys, so inherited "
                             "names there still count as found and the board never reaches the "
                             "number the button promises"),
        ):
            self.assertIn(key, self.unseed,
                          "the un-seed never touches %s -- %s" % (key, why))

    def test_the_snapshot_is_not_overwritten_by_a_second_click(self):
        """The first snapshot is the valuable one; a later one photographs the damage."""
        self.assertRegex(
            self.unseed.replace("\n", " "),
            r"getItem\(\s*'d2r_unseedBackup'\s*\)\s*==\s*null",
            "nothing guards the snapshot, so clicking the un-seed twice rewrites "
            "d2r_unseedBackup from the ALREADY-STRIPPED store and destroys the only record of "
            "the pre-strip state"
        )

    # ---- 5. it cannot ship inert again ----------------------------------------------------

    # ---- 6. THE BEHAVIOURAL HALF: does the round trip actually come back? -------------------

    def test_the_unseed_restore_round_trip_is_symmetric(self):
        """Run the REAL functions against a mock store and compare, byte for byte.

        Everything above is a source law — order, presence, wiring. None of it can answer the
        only question that matters to the person clicking the button: if I undo this, do I get
        my board back? This runs `window._d2rUnseed` and then `window._d2rUnseedRestore`, lifted
        out of bible.html and executed in a vm sandbox, and asserts every store returns to its
        exact prior value AND that the ledger name is REMOVED rather than set to ''.

        The ledger half is the one that matters most and the easiest to get subtly wrong: only
        ABSENCE re-arms the has-a-chronicle heuristic that Konyo's own board depends on, so a
        restore that writes an empty string would return the data and leave the floors off.
        """
        node = _node()
        frag = _script_fragment()
        harness = _ROUND_TRIP_JS % json.dumps(frag)
        r = subprocess.run([node, "-e", harness], capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("the round-trip harness would not run: %s" % (r.stderr or "")[:300])
        out = (r.stdout or "").strip()
        self.assertIn("SYMMETRIC", out,
                      "the un-seed/restore round trip did not come back. Output:\n%s" % out[-600:])
        self.assertNotIn("NOT SYMMETRIC", out,
                         "a store did not return to its prior value:\n%s" % out[-600:])

    def test_a_second_unseed_after_a_restore_takes_its_own_snapshot(self):
        """The stale-snapshot trap the v2699 no-overwrite guard created.

        un-seed -> Undo -> a week of real finds -> un-seed again -> Undo. If the restore does not
        CONSUME the snapshot, the second un-seed sees a non-null backup, keeps the first one, takes
        none of its own, and the second Undo rolls the week back. The guard is right for a second
        un-seed with no restore in between; a restore is what makes the old snapshot spent.
        """
        node = _node()
        harness = _TWICE_JS % json.dumps(_script_fragment())
        r = subprocess.run([node, "-e", harness], capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("the twice-round-trip harness would not run: %s" % (r.stderr or "")[:300])
        out = (r.stdout or "").strip()
        self.assertIn("THE WEEK SURVIVED", out,
                      "a second un-seed after a restore reused the FIRST snapshot, so the Undo "
                      "rolled back work done in between:\n%s" % out[-500:])
        self.assertIn("cleared", out,
                      "the restore left the snapshot in place; the next un-seed cannot take its "
                      "own:\n%s" % out[-500:])

    def test_neither_control_lives_inside_an_onclick_attribute(self):
        """v2696: an apostrophe in "Gloom's Trap" terminated onclick="…" and the button did
        nothing while looking perfect. Bodies belong in a script block; attributes may only CALL."""
        for m in re.finditer(r'onclick="([^"]*)"', self.src):
            body = m.group(1)
            if "_d2rUnseed" in body:
                self.assertLess(
                    len(body), 120,
                    "an onclick attribute carries %d characters of un-seed logic. A quote or "
                    "apostrophe anywhere in it terminates the attribute and the control ships "
                    "inert -- which has already happened once here." % len(body)
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
