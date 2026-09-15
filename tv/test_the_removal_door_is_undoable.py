# -*- coding: utf-8 -*-
"""v3168 (#96) — THE REMOVAL DOOR IS DATED, LISTED, UNDOABLE, AND STAMPED ONCE.

HIS ORDER, 2026-09-15: *"Build a removal door — a board-side vault_remove(names[]) with the same
care as chronicleApply: dated, listed, undoable, and stamped once."*

WHY A LAW AND NOT A NOTE. #96 has to take ~150 backfilled names out of `d2r_owned`. The only
board-side remover that existed was `vaultUnown(name)` — one name, one render, one save, one
status line, and NO RECORD. Removing 150 through it means 150 renders and an undo that exists
only in his memory. The window where that is recoverable is the window before he closes the tab.

★ WHAT THIS LAW PINS — and it drives the SHIPPED function bodies in node, never a paraphrase:
  1. a name the board does not hold is `skipped`, never counted as `removed`;
  2. the batch is DATED (ts + ISO day) and LISTED in d2r_vaultRemoved;
  3. the locker assignment is recorded and RESTORED — an undo that returns the item unfiled has
     lost where it lived while looking like it worked [[the-unjoined-end]];
  4. STAMPED ONCE — one persist, one render, one status line for the whole batch, not N;
  5. a name he re-checked himself is LEFT ALONE by the restore (chronicleUndoLast's own rule);
  6. a batch cut on another ledger is REFUSED, and stays in the journal for its own board —
     v2692 is this hazard in the other direction and it reached his cousin's board;
  7. an empty removal writes NO batch (it would push a real one out of the 20-deep ring).
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")

START = "var _VR_LOG = 'd2r_vaultRemoved'"
END = "  // v342.3 — throw out a Magic & Rare keeper"


def _between(src, start, end):
    """Both ends anchored. A fixed-size window past the region reads as ABSENT and would let
    this law pass on a file that no longer contains the door. [[source-reading-guard]]"""
    i = src.find(start)
    assert i >= 0, "start anchor %r not found — the removal door is gone" % start
    j = src.find(end, i)
    assert j > i, "end anchor %r not found after the door" % end
    return src[i:j]


UNOWN_START = "  window.vaultUnown = function(name){"
UNOWN_END = "  /* \u2550\u2550\u2550\u2550\u2550 v3168 (#96) \u2014 THE REMOVAL DOOR"


def _door_source():
    """BOTH shipped removal paths: the batch door and the one-click path that now routes
    through it. Extracting only the door would leave vaultUnown undefined and the law would
    be testing a function the board does not have."""
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    return _between(src, START, END) + "\n" + _between(src, UNOWN_START, UNOWN_END)


HARNESS = r"""
// ── the board, stubbed only where the door TOUCHES it ──────────────────────────
var owned = new Set(%(owned)s);
var assign = %(assign)s;
var STORE = %(store)s;
var calls = {persist:0, save:0, render:0, refresh:0, repaint:0, status:[]};
function persistOwned(){ calls.persist++; }
function saveA(){ calls.save++; }
function renderVault(){ calls.render++; }
function refreshOpenCard(){ calls.refresh++; }
function status(s){ calls.status.push(String(s)); }
function muleById(id){ return %(mules)s.indexOf(id) >= 0 ? {id:id} : null; }
var window = {
  LSR: { getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE,k) ? STORE[k] : null; },
         setItem: function(k,v){ STORE[k] = String(v); } },
  _D2R_LEDGER: %(ledger)s,
  D2R_PROFILE: 'main',
  _repaintOwned: function(){ calls.repaint++; }
};

%(door)s

var out = (function(){ %(script)s })();
console.log(JSON.stringify({result: out, owned: Array.from(owned).sort(),
                            assign: assign, store: STORE, calls: calls}));
"""


class TheRemovalDoorIsUndoable(unittest.TestCase):

    def drive(self, script, owned=None, assign=None, store=None,
              mules=None, ledger="KonyoEndgame"):
        js = HARNESS % {
            "owned": json.dumps(sorted(owned or [])),
            "assign": json.dumps(assign or {}),
            "store": json.dumps(store or {}),
            "mules": json.dumps(mules or []),
            "ledger": json.dumps(ledger),
            "door": _door_source(),
            "script": script,
        }
        path = os.path.join(HERE, ".vrdoor_drive.js")
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(js)
        try:
            r = subprocess.run(["node", path], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            self.skipTest("node unavailable — a skip is NOT a pass")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        self.assertEqual(r.returncode, 0,
                         "the shipped door threw in node:\n%s" % (r.stderr or "")[-1200:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    # 1 — a name not held is skipped, and the numerator is what was actually there
    def test_a_name_the_board_does_not_hold_is_skipped_not_removed(self):
        o = self.drive("return window.vaultRemove(['Shako','Ghostwhatever','Occy']);",
                       owned=["Shako", "Occy", "Tal Rasha's Mask"])
        r = o["result"]
        self.assertEqual(r["requested"], 3)
        self.assertEqual(sorted(r["removed"]), ["Occy", "Shako"])
        self.assertEqual(r["skipped"], ["Ghostwhatever"])
        self.assertEqual(o["owned"], ["Tal Rasha's Mask"])

    # 2 — DATED and LISTED
    def test_the_batch_is_dated_and_listed(self):
        o = self.drive("return window.vaultRemove(['Shako'], {why:'#96 backfill', lane:'vault-prune'});",
                       owned=["Shako"])
        log = json.loads(o["store"]["d2r_vaultRemoved"])
        self.assertEqual(len(log), 1, "exactly one batch was cut")
        b = log[0]
        self.assertTrue(isinstance(b["ts"], (int, float)) and b["ts"] > 0, "batch carries a ts")
        self.assertRegex(b["day"] or "", r"^\d{4}-\d{2}-\d{2}$", "batch carries an ISO day")
        self.assertEqual(b["names"], ["Shako"])
        self.assertEqual(b["why"], "#96 backfill")
        self.assertEqual(b["lane"], "vault-prune")
        self.assertEqual(b["ledger"], "KonyoEndgame", "the batch is stamped with its world")

    # 3 — the filing is part of the removal, and comes back
    def test_the_locker_assignment_is_recorded_and_restored(self):
        o = self.drive(
            "window.vaultRemove(['Shako']);"
            "return window.vaultRestoreLast();",
            owned=["Shako"], assign={"Shako": "mule7"}, mules=["mule7"])
        self.assertEqual(o["result"]["restored"], 1)
        self.assertEqual(o["owned"], ["Shako"], "the name is back in owned")
        self.assertEqual(o["assign"].get("Shako"), "mule7",
                         "an undo that returns the item UNFILED has lost where it lived")

    # 4 — STAMPED ONCE: one persist / render / status for the whole batch
    def test_a_batch_of_many_stamps_exactly_once(self):
        names = ["N%02d" % i for i in range(40)]
        o = self.drive("return window.vaultRemove(%s);" % json.dumps(names), owned=names)
        self.assertEqual(o["result"]["removed"].__len__(), 40)
        c = o["calls"]
        self.assertEqual(c["persist"], 1, "40 names must not cost 40 saves")
        self.assertEqual(c["render"], 1, "40 names must not cost 40 renders")
        self.assertEqual(len(c["status"]), 1, "one line for the batch, not forty")
        self.assertIn("40 of 40", c["status"][0], "the line reports removed-of-requested")

    # 5 — his own re-check is never overruled
    def test_a_name_he_rechecked_himself_is_left_alone(self):
        o = self.drive(
            "window.vaultRemove(['Shako','Occy']);"
            "owned.add('Shako');"                      # he re-ticked it by hand afterwards
            "return window.vaultRestoreLast();",
            owned=["Shako", "Occy"])
        r = o["result"]
        self.assertEqual(r["restored"], 1, "only Occy was restored")
        self.assertEqual(r["kept"], 1, "Shako was his truth, left alone")
        self.assertEqual(o["owned"], ["Occy", "Shako"])

    # 6 — a batch never crosses worlds, and refusing does not consume it
    def test_a_batch_from_another_ledger_is_refused_and_kept(self):
        prior = json.dumps([{"ts": 1700000000000, "day": "2026-09-01", "ledger": "SomeCousin",
                             "profile": "main", "names": ["Shako"], "filed": {},
                             "why": "x", "lane": "y"}])
        o = self.drive("return window.vaultRestoreLast();",
                       owned=[], store={"d2r_vaultRemoved": prior}, ledger="KonyoEndgame")
        self.assertEqual(o["result"]["restored"], 0)
        self.assertIn("SomeCousin", o["result"]["why"])
        self.assertEqual(o["owned"], [], "it must not write a find nobody made")
        self.assertEqual(len(json.loads(o["store"]["d2r_vaultRemoved"])), 1,
                         "a refused batch stays undoable on its OWN board")

    # 7 — an empty removal writes no batch
    def test_an_empty_removal_writes_no_batch(self):
        o = self.drive("return window.vaultRemove(['NotHeld']);", owned=["Shako"])
        self.assertEqual(o["result"]["removed"], [])
        self.assertNotIn("d2r_vaultRemoved", o["store"],
                         "a stamp for nothing would push a real batch out of the ring")
        self.assertEqual(o["calls"]["persist"], 0, "nothing changed, so nothing is saved")

    # 8 — the ONE-CLICK path goes through the same door, or the journal counts the wrong thing
    def test_the_one_click_path_is_journaled_too(self):
        """vaultUnown used to delete straight out of `owned` and record nothing. A journal that
        covered only batches would report zero removals while items left the board beside it —
        a denominator nobody asked for. [[zero-needs-a-denominator]]"""
        o = self.drive("window.vaultUnown('Shako');"
                       "return window.vaultRestoreLast();",
                       owned=["Shako"], assign={"Shako": "mule3"}, mules=["mule3"])
        self.assertEqual(o["result"]["restored"], 1,
                         "a one-click un-own must be undoable like any other removal")
        self.assertEqual(o["owned"], ["Shako"])
        self.assertEqual(o["assign"].get("Shako"), "mule3",
                         "and it must give the locker back too")

    def test_the_one_click_path_still_says_what_he_expects(self):
        o = self.drive("window.vaultUnown('Shako'); return null;", owned=["Shako"])
        lines = o["calls"]["status"]
        self.assertEqual(len(lines), 1, "one click is still one line, not two")
        self.assertIn("re-\u2713 it on its item card", lines[0],
                      "his own wording survived the replumbing")

class TheRemovalJournalForksLikeTheStore(unittest.TestCase):
    """The journal must resolve in the SAME worlds as the store it describes. If d2r_owned is
    bare in all four worlds and the journal is prefixed (or vice versa), the board would offer a
    restore for names the active world never held. Parsed, never grepped."""

    def test_the_journal_and_the_owned_store_share_a_fork_class(self):
        with io.open(BIBLE, encoding="utf-8") as fh:
            src = fh.read()
        sets = {}
        for nm in ("_LP_FORKED", "_WP_FORKED"):
            m = re.search(r"window\." + nm + r"\s*=\s*new Set\((.*?)\);", src, re.S)
            self.assertIsNotNone(m, "%s is gone — the fork rule cannot be checked" % nm)
            sets[nm] = set(re.findall(r"'([^']+)'", m.group(1)))
        # _WP_FORKED is built by concat over _LP_FORKED, so membership is the union
        wp = sets["_WP_FORKED"] | sets["_LP_FORKED"]
        lp = sets["_LP_FORKED"]
        self.assertEqual("d2r_owned" in lp, "d2r_vaultRemoved" in lp,
                         "the journal and d2r_owned must fork the same way on LADDER")
        self.assertEqual("d2r_owned" in wp, "d2r_vaultRemoved" in wp,
                         "the journal and d2r_owned must fork the same way on a GUEST world")


class TheRemovalIsWatchedByTheHeart(unittest.TestCase):
    """*"connect it to the heart of the console so its tracked"* — a door nobody watches is a
    door that can quietly stop working. [[the-unjoined-end]]"""

    def setUp(self):
        import tempfile
        sys_path = os.path.dirname(os.path.abspath(__file__))
        if sys_path not in __import__("sys").path:
            __import__("sys").path.insert(0, sys_path)
        import health_engine
        self.he = health_engine
        self.tmp = tempfile.mkdtemp(prefix="vrheart_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _backup(self, stores):
        p = os.path.join(self.tmp, "ledger_2026-09-15_120000.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"allStores": stores}))
        return p

    def test_the_organ_is_registered_or_nobody_ever_runs_it(self):
        names = [f.__name__ for f in self.he.CHECKS]
        self.assertIn("check_vault_removals", names,
                      "an organ that is not in CHECKS is never called by the heart")

    def test_an_empty_journal_says_since_when(self):
        self._backup({"d2r_vaultRemoved": "[]"})
        r = self.he.check_vault_removals(backup_dir=self.tmp)
        self.assertEqual(r["state"], self.he.OK)
        self.assertIn("SINCE", r["line"],
                      "a bare zero beside 'removals' reads as 'nothing was ever removed'")

    def test_a_journaled_batch_is_counted_and_dated(self):
        self._backup({"d2r_vaultRemoved": json.dumps(
            [{"ts": 1, "day": "2026-09-14", "names": ["A", "B"], "ledger": "K"},
             {"ts": 2, "day": "2026-09-15", "names": ["C"], "ledger": "K"}])})
        r = self.he.check_vault_removals(backup_dir=self.tmp)
        self.assertIn("3 name(s)", r["line"])
        self.assertIn("2 journaled batch", r["line"])
        self.assertIn("2026-09-15", r["line"], "he is told WHEN, not just how many")

    def test_an_unreadable_backup_is_unknown_not_zero(self):
        p = os.path.join(self.tmp, "ledger_2026-09-15_120000.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        r = self.he.check_vault_removals(backup_dir=self.tmp)
        self.assertEqual(r["state"], self.he.UNKNOWN,
                         "a file that would not parse is not evidence of an empty journal")

    def test_the_evidence_is_a_list_of_lines_not_a_dict(self):
        """_row does list(evidence or []) — a dict lands as its KEY NAMES and every number is
        lost. That shipped once already and printed four labels with no figures."""
        self._backup({"d2r_vaultRemoved": "[]"})
        r = self.he.check_vault_removals(backup_dir=self.tmp)
        self.assertIsInstance(r["evidence"], list)
        self.assertTrue(any(":" in str(e) for e in r["evidence"]),
                        "evidence lines must carry figures, not bare labels")


if __name__ == "__main__":
    unittest.main(verbosity=2)
