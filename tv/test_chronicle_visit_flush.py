#!/usr/bin/env python3
# 📜 TV DIABLO — v1689: A CHRONICLE VISIT THAT IS STILL OPEN AT SESSION CLOSE MUST BE JOURNALLED.
#   python3 tv/test_chronicle_visit_flush.py
#
# THE DEFECT THIS POLICES (measured on his real session s_1786385768689_67392, 2026-08-10
# 21:16-21:19, reel of 217 frames): the deep lane classified 8 frames scene='chronicle' with
# chronicleTab='uniques', but _chron_visit_step() only CLOSES a visit when a LATER deep read
# returns a non-chronicle scene. He looked at the Chronicle LAST — the natural way to register
# finds — so the visit was still {open:True, ledger:'uniques', frames:8} when the session ended
# and ZERO {lane:'chronicle', kind:'visit'} rows were written. chronicle_visits() in control_app
# filters on exactly that row, so /api/chronicle_visits stayed [] and the v1527 "read this visit
# for ZERO classifies" offer could never appear.
#
# The doctrine is NOT relaxed by the fix: recording stays FREE, reading stays OFFERED. The flush
# journals a visit; it must never fire a chronicle read.
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TV_PORT"] = "17972"          # never collide with a live agent (17772 is HIS console)
import tv_diablo as tv
tv.JOURNAL = os.path.join(tempfile.gettempdir(), "tvd_visit_flush_journal.jsonl")  # never the real one


# His sequence, replayed frame for frame: one gameplay frame, then eight consecutive Chronicle
# frames on the Holy Grail (uniques) ledger, then the session ends.
GAMEPLAY_TS = 1786385770000
CHRON_TS = [1786385778600 + i * 1200 for i in range(8)]


class TestChronicleVisitFlush(unittest.TestCase):

    def setUp(self):
        # the live state machine, not a mock of it
        tv._CHRON_VISIT.update({"open": False, "ledger": "", "since": 0, "last": 0, "frames": []})
        self.rows = []
        self._j, self._ev = tv._journal, tv.ev
        tv._journal = lambda row: self.rows.append(dict(row))
        tv.ev = lambda *a, **k: None
        self.addCleanup(self._restore)

    def _restore(self):
        tv._journal, tv.ev = self._j, self._ev
        tv._CHRON_VISIT.update({"open": False, "ledger": "", "since": 0, "last": 0, "frames": []})

    def _replay_his_session(self):
        """gameplay → 8 × chronicle/uniques. Returns nothing; asserts the sequence journalled NOTHING."""
        tv._chron_visit_step("gameplay", "", frame_id="f_%d" % GAMEPLAY_TS, ts=GAMEPLAY_TS)
        for i, ts in enumerate(CHRON_TS):
            closed = tv._chron_visit_step("chronicle", "uniques", frame_id="f_%d" % ts, ts=ts)
            self.assertIsNone(closed, "frame %d ended a visit mid-scroll" % i)
        # ★ the BEFORE number, stated so the proof is not vacuous: 8 frames recorded, 0 rows written.
        self.assertEqual(len(self.rows), 0, "the live lane journalled a visit it never closed")
        now = tv.chron_visit_open()
        self.assertTrue(now["open"])
        self.assertEqual(now["ledger"], "uniques")
        self.assertEqual(now["frames"], 8)

    def test_the_visit_he_never_closed_is_journalled_at_session_end(self):
        self._replay_his_session()
        tv.chron_visit_flush()
        visits = [r for r in self.rows if r.get("lane") == "chronicle" and r.get("kind") == "visit"]
        self.assertEqual(len(visits), 1, "expected exactly ONE visit row, got %d" % len(visits))
        v = visits[0]
        self.assertEqual(v["ledger"], "uniques")
        self.assertEqual(v["n"], 8)
        self.assertEqual(v["frames"], ["f_%d" % t for t in CHRON_TS])
        self.assertEqual(v["since"], CHRON_TS[0])
        self.assertEqual(v["until"], CHRON_TS[-1])
        self.assertTrue(int(v["ts"]) > 0)

    def test_flushing_twice_journals_ONCE(self):
        self._replay_his_session()
        tv.chron_visit_flush()
        tv.chron_visit_flush()
        tv.chron_visit_flush()
        visits = [r for r in self.rows if r.get("kind") == "visit"]
        self.assertEqual(len(visits), 1, "the flush is not idempotent — %d rows" % len(visits))
        self.assertFalse(tv.chron_visit_open()["open"], "the visit is still open after a flush")

    def test_a_flush_with_no_visit_open_writes_nothing(self):
        tv._chron_visit_step("gameplay", "", frame_id="f_1", ts=GAMEPLAY_TS)
        self.assertIsNone(tv.chron_visit_flush())
        self.assertEqual(self.rows, [])

    def test_a_visit_with_zero_frames_is_not_journalled(self):
        # a panel that flickered open with no frame recorded has no honest number to show
        tv._chron_visit_step("chronicle", "uniques", frame_id=None, ts=CHRON_TS[0])
        self.assertIsNone(tv.chron_visit_flush())
        self.assertEqual(self.rows, [])
        self.assertFalse(tv.chron_visit_open()["open"])

    def test_the_row_is_the_SAME_SHAPE_the_live_seam_writes(self):
        # /api/chronicle_visits filters on lane+kind; the console reads ledger/n/since/until/frames
        self._replay_his_session()
        tv.chron_visit_flush()
        v = self.rows[0]
        self.assertEqual(sorted(v.keys()),
                         sorted(["lane", "kind", "ts", "ledger", "frames", "n", "since", "until"]))
        json.dumps(v)   # a journal row must be serialisable or the seal drops it


class TestFlushIsWiredIntoTheCloseSeam(unittest.TestCase):
    """The function existing is not the fix — being CALLED at session close is the fix."""

    def test_close_session_flushes_the_visit_before_it_seals(self):
        import inspect
        src = inspect.getsource(tv.close_session)
        self.assertIn("chron_visit_flush", src, "close_session never flushes the open visit")
        self.assertLess(src.index("chron_visit_flush"), src.index('"session_end"'),
                        "the visit is flushed after session_end — it lands outside its own session")

    def test_the_flush_never_fires_a_chronicle_READ(self):
        # ★ the money question, same one test_agent.py asks of the live seam: recording is free,
        # reading is offered. A flush that read would spend his subscription at every session end.
        import inspect
        # grep the CODE, not the prose: the docstring names both readers to say it never calls
        # them, and an assertion that cannot tell a comment from a call is not an assertion.
        parts = inspect.getsource(tv.chron_visit_flush).split('"""')
        self.assertEqual(len(parts), 3, "flush source is not def+docstring+body — re-read it")
        body = parts[2]
        self.assertNotIn("claude_chronicle_read", body)
        self.assertNotIn("g5_chronicle_read", body)
        self.assertIn("ask the console to read it", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
