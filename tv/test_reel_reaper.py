#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE RECORDER MAY NOT EAT EVIDENCE — the disk-floor reel reaper.

⚠⚠ WHAT WAS THERE, measured 2026-09-05 in `tv_diablo.py` inside the RECORDING path:

    reels = sorted(d2 for d2 in os.listdir(HIST_DIR) if d2.startswith("reel_"))
    if len(reels) > 2 and not foot_files:
        _shr.rmtree(os.path.join(HIST_DIR, reels[0]), ignore_errors=True)

A whole reel, deleted. The comment above it promised *"retire the OLDEST **sealed** reels"* and the
word "sealed" appeared ONLY in that comment — no seal check, no witness check, no retention call,
no tombstone. `TV_AUTO_PRUNE` occurs **zero** times in that file, so the standing rule that the
prune stays OFF never reached this code: it is armed and needs no switch. `ignore_errors=True`
inside `except Exception: pass` made a failed or partial delete silent. And `sorted()` is
LEXICOGRAPHIC, so "oldest" held only while every reel kept the same name shape.

⚠⚠ AND IT WAS ABOUT TO TAKE EVIDENCE, WHICH IS WHY THIS IS A GUARD AND NOT A NOTE.
`vault_accum.json` cites 4 sessions in its `witnesses` lists. TWO ARE ALREADY GONE — including
"Chaotic Grand Charm", whose frame the ledger still names. Of the two still on disk, one is
`reel_s_1784984019250_95276`: the OLDEST reel on his shelf, i.e. exactly `reels[0]`. **The next
time free space crossed the floor, the first reel deleted would have been one the vault still
cites.** His ruling on the two already lost: *"its fine just make sure going forward it will be..
whats in the past is the past."* So nothing is back-filled and nothing is restored; this only
stops it happening again.

⚠ THE EMERGENCY IS KEPT. A full disk stops recording entirely, which is worse than losing a reel.
The reaper still reaps — it refuses to reap EVIDENCE, and it says what it did either way.

⚠ NOTHING HERE TOUCHES HIS SHELF. Every case builds a temp shelf and points TV_HIST at it.
[[feedback-fixtures-never-touch-live-data]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import tv_diablo as T  # noqa: E402


class TheLedgerQuestionIsAskedHonestly(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="reap_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.hist = os.path.join(self.dir, "frames", "hist")
        os.makedirs(self.hist)
        self._saved = T.HIST_DIR
        T.HIST_DIR = self.hist
        self.addCleanup(setattr, T, "HIST_DIR", self._saved)
        T._WACC_STATE["sess"] = None
        T._WACC_STATE["mtime"] = None
        self.addCleanup(lambda: T._WACC_STATE.update({"sess": None, "mtime": None}))

    def _accum(self, text):
        p = os.path.join(self.dir, "vault_accum.json")
        io.open(p, "w", encoding="utf-8").write(text)
        return p

    def test_it_reads_the_ledger_beside_the_SHELF_not_beside_the_code(self):
        """★ Anchoring on HERE would make every fixture consult his live vault_accum.json."""
        self._accum(json.dumps({"owned": [{"witnesses": [{"session": "s_fixture_1"}]}]}))
        self.assertEqual(T._witness_protected_sessions(), {"s_fixture_1"},
                         "it read a ledger other than the one beside the shelf under test")

    def test_NO_ledger_is_an_empty_set_because_that_is_a_real_answer(self):
        self.assertEqual(T._witness_protected_sessions(), set())

    def test_an_UNREADABLE_ledger_is_None_and_NEVER_an_empty_set(self):
        """★★ [[unknown-stays-unknown]]. An empty set means "nothing is cited" and licenses a
        deletion. A corrupt ledger means we could not ask, and must license nothing."""
        self._accum("{not json at all")
        self.assertIsNone(T._witness_protected_sessions(),
                          "a corrupt ledger read as 'nothing is cited', which permits a delete")

    def test_the_clock_is_the_reel_id_not_lexicographic_order(self):
        """`sorted()` on names is only 'oldest' while every name keeps one shape."""
        self.assertEqual(T._reel_capture_ms("reel_s_1784984019250_95276"), 1784984019250)
        self.assertEqual(T._reel_capture_ms("reel_odd"), 0)
        names = ["reel_s_1788087297344_53906", "reel_s_1784984019250_95276"]
        self.assertEqual(sorted(names, key=T._reel_capture_ms)[0],
                         "reel_s_1784984019250_95276", "the older reel did not sort first")

    def test_a_reel_with_NO_readable_clock_is_reaped_LAST_not_first(self):
        """★ A defect in my own fix, caught by this case. `_reel_capture_ms` answers 0 for an
        un-datable name, so a bare sort key put every unknown reel at the FRONT of the kill list —
        making the reel we know least about the preferred victim. Unknown never jumps the queue,
        in either direction. [[unknown-stays-unknown]]"""
        names = ["reel_odd", "reel_s_1788087297344_53906", "reel_s_1784984019250_95276"]
        key = lambda r: (T._reel_capture_ms(r) == 0, T._reel_capture_ms(r))  # noqa: E731
        self.assertEqual(sorted(names, key=key),
                         ["reel_s_1784984019250_95276", "reel_s_1788087297344_53906", "reel_odd"])
        import inspect
        src = inspect.getsource(T.archive_read_frame)
        self.assertIn("_reel_capture_ms(_r) == 0", src,
                      "the shipped reaper still sorts un-datable reels to the front")


class TheReaperRefusesEvidence(unittest.TestCase):
    """★★ THE POINT, and it is checked on the SHIPPED SOURCE rather than re-implemented here.
    Re-implementing the decision in the test would grade my copy of it, not the code that runs."""

    def _block(self):
        import inspect
        src = inspect.getsource(T.archive_read_frame)
        i = src.index("REELS DIE WHOLE")
        j = src.index("YOUTH SHIELD", i)
        return src[i:j]

    def test_the_block_consults_the_witness_ledger(self):
        b = self._block()
        self.assertIn("_witness_protected_sessions", b,
                      "the reel reaper does not ask whether a reel is still cited as evidence")

    def test_an_UNREADABLE_ledger_refuses_the_reap(self):
        b = self._block()
        self.assertIn("is None", b, "no branch handles the could-not-ask answer")
        self.assertIn("REFUSED", b, "a could-not-ask ledger does not visibly refuse the reap")

    def test_it_sorts_by_the_capture_clock_not_lexicographically(self):
        b = self._block()
        self.assertIn("_reel_capture_ms", b, "'oldest' is still lexicographic")
        self.assertNotIn("sorted(d2 for d2 in os.listdir", b)

    def test_it_never_takes_one_of_the_two_newest(self):
        self.assertIn("[:-2]", self._block())

    def test_every_deletion_leaves_a_record(self):
        b = self._block()
        self.assertIn("_reap_record", b, "a reel can still be deleted leaving no trace")

    def test_a_FAILURE_is_said_out_loud_and_not_swallowed(self):
        """`except Exception: pass` made 'it broke' and 'it had nothing to do' the same event."""
        b = self._block()
        self.assertIn("_dbg", b)
        self.assertNotIn("except Exception:\n                    pass", b)

    def test_the_EMERGENCY_still_exists(self):
        """⚠ THE BASELINE. A reaper that can only refuse lets the disk fill, which stops recording
        entirely — worse than losing a reel. It must still be able to take something."""
        b = self._block()
        self.assertIn("rmtree", b, "the emergency was removed rather than made honest")


class TheRecordIsNotTheTombstoneStore(unittest.TestCase):
    """`reel_retention._tombstone` is the ONE writer of reel_tombstones.json. A second writer would
    put two authorities on one store — the defect this repo keeps paying for."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="reap2_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.hist = os.path.join(self.dir, "frames", "hist")
        os.makedirs(self.hist)
        self._saved = T.HIST_DIR
        T.HIST_DIR = self.hist
        self.addCleanup(setattr, T, "HIST_DIR", self._saved)

    def test_it_writes_its_own_store_and_says_who_wrote_it(self):
        T._reap_record("reel_s_1", 42, True, 9)
        p = os.path.join(self.dir, "reel_reaps.jsonl")
        self.assertTrue(os.path.exists(p), "an emergency deletion left no durable record")
        row = json.loads(io.open(p, encoding="utf-8").read().strip().splitlines()[-1])
        self.assertEqual(row["reel"], "reel_s_1")
        self.assertEqual(row["by"], "recorder-disk-floor")
        self.assertIn("agentVer", row, "the record cannot say which build wrote it")

    def test_it_does_NOT_write_the_tombstone_store(self):
        T._reap_record("reel_s_1", 1, True, 3)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "reel_tombstones.json")),
                         "the recorder became a second writer of the tombstone store")

    def test_an_unmeasured_frame_count_stays_minus_one_not_zero(self):
        """[[unknown-stays-unknown]] — 0 frames and 'could not count' are different facts."""
        T._reap_record("reel_s_2", -1, False, 3)
        p = os.path.join(self.dir, "reel_reaps.jsonl")
        row = json.loads(io.open(p, encoding="utf-8").read().strip().splitlines()[-1])
        self.assertEqual(row["frames"], -1)
        self.assertFalse(row["removed"])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
